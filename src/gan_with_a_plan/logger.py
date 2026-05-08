from .types import IterationLog

# Re-export for backwards compatibility with existing imports
__all__ = ["Logger", "IterationLog"]

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
            "total_turn_count": sum(l.turn_count for l in sprint_logs),
            "total_duration_ms": sum(l.duration_ms for l in sprint_logs),
            "iterations": len(sprint_logs),
        }

    def phase_report(self) -> dict:
        phases = sorted({l.phase for l in self._logs})
        result = {}
        for phase in phases:
            logs = [l for l in self._logs if l.phase == phase]
            scored = [l for l in logs if l.passed is not None]
            result[phase] = {
                "input_tokens": sum(l.input_tokens for l in logs),
                "output_tokens": sum(l.output_tokens for l in logs),
                "total_tokens": sum(l.input_tokens + l.output_tokens for l in logs),
                "turn_count": sum(l.turn_count for l in logs),
                "duration_ms": sum(l.duration_ms for l in logs),
                "call_count": len(logs),
                "pass_rate": (sum(1 for l in scored if l.passed) / len(scored)) if scored else None,
            }
        return result

    def full_report(self, mode: str | None = None) -> dict:
        total_input = sum(l.input_tokens for l in self._logs)
        total_output = sum(l.output_tokens for l in self._logs)
        return {
            "mode": mode,
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
            "total_tokens": total_input + total_output,
            "total_turn_count": sum(l.turn_count for l in self._logs),
            "total_duration_ms": sum(l.duration_ms for l in self._logs),
            "sprints": [self.sprint_summary(n) for n in sorted({l.sprint_number for l in self._logs})],
            "phases": self.phase_report(),
        }
