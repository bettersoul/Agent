"""
AI Agent 每日代码 · 2026-11-17
主题：带记忆的对话式 Agent 会话管理
由 agent-green 自动生成。
"""

"""带记忆的对话式 Agent 会话管理模块。

日期标记: 2026-11-17
设计目标: 在有限的上下文窗口内, 对多轮对话做"摘要 + 最近轮次"的
混合记忆管理, 避免 token 无限增长, 同时保持语义连贯。
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Callable, Iterable, List, Optional, Dict, Any


# ---------- 占位 LLM 接口 (实际项目中替换为真实模型调用) ----------

def llm_summarize(prompt: str) -> str:
    """占位摘要函数: 真实实现应调用 LLM 生成会话摘要。"""
    return "[摘要占位] " + prompt[:120]


def llm_reply(history: List[Dict[str, str]], memory: str, user_input: str) -> str:
    """占位回复函数: 真实实现应把 memory + history 一起送入 LLM。"""
    return f"回复(基于记忆: {memory[:40]}...): {user_input}"


# ---------- 数据结构 ----------

@dataclass
class Message:
    """单条对话消息。"""

    role: str                      # "user" / "assistant" / "system"
    content: str
    tokens: int = 0                # 粗略 token 估计

    def to_dict(self) -> Dict[str, str]:
        return {"role": self.role, "content": self.content}


@dataclass
class Session:
    """一个会话: 原始消息 + 滚动摘要 + 计数器。"""

    session_id: str
    messages: List[Message] = field(default_factory=list)
    summary: str = ""
    turn_count: int = 0
    token_budget: int = 500

    def total_tokens(self) -> int:
        return sum(m.tokens for m in self.messages)


# ---------- 核心类 ----------

class MemorySessionManager:
    """带记忆的会话管理器。

    策略:
      1. 估算每条消息的 token 数;
      2. 超出预算时, 把最旧的消息压缩进滚动摘要 (summary);
      3. 上下文 = 摘要 + 最近若干轮消息, 始终送给 LLM;
      4. 摘要本身过长时再做一次递归压缩, 保证不失控。
    """

    def __init__(
        self,
        token_budget: int = 500,
        summarizer: Callable[[str], str] = llm_summarize,
        responder: Callable[[List[Dict[str, str]], str, str], str] = llm_reply,
        keep_turns: int = 4,
    ) -> None:
        self.token_budget = token_budget
        self.summarizer = summarizer
        self.responder = responder
        self.keep_turns = keep_turns
        self.sessions: Dict[str, Session] = {}

    # ---- 工具方法 ----

    @staticmethod
    def estimate_tokens(text: str) -> int:
        """粗略 token 估算: 中文字符约 1 个 token, 英文约 4 字符 1 token。"""
        cjk = len(re.findall(r"[\u4e00-\u9fff]", text))
        other = len(text) - cjk
        return cjk + other // 4 + 1

    def get_or_create(self, session_id: str) -> Session:
        """获取会话, 不存在则创建。"""
        if session_id not in self.sessions:
            self.sessions[session_id] = Session(
                session_id=session_id, token_budget=self.token_budget
            )
        return self.sessions[session_id]

    # ---- 核心逻辑 ----

    def add_user_message(self, session_id: str, content: str) -> Message:
        """记录用户输入并返回该消息对象。"""
        session = self.get_or_create(session_id)
        msg = Message(role="user", content=content, tokens=self.estimate_tokens(content))
        session.messages.append(msg)
        return msg

    def build_context(self, session_id: str) -> List[Dict[str, str]]:
        """构造送给 LLM 的上下文: 摘要 + 最近消息。"""
        session = self.get_or_create(session_id)
        recent = session.messages[-(self.keep_turns * 2):]
        context: List[Dict[str, str]] = []
        if session.summary:
            context.append({"role": "system", "content": f"历史摘要: {session.summary}"})
        context.extend(m.to_dict() for m in recent)
        return context

    def compress(self, session_id: str) -> None:
        """把旧消息压进摘要, 直到总量回到预算内。"""
        session = self.get_or_create(session_id)
        while session.total_tokens() > self.token_budget and len(session.messages) > 2:
            old = session.messages.pop(0)
            transcript = f"{old.role}: {old.content}"
            session.summary = self.summarizer(
                f"已有摘要: {session.summary}\n新增内容: {transcript}"
            )
        # 摘要本身过长 -> 递归压缩
        if self.estimate_tokens(session.summary) > self.token_budget // 2:
            session.summary = self.summarizer(f"精简以下摘要: {session.summary}")

    def reply(self, session_id: str, user_input: str) -> str:
        """完整一轮: 记录 -> 压缩 -> 生成回复 -> 记录。"""
        session = self.get_or_create(session_id)
        self.add_user_message(session_id, user_input)
        self.compress(session_id)

        context = self.build_context(session_id)
        answer = self.responder(context, session.summary, user_input)

        msg = Message(
            role="assistant", content=answer, tokens=self.estimate_tokens(answer)
        )
        session.messages.append(msg)
        session.turn_count += 1
        self.compress(session_id)
        return answer

    def stats(self, session_id: str) -> Dict[str, Any]:
        """返回会话统计信息, 便于观测。"""
        session = self.get_or_create(session_id)
        return {
            "session_id": session.session_id,
            "turns": session.turn_count,
            "messages": len(session.messages),
            "tokens": session.total_tokens(),
            "summary_len": len(session.summary),
        }


if __name__ == "__main__":
    manager = MemorySessionManager(token_budget=120, keep_turns=2)

    inputs = [
        "我叫小明, 正在准备 2026 年的期末考试。",
        "我最喜欢的科目是人工智能。",
        "帮我制定一个两周复习计划。",
        "我刚才说我叫什么来着?",
        "再补充一下, 我每天只有两个小时学习时间。",
    ]

    for text in inputs:
        answer = manager.reply("demo-session", text)
        print(f"用户: {text}")
        print(f"助手: {answer}")
        print("统计:", manager.stats("demo-session"))
        print("-" * 40)

    ctx = manager.build_context("demo-session")
    print("最终上下文条数:", len(ctx))
    for item in ctx:
        print(f"  [{item['role']}] {item['content'][:60]}")
