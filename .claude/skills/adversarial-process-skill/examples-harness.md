# Adversarial Process Skill — Python Examples: Harness

## logger.py

```python
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
```

- Token counts come from `message.usage.input_tokens` / `message.usage.output_tokens` on `result`-type SDK messages.
- `passed` is `None` for components that don't produce a pass/fail verdict (e.g., Planner).

## harness.py

```python
import os, time
from claude_code_sdk import query, ClaudeCodeOptions
from .types import HarnessConfig, HarnessResult, SprintResult, SprintContract
from .planner import run_planner
from .generator import run_generator, run_generator_plan_only
from .evaluator import run_evaluator

async def _generator_propose_contract(config: HarnessConfig, sprint_num: int) -> SprintContract:
    """Generator reads spec.md and proposes a sprint contract as JSON."""
    import json as _json
    spec_path = os.path.join(config.work_dir, "spec.md")
    prompt = f"Read {spec_path} and propose a SprintContract JSON for sprint {sprint_num}. Output only the JSON object."
    options = ClaudeCodeOptions(
        cwd=config.work_dir,
        system_prompt="You are a sprint planner. Produce a single SprintContract JSON object and nothing else.",
        permission_mode="bypassPermissions",
        tools=["Read"],
        model=config.generator_model,
        max_turns=10,
    )
    raw = ""
    async for message in query(prompt=prompt, options=options):
        if message.type == "assistant":
            for block in message.message.content:
                if block.type == "text":
                    raw += block.text
        elif message.type == "result":
            break
    return _extract_json(raw)

def _extract_json(raw: str) -> dict:
    import re, json
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.DOTALL)
    if m:
        return json.loads(m.group(1))
    start = raw.find("{")
    if start != -1:
        depth, end = 0, -1
        for i, ch in enumerate(raw[start:], start):
            if ch == "{": depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0: end = i; break
        if end != -1:
            return json.loads(raw[start:end + 1])
    return json.loads(raw)

async def _negotiate_contract(config: HarnessConfig, sprint_num: int):
    """Generator proposes a contract; Evaluator approves it."""
    for _ in range(config.max_retries_per_sprint):
        contract = await _generator_propose_contract(config, sprint_num)
        review = await run_evaluator(contract, config, evaluation_mode="contract")
        if review["passed"]:
            return contract
    raise RuntimeError(f"Could not negotiate a contract for sprint {sprint_num}")

async def _run_plan_approval_loop(contract, config: HarnessConfig) -> None:
    """Plan-gated variant: approve a Generator plan before implementation."""
    plan_path = os.path.join(config.work_dir, "plan.md")
    previous_plan_feedback = None
    for _ in range(config.max_retries_per_sprint):
        plan = await run_generator_plan_only(contract, config, previous_plan_feedback)
        # Write plan to disk so the Evaluator agent can read it via its filesystem tools
        with open(plan_path, "w") as f:
            f.write(plan)
        review = await run_evaluator(contract, config, evaluation_mode="plan")
        if review["passed"]:
            return
        previous_plan_feedback = review
    raise RuntimeError("Plan approval loop exhausted retries")

async def run_harness(config: HarnessConfig, plan_loop: bool = False) -> HarnessResult:
    os.makedirs(config.work_dir, exist_ok=True)
    start = time.time()

    await run_planner(config)

    sprint_results = []
    for sprint_num in range(1, config.max_sprints + 1):
        contract = await _negotiate_contract(config, sprint_num)

        if plan_loop:
            await _run_plan_approval_loop(contract, config)

        session_id, previous_feedback = None, None
        for retry in range(config.max_retries_per_sprint):
            _, session_id = await run_generator(contract, config, previous_feedback, session_id)
            eval_result = await run_evaluator(contract, config)
            if eval_result["passed"]:
                sprint_results.append(SprintResult(sprint_num, True, retry, eval_result))
                break
            previous_feedback = eval_result
        else:
            # Python for/else: this block runs only when the loop exhausted all retries without break
            sprint_results.append(SprintResult(sprint_num, False, config.max_retries_per_sprint, previous_feedback))
            break  # halt harness on sprint failure

    success = all(s.passed for s in sprint_results)
    return HarnessResult(success, sprint_results, (time.time() - start) * 1000)
```

- `_generator_propose_contract` calls the Generator agent with read-only tools to produce a `SprintContract` JSON from `spec.md`; `_extract_json` reuses the same 3-pass extraction logic as the Evaluator.
- `_run_plan_approval_loop` writes the plan string to `plan.md` before calling the Evaluator, giving the Evaluator's filesystem tools something to read.
- Python's `for/else` idiom — the `else` clause runs only when the loop exhausted all retries without `break`, cleanly distinguishing pass vs. exhaustion.
- `session_id` is threaded through retry iterations so the Generator resumes its prior context.
- `plan_loop=True` inserts `_run_plan_approval_loop` between contract negotiation and implementation — the implementation retry loop is unchanged.

## main.py / Entry Point

```python
import asyncio, argparse, os
from .types import HarnessConfig
from .harness import run_harness

def main():
    parser = argparse.ArgumentParser(description="GAN-style adversarial code generation harness")
    parser.add_argument("prompt", nargs="?", help="Task description")
    parser.add_argument("--file", help="Read prompt from file instead of CLI arg")
    parser.add_argument("--plan-loop", action="store_true", help="Enable plan-gated loop")
    parser.add_argument("--work-dir", default="./workspace", help="Working directory for agents")
    parser.add_argument("--max-sprints", type=int, default=3)
    parser.add_argument("--max-retries", type=int, default=3)
    parser.add_argument("--pass-threshold", type=float, default=8.0)
    parser.add_argument("--planner-model",
        default=os.environ.get("PLANNER_MODEL", "claude-sonnet-4-6"))
    parser.add_argument("--generator-model",
        default=os.environ.get("GENERATOR_MODEL", "claude-sonnet-4-6"))
    parser.add_argument("--evaluator-model",
        default=os.environ.get("EVALUATOR_MODEL", "claude-opus-4-7"))
    args = parser.parse_args()

    if not args.prompt and not args.file:
        parser.error("provide a prompt argument or --file")
    prompt = args.prompt or open(args.file).read()
    config = HarnessConfig(
        work_dir=args.work_dir,
        user_prompt=prompt,
        max_sprints=args.max_sprints,
        max_retries_per_sprint=args.max_retries,
        pass_threshold=args.pass_threshold,
        planner_model=args.planner_model,
        generator_model=args.generator_model,
        evaluator_model=args.evaluator_model,
    )
    result = asyncio.run(run_harness(config, plan_loop=args.plan_loop))

    for s in result.sprints:
        status = "PASSED" if s.passed else "FAILED"
        print(f"Sprint {s.sprint_number}: {status} ({s.retries} retries)")
    print(f"Overall: {'SUCCESS' if result.success else 'FAILED'} in {result.total_duration_ms:.0f}ms")

if __name__ == "__main__":
    main()
```

- `parser.error()` is called when neither `prompt` nor `--file` is supplied — this prints a usage message and exits with code 2, which is standard argparse behaviour.
- `asyncio.run()` is the entry point for the async harness from a synchronous CLI context.
- Exit code is not set explicitly; add `sys.exit(0 if result.success else 1)` for CI integration.
