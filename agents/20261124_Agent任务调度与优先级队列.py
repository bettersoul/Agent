"""
Agent 任务调度与优先级队列
Auto-generated module skeleton.
"""

"""Agent 任务调度与优先级队列模块。

提供基于堆的优先级调度器，支持任务按优先级与提交时间排序，
并可通过工作线程执行任务回调。
日期标记: 2026-11-24
"""

from __future__ import annotations

import heapq
import itertools
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Callable, List, Optional


@dataclass(order=True)
class Task:
    """可调度的任务项，排序依据：优先级降序、提交序列升序。"""

    priority: int
    seq: int
    name: str = field(compare=False)
    fn: Callable[[], Any] = field(compare=False)
    created_at: float = field(default_factory=time.time, compare=False)


class PriorityScheduler:
    """基于优先级的 Agent 任务调度器。

    使用负优先级将高优先级任务排在堆顶；同优先级按提交顺序 FIFO。
    """

    def __init__(self) -> None:
        self._heap: List[Task] = []
        self._counter = itertools.count()
        self._lock = threading.Lock()
        self._cv = threading.Condition(self._lock)
        self._stopped = False

    def submit(self, name: str, fn: Callable[[], Any], priority: int = 0) -> Task:
        """提交任务，priority 越大越先执行。"""
        task = Task(priority=-priority, seq=next(self._counter), name=name, fn=fn)
        with self._cv:
            heapq.heappush(self._heap, task)
            self._cv.notify()
        return task

    def pop(self, timeout: Optional[float] = None) -> Optional[Task]:
        """取出下一个最高优先级任务，超时或停止时返回 None。"""
        deadline = None if timeout is None else time.time() + timeout
        with self._cv:
            while not self._heap and not self._stopped:
                remaining = None if deadline is None else deadline - time.time()
                if remaining is not None and remaining <= 0:
                    return None
                self._cv.wait(remaining)
            if self._stopped or not self._heap:
                return None
            return heapq.heappop(self._heap)

    def run_once(self) -> Optional[str]:
        """取出并执行一个任务，返回任务名。"""
        task = self.pop()
        if task is None:
            return None
        task.fn()
        return task.name

    def start_worker(self, name: str = "agent-worker") -> threading.Thread:
        """启动后台工作线程，持续消费任务。"""

        def loop() -> None:
            while True:
                task = self.pop(timeout=0.5)
                if task is None and self._stopped:
                    return
                if task is not None:
                    try:
                        task.fn()
                    except Exception as exc:  # 单个任务失败不阻塞调度
                        print(f"[{name}] task {task.name} failed: {exc}")

        thread = threading.Thread(target=loop, name=name, daemon=True)
        thread.start()
        return thread

    def stop(self) -> None:
        """停止调度器，唤醒阻塞的消费者。"""
        with self._cv:
            self._stopped = True
            self._cv.notify_all()

    def __len__(self) -> int:
        with self._lock:
            return len(self._heap)


if __name__ == "__main__":
    scheduler = PriorityScheduler()
    scheduler.submit("low", lambda: print("run low"), priority=1)
    scheduler.submit("high", lambda: print("run high"), priority=10)
    scheduler.submit("mid", lambda: print("run mid"), priority=5)

    while len(scheduler) > 0:
        scheduler.run_once()

    worker = scheduler.start_worker()
    scheduler.submit("async-high", lambda: print("run async-high"), priority=100)
    time.sleep(0.3)
    scheduler.stop()
    worker.join(timeout=1.0)
    print("scheduler demo done")
