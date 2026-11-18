"""
规划器 Planner：把目标拆解为子任务
Auto-generated module skeleton.
"""

"""Planner 模块：把目标拆解为子任务（2026-11-18）。

提供将高层目标按规则或 LLM 拆解为有序子任务的规划器。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Iterable


def llm_plan(prompt: str) -> list[str]:
    """占位 LLM 调用：真实实现应返回拆解后的子任务文本列表。"""
    return [f"step-{i}" for i in range(1, 4)]


@dataclass
class Task:
    """单个子任务。"""

    name: str
    depends_on: list[int] = field(default_factory=list)
    done: bool = False


class Planner:
    """将目标拆解为子任务的规划器。

    支持注入自定义拆解函数（如 LLM），否则使用内置启发式规则。
    """

    def __init__(self, splitter: Callable[[str], Iterable[str]] | None = None) -> None:
        self._splitter = splitter or self._default_split

    @staticmethod
    def _default_split(goal: str) -> list[str]:
        """启发式拆解：按分句/连接词切分，否则生成三段式模板。"""
        for sep in ("然后", "接着", "，", ",", "；", ";"):
            if sep in goal:
                parts = [p.strip() for p in goal.split(sep) if p.strip()]
                if len(parts) > 1:
                    return parts
        return [f"分析目标：{goal}", f"执行核心步骤：{goal}", f"验证结果：{goal}"]

    def plan(self, goal: str) -> list[Task]:
        """为给定目标生成带顺序依赖的子任务列表。"""
        names = list(self._splitter(goal))
        return [
            Task(name=n, depends_on=[i - 1] if i > 0 else [])
            for i, n in enumerate(names)
        ]

    @staticmethod
    def next_runnable(tasks: list[Task]) -> Task | None:
        """返回下一个可执行任务（依赖已完成且自身未完成）。"""
        done = {i for i, t in enumerate(tasks) if t.done}
        for i, t in enumerate(tasks):
            if not t.done and all(d in done for d in t.depends_on):
                return t
        return None

    @staticmethod
    def execute(tasks: list[Task]) -> list[str]:
        """按依赖顺序模拟执行，返回执行顺序。"""
        order: list[str] = []
        while (task := Planner.next_runnable(tasks)) is not None:
            task.done = True
            order.append(task.name)
        return order


if __name__ == "__main__":
    goal = "准备季度报告，然后收集数据，接着撰写初稿"
    planner = Planner()
    tasks = planner.plan(goal)
    print("子任务：", [t.name for t in tasks])
    print("执行顺序：", Planner.execute(tasks))

    llm_tasks = Planner(splitter=llm_plan).plan("发布新版本")
    print("LLM 拆解：", [t.name for t in llm_tasks])
