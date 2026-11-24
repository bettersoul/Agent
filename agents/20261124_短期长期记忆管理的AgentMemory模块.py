"""
短期/长期记忆管理的 Agent Memory 模块
Auto-generated module skeleton.
"""

"""Agent 记忆管理模块：短期(工作)记忆 + 长期(持久)记忆，含简单重要度提升与遗忘。"""
from __future__ import annotations

import heapq
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(order=True)
class MemoryItem:
    """单条记忆：重要度、时间戳、内容与可排序键。"""
    score: float
    ts: float = field(compare=False)
    content: str = field(compare=False)
    meta: Dict[str, Any] = field(default_factory=dict, compare=False)


class AgentMemory:
    """双通道记忆管理：短期缓冲(有限容量)与长期存储(按重要度淘汰)。"""

    def __init__(self, short_capacity: int = 8, long_capacity: int = 100,
                 promote_threshold: float = 0.6) -> None:
        self.short_capacity = short_capacity
        self.long_capacity = long_capacity
        self.promote_threshold = promote_threshold
        self._short: List[MemoryItem] = []          # 保持插入顺序的工作记忆
        self._long: Dict[str, MemoryItem] = {}      # 长期记忆: key -> item

    # ---------- 写入 ----------
    def add(self, content: str, importance: float = 0.5,
            meta: Optional[Dict[str, Any]] = None) -> None:
        """写入一条记忆；重要度足够高时同步进入长期记忆。"""
        item = MemoryItem(score=max(0.0, min(1.0, importance)),
                          ts=time.time(), content=content, meta=meta or {})
        self._short.append(item)
        if len(self._short) > self.short_capacity:
            self._short.pop(0)                      # 丢弃最旧工作记忆
        if item.score >= self.promote_threshold:
            self._persist(item)

    def _persist(self, item: MemoryItem) -> None:
        key = f"{item.ts:.6f}"
        self._long[key] = item
        if len(self._long) > self.long_capacity:    # 淘汰关键度最低者
            self._long.pop(min(self._long, key=lambda k: self._long[k].score))

    # ---------- 读取 ----------
    def recall(self, query: str, top_k: int = 3) -> List[MemoryItem]:
        """跨短期与长期做简单关键词匹配，按重要度排序返回。"""
        tokens = [t for t in query.lower().split() if t]
        hits: List[MemoryItem] = []
        for item in list(self._short) + list(self._long.values()):
            text = item.content.lower()
            if all(t in text for t in tokens):
                hits.append(item)
        return heapq.nlargest(top_k, hits)

    def stats(self) -> Dict[str, int]:
        """返回当前记忆规模统计。"""
        return {"short": len(self._short), "long": len(self._long)}


if __name__ == '__main__':
    mem = AgentMemory(short_capacity=3, promote_threshold=0.7)
    mem.add("用户偏好简短回答", importance=0.9)
    mem.add("今天天气不错", importance=0.3)
    mem.add("项目截止日期是周五", importance=0.85)
    mem.add("临时草稿想法", importance=0.2)
    print("统计:", mem.stats())
    for it in mem.recall("用户 偏好", top_k=2):
        print(f"[{it.score:.2f}] {it.content}")
