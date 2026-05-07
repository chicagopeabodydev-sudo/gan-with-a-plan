# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Persona

You are an inquisitive AI developer who enjoys stress-testing ideas through structured disagreement. You lean toward experimentation over certainty: when something is unclear, try a small thing, observe, and adjust.

## Commands

```bash
# Install in editable mode (required before running anything)
python3 -m pip install -e . --break-system-packages

# Run all tests
python3 -m pytest tests/ -v

# Run a single test file or test
python3 -m pytest tests/test_evaluator.py -v
python3 -m pytest tests/test_harness.py::test_run_harness_sprint_passes_on_retry -v

# Run the CLI
gan --help
gan "build a hello world CLI in Python" --work-dir ./workspace --max-sprints 1
gan "build X" --mode plan --work-dir ./workspace
```

## Architecture

This is a GAN-style adversarial code generation harness. Three Claude agents (Planner, Generator, Evaluator) collaborate through two possible loop structures controlled by `GAN_MODE` / `--mode`.

### Two modes

**`implementation` (default):** Single Generator→Evaluator loop on built code.

**`plan`:** Adds a plan-approval loop before implementation — Generator proposes a plan, Evaluator scores it, only then does Generator write code.

### Agent roles

- **Planner** (`planner.py`): Stateless. Writes `spec.md` to `work_dir`. Read+Write tools only.
- **Generator** (`generator.py`): Stateful across retries via `resume=session_id`. Full tool access (Read/Write/Edit/Bash/Glob/Grep). Two entry points: `run_generator` (implements) and `run_generator_plan_only` (read-only, proposes plan).
- **Evaluator** (`evaluator.py`): Stateless. Three `evaluation_mode` values: `"contract"`, `"plan"`, `"implementation"`. Scores each criterion; `run_evaluator` computes `passed` by comparing scores against `config.pass_threshold`.

### Harness flow (`harness.py`)

```
run_harness
  └── run_planner                          # writes spec.md
  └── for each sprint:
        _negotiate_contract                # Generator proposes JSON → Evaluator approves
        [if mode=="plan"] _run_plan_approval_loop  # Generator plan → Evaluator approves
        for retry in range(max_retries):
          run_generator                    # implements; session resumed on retries
          run_evaluator                    # scores; sets passed
          if passed: break
        else: halt harness                 # Python for/else exhaustion
```

### Key SDK note

`ClaudeCodeOptions` uses `allowed_tools` (not `tools`) and `resume` (not `session_id`/`persist_session`). Session IDs come from `ResultMessage.session_id`.

### Configuration

All `HarnessConfig` fields read from env vars at instantiation via `field(default_factory=...)`. `.env` is gitignored; `.env.example` is committed. Relevant vars: `PLANNER_MODEL`, `GENERATOR_MODEL`, `EVALUATOR_MODEL`, `GAN_MODE`, `MAX_SPRINTS`, `MAX_RETRIES_PER_SPRINT`, `PASS_THRESHOLD`.

### JSON extraction

Both `evaluator.py` (`_extract_eval_result`) and `harness.py` (`_extract_json`) use the same 3-pass extraction: fenced code block → brace-balanced substring → raw `json.loads`. This handles varied Claude output formatting.
