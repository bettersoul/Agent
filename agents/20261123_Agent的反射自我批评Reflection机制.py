"""
Agent 的反射/自我批评（Reflection）机制
Auto-generated module skeleton.
"""

"""Agent 反射/自我批评机制模块。

日期: 2026-11-23
提供 ReflectionEngine，用于对 Agent 的输出进行自我批评并生成改进建议。
"""

from dataclasses import dataclass, field
from typing import Callable, List, Optional


def llm_call(prompt: str) -> str:
    """占位 LLM 调用函数，真实环境中替换为模型接口。"""
    return "反思: 输出未覆盖边界条件，建议补充异常处理。"


@dataclass
class Reflection:
    """一次反射的批评结果与改进建议。"""

    critique: str
    suggestions: List[str] = field(default_factory=list)
    score: float = 0.0


class ReflectionEngine:
    """Agent 自我批评引擎。

    对一次 Agent 输出执行反射评估：生成批评、提取建议、计算质量分，
    并可通过多轮反射逐步改进输出。
    """

    def __init__(self, max_rounds: int = 2, generator: Optional[Callable[[str], str]] = None) -> None:
        self.max_rounds: int = max_rounds
        self._gen: Callable[[str], str] = generator or llm_call

    def _build_prompt(self, task: str, output: str, history: List[Reflection]) -> str:
        ctx = "\n".join(f"第{i+1}轮: {r.critique}" for i, r in enumerate(history))
        return f"任务: {task}\n输出: {output}\n历史批评:\n{ctx}\n请批评并给出建议。"

    def reflect(self, task: str, output: str) -> Reflection:
        """单轮反射，返回批评与建议。"""
        raw = self._gen(self._build_prompt(task, output, []))
        suggestions = [s.strip() for s in raw.split("；") if s.strip()]
        score = min(1.0, 0.4 + 0.1 * len(suggestions))
        return Reflection(critique=raw, suggestions=suggestions, score=score)

    def improve(self, task: str, output: str) -> tuple[str, List[Reflection]]:
        """多轮反射迭代，返回最终输出与反射记录列表。"""
        history: List[Reflection] = []
        current = output
        for _ in range(self.max_rounds):
            r = self.reflect(task, current)
            history.append(r)
            if r.score >= 0.8:
                break
            current = f"{current}\n# 改进: {'; '.join(r.suggestions)}"
        return current, history


if __name__ == "__main__":
    engine = ReflectionEngine(max_rounds=3)
    final, records = engine.improve("实现一个排序函数", "def sort(xs): return xs")
    for i, rec in enumerate(records, 1):
        print(f"[轮次 {i}] 分数={rec.score:.2f} 批评={rec.critique}")
    print("最终输出:\n", final)
