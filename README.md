# gan-with-a-plan

A GAN-style adversarial code generation harness where a Generator agent builds code and an Evaluator agent scores it, returning it to the Generator with improvement suggestions until it passes the threshold. Supports two loop variants — see [How It Works](#how-it-works) for the full flow.

- **implementation** (default): a single Generator→Evaluator loop; the Generator implements the sprint and the Evaluator scores it.
- **plan and implementation**: two Generator→Evaluator loops; the Evaluator first approves a plan before any code is written, then scores the implementation.

## Motivation (theory being tested)

Plans are far more concise than full code implementations, so iterating on a plan is cheaper per token and converges faster. A better plan also improves the Generator's first implementation attempt, which reduces retries in the implementation loop. The hypothesis is that savings in the implementation loop more than offset the cost of the plan-approval loop.


## Requirements

- Python 3.11+
- [Claude Code SDK](https://github.com/anthropics/claude-code) (`claude-code-sdk`)
- A valid Anthropic API key available to the Claude Code SDK

## Installation

```bash
pip install -e .
```

## Environment Variables

Copy `.env.example` to `.env` and adjust as needed:

```bash
cp .env.example .env
```

| Variable | Default | Description |
|---|---|---|
| `GAN_MODE` | `implementation` | Loop variant: `implementation` or `plan` |
| `PLANNER_MODEL` | `claude-haiku` | Model used by the Planner agent |
| `GENERATOR_MODEL` | `claude-haiku` | Model used by the Generator agent |
| `EVALUATOR_MODEL` | `claude-sonnet-4-6` | Model used by the Evaluator agent |
| `MAX_SPRINTS` | `3` | Number of sprints to attempt |
| `MAX_RETRIES_PER_SPRINT` | `3` | Max Generator→Evaluator retries per sprint |
| `PASS_THRESHOLD` | `8.0` | Minimum score (0–10) for a criterion to pass |

## Usage

```bash
# Standard mode — Generator builds, Evaluator scores
gan "build a hello world CLI in Python" --work-dir ./workspace

# Plan-gated mode — Evaluator approves the plan before any code is written
gan "build a hello world CLI in Python" --work-dir ./workspace --mode plan

# Read prompt from a file
gan --file prompt.txt --work-dir ./workspace --max-sprints 2
```

All env var defaults can be overridden via CLI flags — run `gan --help` for the full list.

## How It Works

1. **Planner** reads the prompt and writes a `spec.md` to the working directory
2. **Generator** and **Evaluator** negotiate a sprint contract (structured acceptance criteria)
3. *(plan mode)* Generator proposes a plan; Evaluator must approve it before implementation
4. **Generator** implements the sprint; **Evaluator** scores it against the contract
5. If the score meets `PASS_THRESHOLD`, the sprint passes — otherwise the Generator retries with feedback

## Running Tests

```bash
pytest
```
