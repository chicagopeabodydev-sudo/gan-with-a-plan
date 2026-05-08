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

def test_phase_report_groups_by_phase():
    logger = Logger()
    logger.record(IterationLog(sprint_number=1, retry_number=0, component="generator",
                               phase="contract", input_tokens=40, output_tokens=10, duration_ms=50.0))
    logger.record(IterationLog(sprint_number=1, retry_number=0, component="generator",
                               phase="implementation", input_tokens=100, output_tokens=60, duration_ms=200.0))
    logger.record(IterationLog(sprint_number=1, retry_number=0, component="evaluator",
                               phase="implementation", input_tokens=80, output_tokens=30, duration_ms=150.0, passed=True))
    report = logger.phase_report()
    assert "contract" in report
    assert "implementation" in report
    assert report["contract"]["call_count"] == 1
    assert report["implementation"]["call_count"] == 2
    assert report["implementation"]["total_tokens"] == 100 + 60 + 80 + 30

def test_full_report_includes_phase_data():
    logger = Logger()
    logger.record(IterationLog(sprint_number=1, retry_number=0, component="generator",
                               phase="implementation", input_tokens=100, output_tokens=50, duration_ms=200.0))
    report = logger.full_report(mode="implementation")
    assert "phases" in report
    assert "mode" in report
    assert report["mode"] == "implementation"
    assert "implementation" in report["phases"]

def test_sprint_summary_includes_turn_count():
    logger = Logger()
    logger.record(IterationLog(sprint_number=1, retry_number=0, component="generator",
                               turn_count=3, input_tokens=100, output_tokens=50, duration_ms=200.0))
    logger.record(IterationLog(sprint_number=1, retry_number=0, component="evaluator",
                               turn_count=2, input_tokens=80, output_tokens=30, duration_ms=150.0))
    summary = logger.sprint_summary(1)
    assert summary["total_turn_count"] == 5

def test_pass_rate_calculation():
    logger = Logger()
    logger.record(IterationLog(sprint_number=1, retry_number=0, component="evaluator",
                               phase="implementation", input_tokens=10, output_tokens=5, duration_ms=50.0, passed=True))
    logger.record(IterationLog(sprint_number=1, retry_number=1, component="evaluator",
                               phase="implementation", input_tokens=10, output_tokens=5, duration_ms=50.0, passed=True))
    logger.record(IterationLog(sprint_number=1, retry_number=2, component="evaluator",
                               phase="implementation", input_tokens=10, output_tokens=5, duration_ms=50.0, passed=False))
    report = logger.phase_report()
    assert abs(report["implementation"]["pass_rate"] - 2/3) < 0.001
