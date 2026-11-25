"""
短期/长期记忆管理的 Agent Memory 模块
Auto-generated module skeleton.
"""

"""短期/长期记忆管理模块 (2026-11-25)。"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class MemoryItem:
    """单条记忆。"""
    content: str
    importance: float = 0.5
    created_at: float = field(default_factory=time.time)
    last_access: float = field(default_factory=time.time)
    access_count: int = 0


class AgentMemory:
    """双层记忆管理：短期缓冲（容量受限、FIFO 淘汰）与长期存储（按重要度晋升）。

    短期记忆保存最近交互，超出容量时最不重要的条目被移除；
    重要度超过阈值的条目会晋升到长期记忆，长期记忆按重要度与访问频率检索。
    """

    def __init__(self, short_capacity: int = 5, promote_threshold: float = 0.7) -> None:
        self.short_capacity = short_capacity
        self.promote_threshold = promote_threshold
        self._short: List[MemoryItem] = []
        self._long: List[MemoryItem] = []

    def add(self, content: str, importance: float = 0.5) -> None:
        """写入一条记忆，重要度高者直接进入长期记忆。"""
        item = MemoryItem(content=content, importance=importance)
        if importance >= self.promote_threshold:
            self._long.append(item)
            return
        self._short.append(item)
        if len(self._short) > self.short_capacity:
            self._short.sort(key=lambda i: i.importance)
            self._short.pop(0)

    def recall(self, query: str, top_k: int = 3) -> List[str]:
        """基于关键词重合度检索，返回最相关的记忆内容。"""
        tokens = set(query.lower().split())
        scored: List[tuple[float, MemoryItem]] = []
        for item in self._short + self._long:
            overlap = len(tokens & set(item.content.lower().split()))
            score = overlap * 0.6 + item.importance * 0.4
            scored.append((score, item))
        scored.sort(key=lambda p: p[0], reverse=True)
        results = []
        for _, item in scored[:top_k]:
            item.last_access = time.time()
            item.access_count += 1
            results.append(item.content)
        return results

    def consolidate(self) -> int:
        """将短期记忆中访问频繁的条目晋升到长期记忆，返回晋升数量。"""
        promoted = 0
        remaining: List[MemoryItem] = []
        for item in self._short:
            if item.access_count >= 2 or item.importance >= self.promote_threshold:
                self._long.append(item)
                promoted += 1
            else:
                remaining.append(item)
        self._short = remaining
        return promoted

    def stats(self) -> Dict[str, Any]:
        """返回记忆统计信息。"""
        return {
            "short_count": len(self._short),
            "long_count": len(self._long),
            "short": [i.content for i in self._short],
            "long": [i.content for i in self._long],
        }


if __name__ == "__main__":
    mem = AgentMemory(short_capacity=3, promote_threshold=0.8)
    mem.add("用户喜欢 Python 编程", 0.5)
    mem.add("用户的名字是 Alex", 0.6)
    mem.add("项目截止日期是下周", 0.9)
    mem.add("用户问过缓存策略", 0.4)
    mem.add("用户关注分布式系统", 0.3)

    print("初始统计:", mem.stats())
    print("检索 '用户 python':", mem.recall("用户 python"))
    print("检索 '用户 python' 后:", mem.recall("用户 python"))
    print("晋升数量:", mem.consolidate())
    print("最终统计:", mem.stats())
