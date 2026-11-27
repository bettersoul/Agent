"""
带记忆的对话式 Agent 会话管理
Auto-generated module skeleton.
"""

"""带记忆的对话式 Agent 会话管理模块 (2026-11-27)。"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional


@dataclass
class Message:
    """单条对话消息。"""
    role: str  # "user" | "assistant" | "system"
    content: str
    ts: float = field(default_factory=time.time)


def _default_llm(messages: List[Message]) -> str:
    """占位 LLM 调用：真实环境中替换为模型接口。"""
    last = messages[-1].content if messages else ""
    return f"[echo] {last}"


class Session:
    """对话式 Agent 会话，维护消息历史并支持记忆窗口管理。

    - 自动裁剪历史到最近 `max_turns` 轮
    - 支持外部 LLM 回调与系统提示词
    """

    def __init__(
        self,
        session_id: str,
        system_prompt: str = "你是一个有帮助的助手。",
        max_turns: int = 20,
        llm: Optional[Callable[[List[Message]], str]] = None,
    ) -> None:
        self.session_id = session_id
        self.max_turns = max_turns
        self.llm = llm or _default_llm
        self.history: List[Message] = [Message("system", system_prompt)]

    def _trim(self) -> None:
        """保留 system 提示词，裁剪超出窗口的旧消息。"""
        sys_msgs = [m for m in self.history if m.role == "system"]
        others = [m for m in self.history if m.role != "system"]
        limit = self.max_turns * 2  # 每轮含 user + assistant
        self.history = sys_msgs + others[-limit:]

    def send(self, user_input: str) -> str:
        """发送用户消息并返回 Agent 回复。"""
        self.history.append(Message("user", user_input))
        reply = self.llm(self.history)
        self.history.append(Message("assistant", reply))
        self._trim()
        return reply

    def memory_summary(self) -> Dict[str, object]:
        """返回会话记忆概览。"""
        return {
            "session_id": self.session_id,
            "messages": len(self.history),
            "turns": sum(1 for m in self.history if m.role == "user"),
        }

    def reset(self, keep_system: bool = True) -> None:
        """清空会话，可选择保留 system 提示。"""
        if keep_system:
            self.history = [m for m in self.history if m.role == "system"]
        else:
            self.history.clear()


if __name__ == "__main__":
    sess = Session("demo-1", max_turns=3)
    for text in ["你好", "我叫小明", "帮我记一下明天开会", "我刚才说了什么？", "再见"]:
        print("用户:", text)
        print("Agent:", sess.send(text))
    print("记忆概览:", sess.memory_summary())
