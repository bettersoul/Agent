"""
AI Agent 每日代码 · 2026-11-17
主题：短期/长期记忆管理的 Agent Memory 模块
由 agent-green 自动生成。
"""

"""Agent Memory 模块 —— 短期/长期记忆管理。

日期标记: 2026-11-17
设计要点:
  - 短期记忆(S短期上下文): 固定容量 FIFO/LRU 淘汰, 随会话结束丢弃。
  - 长期记忆(长期知识库): 带关键词/标签索引, 相似度检索后持久化。
  - 统一的 MemoryStore 对外暴露 remember/recall/forget 接口。
"""

from __future__ import annotations

import math
import re
import time
from collections import OrderedDict, defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple


@dataclass
class MemoryRecord:
    """单条记忆记录。"""

    key: str
    content: str
    tags: Set[str] = field(default_factory=set)
    score: float = 1.0
    created_at: float = field(default_factory=time.time)
    hits: int = 0

    def tokens(self) -> List[str]:
        """把内容切成用于相似度计算的 token 列表。"""
        return [t for t in re.split(r"[\W_]+", self.content.lower()) if t]


def _cosine(a: Sequence[str], b: Sequence[str]) -> float:
    """基于 token 集合的余弦相似度(可复现、无外部依赖)。"""
    sa, sb = set(a), set(b)
    if not sa or not sb:
        return 0.0
    inter = len(sa & sb)
    if inter == 0:
        return 0.0
    return inter / math.sqrt(len(sa) * len(sb))


class ShortTermMemory:
    """短期记忆: 容量受限的会话工作区, 超出容量按 LRU 淘汰。"""

    def __init__(self, capacity: int = 10) -> None:
        self.capacity = max(1, capacity)
        self._items: "OrderedDict[str, MemoryRecord]" = OrderedDict()

    def put(self, record: MemoryRecord) -> None:
        self._items[record.key] = record
        self._items.move_to_end(record.key)
        while len(self._items) > self.capacity:
            self._items.popitem(last=False)

    def get(self, key: str) -> Optional[MemoryRecord]:
        rec = self._items.get(key)
        if rec is not None:
            self._items.move_to_end(key)
        return rec

    def keys(self) -> List[str]:
        return list(self._items.keys())

    def clear(self) -> None:
        self._items.clear()

    def __len__(self) -> int:
        return len(self._items)


class LongTermMemory:
    """长期记忆: 按标签建立倒排索引, 支持关键词 + 相似度检索。"""

    def __init__(self) -> None:
        self._records: Dict[str, MemoryRecord] = {}
        self._index: Dict[str, Set[str]] = defaultdict(set)

    def put(self, record: MemoryRecord) -> None:
        self._records[record.key] = record
        for tag in record.tags:
            self._index[tag].add(record.key)

    def get(self, key: str) -> Optional[MemoryRecord]:
        return self._records.get(key)

    def search(self, query: str, tags: Iterable[str] = (), top_k: int = 5) -> List[MemoryRecord]:
        """检索长期记忆: 标签过滤 + 余弦相似度排序。"""
        want = {t.lower() for t in tags}
        qtok = re.split(r"[\W_]+", query.lower())
        scored: List[Tuple[float, MemoryRecord]] = []
        for rec in self._records.values():
            if want and not (want & {t.lower() for t in rec.tags}):
                continue
            s = _cosine(qtok, rec.tokens()) + 0.1 * len(want & {t.lower() for t in rec.tags})
            if s > 0:
                scored.append((s, rec))
        scored.sort(key=lambda x: x[0], reverse=True)
        for _, rec in scored[:top_k]:
            rec.hits += 1
        return [rec for _, rec in scored[:top_k]]

    def forget(self, key: str) -> bool:
        rec = self._records.pop(key, None)
        if rec is None:
            return False
        for tag in rec.tags:
            self._index[tag].discard(key)
        return True

    def __len__(self) -> int:
        return len(self._records)


class AgentMemory:
    """Agent 记忆门面: 短期缓冲 + 长期库, 统一 remember/recall/forget。"""

    def __init__(self, short_capacity: int = 8) -> None:
        self.short = ShortTermMemory(short_capacity)
        self.long = LongTermMemory()
        self._seq = 0

    def _next_key(self, prefix: str) -> str:
        self._seq += 1
        return f"{prefix}-{self._seq}"

    def remember(self, content: str, tags: Iterable[str] = (),
                 persist: bool = True, key: Optional[str] = None) -> MemoryRecord:
        """写入记忆。persist=True 同时进入长期记忆。"""
        rec = MemoryRecord(key=key or self._next_key("mem"), content=content,
                           tags={t.lower() for t in tags})
        self.short.put(rec)
        if persist:
            self.long.put(rec)
        return rec

    def recall(self, query: str = "", tags: Iterable[str] = (), top_k: int = 5) -> List[MemoryRecord]:
        """召回记忆: 优先检索长期库, 关键词命中短期记忆时提升其分数。"""
        results = self.long.search(query, tags, top_k)
        short_hit = self.short.get(query) if query else None
        if short_hit is not None and short_hit not in results:
            results.insert(0, short_hit)
        return results[:top_k]

    def forget(self, key: str) -> bool:
        """遗忘: 从短期与长期记忆中移除。"""
        self.short.get(key)  # 触发 LRU 更新
        self.short._items.pop(key, None)
        return self.long.forget(key)

    def stats(self) -> Dict[str, Any]:
        return {"short": len(self.short), "long": len(self.long), "seq": self._seq}


def llm_summarize(memory: List[MemoryRecord]) -> str:
    """占位: 实际项目中替换为真实 LLM 调用, 用于压缩长期记忆。"""
    return "\n".join(f"- [{','.join(sorted(r.tags)) or 'untagged'}] {r.content}" for r in memory)


if __name__ == "__main__":
    mem = AgentMemory(short_capacity=3)
    mem.remember("用户喜欢 Python 异步编程", tags=["user", "pref"], persist=True)
    mem.remember("项目使用 FastAPI 与 PostgreSQL", tags=["project"], persist=True)
    mem.remember("临时: 调试中的堆栈信息", tags=["debug"], persist=False)
    mem.remember("用户时区为 Asia/Shanghai", tags=["user", "pref"], persist=True)

    print("统计:", mem.stats())
    print("\n-- 召回(user 偏好) --")
    for r in mem.recall("用户 偏好 时区", tags=["user"], top_k=3):
        print(f"  {r.score:.2f} hits={r.hits} {r.content}")

    print("\n-- 短期记忆 LRU 淘汰 --")
    print("  keys:", mem.short.keys())

    print("\n-- 遗忘 --")
    mem.forget("mem-2")
    print("  统计:", mem.stats())

    print("\n-- 压缩摘要(LLM 占位) --")
    print(llm_summarize(mem.recall(top_k=5)))
