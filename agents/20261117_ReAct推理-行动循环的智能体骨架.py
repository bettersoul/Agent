"""
每日自动生成代码 · 2026-11-17
主题：ReAct 推理-行动循环的智能体骨架
由 agent-green 自动生成。
"""

"""ReAct 推理-行动循环智能体骨架。日期标记：2026-11-17。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Protocol


class LanguageModel(Protocol):
    """根据消息生成文本的通用模型接口。"""

    def __call__(self, messages: list[dict[str, str]]) -> str:
        ...


@dataclass
class AgentConfig:
    """智能体运行配置。"""

    max_steps: int = 8
    system_prompt: str = (
        "你是一个 ReAct 智能体。请严格使用以下格式：\n"
        "Thought: 你的推理\n"
        "Action: 工具名称\n"
        "Action Input: JSON 参数\n"
        "Observation: 工具结果\n"
        "最终答案请使用 Final Answer: 前缀。"
    )


@dataclass
class Tool:
    """可调用工具及其描述。"""

    name: str
    description: str
    func: Callable[[dict], object]
    schema: dict[str, str] = field(default_factory=dict)


@dataclass
class Step:
    """一次 ReAct 循环记录。"""

    thought: str
    action: str | None = None
    action_input: dict | None = None
    observation: object | None = None
    final_answer: str | None = None


class ReActAgent:
    """驱动“推理—行动—观察”循环，直到得到答案或达到步数限制。"""

    def __init__(
        self,
        model: LanguageModel,
        tools: list[Tool] | None = None,
        config: AgentConfig | None = None,
    ) -> None:
        self.model = model
        self.config = config or AgentConfig()
        self.tools = {tool.name: tool for tool in (tools or [])}
        self.history: list[dict[str, str]] = []
        self.steps: list[Step] = []

    def run(self, task: str) -> str:
        """执行任务并返回最终答案。"""
        self.history = [{"role": "user", "content": task}]
        self.steps = []

        for _ in range(self.config.max_steps):
            response = self.model(self._build_messages())
            parsed = self._parse_response(response)
            step = Step(
                thought=parsed["thought"],
                action=parsed.get("action"),
                action_input=parsed.get("action_input"),
            )
            self.steps.append(step)

            if parsed.get("final_answer") is not None:
                step.final_answer = parsed["final_answer"]
                self.history.append({"role": "assistant", "content": response})
                return parsed["final_answer"]

            if not step.action:
                raise ValueError("模型输出必须包含 Action 或 Final Answer。")
            if step.action not in self.tools:
                observation: object = f"错误：不存在工具 {step.action}"
            else:
                try:
                    observation = self.tools[step.action].func(step.action_input or {})
                except Exception as exc:
                    observation = f"工具执行失败：{exc}"

            step.observation = observation
            self.history.append({"role": "assistant", "content": response})
            self.history.append(
                {"role": "user", "content": f"Observation: {observation}"}
            )

        raise RuntimeError(f"达到最大步数：{self.config.max_steps}")

    def _build_messages(self) -> list[dict[str, str]]:
        """构建模型消息，附带可用工具说明。"""
        tool_text = "\n".join(
            f"- {tool.name}: {tool.description}; 参数 schema={tool.schema}"
            for tool in self.tools.values()
        )
        system = self.config.system_prompt
        if tool_text:
            system += "\n可用工具：\n" + tool_text
        return [{"role": "system", "content": system}, *self.history]

    @staticmethod
    def _parse_response(text: str) -> dict:
        """解析结构化 ReAct 文本，也兼容简单 Action 行。"""
        result: dict = {"thought": "", "final_answer": None}
        lines = text.splitlines()
        action: str | None = None
        action_input: dict = {}

        for line in lines:
            stripped = line.strip()
            if stripped.startswith("Thought:"):
                result["thought"] = stripped[8:].strip()
            elif stripped.startswith("Final Answer:"):
                result["final_answer"] = stripped[13:].strip()
            elif stripped.startswith("Action:"):
                action = stripped[7:].strip()
            elif stripped.startswith("Action Input:"):
                raw = stripped[13:].strip()
                try:
                    import json

                    action_input = json.loads(raw) if raw else {}
                except ValueError:
                    action_input = {"input": raw}

        if action:
            result["action"] = action
            result["action_input"] = action_input
        return result


def demo_model(messages: list[dict[str, str]]) -> str:
    """占位模型：演示一次工具调用和最终回答。"""
    if any("Observation:" in item["content"] for item in messages):
        return "Thought: 已获得工具结果\nFinal Answer: 今天适合安排一次户外活动。"
    return (
        "Thought: 我需要查询天气。\n"
        "Action: get_weather\n"
        'Action Input: {"city": "北京"}'
    )


def get_weather(arguments: dict) -> str:
    """示例天气工具。"""
    city = arguments.get("city", "未知城市")
    return f"{city}晴，25°C"


if __name__ == "__main__":
    agent = ReActAgent(
        model=demo_model,
        tools=[
            Tool(
                name="get_weather",
                description="查询指定城市的天气",
                func=get_weather,
                schema={"city": "string"},
            )
        ],
    )
    print(agent.run("北京今天的天气如何？"))
