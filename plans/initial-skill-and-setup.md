# Plan: adversarial-process-skill SKILL.md + Python examples.md

## Context

The `adversarial-process-skill` directory exists but its `SKILL.md` is an empty directory (not a file) and `examples.md` is empty. The project is a GAN-style code generation harness with TypeScript reference implementations for five components: Planner, Generator, Evaluator, Logger, and Harness. This plan defines the content for both files and converts the TypeScript examples to idiomatic Python using `claude_code_sdk`.

---

## Prerequisite

`SKILL.md` is currently an empty **directory** at `.claude/skills/adversarial-process-skill/SKILL.md`. It must be removed with `rmdir` before the file can be written.

```
rmdir /Users/peabody/Documents/repos/gan-with-a-plan/.claude/skills/adversarial-process-skill/SKILL.md
```

---

## File 1: `.claude/skills/adversarial-process-skill/SKILL.md`

### Frontmatter
```
---
name: adversarial-process-skill
description: Guides building an adversarial agent network for code generation using either a no-plan loop or a plan-gated loop with Planner, Generator, and Evaluator agents.
---
```

### Sections

**# Generative Adversarial Network for Code Generation**
Brief prose intro — what the pattern is, when to use it, the two loop variants.

**## When to Use This Skill**
Trigger when a user wants to:
- Build a self-improving multi-agent code generation pipeline
- Implement generator-evaluator retry loops (GAN-style)
- Compare plan-gated vs. direct-build agentic approaches
- Replace human review with an autonomous evaluator agent

**## Components**

| Component | Role | SDK Tools | `persist_session` |
|-----------|------|-----------|-------------------|
| Planner | Converts user prompt → `spec.md` | Read, Write | false |
| Generator | Negotiates contract, builds code | Read, Write, Edit, Bash, Glob, Grep | **true** |
| Evaluator | Scores builds, returns pass/fail + feedback | Read, Bash, Glob, Grep | false |
| Logger | Tracks token usage and iteration stats | (none — bookkeeping only) | n/a |
| Harness | Orchestrates the full loop | (calls other components) | n/a |

Note: only the Generator uses `persistSession: true` — it must maintain session state across retry iterations within a sprint.

**## Key Configuration Options**

| Option | Type | Description |
|--------|------|-------------|
| `passThreshold` | float 0–10 | Minimum score per criterion for Evaluator to pass |
| `maxRetriesPerSprint` | int | Max Generator→Evaluator cycles before sprint fails |
| `maxSprints` | int | Max sprint contracts to attempt |
| `workDir` | string | Filesystem path where the Harness initializes the workspace |
| `model` | string | Claude model ID used by all agents |

**## Steps with NO Planning Loop** (numbered, bold sub-headings per skill-reviewer style)

1. **Accept user prompt** — Read prompt from CLI args or `--file`. Construct `HarnessConfig`.
2. **Planner generates spec** — Call Planner (`tools: ["Read","Write"]`, `persistSession: false`). Planner writes `spec.md` to `workDir`. Accumulate assistant text blocks; stop on `result` message.
3. **Negotiate sprint contract** — Harness calls Generator to propose a `SprintContract` JSON. Harness calls Evaluator in `contract` mode to review it. Repeat until approved or attempts exhausted.
4. **Generator builds** — Call Generator with the approved contract and optional `previousFeedback` from prior retries. Capture `{ response, sessionId }`.
5. **Evaluator scores** — Call Evaluator with `persistSession: false`. Parse `EvalResult` using 3-pass JSON extraction (code block → brace match → raw parse). Compute score vs. `passThreshold`.
6. **Retry or advance** — If passing: record sprint passed. If failing and retries remain: pass `EvalResult` back to Generator as `previousFeedback` and return to step 4. If retries exhausted: mark sprint failed and halt.
7. **Log results** — Logger records token usage and per-sprint stats. Harness returns `HarnessResult`.

**## Steps with Planning Loop**

Steps 1–3 same as above, then:

4. **Generator proposes plan** — Call Generator with plan-only system prompt (no code writing). `persistSession: false`.
5. **Evaluator reviews plan** — Score plan on approach quality, coverage, and feasibility. If failing, return to step 4 with feedback. If passing, continue.
6. **Generator implements** — Call Generator to build code based on approved plan and contract. `persistSession: true`. Capture `{ response, sessionId }`.
7. **Evaluator scores implementation** — Same as no-plan step 5.
8. **Retry or advance** — Same as no-plan step 6 (retries apply to the implementation loop only).
9. **Log results** — Same as no-plan step 7.

**## Additional Resources**

Link: `[Python code examples](./examples.md)`

---

## File 2: `.claude/skills/adversarial-process-skill/examples.md`

### Document structure

```
# Adversarial Process Skill — Python Examples

## Type Definitions       (types.py)
## planner.py
## generator.py           (includes plan-only variant)
## evaluator.py           (includes _extract_eval_result helper)
## logger.py
## harness.py
## main.py / Entry Point
```

Each section: one fenced Python code block + 2–4 bullet notes on key decisions.

### Type definitions (replaces TypeScript interfaces)

- `CriterionFeedback`, `EvalResult`, `SprintContract` → `TypedDict` (parsed directly from `json.loads()`)
- `HarnessConfig`, `SprintResult`, `HarnessResult` → `@dataclass` (constructed by application code)

```python
from dataclasses import dataclass, field
from typing import TypedDict

class CriterionFeedback(TypedDict):
    criterion: str
    score: float
    details: str

class EvalResult(TypedDict):
    passed: bool
    feedback: list[CriterionFeedback]
    overallSummary: str

class SprintCriterion(TypedDict):
    name: str
    description: str
    threshold: float

class SprintContract(TypedDict):
    sprintNumber: int
    features: list[str]
    criteria: list[SprintCriterion]

@dataclass
class HarnessConfig:
    work_dir: str
    user_prompt: str
    max_sprints: int = 3
    max_retries_per_sprint: int = 3
    pass_threshold: float = 8.0
    model: str = "claude-opus-4-5"

@dataclass
class SprintResult:
    sprint_number: int
    passed: bool
    retries: int
    eval_result: EvalResult | None = None

@dataclass
class HarnessResult:
    success: bool
    sprints: list[SprintResult] = field(default_factory=list)
    total_duration_ms: float = 0.0
```

### planner.py

```python
from claude_code_sdk import query, ClaudeCodeOptions
from .types import HarnessConfig

async def run_planner(config: HarnessConfig) -> str:
    options = ClaudeCodeOptions(
        cwd=config.work_dir,
        system_prompt=PLANNER_SYSTEM_PROMPT,
        permission_mode="bypassPermissions",
        tools=["Read", "Write"],
        model=config.model,
        max_turns=20,
    )
    full_response = ""
    async for message in query(prompt=config.user_prompt, options=options):
        if message.type == "assistant":
            for block in message.message.content:
                if block.type == "text":
                    full_response += block.text
        elif message.type == "result":
            break
    return full_response
```

Key notes: `persist_session` not set (defaults false). Planner writes `spec.md` to disk; the returned text is a fallback if the file isn't written.

### generator.py

```python
async def run_generator(
    contract: SprintContract,
    config: HarnessConfig,
    previous_feedback: EvalResult | None = None,
    session_id: str | None = None,
) -> tuple[str, str]:  # (response, session_id)
    options = ClaudeCodeOptions(
        cwd=config.work_dir,
        system_prompt=build_generator_prompt(contract, previous_feedback),
        permission_mode="bypassPermissions",
        tools=["Read", "Write", "Edit", "Bash", "Glob", "Grep"],
        model=config.model,
        max_turns=40,
        persist_session=True,
        session_id=session_id,      # resume prior session on retries
    )
    full_response, new_session_id = "", None
    async for message in query(prompt="Implement the sprint contract.", options=options):
        if message.type == "assistant":
            for block in message.message.content:
                if block.type == "text":
                    full_response += block.text
        elif message.type == "result":
            new_session_id = message.session_id
            break
    return full_response, new_session_id

async def run_generator_plan_only(
    contract: SprintContract,
    config: HarnessConfig,
    previous_plan_feedback: EvalResult | None = None,
) -> str:
    # persist_session=False — plan proposals don't carry state
    ...
```

### evaluator.py

```python
async def run_evaluator(
    contract: SprintContract,
    config: HarnessConfig,
    evaluation_mode: str = "implementation",  # "plan" | "contract" | "implementation"
) -> EvalResult:
    options = ClaudeCodeOptions(
        cwd=config.work_dir,
        system_prompt=build_evaluator_prompt(contract, evaluation_mode),
        permission_mode="bypassPermissions",
        tools=["Read", "Bash", "Glob", "Grep"],
        model=config.model,
        max_turns=20,
    )
    raw = ""
    async for message in query(prompt="Evaluate per the contract criteria.", options=options):
        if message.type == "assistant":
            for block in message.message.content:
                if block.type == "text":
                    raw += block.text
        elif message.type == "result":
            break
    result = _extract_eval_result(raw)
    result["passed"] = all(f["score"] >= config.pass_threshold for f in result["feedback"])
    return result

def _extract_eval_result(raw: str) -> EvalResult:
    import re, json
    # Pass 1: fenced code block
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.DOTALL)
    if m:
        return json.loads(m.group(1))
    # Pass 2: brace-balanced substring
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
    # Pass 3: raw parse (raises on failure)
    return json.loads(raw)
```

### logger.py

```python
@dataclass
class IterationLog:
    sprint_number: int
    retry_number: int
    component: str          # "planner" | "generator" | "evaluator"
    input_tokens: int
    output_tokens: int
    duration_ms: float
    passed: bool | None = None

class Logger:
    def __init__(self) -> None:
        self._logs: list[IterationLog] = []

    def record(self, log: IterationLog) -> None:
        self._logs.append(log)

    def sprint_summary(self, sprint_number: int) -> dict: ...
    def full_report(self) -> dict: ...
```

Token counts come from `message.usage.input_tokens` / `message.usage.output_tokens` on `result`-type messages.

### harness.py

```python
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
            sprint_results.append(SprintResult(sprint_num, False, config.max_retries_per_sprint, previous_feedback))
            break   # halt harness on sprint failure

    success = all(s.passed for s in sprint_results)
    return HarnessResult(success, sprint_results, (time.time() - start) * 1000)
```

Key note: Python's `for/else` idiom — the `else` clause runs only when the loop exhausted all retries without `break`.

### main.py / Entry Point

```python
import asyncio, argparse
from .types import HarnessConfig
from .harness import run_harness

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("prompt", nargs="?")
    parser.add_argument("--file")
    parser.add_argument("--plan-loop", action="store_true")
    parser.add_argument("--work-dir", default="./workspace")
    parser.add_argument("--max-sprints", type=int, default=3)
    parser.add_argument("--max-retries", type=int, default=3)
    parser.add_argument("--pass-threshold", type=float, default=8.0)
    args = parser.parse_args()

    prompt = args.prompt or open(args.file).read()
    config = HarnessConfig(
        work_dir=args.work_dir,
        user_prompt=prompt,
        max_sprints=args.max_sprints,
        max_retries_per_sprint=args.max_retries,
        pass_threshold=args.pass_threshold,
    )
    result = asyncio.run(run_harness(config, plan_loop=args.plan_loop))
    for s in result.sprints:
        print(f"Sprint {s.sprint_number}: {'PASSED' if s.passed else 'FAILED'} ({s.retries} retries)")
    print(f"Overall: {'SUCCESS' if result.success else 'FAILED'} in {result.total_duration_ms:.0f}ms")

if __name__ == "__main__":
    main()
```

---

## Critical Files

| Action | Path |
|--------|------|
| Remove (empty dir) | `.claude/skills/adversarial-process-skill/SKILL.md` |
| Create (new file) | `.claude/skills/adversarial-process-skill/SKILL.md` |
| Write | `.claude/skills/adversarial-process-skill/examples.md` |
| Reference (do not modify) | `.claude/skills/project-overview-skill/SKILL.md` |
| Reference (do not modify) | `.claude/skills/skill-reviewer/SKILL.md` |

---

## Verification

1. Confirm `SKILL.md` is a file, not a directory: `ls -la .claude/skills/adversarial-process-skill/`
2. Confirm frontmatter `name:` matches the directory name exactly
3. Confirm the relative link `./examples.md` in SKILL.md resolves to the examples file
4. Run `/skill-reviewer` on the new `adversarial-process-skill` to validate formatting, links, and content quality
