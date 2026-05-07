import pytest
from gan_with_a_plan.logger import Logger, IterationLog

def test_record_and_sprint_summary():
    logger = Logger()
    logger.record(IterationLog(sprint_number=1, retry_number=0, component="generator",
                               input_tokens=100, output_tokens=50, duration_ms=200.0, passed=True))
    logger.record(IterationLog(sprint_number=1, retry_number=0, component="evaluator",
                               input_tokens=80, output_tokens=30, duration_ms=150.0, passed=True))
    summary = logger.sprint_summary(1)
    assert summary["sprint"] == 1
    assert summary["total_input_tokens"] == 180
    assert summary["total_output_tokens"] == 80
    assert summary["iterations"] == 2

def test_full_report():
    logger = Logger()
    logger.record(IterationLog(sprint_number=1, retry_number=0, component="planner",
                               input_tokens=50, output_tokens=20, duration_ms=100.0))
    logger.record(IterationLog(sprint_number=2, retry_number=0, component="generator",
                               input_tokens=200, output_tokens=100, duration_ms=300.0, passed=True))
    report = logger.full_report()
    assert report["total_input_tokens"] == 250
    assert report["total_output_tokens"] == 120
    assert len(report["sprints"]) == 2
    assert report["sprints"][0]["sprint"] == 1
    assert report["sprints"][1]["sprint"] == 2

def test_empty_logger():
    logger = Logger()
    report = logger.full_report()
    assert report["total_input_tokens"] == 0
    assert report["sprints"] == []
