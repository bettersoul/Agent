"""
工具结果的结构化解析与重试策略
Auto-generated module skeleton.
"""

"""工具结果的结构化解析与重试策略模块 (2026-11-27)。

提供 ToolResultParser，用于把工具返回的原始文本解析为结构化 dict，
并在解析失败或结果不合规时按指数退避重试调用工具。
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional


@dataclass
class RetryPolicy:
    """重试策略配置。

    Attributes:
        max_attempts: 最大尝试次数（含首次调用），至少为 1。
        base_delay: 首次重试前的等待秒数。
        factor: 每次重试的延迟倍数。
        max_delay: 单次等待上限秒数。
    """

    max_attempts: int = 3
    base_delay: float = 0.1
    factor: float = 2.0
    max_delay: float = 2.0

    def delay_for(self, attempt: int) -> float:
        """返回第 attempt 次（从 0 开始）失败后的等待时间。"""
        return min(self.base_delay * (self.factor ** attempt), self.max_delay)


@dataclass
class ParseOutcome:
    """单次解析结果。

    Attributes:
        ok: 是否解析成功且结构合规。
        data: 解析出的结构化数据，失败时为 None。
        error: 失败原因，成功时为 None。
        raw: 工具原始返回文本。
        attempts: 实际尝试次数。
    """

    ok: bool
    data: Optional[Dict[str, Any]]
    error: Optional[str]
    raw: str
    attempts: int = 1


class ToolResultParser:
    """解析工具返回文本，并在失败时按策略重试调用工具。

    预期工具返回 JSON 对象；解析失败、非 dict 或缺少必需字段
    均视为失败并触发重试。
    """

    def __init__(
        self,
        required_keys: tuple[str, ...] = (),
        policy: Optional[RetryPolicy] = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.required_keys = required_keys
        self.policy = policy or RetryPolicy()
        self._sleep = sleep

    def parse(self, raw: str) -> Dict[str, Any]:
        """将原始文本解析为 dict，不合规时抛出 ValueError。"""
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid json: {exc}") from exc
        if not isinstance(data, dict):
            raise ValueError(f"expected object, got {type(data).__name__}")
        missing = [k for k in self.required_keys if k not in data]
        if missing:
            raise ValueError(f"missing keys: {missing}")
        return data

    def call_and_parse(self, tool: Callable[[], str]) -> ParseOutcome:
        """调用工具并解析结果，失败时按策略重试。

        Args:
            tool: 无参可调用对象，返回原始文本。

        Returns:
            ParseOutcome，包含最终状态与尝试次数。
        """
        last_error: Optional[str] = None
        raw = ""
        for attempt in range(max(1, self.policy.max_attempts)):
            try:
                raw = tool()
                data = self.parse(raw)
                return ParseOutcome(True, data, None, raw, attempt + 1)
            except Exception as exc:  # 工具异常与解析异常统一重试
                last_error = str(exc)
                if attempt + 1 < self.policy.max_attempts:
                    self._sleep(self.policy.delay_for(attempt))
        return ParseOutcome(False, None, last_error, raw,
                            self.policy.max_attempts)


if __name__ == '__main__':
    calls = {"n": 0}

    def flaky_tool() -> str:
        """前两次返回坏数据，第三次返回合法 JSON。"""
        calls["n"] += 1
        return '{"status": "ok", "value": 42}' if calls["n"] >= 3 else "oops"

    parser = ToolResultParser(required_keys=("status",),
                              policy=RetryPolicy(max_attempts=3, base_delay=0),
                              sleep=lambda _: None)
    outcome = parser.call_and_parse(flaky_tool)
    print(f"ok={outcome.ok} data={outcome.data} attempts={outcome.attempts}")

    bad = ToolResultParser(policy=RetryPolicy(max_attempts=2, base_delay=0),
                           sleep=lambda _: None)
    print(bad.call_and_parse(lambda: "not json").error)
