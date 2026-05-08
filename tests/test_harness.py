import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from gan_with_a_plan.harness import run_harness
from gan_with_a_plan.types import HarnessConfig, HarnessResult, CallMetrics

SAMPLE_CONTRACT = {"sprintNumber": 1, "features": ["feature-a"], "criteria": []}
PASSING_EVAL = {"passed": True, "feedback": [{"criterion": "c", "score": 9.0, "details": ""}], "overallSummary": "pass"}
FAILING_EVAL = {"passed": False, "feedback": [{"criterion": "c", "score": 5.0, "details": ""}], "overallSummary": "fail"}
SAMPLE_METRICS = CallMetrics(input_tokens=10, output_tokens=5, turn_count=2, duration_ms=100.0)

@pytest.fixture
def config():
    return HarnessConfig(work_dir="/tmp/test-harness", user_prompt="build something",
                         max_sprints=1, max_retries_per_sprint=2, pass_threshold=8.0)

@pytest.mark.asyncio
async def test_run_harness_sprint_passes_on_first_try(config, tmp_path):
    config.work_dir = str(tmp_path)
    with patch("gan_with_a_plan.harness.run_planner", new=AsyncMock(return_value=("spec", SAMPLE_METRICS))), \
         patch("gan_with_a_plan.harness._negotiate_contract", new=AsyncMock(return_value=SAMPLE_CONTRACT)), \
         patch("gan_with_a_plan.harness.run_generator", new=AsyncMock(return_value=("code", "sid-1", SAMPLE_METRICS))), \
         patch("gan_with_a_plan.harness.run_evaluator", new=AsyncMock(return_value=(PASSING_EVAL, SAMPLE_METRICS))):
        result = await run_harness(config)

    assert result.success is True
    assert len(result.sprints) == 1
    assert result.sprints[0].passed is True
    assert result.sprints[0].retries == 0

@pytest.mark.asyncio
async def test_run_harness_sprint_passes_on_retry(config, tmp_path):
    config.work_dir = str(tmp_path)
    eval_calls = [(FAILING_EVAL, SAMPLE_METRICS), (PASSING_EVAL, SAMPLE_METRICS)]
    eval_mock = AsyncMock(side_effect=eval_calls)

    with patch("gan_with_a_plan.harness.run_planner", new=AsyncMock(return_value=("spec", SAMPLE_METRICS))), \
         patch("gan_with_a_plan.harness._negotiate_contract", new=AsyncMock(return_value=SAMPLE_CONTRACT)), \
         patch("gan_with_a_plan.harness.run_generator", new=AsyncMock(return_value=("code", "sid-1", SAMPLE_METRICS))), \
         patch("gan_with_a_plan.harness.run_evaluator", new=eval_mock):
        result = await run_harness(config)

    assert result.success is True
    assert result.sprints[0].retries == 1

@pytest.mark.asyncio
async def test_run_harness_sprint_exhausts_retries(config, tmp_path):
    config.work_dir = str(tmp_path)
    with patch("gan_with_a_plan.harness.run_planner", new=AsyncMock(return_value=("spec", SAMPLE_METRICS))), \
         patch("gan_with_a_plan.harness._negotiate_contract", new=AsyncMock(return_value=SAMPLE_CONTRACT)), \
         patch("gan_with_a_plan.harness.run_generator", new=AsyncMock(return_value=("code", "sid-1", SAMPLE_METRICS))), \
         patch("gan_with_a_plan.harness.run_evaluator", new=AsyncMock(return_value=(FAILING_EVAL, SAMPLE_METRICS))):
        result = await run_harness(config)

    assert result.success is False
    assert result.sprints[0].passed is False
    assert result.sprints[0].retries == config.max_retries_per_sprint

@pytest.mark.asyncio
async def test_log_report_attached_to_result(config, tmp_path):
    config.work_dir = str(tmp_path)
    with patch("gan_with_a_plan.harness.run_planner", new=AsyncMock(return_value=("spec", SAMPLE_METRICS))), \
         patch("gan_with_a_plan.harness._negotiate_contract", new=AsyncMock(return_value=SAMPLE_CONTRACT)), \
         patch("gan_with_a_plan.harness.run_generator", new=AsyncMock(return_value=("code", "sid-1", SAMPLE_METRICS))), \
         patch("gan_with_a_plan.harness.run_evaluator", new=AsyncMock(return_value=(PASSING_EVAL, SAMPLE_METRICS))):
        result = await run_harness(config)

    assert result.log_report["mode"] == "implementation"
    assert result.log_report["total_tokens"] > 0
    assert "implementation" in result.log_report["phases"]
