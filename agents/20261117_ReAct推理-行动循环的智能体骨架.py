"""
AI Agent 每日代码 · 2026-11-17
主题：ReAct 推理-行动循环的智能体骨架
由 agent-green 自动生成。
"""

"""ReAct 推理-行动循环智能体骨架，日期标记：2026-11-17。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Protocol, Union


@dataclass
class Message:
    """对话消息。"""

    role: str
    content: str


@dataclass
class Action:
    """模型提出的行动。"""

    name: str
    args: Dict[str, object] = field(default_factory=dict)


@dataclass
class Observation:
    """行动执行后返回的观察结果。"""

    action: Action
    content: str


class LLM(Protocol):
    """通用大模型接口占位。"""

    def __call__(self, messages: List[Message]) -> str:
        ...


class Agent:
    """执行“思考 -> 行动 -> 观察”循环的最小智能体。"""

    def __init__(
        self,
        llm: LLM,
        tools: Dict[str, Callable[..., str]],
        max_steps: int = 6,
    ) -> None:
        self.llm = llm
        self.tools = tools
        self.max_steps = max_steps
        self.messages: List[Message] = []

    def think(self) -> Action:
        """调用模型并解析其 JSON 行动。"""
        import json

        raw = self.llm(self.messages)
        try:
            data = json.loads(raw)
            return Action(name=data["name"], args=data.get("args", {}))
        except (ValueError, KeyError, TypeError) as exc:
            raise ValueError(f"模型未返回合法行动 JSON：{raw!r}") from exc

    def act(self, action: Action) -> str:
        """执行工具；未知工具或参数错误均转为观察文本。"""
        tool = self.tools.get(action.name)
        if tool is None:
            return f"错误：不存在工具 {action.name}"
        try:
            return str(tool(**action.args))
        except Exception as exc:
            return f"错误：行动 {action.name} 执行失败：{exc}"

    def run(self, task: str) -> str:
        """运行完整 ReAct 循环并返回最终答案。"""
        self.messages = [Message("user", task)]
        for _ in range(self.max_steps):
            action = self.think()
            result = self.act(action)
            observation = Observation(action, result)
            self.messages.extend(
                [
                    Message("assistant", repr(action)),
                    Message("observation", observation.content),
                ]
            )
            if action.name == "finish":
                return result
        return "已达到最大步数，任务未完成。"


def echo(text: str = "") -> str:
    """演示工具：回显输入。"""
    return text


def demo_llm(messages: List[Message]) -> str:
    """演示模型：第一次调用工具，第二次结束。"""
    if any(message.role == "observation" for message in messages):
        return '{"name": "finish", "args": {"answer": "任务已完成"}}'
    return '{"name": "echo", "args": {"text": "正在执行 ReAct"}}'


def main() -> None:
    """演示入口。"""
    agent = Agent(llm=demo_llm, tools={"echo": echo, "finish": echo})
    print(agent.run("演示一个 ReAct 智能体"))


if __name__ == "__main__":
    main()
