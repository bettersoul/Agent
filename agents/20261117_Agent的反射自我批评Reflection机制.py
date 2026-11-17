"""
每日自动生成代码 · 2026-11-17
主题：Agent 的反射/自我批评（Reflection）机制
由 agent-green 自动生成。
"""

"""Agent 反射与自我批评机制示例（2026-11-17）。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Iterable


@dataclass
class Critique:
    """一次自我批评的结果。"""

    issues: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)
    score: float = 0.0


class ReflectionAgent:
    """通过执行、批评和修订三个阶段改进输出。"""

    def __init__(
        self,
        solver: Callable[[str, int], str],
        critic: Callable[[str, str], Critique],
        max_iterations: int = 3,
    ) -> None:
        self.solver = solver
        self.critic = critic
        self.max_iterations = max_iterations

    def reflect(self, task: str) -> tuple[str, list[Critique]]:
        """执行任务并迭代反思，返回最佳答案和批评历史。"""
        history: list[Critique] = []
        answer = ""
        best_score = float("-inf")

        for iteration in range(self.max_iterations):
            answer = self.solver(task, iteration)
            critique = self.critic(task, answer)
            history.append(critique)

            if critique.score > best_score:
                best_score = critique.score
                best_answer = answer

            if critique.score >= 9.0:
                break

            answer = self._revise(answer, critique)

        return best_answer, history

    @staticmethod
    def _revise(answer: str, critique: Critique) -> str:
        """根据批评意见拼接修订指令，作为下一轮求解上下文。"""
        advice = "；".join(critique.suggestions)
        return f"{answer}\n[请根据以下意见改进：{advice}]"


def mock_solver(task: str, iteration: int) -> str:
    """模拟求解器：迭代次数越高，输出越完整。"""
    return f"{task}｜迭代版本={iteration + 1}"


def mock_critic(task: str, answer: str) -> Critique:
    """模拟批评器：根据答案中的迭代版本评分。"""
    version = int(answer.rsplit("=", 1)[-1])
    return Critique(
        issues=[] if version >= 3 else ["缺少细节"],
        suggestions=["补充结构化说明" if version < 3 else "保持简洁"],
        score=min(10.0, 3.0 + version * 2.0),
    )


def main() -> None:
    """演示反射流程。"""
    agent = ReflectionAgent(mock_solver, mock_critic)
    answer, history = agent.reflect("解释 Agent 的反思机制")

    print("最终答案：", answer)
    print("批评轮次：", len(history))
    for index, critique in enumerate(history, 1):
        print(
            f"第 {index} 轮："
            f"评分={critique.score:.1f}，"
            f"问题={critique.issues or '无'}，"
            f"建议={critique.suggestions or '无'}"
        )


if __name__ == "__main__":
    main()
