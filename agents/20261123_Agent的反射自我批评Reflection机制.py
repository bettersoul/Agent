"""
Agent 的反射/自我批评（Reflection）机制
Auto-generated module skeleton.
"""

"""Agent 反射/自我批评机制，2026-11-23。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List, Optional


def llm(prompt: str) -> str:
    """占位 LLM 调用：返回模拟的批评意见。"""
    return f"[critique] 针对输入给出的改进建议: {prompt[:30]}"


@dataclass
class ReflectionRecord:
    """一次反射迭代的记录。"""
    attempt: int
    answer: str
    critique: str
    score: float


class ReflexiveAgent:
    """带反射机制的 Agent：产出答案后自我批评并迭代改进。"""

    def __init__(self, solve: Callable[[str], str], judge: Callable[[str, str], float],
                 max_rounds: int = 3, threshold: float = 0.8) -> None:
        self._solve = solve
        self._judge = judge
        self.max_rounds = max_rounds
        self.threshold = threshold
        self.history: List[ReflectionRecord] = []

    def _reflect(self, question: str, answer: str) -> str:
        """生成针对当前答案的批评意见。"""
        return llm(f"问题: {question}\n答案: {answer}")

    def run(self, question: str) -> str:
        """执行解题-反思循环，返回最终答案。"""
        answer = self._solve(question)
        for i in range(1, self.max_rounds + 1):
            score = self._judge(question, answer)
            critique = self._reflect(question, answer)
            self.history.append(ReflectionRecord(i, answer, critique, score))
            if score >= self.threshold:
                break
            answer = self._solve(f"{question}\n改进建议: {critique}")
        return answer


if __name__ == '__main__':
    def solve(q: str) -> str:
        return f"根据问题生成答案 -> {q.splitlines()[0]}"

    def judge(q: str, a: str) -> float:
        return min(1.0, 0.3 + 0.15 * a.count("改进"))

    agent = ReflexiveAgent(solve, judge, max_rounds=2)

    class _Demo(ReflexiveAgent):
        def _reflect(self, question: str, answer: str) -> str:
            return "改进：补充关键细节并精简表述"

    demo = _Demo(solve, judge, max_rounds=2)
    final = demo.run("如何提升 Agent 的可靠性？")
    print("最终答案:", final)
    for rec in demo.history:
        print(f"轮次{rec.attempt} 分数={rec.score:.2f} 批评={rec.critique}")
