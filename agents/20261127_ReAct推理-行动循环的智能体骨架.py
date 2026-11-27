"""
ReAct 推理-行动循环的智能体骨架
Auto-generated module skeleton.
"""

"""ReAct 推理-行动循环智能体骨架。日期：2026-11-27"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional


def llm_complete(prompt: str) -> str:
    """占位 LLM 接口：真实实现替换为模型调用。"""
    return "Thought: 我需要计算 2+3\nAction: calc\nAction Input: 2+3"


@dataclass
class Step:
    """单步推理-行动记录。"""
    thought: str
    action: Optional[str] = None
    action_input: Optional[str] = None
    observation: Optional[str] = None


class ReActAgent:
    """ReAct 智能体：交替进行推理（Thought）与行动（Action），直到得出最终答案。"""

    def __init__(self, tools: Dict[str, Callable[[str], str]], max_steps: int = 5) -> None:
        self.tools = tools
        self.max_steps = max_steps
        self.trace: List[Step] = []

    def _parse(self, text: str) -> Dict[str, str]:
        """从 LLM 输出中解析 Thought / Action / Action Input / Final Answer。"""
        fields: Dict[str, str] = {}
        for key in ("Thought", "Action", "Action Input", "Final Answer"):
            m = re.search(rf"{key}:\s*(.+)", text)
            if m:
                fields[key] = m.group(1).strip()
        return fields

    def _dispatch(self, action: str, arg: str) -> str:
        """执行工具调用并捕获异常。"""
        tool = self.tools.get(action)
        if tool is None:
            return f"错误：未知工具 {action}，可用工具：{list(self.tools)}"
        try:
            return tool(arg)
        except Exception as exc:  # noqa: BLE001
            return f"错误：工具执行失败 {exc}"

    def run(self, question: str) -> str:
        """执行完整 ReAct 循环，返回最终答案。"""
        history: List[str] = [f"Question: {question}"]
        for _ in range(self.max_steps):
            parsed = self._parse(llm_complete("\n".join(history)))
            step = Step(thought=parsed.get("Thought", ""))
            if "Final Answer" in parsed:
                step.observation = parsed["Final Answer"]
                self.trace.append(step)
                return parsed["Final Answer"]
            action, arg = parsed.get("Action"), parsed.get("Action Input", "")
            step.action, step.action_input = action, arg
            step.observation = self._dispatch(action, arg) if action else "错误：缺少 Action"
            self.trace.append(step)
            history += [f"Thought: {step.thought}", f"Action: {action}",
                        f"Action Input: {arg}", f"Observation: {step.observation}"]
        return "达到最大步数仍未得出结论。"


if __name__ == "__main__":
    agent = ReActAgent(tools={"calc": lambda expr: str(eval(expr, {"__builtins__": {}}))})  # noqa: S307
    print(agent.run("2+3 等于多少？"))
    for i, s in enumerate(agent.trace, 1):
        print(f"步骤 {i}: {s}")
