"""
ReAct 推理-行动循环的智能体骨架
Auto-generated module skeleton.
"""

"""ReAct 推理-行动循环智能体骨架 (2026-11-19)。"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional


@dataclass
class Step:
    """单轮循环记录。"""
    thought: str
    action: Optional[str] = None
    action_input: Optional[str] = None
    observation: Optional[str] = None


@dataclass
class ReActAgent:
    """ReAct 智能体：交替进行推理(Thought)与行动(Action)直至给出最终答案。

    llm: 占位 LLM 函数，接收 prompt 字符串返回文本。
    tools: 工具名到可调用对象的映射。
    max_steps: 最大循环轮数，防止无限循环。
    """

    llm: Callable[[str], str]
    tools: Dict[str, Callable[[str], str]]
    max_steps: int = 5
    history: List[Step] = field(default_factory=list)

    def _build_prompt(self, question: str) -> str:
        """构造 ReAct 提示词，包含工具列表与历史轨迹。"""
        tool_desc = "\n".join(f"- {name}: {fn.__doc__ or ''}" for name, fn in self.tools.items())
        trace = "\n".join(
            f"Thought: {s.thought}\nAction: {s.action}\nAction Input: {s.action_input}\nObservation: {s.observation}"
            for s in self.history
        )
        return (
            f"可用工具:\n{tool_desc}\n\n问题: {question}\n{trace}\n"
            "请输出 Thought 与 Action，或给出 Final Answer。"
        )

    @staticmethod
    def _parse(text: str) -> Dict[str, str]:
        """从 LLM 输出中解析 Thought / Action / Action Input。"""
        def grab(key: str) -> Optional[str]:
            m = re.search(rf"{key}\s*:\s*(.+)", text)
            return m.group(1).strip() if m else None

        return {
            "thought": grab("Thought") or "",
            "action": grab("Action") or "",
            "action_input": grab("Action Input") or "",
            "final": grab("Final Answer") or "",
        }

    def run(self, question: str) -> str:
        """执行 ReAct 循环并返回最终答案或兜底信息。"""
        for _ in range(self.max_steps):
            parsed = self._parse(self.llm(self._build_prompt(question)))
            if parsed["final"]:
                return parsed["final"]
            action, arg = parsed["action"], parsed["action_input"]
            if action in self.tools:
                try:
                    obs = self.tools[action](arg)
                except Exception as exc:  # 工具异常转为观察结果
                    obs = f"工具执行失败: {exc}"
            else:
                obs = f"未知工具: {action}"
            self.history.append(Step(parsed["thought"], action, arg, obs))
        return "达到最大步数仍未得出结论。"


def _fake_llm(prompt: str) -> str:
    """占位 LLM：首轮调用搜索工具，拿到观察后给出最终答案。"""
    if "Observation:" not in prompt:
        return "Thought: 需要查询天气\nAction: weather\nAction Input: 北京"
    return "Thought: 已获得结果\nFinal Answer: " + prompt.split("Observation:")[-1].split("\n")[0].strip()


def _weather(city: str) -> str:
    """查询城市天气（模拟）。"""
    return f"{city} 晴，25℃"


if __name__ == "__main__":
    agent = ReActAgent(llm=_fake_llm, tools={"weather": _weather})
    print(agent.run("北京天气如何？"))
    for i, s in enumerate(agent.history, 1):
        print(f"[{i}] {s.thought} | {s.action}({s.action_input}) -> {s.observation}")
