# Adversarial Process Skill — Python Examples: Types

## Type Definitions (types.py)

```python
import os
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
    planner_model: str = field(default_factory=lambda: os.environ.get("PLANNER_MODEL", "claude-sonnet-4-6"))
    generator_model: str = field(default_factory=lambda: os.environ.get("GENERATOR_MODEL", "claude-sonnet-4-6"))
    evaluator_model: str = field(default_factory=lambda: os.environ.get("EVALUATOR_MODEL", "claude-opus-4-7"))

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

- Each model field reads its env var at instantiation time via `field(default_factory=...)`. Set `PLANNER_MODEL`, `GENERATOR_MODEL`, or `EVALUATOR_MODEL` to override without changing code. The Evaluator defaults to `claude-opus-4-7` while the Generator defaults to `claude-sonnet-4-6` — ensuring the judge is a different (more capable) model than the builder by default.
- `CriterionFeedback`, `EvalResult`, `SprintContract` use `TypedDict` — they are parsed directly from `json.loads()` output.
- `HarnessConfig`, `SprintResult`, `HarnessResult` use `@dataclass` — they are constructed by application code.
- `SprintResult.eval_result` is `None` when a sprint fails due to exhausted retries before any evaluation completes.
