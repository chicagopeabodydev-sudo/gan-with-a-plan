import os, time
from claude_code_sdk import query, ClaudeCodeOptions
from .types import HarnessConfig, HarnessResult, SprintResult, SprintContract, IterationLog
from .logger import Logger
from .planner import run_planner
from .generator import run_generator, run_generator_plan_only
from .evaluator import run_evaluator

async def _generator_propose_contract(config: HarnessConfig, sprint_num: int) -> tuple[SprintContract, object]:
    """Generator reads spec.md and proposes a sprint contract as JSON."""
    import time as _time
    from .types import CallMetrics
    spec_path = os.path.join(config.work_dir, "spec.md")
    prompt = f"Read {spec_path} and propose a SprintContract JSON for sprint {sprint_num}. Output only the JSON object."
    options = ClaudeCodeOptions(
        cwd=config.work_dir,
        system_prompt="You are a sprint planner. Produce a single SprintContract JSON object and nothing else.",
        permission_mode="bypassPermissions",
        allowed_tools=["Read"],
        model=config.generator_model,
        max_turns=10,
    )
    raw = ""
    turn_count = 0
    input_tokens = output_tokens = 0
    t0 = _time.monotonic()
    async for message in query(prompt=prompt, options=options):
        if message.type == "assistant":
            turn_count += 1
            for block in message.message.content:
                if block.type == "text":
                    raw += block.text
        elif message.type == "result":
            u = getattr(message, "usage", None)
            if u:
                input_tokens = getattr(u, "input_tokens", 0)
                output_tokens = getattr(u, "output_tokens", 0)
            break
    duration_ms = (_time.monotonic() - t0) * 1000
    metrics = CallMetrics(input_tokens, output_tokens, turn_count, duration_ms)
    return _extract_json(raw), metrics

def _extract_json(raw: str) -> dict:
    import re, json
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.DOTALL)
    if m:
        return json.loads(m.group(1))
    start = raw.find("{")
    if start != -1:
        depth, end = 0, -1
        for i, ch in enumerate(raw[start:], start):
            if ch == "{": depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0: end = i; break
        if end != -1:
            return json.loads(raw[start:end + 1])
    return json.loads(raw)

async def _negotiate_contract(config: HarnessConfig, sprint_num: int, logger: Logger) -> SprintContract:
    """Generator proposes a contract; Evaluator approves it."""
    for _ in range(config.max_retries_per_sprint):
        contract, gen_metrics = await _generator_propose_contract(config, sprint_num)
        logger.record(IterationLog(
            sprint_number=sprint_num, retry_number=0, component="generator",
            phase="contract",
            input_tokens=gen_metrics.input_tokens, output_tokens=gen_metrics.output_tokens,
            turn_count=gen_metrics.turn_count, duration_ms=gen_metrics.duration_ms,
        ))
        review, eval_metrics = await run_evaluator(contract, config, evaluation_mode="contract")
        logger.record(IterationLog(
            sprint_number=sprint_num, retry_number=0, component="evaluator",
            phase="contract",
            input_tokens=eval_metrics.input_tokens, output_tokens=eval_metrics.output_tokens,
            turn_count=eval_metrics.turn_count, duration_ms=eval_metrics.duration_ms,
            passed=review["passed"],
        ))
        if review["passed"]:
            return contract
    raise RuntimeError(f"Could not negotiate a contract for sprint {sprint_num}")

async def _run_plan_approval_loop(contract, config: HarnessConfig, sprint_num: int, logger: Logger) -> None:
    """Plan-gated variant: approve a Generator plan before implementation."""
    plan_path = os.path.join(config.work_dir, "plan.md")
    previous_plan_feedback = None
    for retry in range(config.max_retries_per_sprint):
        plan, gen_metrics = await run_generator_plan_only(contract, config, previous_plan_feedback)
        logger.record(IterationLog(
            sprint_number=sprint_num, retry_number=retry, component="generator",
            phase="plan",
            input_tokens=gen_metrics.input_tokens, output_tokens=gen_metrics.output_tokens,
            turn_count=gen_metrics.turn_count, duration_ms=gen_metrics.duration_ms,
        ))
        with open(plan_path, "w") as f:
            f.write(plan)
        review, eval_metrics = await run_evaluator(contract, config, evaluation_mode="plan")
        logger.record(IterationLog(
            sprint_number=sprint_num, retry_number=retry, component="evaluator",
            phase="plan",
            input_tokens=eval_metrics.input_tokens, output_tokens=eval_metrics.output_tokens,
            turn_count=eval_metrics.turn_count, duration_ms=eval_metrics.duration_ms,
            passed=review["passed"],
        ))
        if review["passed"]:
            return
        previous_plan_feedback = review
    raise RuntimeError("Plan approval loop exhausted retries")

async def run_harness(config: HarnessConfig) -> HarnessResult:
    os.makedirs(config.work_dir, exist_ok=True)
    start = time.time()
    logger = Logger()

    _, planner_metrics = await run_planner(config)
    logger.record(IterationLog(
        sprint_number=0, retry_number=0, component="planner",
        phase="planner",
        input_tokens=planner_metrics.input_tokens, output_tokens=planner_metrics.output_tokens,
        turn_count=planner_metrics.turn_count, duration_ms=planner_metrics.duration_ms,
    ))

    sprint_results = []
    for sprint_num in range(1, config.max_sprints + 1):
        contract = await _negotiate_contract(config, sprint_num, logger)

        if config.mode == "plan":
            await _run_plan_approval_loop(contract, config, sprint_num, logger)

        session_id, previous_feedback = None, None
        for retry in range(config.max_retries_per_sprint):
            _, session_id, gen_metrics = await run_generator(contract, config, previous_feedback, session_id)
            logger.record(IterationLog(
                sprint_number=sprint_num, retry_number=retry, component="generator",
                phase="implementation",
                input_tokens=gen_metrics.input_tokens, output_tokens=gen_metrics.output_tokens,
                turn_count=gen_metrics.turn_count, duration_ms=gen_metrics.duration_ms,
            ))
            eval_result, eval_metrics = await run_evaluator(contract, config)
            logger.record(IterationLog(
                sprint_number=sprint_num, retry_number=retry, component="evaluator",
                phase="implementation",
                input_tokens=eval_metrics.input_tokens, output_tokens=eval_metrics.output_tokens,
                turn_count=eval_metrics.turn_count, duration_ms=eval_metrics.duration_ms,
                passed=eval_result["passed"],
            ))
            if eval_result["passed"]:
                sprint_results.append(SprintResult(sprint_num, True, retry, eval_result))
                break
            previous_feedback = eval_result
        else:
            sprint_results.append(SprintResult(sprint_num, False, config.max_retries_per_sprint, previous_feedback))
            break

    success = all(s.passed for s in sprint_results)
    log_report = logger.full_report(mode=config.mode)
    return HarnessResult(success, sprint_results, (time.time() - start) * 1000, log_report)
