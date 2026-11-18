"""
基于状态机（State Machine）的 Agent 工作流
Auto-generated module skeleton.
"""

"""基于状态机的 Agent 工作流模块 (2026-11-18)."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Callable, Dict, List, Optional


class State(Enum):
    """Agent 工作流状态。"""
    IDLE = auto()
    PLANNING = auto()
    EXECUTING = auto()
    REVIEWING = auto()
    DONE = auto()
    FAILED = auto()


def _llm_placeholder(prompt: str) -> str:
    """占位 LLM 调用，实际项目中替换为真实接口。"""
    return f"[llm-response] {prompt}"


@dataclass
class Transition:
    """一条状态转移规则：源状态 + 触发事件 -> 目标状态。"""
    source: State
    event: str
    target: State
    action: Optional[Callable[["AgentFSM"], None]] = None


@dataclass
class AgentFSM:
    """基于状态机的 Agent 工作流引擎。

    通过注册转移规则驱动 Agent 在规划、执行、复核之间流转，
    每次触发事件执行对应动作并推进状态。
    """

    state: State = State.IDLE
    context: Dict[str, str] = field(default_factory=dict)
    history: List[State] = field(default_factory=lambda: [State.IDLE])
    _transitions: Dict[tuple[State, str], Transition] = field(default_factory=dict)

    def add_transition(self, source: State, event: str, target: State,
                       action: Optional[Callable[["AgentFSM"], None]] = None) -> None:
        """注册一条状态转移规则。"""
        self._transitions[(source, event)] = Transition(source, event, target, action)

    def trigger(self, event: str) -> bool:
        """触发事件，成功转移返回 True，否则 False。"""
        trans = self._transitions.get((self.state, event))
        if trans is None:
            return False
        if trans.action:
            trans.action(self)
        self.state = trans.target
        self.history.append(self.state)
        return True

    def run(self, events: List[str]) -> None:
        """按顺序处理事件列表。"""
        for ev in events:
            if not self.trigger(ev):
                print(f"无法从 {self.state.name} 处理事件 '{ev}'")

    # 默认动作
    def _plan(self) -> None:
        self.context["plan"] = _llm_placeholder("制定计划")

    def _execute(self) -> None:
        self.context["result"] = _llm_placeholder("执行计划")

    def _review(self) -> None:
        ok = "llm-response" in self.context.get("result", "")
        self.context["review"] = "pass" if ok else "fail"


def build_default_agent() -> AgentFSM:
    """构建默认 Agent 工作流状态机。"""
    agent = AgentFSM()
    agent.add_transition(State.IDLE, "start", State.PLANNING, lambda a: a._plan())
    agent.add_transition(State.PLANNING, "go", State.EXECUTING, lambda a: a._execute())
    agent.add_transition(State.EXECUTING, "check", State.REVIEWING, lambda a: a._review())
    agent.add_transition(State.REVIEWING, "approve", State.DONE)
    agent.add_transition(State.REVIEWING, "reject", State.FAILED)
    return agent


if __name__ == "__main__":
    agent = build_default_agent()
    agent.run(["start", "go", "check", "approve"])
    print("状态轨迹:", " -> ".join(s.name for s in agent.history))
    print("上下文:", agent.context)
