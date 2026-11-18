"""
短期/长期记忆管理的 Agent Memory 模块
Auto-generated module skeleton.
"""

"""短期/长期记忆管理模块（2026-11-18）。短期记忆为有界队列，长期记忆做持久摘要。"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Callable, Deque, Dict, List, Optional


@dataclass
class MemoryItem:
    """单条记忆：内容、重要性分数、来源标签。"""
    content: str
    importance: float = 0.5
    tags: List[str] = field(default_factory=list)


class AgentMemory:
    """管理短期与长期记忆的 Agent 记忆模块。

    短期记忆保存最近若干条交互，超出容量时按重要性淘汰；
    被淘汰或高重要性的条目可提升进长期记忆，长期记忆按主题做摘要。
    """

    def __init__(self, short_capacity: int = 8, long_capacity: int = 32,
                 summarizer: Optional[Callable[[List[str]], str]] = None) -> None:
        self.short_capacity = short_capacity
        self.long_capacity = long_capacity
        self._short: Deque[MemoryItem] = deque()
        self._long: List[MemoryItem] = []
        self._summarizer = summarizer or (lambda texts: " | ".join(texts))

    def remember(self, content: str, importance: float = 0.5,
                 tags: Optional[List[str]] = None) -> None:
        """写入短期记忆，容量溢出时把最不重要的条目晋升到长期记忆。"""
        item = MemoryItem(content, importance, tags or [])
        self._short.append(item)
        if len(self._short) > self.short_capacity:
            victim = min(self._short, key=lambda x: x.importance)
            self._short.remove(victim)
            self._promote(victim)
        if importance >= 0.8:
            self._promote(item)

    def _promote(self, item: MemoryItem) -> None:
        """将条目转入长期记忆并维持容量上限。"""
        self._long.append(item)
        if len(self._long) > self.long_capacity:
            self._long.pop(0)

    def recall(self, query: str, top_k: int = 3) -> List[MemoryItem]:
        """按关键词粗检索短期与长期记忆，返回最相关条目。"""
        pool = list(self._short) + self._long
        scored = [(sum(1 for t in m.tags if t in query) + (query in m.content), m)
                  for m in pool]
        scored = [p for p in scored if p[0] > 0] or [(0, m) for m in pool]
        scored.sort(key=lambda p: (p[0], p[1].importance), reverse=True)
        return [m for _, m in scored[:top_k]]

    def summarize_long_term(self) -> str:
        """把长期记忆压缩成一段摘要文本。"""
        return self._summarizer([m.content for m in self._long])

    def stats(self) -> Dict[str, int]:
        """返回两级记忆的当前规模。"""
        return {"short": len(self._short), "long": len(self._long)}


if __name__ == '__main__':
    mem = AgentMemory(short_capacity=3, summarizer=lambda t: "; ".join(t))
    for i, text in enumerate(["用户喜欢简洁回答", "排查数据库超时", "多用中文交流",
                              "部署使用 Docker", "偏好异步接口"]):
        mem.remember(text, importance=0.9 if i == 2 else 0.4, tags=[text[:2]])
    print("stats:", mem.stats())
    print("recall:", [m.content for m in mem.recall("中文回答")])
    print("summary:", mem.summarize_long_term())
