"""
多智能体协作（Multi-Agent）消息总线
Auto-generated module skeleton.
"""

"""多智能体协作消息总线 (Multi-Agent Message Bus), 2026-11-27."""
from __future__ import annotations

import queue
import threading
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional


@dataclass
class Message:
    """一条总线消息。"""
    sender: str
    topic: str
    payload: object
    recipients: List[str] = field(default_factory=list)  # 空表示广播


Handler = Callable[[Message], None]


class MessageBus:
    """线程安全的多智能体消息总线，支持订阅、定向与广播投递。"""

    def __init__(self) -> None:
        self._subs: Dict[str, Dict[str, Handler]] = {}  # topic -> agent -> handler
        self._lock = threading.RLock()
        self._q: "queue.Queue[Message]" = queue.Queue()
        self._running = False
        self._worker: Optional[threading.Thread] = None

    def join(self, agent: str) -> None:
        """注册智能体（可订阅多个主题）。"""
        with self._lock:
            self._subs.setdefault(agent, {})

    def subscribe(self, agent: str, topic: str, handler: Handler) -> None:
        """智能体订阅某主题并绑定处理函数。"""
        with self._lock:
            self._subs.setdefault(agent, {})[topic] = handler

    def unsubscribe(self, agent: str, topic: str) -> None:
        with self._lock:
            self._subs.get(agent, {}).pop(topic, None)

    def publish(self, msg: Message) -> None:
        """发布消息到队列（异步）。"""
        self._q.put(msg)

    def _dispatch(self, msg: Message) -> List[str]:
        """同步投递一条消息，返回实际接收的智能体列表。"""
        delivered: List[str] = []
        with self._lock:
            targets = msg.recipients or list(self._subs.keys())
            for agent in targets:
                handler = self._subs.get(agent, {}).get(msg.topic)
                if handler is not None:
                    handler(msg)
                    delivered.append(agent)
        return delivered

    def send(self, msg: Message) -> List[str]:
        """同步发送并立即投递。"""
        return self._dispatch(msg)

    def run_once(self) -> int:
        """处理队列中积压的消息，返回处理数量。"""
        count = 0
        while not self._q.empty():
            self._dispatch(self._q.get())
            count += 1
        return count

    def start(self) -> None:
        """启动后台消费线程。"""
        if self._running:
            return
        self._running = True

        def loop() -> None:
            while self._running:
                try:
                    self._dispatch(self._q.get(timeout=0.1))
                except queue.Empty:
                    continue

        self._worker = threading.Thread(target=loop, daemon=True)
        self._worker.start()

    def stop(self) -> None:
        self._running = False
        if self._worker is not None:
            self._worker.join(timeout=1.0)
            self._worker = None


if __name__ == "__main__":
    bus = MessageBus()
    log: List[str] = []

    def make(agent: str) -> Handler:
        def h(m: Message) -> None:
            log.append(f"{agent} <- {m.sender}:{m.topic}:{m.payload}")
        return h

    for a in ("planner", "coder", "reviewer"):
        bus.join(a)
        bus.subscribe(a, "task", make(a))

    bus.send(Message("planner", "task", "拆解需求"))
    bus.send(Message("planner", "task", "审查代码", recipients=["reviewer"]))
    print("\n".join(log))

    bus.start()
    bus.publish(Message("coder", "task", "提交 PR"))
    bus.stop()
    print("queue drained:", bus.run_once())
