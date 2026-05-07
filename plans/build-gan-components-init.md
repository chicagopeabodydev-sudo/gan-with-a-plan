# Plan: Implement GAN-with-a-Plan Python Package

## Context

The repo has full architectural documentation (skill files + examples) but zero Python code. This plan creates the complete working Python package — `src` layout, pip-installable `gan` CLI, pytest scaffolding, and both `.env` files — based on the code patterns defined in `.claude/skills/adversarial-process-skill/examples-*.md`.

---

## File Layout to Create

```
gan-with-a-plan/
├── src/
│   └── gan_with_a_plan/
│       ├── __init__.py          (empty, marks package)
│       ├── types.py
│       ├── planner.py
│       ├── generator.py
│       ├── evaluator.py
│       ├── logger.py
│       ├── harness.py
│       └── main.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_types.py
│   ├── test_evaluator.py
│   ├── test_logger.py
│   └── test_harness.py
├── pyproject.toml
├── .env                         (gitignored — working values)
└── .env.example                 (committed — template)
```

---

## pyproject.toml

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "gan-with-a-plan"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "claude-code-sdk",
    "python-dotenv",
]

[project.scripts]
gan = "gan_with_a_plan.main:main"

[tool.hatch.build.targets.wheel]
packages = ["src/gan_with_a_plan"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

---

## .env.example (committed to git)

```dotenv
PLANNER_MODEL=claude-sonnet-4-6
GENERATOR_MODEL=claude-sonnet-4-6
EVALUATOR_MODEL=claude-opus-4-7
GAN_MODE=implementation
MAX_SPRINTS=3
MAX_RETRIES_PER_SPRINT=3
PASS_THRESHOLD=8.0
```

## .env (gitignored — identical defaults, ready to edit)

Same content as `.env.example`. The `.gitignore` already has `.env` covered.

---

## Source Files

### types.py
Verbatim from `examples-types.md` with one addition: `max_sprints`, `max_retries_per_sprint`, and `pass_threshold` in `HarnessConfig` also read from env vars (matching the model fields pattern):

```python
max_sprints: int = field(default_factory=lambda: int(os.environ.get("MAX_SPRINTS", "3")))
max_retries_per_sprint: int = field(default_factory=lambda: int(os.environ.get("MAX_RETRIES_PER_SPRINT", "3")))
pass_threshold: float = field(default_factory=lambda: float(os.environ.get("PASS_THRESHOLD", "8.0")))
```

### planner.py
Verbatim from `examples-planner.md`. Source: `.claude/skills/adversarial-process-skill/examples-planner.md`

### generator.py
Verbatim from `examples-generator.md` (includes `run_generator` + `run_generator_plan_only`). Source: `.claude/skills/adversarial-process-skill/examples-generator.md`

### evaluator.py
Verbatim from `examples-evaluator.md` (includes `run_evaluator` + `_extract_eval_result`). Source: `.claude/skills/adversarial-process-skill/examples-evaluator.md`

### logger.py
Extract logger section from `examples-harness.md` (`IterationLog` dataclass + `Logger` class). Source: `.claude/skills/adversarial-process-skill/examples-harness.md`

### harness.py
Extract harness section from `examples-harness.md` (`_generator_propose_contract`, `_extract_json`, `_negotiate_contract`, `_run_plan_approval_loop`, `run_harness`). Source: `.claude/skills/adversarial-process-skill/examples-harness.md`

### main.py
Extract main section from `examples-harness.md`. Add `python-dotenv` load at top:
```python
from dotenv import load_dotenv
load_dotenv()
```
Add `sys.exit(0 if result.success else 1)` for CI integration.

---

## Tests

### conftest.py
AsyncMock fixture for `claude_code_sdk.query` that yields a fake assistant message then a fake result message. Used across all component tests.

### test_types.py
- `HarnessConfig` reads `MAX_SPRINTS` / `MAX_RETRIES_PER_SPRINT` / `PASS_THRESHOLD` from env (monkeypatching `os.environ`)

### test_evaluator.py
- `_extract_eval_result` — 3 subtests: fenced JSON block, brace-matched, raw JSON string
- `run_evaluator` passes/fails based on threshold (mocked SDK)

### test_logger.py
- `Logger.record` → `sprint_summary` → `full_report` round-trip

### test_harness.py
- `run_harness` with mocked `run_planner`, `_negotiate_contract`, `run_generator`, `run_evaluator` — verifies sprint pass/fail logic and `for/else` exhaustion path

---

## Critical Files

| Action | Path |
|--------|------|
| Reference | `.claude/skills/adversarial-process-skill/examples-types.md` |
| Reference | `.claude/skills/adversarial-process-skill/examples-planner.md` |
| Reference | `.claude/skills/adversarial-process-skill/examples-generator.md` |
| Reference | `.claude/skills/adversarial-process-skill/examples-evaluator.md` |
| Reference | `.claude/skills/adversarial-process-skill/examples-harness.md` |
| Write | `pyproject.toml` |
| Write | `.env` |
| Write | `.env.example` |
| Write | `src/gan_with_a_plan/__init__.py` |
| Write | `src/gan_with_a_plan/types.py` |
| Write | `src/gan_with_a_plan/planner.py` |
| Write | `src/gan_with_a_plan/generator.py` |
| Write | `src/gan_with_a_plan/evaluator.py` |
| Write | `src/gan_with_a_plan/logger.py` |
| Write | `src/gan_with_a_plan/harness.py` |
| Write | `src/gan_with_a_plan/main.py` |
| Write | `tests/__init__.py` |
| Write | `tests/conftest.py` |
| Write | `tests/test_types.py` |
| Write | `tests/test_evaluator.py` |
| Write | `tests/test_logger.py` |
| Write | `tests/test_harness.py` |

---

## Verification

1. `pip install -e ".[dev]"` — installs package in editable mode
2. `gan --help` — confirms CLI entry point works
3. `pytest` — all tests pass
4. `gan "build a hello world CLI in Python" --work-dir ./workspace --max-sprints 1` — smoke test with real SDK
