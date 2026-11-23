"""
Agent 的反射/自我批评（Reflection）机制
Auto-generated module skeleton.
"""

"""Agent 反射/自我批评机制（Reflection）模块。日期：2026-11-23。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List, Optional


def _placeholder_llm(prompt: str) -> str:
    """占位 LLM 调用：真实环境中替换为实际模型接口。"""
    return f"[feedback] 针对输入的分析已完成（长度={len(prompt)}）。"


@dataclass
class ReflectionStep:
    """单次反思的产物：批评文本与可选的改进建议。"""

    critique: str
    revision: Optional[str] = None


class Reflector:
    """基于批评-修订循环的 Agent 反射器。

    通过 ``llm`` 可选注入生成函数（默认用占位实现），
    对初始输出做最多 ``max_rounds`` 轮自我批评，并收敛到稳定结果。
    """

    def __init__(
        self,
        llm: Optional[Callable[[str], str]] = None,
        max_rounds: int = 2,
    ) -> None:
        self.llm: Callable[[str], str] = llm or _placeholder_llm
        self.max_rounds = max(1, max_rounds)
        self.history: List[ReflectionStep] = []

    def _critique(self, task: str, output: str) -> str:
        """生成针对当前输出的批评。"""
        prompt = (
            f"任务：{task}\n当前输出：{output}\n"
            "请指出不足并给出具体改进方向。"
        )
        return self.llm(prompt)

    def _revise(self, output: str, critique: str) -> str:
        """依据批评修订输出。"""
        prompt = f"原输出：{output}\n批评：{critique}\n请给出修订后的输出。"
        return self.llm(prompt)

    def run(self, task: str, initial_output: str) -> str:
        """执行反射循环，返回最终输出；收敛或达到轮数上限即停止。"""
        self.history.clear()
        current = initial_output
        for _ in range(self.max_rounds):
            critique = self._critique(task, current)
            revised = self._revise(current, critique)
            self.history.append(ReflectionStep(critique=critique, revision=revised))
            if revised.strip() == current.strip():
                break
            current = revised
        return current

    @property
    def rounds(self) -> int:
        """已执行的反思轮数。"""
        return len(self.history)


if __name__ == '__main__':
    reflector = Reflector(max_rounds=3)
    result = reflector.run("总结一篇技术文章", "文章讲了 Agent 架构。")
    print(f"轮数: {reflector.rounds}")
    for i, step in enumerate(reflector.history, 1):
        print(f"第{i}轮批评: {step.critique}")
        print(f"第{i}轮修订: {step.revision}")
    print(f"最终输出: {result}")
