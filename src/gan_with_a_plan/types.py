import os
from dataclasses import dataclass, field
from typing import Literal, TypedDict

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
    max_sprints: int = field(default_factory=lambda: int(os.environ.get("MAX_SPRINTS", "3")))
    max_retries_per_sprint: int = field(default_factory=lambda: int(os.environ.get("MAX_RETRIES_PER_SPRINT", "3")))
    pass_threshold: float = field(default_factory=lambda: float(os.environ.get("PASS_THRESHOLD", "8.0")))
    planner_model: str = field(default_factory=lambda: os.environ.get("PLANNER_MODEL", "claude-sonnet-4-6"))
    generator_model: str = field(default_factory=lambda: os.environ.get("GENERATOR_MODEL", "claude-sonnet-4-6"))
    evaluator_model: str = field(default_factory=lambda: os.environ.get("EVALUATOR_MODEL", "claude-opus-4-7"))
    mode: str = field(default_factory=lambda: os.environ.get("GAN_MODE", "implementation"))
    # "implementation" = no-plan loop; "plan" = plan-gated loop

@dataclass
class CallMetrics:
    input_tokens: int
    output_tokens: int
    turn_count: int
    duration_ms: float

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
    log_report: dict = field(default_factory=dict)
