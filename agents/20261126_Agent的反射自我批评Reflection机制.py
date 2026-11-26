"""
Agent 的反射/自我批评（Reflection）机制
Auto-generated module skeleton.
"""

"""Agent 反射/自我批评机制（Reflection），支持生成批判并迭代改进答案。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List, Optional

# LLM 占位接口：输入提示词返回文本，实际使用时替换为真实模型调用
LLM = Callable[[str], str]


@dataclass
class ReflectionRecord:
    """单轮反思记录。"""
    attempt: int
    answer: str
    critique: str
    score: float


@dataclass
class ReflectiveAgent:
    """带反射机制的 Agent。

    流程：给出初稿 -> 自我批评打分 -> 若未达标则依据批评重写。
    """

    llm: LLM
    threshold: float = 0.8
    max_rounds: int = 3
    history: List[ReflectionRecord] = field(default_factory=list)

    def _critique(self, question: str, answer: str) -> tuple[str, float]:
        """生成批评文本与评分（0~1）。"""
        raw = self.llm(f"批判以下回答的问题与缺陷，并给出0-1分数：\nQ:{question}\nA:{answer}")
        try:
            score = float(raw.strip().splitlines()[-1])
        except (ValueError, IndexError):
            score = 0.5
        return raw, max(0.0, min(1.0, score))

    def _revise(self, question: str, answer: str, critique: str) -> str:
        """依据批评重写答案。"""
        return self.llm(f"Q:{question}\n原回答:{answer}\n批评:{critique}\n请改进：")

    def run(self, question: str) -> str:
        """执行带反射的求解，返回最终答案。"""
        answer = self.llm(f"回答：{question}")
        for i in range(1, self.max_rounds + 1):
            critique, score = self._critique(question, answer)
            self.history.append(ReflectionRecord(i, answer, critique, score))
            if score >= self.threshold:
                return answer
            answer = self._revise(question, answer, critique)
        return answer


def _demo_llm(prompt: str) -> str:
    """演示用占位 LLM：模拟逐步改进。"""
    if "批判" in prompt:
        return "回答过于笼统，缺少例子。\n0.6" if "1." not in prompt else "较好。\n0.9"
    if "改进" in prompt:
        return "1. 补充具体示例后再作答。"
    return "初始草稿答案。"


if __name__ == "__main__":
    agent = ReflectiveAgent(llm=_demo_llm)
    result = agent.run("如何设计可靠的 Agent？")
    print("最终答案:", result)
    for r in agent.history:
        print(f"轮次{r.attempt} 评分={r.score:.2f} 批评={r.critique!r}")
