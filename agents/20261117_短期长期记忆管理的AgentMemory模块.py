"""
短期/长期记忆管理的 Agent Memory 模块
Auto-generated module skeleton.
"""

"""短期/长期记忆管理模块（2026-11-17）。"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Iterable


@dataclass
class MemoryItem:
    """单条记忆。"""

    content: str
    importance: float = 0.5
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    tags: set[str] = field(default_factory=set)


class AgentMemory:
    """管理短期会话记忆，并按重要度归档长期记忆。"""

    def __init__(self, short_limit: int = 10, long_limit: int = 100) -> None:
        if short_limit < 1 or long_limit < 1:
            raise ValueError("记忆容量必须大于零")
        self.short_limit = short_limit
        self.long_limit = long_limit
        self.short: list[MemoryItem] = []
        self.long: list[MemoryItem] = []

    def remember(
        self,
        content: str,
        importance: float = 0.5,
        tags: Iterable[str] = (),
    ) -> MemoryItem:
        """保存记忆；容量不足时优先淘汰低价值短期记忆。"""
        if not content.strip():
            raise ValueError("记忆内容不能为空")
        if not 0 <= importance <= 1:
            raise ValueError("importance 必须位于 0 到 1 之间")

        item = MemoryItem(content.strip(), importance, tags=set(tags))
        self.short.append(item)
        self.short.sort(key=lambda memory: memory.created_at)
        while len(self.short) > self.short_limit:
            index = min(
                range(len(self.short)),
                key=lambda i: (self.short[i].importance, self.short[i].created_at),
            )
            self.long.append(self.short.pop(index))
        self._trim_long()
        return item

    def recall(self, query: str = "", limit: int = 5) -> list[MemoryItem]:
        """按关键词和重要度召回最近记忆。"""
        if limit < 1:
            return []
        terms = {term.lower() for term in query.split() if term}
        candidates = self.short + self.long
        matches = [
            item
            for item in candidates
            if not terms
            or terms.intersection(
                {word.lower() for word in item.content.split()}
                | {tag.lower() for tag in item.tags}
            )
        ]
        matches.sort(
            key=lambda item: (item.importance, item.created_at),
            reverse=True,
        )
        return matches[:limit]

    def forget(self, content: str) -> int:
        """删除内容完全匹配的记忆，返回删除数量。"""
        target = content.strip()
        removed = 0
        for collection in (self.short, self.long):
            before = len(collection)
            collection[:] = [item for item in collection if item.content != target]
            removed += before - len(collection)
        return removed

    def promote(self, content: str) -> bool:
        """将指定短期记忆提升为长期记忆。"""
        for index, item in enumerate(self.short):
            if item.content == content.strip():
                self.short.pop(index)
                self.long.append(item)
                self._trim_long()
                return True
        return False

    def _trim_long(self) -> None:
        """限制长期记忆数量，优先保留高价值和新记忆。"""
        self.long.sort(key=lambda item: (item.importance, item.created_at))
        while len(self.long) > self.long_limit:
            self.long.pop(0)

    def summary(self) -> dict[str, int]:
        """返回当前记忆数量统计。"""
        return {"short": len(self.short), "long": len(self.long)}


if __name__ == "__main__":
    memory = AgentMemory(short_limit=3, long_limit=5)
    memory.remember("用户喜欢 Python", importance=0.9, tags=["偏好"])
    memory.remember("今天讨论 Agent 架构", importance=0.7, tags=["工作"])
    memory.remember("临时任务：修复测试", importance=0.2)
    memory.remember("用户偏好简洁回答", importance=0.8, tags=["偏好"])
    memory.remember("历史项目使用 PostgreSQL", importance=0.6)

    print("统计：", memory.summary())
    print("召回：", [item.content for item in memory.recall("偏好")])
    print("提升：", memory.promote("用户喜欢 Python"))
    print("长期记忆：", [item.content for item in memory.long])
