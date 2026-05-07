from dataclasses import dataclass
from typing import Literal

@dataclass
class IterationLog:
    sprint_number: int
    retry_number: int
    component: Literal["planner", "generator", "evaluator"]
    input_tokens: int
    output_tokens: int
    duration_ms: float
    passed: bool | None = None

class Logger:
    def __init__(self) -> None:
        self._logs: list[IterationLog] = []

    def record(self, log: IterationLog) -> None:
        self._logs.append(log)

    def sprint_summary(self, sprint_number: int) -> dict:
        sprint_logs = [l for l in self._logs if l.sprint_number == sprint_number]
        return {
            "sprint": sprint_number,
            "total_input_tokens": sum(l.input_tokens for l in sprint_logs),
            "total_output_tokens": sum(l.output_tokens for l in sprint_logs),
            "iterations": len(sprint_logs),
        }

    def full_report(self) -> dict:
        return {
            "total_input_tokens": sum(l.input_tokens for l in self._logs),
            "total_output_tokens": sum(l.output_tokens for l in self._logs),
            "sprints": [self.sprint_summary(n) for n in sorted({l.sprint_number for l in self._logs})],
        }
