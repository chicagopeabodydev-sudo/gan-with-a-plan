# Adversarial Process Skill — Python Examples: Types

## Type Definitions (types.py)

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
    model: str = "claude-sonnet-4-6"

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

- `CriterionFeedback`, `EvalResult`, `SprintContract` use `TypedDict` — they are parsed directly from `json.loads()` output.
- `HarnessConfig`, `SprintResult`, `HarnessResult` use `@dataclass` — they are constructed by application code.
- `SprintResult.eval_result` is `None` when a sprint fails due to exhausted retries before any evaluation completes.
