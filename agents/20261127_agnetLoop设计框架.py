"""
agnet Loop 设计框架
Auto-generated module skeleton.
"""

"""Agent Loop 设计框架 — 2026-11-27

一个极简的 Agent 执行循环：观察 -> 决策 -> 行动，直到任务结束或达到最大轮次。
"""
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Any


@dataclass
class Step:
    """单轮循环记录。"""
    index: int
    observation: str
    action: Optional[str]
    result: str


class AgentLoop:
    """Agent Loop 框架核心类。

    通过可插拔的 `policy`（决定动作）与 `tools`（执行动作）实现循环。
    """

    def __init__(
        self,
        policy: Callable[[str], Optional[str]],
        tools: Dict[str, Callable[[str], str]],
        max_turns: int = 5,
        done_token: str = "DONE",
    ) -> None:
        self.policy = policy
        self.tools = tools
        self.max_turns = max_turns
        self.done_token = done_token
        self.history: List[Step] = []

    def _dispatch(self, action: str) -> str:
        """解析并执行动作，格式为 `tool:argument`。"""
        if ":" not in action:
            return f"未知动作格式: {action}"
        name, arg = action.split(":", 1)
        tool = self.tools.get(name.strip())
        if tool is None:
            return f"未注册工具: {name.strip()}"
        try:
            return tool(arg.strip())
        except Exception as exc:  # 保证循环不因单次工具异常中断
            return f"工具执行异常: {exc}"

    def run(self, task: str) -> List[Step]:
        """执行循环直到完成或超出最大轮次，返回历史步骤。"""
        observation = task
        for i in range(self.max_turns):
            action = self.policy(observation)
            if action is None or action.strip() == self.done_token:
                self.history.append(Step(i, observation, None, "任务结束"))
                break
            result = self._dispatch(action)
            self.history.append(Step(i, observation, action, result))
            observation = result
        return self.history

    def summary(self) -> str:
        """返回可读的循环摘要。"""
        lines = [f"[{s.index}] action={s.action} -> {s.result}" for s in self.history]
        return "\n".join(lines)


if __name__ == "__main__":
    # 简单工具：回声与计数
    counter: Dict[str, int] = {"n": 0}

    def echo(arg: str) -> str:
        return f"echo({arg})"

    def inc(arg: str) -> str:
        counter["n"] += 1
        return f"count={counter['n']}"

    # 策略：先 echo，再 inc，最后结束
    plan = iter(["echo:hello", "inc:+", "DONE"])

    loop = AgentLoop(
        policy=lambda obs: next(plan, "DONE"),
        tools={"echo": echo, "inc": inc},
        max_turns=4,
    )
    loop.run("demo task")
    print(loop.summary())
