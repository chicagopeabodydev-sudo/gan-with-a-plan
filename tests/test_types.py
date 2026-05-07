import pytest
from gan_with_a_plan.types import HarnessConfig

def test_harness_config_env_defaults(monkeypatch):
    monkeypatch.delenv("MAX_SPRINTS", raising=False)
    monkeypatch.delenv("MAX_RETRIES_PER_SPRINT", raising=False)
    monkeypatch.delenv("PASS_THRESHOLD", raising=False)
    config = HarnessConfig(work_dir="/tmp", user_prompt="test")
    assert config.max_sprints == 3
    assert config.max_retries_per_sprint == 3
    assert config.pass_threshold == 8.0

def test_harness_config_reads_env(monkeypatch):
    monkeypatch.setenv("MAX_SPRINTS", "5")
    monkeypatch.setenv("MAX_RETRIES_PER_SPRINT", "2")
    monkeypatch.setenv("PASS_THRESHOLD", "7.5")
    config = HarnessConfig(work_dir="/tmp", user_prompt="test")
    assert config.max_sprints == 5
    assert config.max_retries_per_sprint == 2
    assert config.pass_threshold == 7.5

def test_harness_config_model_env(monkeypatch):
    monkeypatch.setenv("PLANNER_MODEL", "claude-opus-4-7")
    monkeypatch.setenv("GENERATOR_MODEL", "claude-haiku-4-5-20251001")
    monkeypatch.setenv("EVALUATOR_MODEL", "claude-sonnet-4-6")
    config = HarnessConfig(work_dir="/tmp", user_prompt="test")
    assert config.planner_model == "claude-opus-4-7"
    assert config.generator_model == "claude-haiku-4-5-20251001"
    assert config.evaluator_model == "claude-sonnet-4-6"
