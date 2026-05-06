---
name: adversarial-process-skill
description: Guides building an adversarial agent network for code generation using either a no-plan loop or a plan-gated loop with Planner, Generator, and Evaluator agents.
---

# Generative Adversarial Network for Code Generation

This pattern uses two competing agents — a Generator that builds code and an Evaluator that scores it — to drive iterative improvement without human review. The loop repeats until the Evaluator is satisfied or retry limits are reached. Two variants exist: a **no-plan loop** where the Generator builds directly, and a **plan-gated loop** where the Generator's approach is evaluated before any code is written.

## When to Use This Skill

Trigger when a user wants to:

- Build a self-improving multi-agent code generation pipeline
- Implement generator-evaluator retry loops (GAN-style)

## Components

| Component | Role | SDK Tools | `persist_session` |
|-----------|------|-----------|-------------------|
| Planner | Converts user prompt → `spec.md` | Read, Write | false |
| Generator | Negotiates contract, builds code | Read, Write, Edit, Bash, Glob, Grep | **true** |
| Evaluator | Scores builds, returns pass/fail + feedback | Read, Bash, Glob, Grep | false |
| Logger | Tracks token usage and iteration stats | (none — bookkeeping only) | n/a |
| Harness | Orchestrates the full loop | (calls other components) | n/a |

Note: only the Generator uses `persist_session: true` — it must maintain session state across retry iterations within a sprint.

## Key Configuration Options

| Option | Type | Description |
|--------|------|-------------|
| `pass_threshold` | float 0–10 | Minimum score per criterion for Evaluator to pass |
| `max_retries_per_sprint` | int | Max Generator→Evaluator cycles before sprint fails |
| `max_sprints` | int | Max sprint contracts to attempt |
| `work_dir` | string | Filesystem path where the Harness initializes the workspace |
| `model` | string | Claude model ID used by all agents |

## Steps with NO Planning Loop

1. **Accept user prompt** — Read prompt from CLI args or `--file`. Construct `HarnessConfig`.
2. **Planner generates spec** — Call Planner (`tools: ["Read","Write"]`, `persist_session: false`). Planner writes `spec.md` to `work_dir`. Accumulate assistant text blocks; stop on `result` message.
3. **Negotiate sprint contract** — Harness calls Generator to propose a `SprintContract` JSON. Harness calls Evaluator in `contract` mode to review it. Repeat until approved or attempts exhausted.
4. **Generator builds** — Call Generator with the approved contract and optional `previous_feedback` from prior retries. Capture `(response, session_id)`.
5. **Evaluator scores** — Call Evaluator with `persist_session: false`. Parse `EvalResult` using 3-pass JSON extraction (code block → brace match → raw parse). Compute score vs. `pass_threshold`.
6. **Retry or advance** — If passing: record sprint passed. If failing and retries remain: pass `EvalResult` back to Generator as `previous_feedback` and return to step 4. If retries exhausted: mark sprint failed and halt.
7. **Log results** — Logger records token usage and per-sprint stats. Harness returns `HarnessResult`.

## Steps with Planning Loop

Steps 1–3 same as above, then:

4. **Generator proposes plan** — Call Generator with plan-only system prompt (no code writing). `persist_session: false`.
5. **Evaluator reviews plan** — Score plan on approach quality, coverage, and feasibility. If failing, return to step 4 with feedback. If passing, continue.
6. **Generator implements** — Call Generator to build code based on approved plan and contract. `persist_session: true`. Capture `(response, session_id)`.
7. **Evaluator scores implementation** — Same as no-plan step 5.
8. **Retry or advance** — Same as no-plan step 6 (retries apply to the implementation loop only).
9. **Log results** — Same as no-plan step 7.

## Additional Resources

- [Type definitions](./examples-types.md)
- [Planner examples](./examples-planner.md)
- [Generator examples](./examples-generator.md)
- [Evaluator examples](./examples-evaluator.md)
- [Harness, Logger & Entry Point examples](./examples-harness.md)
