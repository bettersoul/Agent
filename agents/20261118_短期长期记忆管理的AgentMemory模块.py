"""
短期/长期记忆管理的 Agent Memory 模块
Auto-generated module skeleton.
"""

"""Agent 短期/长期记忆管理模块。

短期记忆: 有容量上限的近期对话缓冲。
长期记忆: 带重要度与时间衰减的持久条目, 支持检索与遗忘。
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class MemoryItem:
    """一条记忆条目。"""
    content: str
    importance: float = 0.5  # 0~1
    ts: float = field(default_factory=time.time)
    meta: Dict[str, Any] = field(default_factory=dict)


class AgentMemory:
    """管理 Agent 的短期与长期记忆。

    短期记忆保存最近交互, 超出容量时按重要度淘汰;
    长期记忆按 (重要度 × 时间衰减) 打分, 供检索与遗忘。
    """

    def __init__(self, short_capacity: int = 5, long_capacity: int = 100,
                 decay_halflife: float = 3600.0) -> None:
        self.short_capacity = short_capacity
        self.long_capacity = long_capacity
        self.decay_halflife = decay_halflife
        self._short: List[MemoryItem] = []
        self._long: List[MemoryItem] = []

    # ---------- 短期记忆 ----------
    def add_short(self, content: str, importance: float = 0.5) -> None:
        """写入短期记忆, 超容量时淘汰得分最低者。"""
        self._short.append(MemoryItem(content, importance))
        if len(self._short) > self.short_capacity:
            self._short.sort(key=lambda m: m.importance, reverse=True)
            self._short = self._short[: self.short_capacity]

    def short_view(self) -> List[str]:
        """返回短期记忆内容 (按写入顺序)。"""
        return [m.content for m in self._short]

    # ---------- 长期记忆 ----------
    def _score(self, item: MemoryItem, now: Optional[float] = None) -> float:
        """重要度 × 指数时间衰减。"""
        now = now or time.time()
        age = max(0.0, now - item.ts)
        decay = 0.5 ** (age / self.decay_halflife)
        return item.importance * decay

    def consolidate(self, threshold: float = 0.7) -> int:
        """将短期记忆中高重要度的条目晋升到长期, 返回晋升数量。"""
        promoted = [m for m in self._short if m.importance >= threshold]
        for m in promoted:
            self._long.append(m)
        self._short = [m for m in self._short if m.importance < threshold]
        self._trim_long()
        return len(promoted)

    def add_long(self, content: str, importance: float = 0.5,
                 meta: Optional[Dict[str, Any]] = None) -> None:
        """直接写入长期记忆。"""
        self._long.append(MemoryItem(content, importance, meta=meta or {}))
        self._trim_long()

    def _trim_long(self) -> None:
        """超出容量时按得分淘汰。"""
        if len(self._long) > self.long_capacity:
            now = time.time()
            self._long.sort(key=lambda m: self._score(m, now), reverse=True)
            self._long = self._long[: self.long_capacity]

    def recall(self, query: str = "", top_k: int = 3) -> List[MemoryItem]:
        """检索长期记忆: 关键词匹配加分, 再按得分排序。"""
        now = time.time()
        q = query.lower()

        def rank(m: MemoryItem) -> float:
            hit = 1.0 if q and q in m.content.lower() else 0.0
            return self._score(m, now) + hit

        return sorted(self._long, key=rank, reverse=True)[:top_k]

    def forget(self, threshold: float = 0.05) -> int:
        """遗忘得分低于阈值的长期记忆, 返回删除数量。"""
        now = time.time()
        before = len(self._long)
        self._long = [m for m in self._long if self._score(m, now) >= threshold]
        return before - len(self._long)


if __name__ == "__main__":
    mem = AgentMemory(short_capacity=3, long_capacity=10, decay_halflife=60.0)
    mem.add_short("用户喜欢黑咖啡", 0.9)
    mem.add_short("临时闲聊", 0.2)
    mem.add_short("用户来自上海", 0.8)
    mem.add_short("随便说说", 0.1)  # 超容量, 淘汰低分者
    print("短期记忆:", mem.short_view())

    promoted = mem.consolidate(threshold=0.7)
    print(f"晋升长期记忆数量: {promoted}")

    mem.add_long("用户的工作是数据工程师", 0.85, {"source": "profile"})
    print("检索 '咖啡':", [m.content for m in mem.recall("咖啡")])
    print("检索 '用户':", [m.content for m in mem.recall("用户", top_k=5)])
    print("遗忘低分条目:", mem.forget(threshold=0.6))
