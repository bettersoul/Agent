"""
RAG 检索增强的 Agent 知识检索器
Auto-generated module skeleton.
"""

"""RAG 检索增强的 Agent 知识检索器模块。日期：2026-11-20。"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Sequence, Tuple


def embed(text: str) -> List[float]:
    """占位嵌入函数：把文本映射为稀疏字符哈希向量。"""
    vec = [0.0] * 64
    for token in re.findall(r"[\w\u4e00-\u9fff]+", text.lower()):
        vec[hash(token) % 64] += 1.0
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


def llm_answer(question: str, contexts: Sequence[str]) -> str:
    """占位 LLM 调用：基于检索上下文生成回答。"""
    joined = "\n".join(f"- {c}" for c in contexts)
    return f"[LLM] 问题：{question}\n依据：\n{joined}"


@dataclass
class Document:
    """知识文档：原文与元数据。"""
    doc_id: str
    text: str
    metadata: Dict[str, str] = field(default_factory=dict)


@dataclass
class Chunk:
    """文档切块及其向量。"""
    chunk_id: str
    doc_id: str
    text: str
    vector: List[float]


class RAGRetriever:
    """检索增强知识检索器：切块、索引、召回、重排与生成。"""

    def __init__(self, chunk_size: int = 120, top_k: int = 3,
                 embed_fn: Callable[[str], List[float]] = embed) -> None:
        self.chunk_size = chunk_size
        self.top_k = top_k
        self.embed_fn = embed_fn
        self._chunks: List[Chunk] = []

    def add_documents(self, docs: Sequence[Document]) -> int:
        """切块并建立内存索引，返回切块数量。"""
        for doc in docs:
            for i in range(0, len(doc.text), self.chunk_size):
                piece = doc.text[i:i + self.chunk_size].strip()
                if not piece:
                    continue
                cid = f"{doc.doc_id}#{i // self.chunk_size}"
                self._chunks.append(Chunk(cid, doc.doc_id, piece, self.embed_fn(piece)))
        return len(self._chunks)

    @staticmethod
    def _cosine(a: List[float], b: List[float]) -> float:
        return sum(x * y for x, y in zip(a, b))

    def _recall(self, query: str, k: int) -> List[Tuple[float, Chunk]]:
        qv = self.embed_fn(query)
        scored = [(self._cosine(qv, c.vector), c) for c in self._chunks]
        scored.sort(key=lambda p: p[0], reverse=True)
        return scored[:k]

    @staticmethod
    def _rerank(query: str, cands: List[Tuple[float, Chunk]]) -> List[Tuple[float, Chunk]]:
        """简单重排：向量分与关键词命中率加权融合。"""
        terms = set(re.findall(r"[\w\u4e00-\u9fff]+", query.lower()))
        out = []
        for score, chunk in cands:
            text = chunk.text.lower()
            hits = sum(1 for t in terms if t in text)
            lexical = hits / (len(terms) or 1)
            out.append((0.7 * score + 0.3 * lexical, chunk))
        out.sort(key=lambda p: p[0], reverse=True)
        return out

    def retrieve(self, query: str, top_k: Optional[int] = None) -> List[Tuple[float, Chunk]]:
        """召回并重排，返回 (得分, 切块) 列表。"""
        k = top_k or self.top_k
        return self._rerank(query, self._recall(query, max(k * 3, k)))[:k]

    def answer(self, query: str, top_k: Optional[int] = None,
               generate_fn: Callable[[str, Sequence[str]], str] = llm_answer) -> str:
        """端到端：检索上下文后调用生成函数作答。"""
        hits = self.retrieve(query, top_k)
        return generate_fn(query, [c.text for _, c in hits])


if __name__ == '__main__':
    rag = RAGRetriever(chunk_size=80, top_k=2)
    total = rag.add_documents([
        Document("d1", "RAG 通过检索外部知识来增强大模型回答的准确性。"),
        Document("d2", "Agent 使用工具调用完成多步推理任务。"),
        Document("d3", "向量检索依赖嵌入模型进行语义相似度计算。"),
    ])
    print("chunks:", total)
    query = "如何提升大模型回答准确性"
    for score, chunk in rag.retrieve(query):
        print(f"{score:.3f} {chunk.chunk_id}: {chunk.text}")
    print(rag.answer(query))
