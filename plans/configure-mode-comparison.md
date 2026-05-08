# Plan: Wire Metrics Logging for GAN Mode Comparison

## Context

The GAN harness has two modes (`implementation` and `plan`) whose comparative "effort cost" needs to be measurable. A `Logger` class and `IterationLog` dataclass already exist but are never instantiated or called — no token data is extracted from SDK result messages, no phase labels exist, and no report is attached to `HarnessResult`. This plan wires everything together so that after any run you can see tokens, turns, loop counts, and duration broken down by phase, and compare across modes.

---

## What to Build

### Additional effort metrics (beyond tokens)
- **Turn count** — how many SDK "assistant" messages each agent call consumed (complexity signal)
- **Duration per phase** — wall-clock ms per loop
- **Pass rate per phase** — fraction of evaluator calls that passed on first try (retry pressure)
- **Retry count per phase** — already partially tracked; now labeled by phase
- **Plan-mode overhead** — visible by comparing "plan" + "contract" phase tokens vs "implementation"-mode totals

---

## File-by-File Changes

### 1. `src/gan_with_a_plan/types.py`

Add `CallMetrics` dataclass (returned by every agent function — agent owns the stream, harness owns the context):

```python
@dataclass
class CallMetrics:
    input_tokens: int
    output_tokens: int
    turn_count: int      # count of "assistant" messages in stream
    duration_ms: float
```

Update `IterationLog` — add `phase` and `turn_count` with defaults so existing test constructions compile without changes:

```python
@dataclass
class IterationLog:
    sprint_number: int
    retry_number: int
    component: Literal["planner", "generator", "evaluator"]
    phase: Literal["planner", "contract", "plan", "implementation"] = "implementation"
    input_tokens: int = 0
    output_tokens: int = 0
    turn_count: int = 0
    duration_ms: float = 0.0
    passed: bool | None = None
```

Update `HarnessResult` — add `log_report`:

```python
@dataclass
class HarnessResult:
    success: bool
    sprints: list[SprintResult] = field(default_factory=list)
    total_duration_ms: float = 0.0
    log_report: dict = field(default_factory=dict)   # NEW
```

---

### 2. `src/gan_with_a_plan/logger.py`

- Remove `IterationLog` dataclass definition (it moves to `types.py`); add `from .types import IterationLog`
- Update `sprint_summary()` to include `total_turn_count` and `total_duration_ms` (additive — existing tests still pass)
- Update `full_report(mode=None)` to include `mode`, `total_tokens`, `total_turn_count`, `total_duration_ms`, and `phases`
- Add `phase_report()` method:

```python
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
```

---

### 3. `src/gan_with_a_plan/planner.py`

- Add `import time` and `from .types import CallMetrics`
- Change return type: `-> tuple[str, CallMetrics]`
- In the stream loop: count `turn_count` on `assistant` messages; on `result` message read `message.usage.input_tokens` / `message.usage.output_tokens` via a safe getter (guard with `getattr`)
- Return `(full_response, CallMetrics(...))`

---

### 4. `src/gan_with_a_plan/generator.py`

- Add `import time` and `from .types import CallMetrics`
- `run_generator` → `tuple[str, str | None, CallMetrics]` (was 2-tuple)
- `run_generator_plan_only` → `tuple[str, CallMetrics]` (was `str`)
- Same stream instrumentation pattern in both

---

### 5. `src/gan_with_a_plan/evaluator.py`

- Add `import time` and `from .types import CallMetrics`
- `run_evaluator` → `tuple[EvalResult, CallMetrics]` (was `EvalResult`)
- Same stream instrumentation pattern

**Shared token-extraction helper** (inline in each file to avoid a new module):
```python
def _get_usage(msg) -> tuple[int, int]:
    u = getattr(msg, "usage", None)
    return (getattr(u, "input_tokens", 0), getattr(u, "output_tokens", 0)) if u else (0, 0)
```

---

### 6. `src/gan_with_a_plan/harness.py`

- Add imports: `from .logger import Logger` and `IterationLog` (already imports from `.types`)
- `_generator_propose_contract` → `tuple[SprintContract, CallMetrics]`
- `_negotiate_contract(config, sprint_num, logger)` — unpack gen + eval metrics, call `logger.record()` for each with `phase="contract"`
- `_run_plan_approval_loop(contract, config, sprint_num, logger)` — unpack metrics, record with `phase="plan"`
- `run_harness`:
  - Instantiate `logger = Logger()` at top
  - Unpack `_, planner_metrics = await run_planner(config)`; record with `phase="planner"`, `sprint_number=0`
  - Pass `logger` and `sprint_num` to `_negotiate_contract` and `_run_plan_approval_loop`
  - In the retry loop: unpack `_, session_id, gen_metrics` and `eval_result, eval_metrics`; record both with `phase="implementation"`
  - At the end: `log_report = logger.full_report(mode=config.mode)` → return `HarnessResult(..., log_report=log_report)`

> Note: `sprint_number=0` for the planner log is intentional — it keeps planner cost visible without polluting per-sprint aggregations.

---

### 7. `src/gan_with_a_plan/main.py`

After the existing sprint-status loop, print the metrics report:

```python
report = result.log_report
if report:
    print(f"\n=== Metrics Report (mode={report.get('mode')}) ===")
    print(f"Total tokens : {report['total_tokens']:,}  "
          f"(in={report['total_input_tokens']:,}, out={report['total_output_tokens']:,})")
    print(f"Total turns  : {report['total_turn_count']}")
    print(f"Total time   : {report['total_duration_ms']:.0f}ms")
    print("\nPhase breakdown:")
    for phase, data in report.get("phases", {}).items():
        pr = f"  pass_rate={data['pass_rate']:.0%}" if data["pass_rate"] is not None else ""
        print(f"  {phase:16s} tokens={data['total_tokens']:>8,}  "
              f"turns={data['turn_count']:>4}  "
              f"time={data['duration_ms']:>8.0f}ms  "
              f"calls={data['call_count']}{pr}")
```

---

## Test Changes

### `tests/conftest.py`
Update fake `result` message to include `usage`:
```python
result.usage = MagicMock()
result.usage.input_tokens = 10
result.usage.output_tokens = 5
```

### `tests/test_evaluator.py`
`run_evaluator` now returns `(result, metrics)` — unpack in each test:
```python
result, _ = await run_evaluator(contract, config)
assert result["passed"] is True
```

### `tests/test_harness.py`
Add `SAMPLE_METRICS = CallMetrics(input_tokens=10, output_tokens=5, turn_count=2, duration_ms=100.0)` at top.

Update mock return values:
- `run_planner` → `("spec", SAMPLE_METRICS)`
- `run_generator` → `("code", "sid-1", SAMPLE_METRICS)`
- `run_evaluator` → `(PASSING_EVAL, SAMPLE_METRICS)` / `(FAILING_EVAL, SAMPLE_METRICS)`
- `eval_calls` side_effect → `[(FAILING_EVAL, SAMPLE_METRICS), (PASSING_EVAL, SAMPLE_METRICS)]`

Add new test: `test_log_report_attached_to_result` — assert `result.log_report["mode"] == "implementation"`, `result.log_report["total_tokens"] > 0`, `"implementation" in result.log_report["phases"]`.

### `tests/test_logger.py`
Existing 3 tests pass unchanged (new `IterationLog` fields have defaults; existing report keys are additive).

Add new tests:
- `test_phase_report_groups_by_phase` — records "contract"/"implementation" phase logs, checks keys
- `test_full_report_includes_phase_data` — checks `"phases"` and `"mode"` keys in report
- `test_sprint_summary_includes_turn_count` — checks `total_turn_count` in summary
- `test_pass_rate_calculation` — 2-of-3 evaluator logs passing → `pass_rate ≈ 0.667`

---

## Execution Order

1. `types.py` (all downstream imports from here)
2. `logger.py`
3. `planner.py`, `generator.py`, `evaluator.py` (independent of each other)
4. `harness.py`
5. `main.py`
6. `tests/conftest.py`
7. `tests/test_evaluator.py`, `tests/test_harness.py`, `tests/test_logger.py`

---

## Verification

Run `implementation` mode first, then `plan` mode sequentially using separate work directories:

```bash
# Install editable
python3 -m pip install -e . --break-system-packages

# Run all tests
python3 -m pytest tests/ -v

# Run 1: implementation mode
gan "build a hello world CLI in Python" --work-dir ./workspace-impl --max-sprints 1 --mode implementation

# Run 2: plan mode
gan "build a hello world CLI in Python" --work-dir ./workspace-plan --max-sprints 1 --mode plan
```

Expected output per run: a metrics table showing phases, tokens, turns, and duration.

- `implementation` run phases: `planner`, `contract`, `implementation`
- `plan` run phases: `planner`, `contract`, `plan`, `implementation`

Compare the two printed reports side-by-side to evaluate plan-mode overhead in tokens, turns, and time vs any reduction in implementation retries.
