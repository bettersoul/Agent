"""
每日自动生成代码 · 2026-11-17
主题：Agent 任务调度与优先级队列
由 agent-green 自动生成。
"""

"""Agent 任务调度与优先级队列示例，日期标记：2026-11-17。"""

from __future__ import annotations

import heapq
import itertools
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Optional


@dataclass(order=True)
class Task:
    """可调度的 Agent 任务。"""

    priority: int
    name: str = field(compare=False)
    payload: Any = field(compare=False, default=None)
    sequence: int = field(compare=False, default=0)


class AgentScheduler:
    """基于优先级的任务调度器；数值越小，优先级越高。"""

    def __init__(self, worker: Optional[Callable[[Task], Any]] = None) -> None:
        """初始化调度器及可选任务执行函数。"""
        self._queue: list[Task] = []
        self._counter = itertools.count()
        self._worker = worker
        self._tasks: dict[str, Task] = {}

    def submit(self, name: str, priority: int = 100, payload: Any = None) -> Task:
        """提交任务并返回任务对象。"""
        task = Task(priority=priority, name=name, payload=payload, sequence=next(self._counter))
        heapq.heappush(self._queue, task)
        self._tasks[name] = task
        return task

    def cancel(self, name: str) -> bool:
        """标记任务取消；任务尚未执行时有效。"""
        task = self._tasks.get(name)
        if task is None or task.sequence < 0:
            return False
        task.sequence = -1
        return True

    def run(self, interval: float = 0.0) -> list[Any]:
        """按优先级顺序执行任务，并返回执行结果列表。"""
        results: list[Any] = []
        while self._queue:
            task = heapq.heappop(self._queue)
            if task.sequence < 0:
                continue
            if self._worker is None:
                results.append(task.payload)
            else:
                results.append(self._worker(task))
            if interval > 0:
                time.sleep(interval)
        return results


def demo_worker(task: Task) -> str:
    """演示任务执行逻辑。"""
    return f"执行 {task.name}，优先级={task.priority}，数据={task.payload}"


def main() -> None:
    """运行调度演示。"""
    scheduler = AgentScheduler(worker=demo_worker)
    scheduler.submit("低优先级", priority=90, payload="普通任务")
    scheduler.submit("高优先级", priority=10, payload="紧急任务")
    scheduler.submit("中优先级", priority=50, payload="常规任务")
    scheduler.cancel("中优先级")

    for result in scheduler.run():
        print(result)


if __name__ == "__main__":
    main()
