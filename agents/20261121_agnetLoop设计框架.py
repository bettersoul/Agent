"""
agnet Loop 设计框架
Auto-generated module skeleton.
"""

"""agnet Loop 设计框架 (2026-11-21)

提供极简的 Agent 循环：规划 -> 执行工具 -> 观察 -> 判断是否结束。
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


@dataclass
class Step:
    """单步循环记录。"""
    thought: str
    action: Optional[str] = None
    observation: Any = None


@dataclass
class AgentLoop:
    """Agent 主循环框架。

    通过 planner 决定下一步动作，通过 tools 执行动作，
    直到 planner 返回终止信号或达到最大步数。
    """

    planner: Callable[[str, List[Step]], Dict[str, Any]]
    tools: Dict[str, Callable[[str], Any]] = field(default_factory=dict)
    max_steps: int = 5

    def run(self, task: str) -> List[Step]:
        """执行任务并返回完整步骤轨迹。"""
        steps: List[Step] = []
        for _ in range(self.max_steps):
            decision = self.planner(task, steps)
            step = Step(thought=decision.get("thought", ""))
            action = decision.get("action")
            if action is None:
                steps.append(step)
                break
            step.action = action
            tool = self.tools.get(action)
            if tool is None:
                step.observation = f"unknown tool: {action}"
            else:
                try:
                    step.observation = tool(decision.get("input", ""))
                except Exception as exc:  # 工具失败不中断循环
                    step.observation = f"error: {exc}"
            steps.append(step)
        return steps


def _planner(task: str, steps: List[Step]) -> Dict[str, Any]:
    """演示用规划器：先搜索，再总结。"""
    if not steps:
        return {"thought": "先检索信息", "action": "search", "input": task}
    if len(steps) == 1:
        return {"thought": "根据检索结果总结", "action": "summarize",
                "input": str(steps[0].observation)}
    return {"thought": "任务完成"}


if __name__ == "__main__":
    loop = AgentLoop(
        planner=_planner,
        tools={
            "search": lambda q: f"关于 {q} 的检索结果",
            "summarize": lambda text: f"摘要: {text[:20]}",
        },
    )
    for i, s in enumerate(loop.run("agent loop 设计"), 1):
        print(f"[{i}] thought={s.thought} action={s.action} obs={s.observation}")
