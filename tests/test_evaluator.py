import pytest
from gan_with_a_plan.evaluator import _extract_eval_result, run_evaluator
from gan_with_a_plan.types import HarnessConfig

SAMPLE_EVAL = '{"passed": false, "feedback": [{"criterion": "correctness", "score": 9.0, "details": "good"}], "overallSummary": "looks good"}'

def test_extract_eval_result_fenced():
    raw = f"```json\n{SAMPLE_EVAL}\n```"
    result = _extract_eval_result(raw)
    assert result["overallSummary"] == "looks good"

def test_extract_eval_result_brace_balanced():
    raw = f"Here is the result: {SAMPLE_EVAL} end"
    result = _extract_eval_result(raw)
    assert result["feedback"][0]["criterion"] == "correctness"

def test_extract_eval_result_raw_json():
    result = _extract_eval_result(SAMPLE_EVAL)
    assert result["passed"] is False

@pytest.mark.asyncio
async def test_run_evaluator_passes(monkeypatch, fake_sdk_query):
    config = HarnessConfig(work_dir="/tmp", user_prompt="test", pass_threshold=8.0)
    contract = {"sprintNumber": 1, "features": [], "criteria": []}

    monkeypatch.setattr(
        "gan_with_a_plan.evaluator.query",
        fake_sdk_query(assistant_text=SAMPLE_EVAL),
    )

    result, _ = await run_evaluator(contract, config)
    assert result["passed"] is True  # score 9.0 >= threshold 8.0

@pytest.mark.asyncio
async def test_run_evaluator_fails_below_threshold(monkeypatch, fake_sdk_query):
    low_score = '{"passed": false, "feedback": [{"criterion": "correctness", "score": 5.0, "details": "poor"}], "overallSummary": "needs work"}'
    config = HarnessConfig(work_dir="/tmp", user_prompt="test", pass_threshold=8.0)
    contract = {"sprintNumber": 1, "features": [], "criteria": []}

    monkeypatch.setattr(
        "gan_with_a_plan.evaluator.query",
        fake_sdk_query(assistant_text=low_score),
    )

    result, _ = await run_evaluator(contract, config)
    assert result["passed"] is False
