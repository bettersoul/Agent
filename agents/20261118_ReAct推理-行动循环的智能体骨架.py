"""
ReAct 推理-行动循环的智能体骨架
Auto-generated module skeleton.
"""

"""ReAct 推理-行动循环的智能体骨架（2026-11-18）。"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Tuple


def llm_call(prompt: str) -> str:
    """占位 LLM 调用：真实实现应由外部模型替换。"""
    return "Thought: 我需要查询天气\nAction: get_weather\nAction Input: 北京"


@dataclass
class Step:
    """单步 ReAct 记录。"""
    thought: str
    action: Optional[str] = None
    action_input: Optional[str] = None
    observation: Optional[str] = None
    final: Optional[str] = None


class ReActAgent:
    """ReAct 智能体：交替进行推理与行动，直到给出最终答案。"""

    _PATTERN = re.compile(
        r"Thought:\s*(?P<thought>.*?)\n"
        r"(?:Action:\s*(?P<action>.*?)\nAction Input:\s*(?P<action_input>.*?)"
        r"|Final Answer:\s*(?P<final>.*))",
        re.S,
    )

    def __init__(
        self,
        tools: Dict[str, Callable[[str], str]],
        llm: Callable[[str], str] = llm_call,
        max_steps: int = 5,
    ) -> None:
        self.tools = tools
        self.llm = llm
        self.max_steps = max_steps
        self.history: List[Step] = []

    def _build_prompt(self, question: str) -> str:
        """拼接包含历史轨迹的提示词。"""
        trace = "".join(
            f"Thought: {s.thought}\n"
            + (f"Action: {s.action}\nAction Input: {s.action_input}\nObservation: {s.observation}\n" if s.action else "")
            + (f"Final Answer: {s.final}\n" if s.final else "")
            for s in self.history
        )
        return f"Question: {question}\n{trace}"

    def _parse(self, text: str) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
        """解析 LLM 输出为 (thought, action, action_input, final)。"""
        m = self._PATTERN.search(text)
        if not m:
            return text.strip(), None, None, None
        return (
            (m.group("thought") or "").strip(),
            (m.group("action") or "").strip() or None,
            (m.group("action_input") or "").strip() or None,
            (m.group("final") or "").strip() or None,
        )

    def _act(self, action: str, action_input: str) -> str:
        """执行工具调用并返回观察结果。"""
        tool = self.tools.get(action)
        if tool is None:
            return f"错误：未知工具 {action}"
        try:
            return str(tool(action_input))
        except Exception as exc:  # 保证循环不中断
            return f"工具执行异常：{exc}"

    def run(self, question: str) -> str:
        """运行推理-行动循环，返回最终答案或超步提示。"""
        self.history.clear()
        for _ in range(self.max_steps):
            thought, action, action_input, final = self._parse(self.llm(self._build_prompt(question)))
            step = Step(thought=thought)
            if final is not None:
                step.final = final
                self.history.append(step)
                return final
            if action and action_input is not None:
                step.action, step.action_input = action, action_input
                step.observation = self._act(action, action_input)
                self.history.append(step)
            else:
                self.history.append(step)
        return "达到最大步数，未能得出最终答案。"


def _demo_weather(city: str) -> str:
    """示例工具：返回固定天气。"""
    return f"{city}：晴，22℃"


if __name__ == "__main__":
    agent = ReActAgent(tools={"get_weather": _demo_weather})
    print(agent.run("北京天气如何？"))
    for i, s in enumerate(agent.history, 1):
        print(i, s)
