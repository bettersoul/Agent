"""
规划器 Planner：把目标拆解为子任务
Auto-generated module skeleton.
"""

"""规划器 Planner：把目标拆解为子任务。日期标记 2026-11-26。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List


@dataclass
class SubTask:
    """拆解后的子任务。"""
    index: int
    description: str
    done: bool = False
    result: str = ""


def _default_llm(prompt: str) -> str:
    """占位 LLM 调用：返回按行分隔的子任务描述。"""
    return f"子任务A(来自:{prompt})\n子任务B\n子任务C"


class Planner:
    """把高层目标拆解为有序子任务并逐步执行。

    - split: 调用 LLM 生成子任务
    - execute: 依次执行未完成子任务
    """

    def __init__(self, llm: Callable[[str], str] | None = None) -> None:
        self.llm = llm or _default_llm
        self.tasks: List[SubTask] = []

    def split(self, goal: str) -> List[SubTask]:
        """将目标拆解为子任务列表。"""
        raw = self.llm(f"请将目标拆解为子任务：{goal}")
        lines = [line.strip() for line in raw.splitlines() if line.strip()]
        self.tasks = [SubTask(i, text) for i, text in enumerate(lines)]
        return self.tasks

    def execute(self, executor: Callable[[SubTask], str] | None = None) -> List[SubTask]:
        """按顺序执行子任务，返回全部任务状态。"""
        executor = executor or (lambda t: f"完成:{t.description}")
        for task in self.tasks:
            if task.done:
                continue
            task.result = executor(task)
            task.done = True
        return self.tasks

    def summary(self) -> str:
        """生成执行摘要。"""
        total = len(self.tasks)
        done = sum(t.done for t in self.tasks)
        return f"共 {total} 个子任务，已完成 {done} 个。"


if __name__ == "__main__":
    planner = Planner()
    for task in planner.split("搭建一个 AI Agent 框架"):
        print(f"[{task.index}] {task.description}")
    planner.execute()
    print(planner.summary())
    for task in planner.tasks:
        print(f"  {task.description} -> {task.result}")
