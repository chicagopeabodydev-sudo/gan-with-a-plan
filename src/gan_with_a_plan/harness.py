import os, time
from claude_code_sdk import query, ClaudeCodeOptions
from .types import HarnessConfig, HarnessResult, SprintResult, SprintContract
from .planner import run_planner
from .generator import run_generator, run_generator_plan_only
from .evaluator import run_evaluator

async def _generator_propose_contract(config: HarnessConfig, sprint_num: int) -> SprintContract:
    """Generator reads spec.md and proposes a sprint contract as JSON."""
    import json as _json
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
    async for message in query(prompt=prompt, options=options):
        if message.type == "assistant":
            for block in message.message.content:
                if block.type == "text":
                    raw += block.text
        elif message.type == "result":
            break
    return _extract_json(raw)

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

async def _negotiate_contract(config: HarnessConfig, sprint_num: int):
    """Generator proposes a contract; Evaluator approves it."""
    for _ in range(config.max_retries_per_sprint):
        contract = await _generator_propose_contract(config, sprint_num)
        review = await run_evaluator(contract, config, evaluation_mode="contract")
        if review["passed"]:
            return contract
    raise RuntimeError(f"Could not negotiate a contract for sprint {sprint_num}")

async def _run_plan_approval_loop(contract, config: HarnessConfig) -> None:
    """Plan-gated variant: approve a Generator plan before implementation."""
    plan_path = os.path.join(config.work_dir, "plan.md")
    previous_plan_feedback = None
    for _ in range(config.max_retries_per_sprint):
        plan = await run_generator_plan_only(contract, config, previous_plan_feedback)
        # Write plan to disk so the Evaluator agent can read it via its filesystem tools
        with open(plan_path, "w") as f:
            f.write(plan)
        review = await run_evaluator(contract, config, evaluation_mode="plan")
        if review["passed"]:
            return
        previous_plan_feedback = review
    raise RuntimeError("Plan approval loop exhausted retries")

async def run_harness(config: HarnessConfig) -> HarnessResult:
    os.makedirs(config.work_dir, exist_ok=True)
    start = time.time()

    await run_planner(config)

    sprint_results = []
    for sprint_num in range(1, config.max_sprints + 1):
        contract = await _negotiate_contract(config, sprint_num)

        if config.mode == "plan":
            await _run_plan_approval_loop(contract, config)

        session_id, previous_feedback = None, None
        for retry in range(config.max_retries_per_sprint):
            _, session_id = await run_generator(contract, config, previous_feedback, session_id)
            eval_result = await run_evaluator(contract, config)
            if eval_result["passed"]:
                sprint_results.append(SprintResult(sprint_num, True, retry, eval_result))
                break
            previous_feedback = eval_result
        else:
            # Python for/else: this block runs only when the loop exhausted all retries without break
            sprint_results.append(SprintResult(sprint_num, False, config.max_retries_per_sprint, previous_feedback))
            break  # halt harness on sprint failure

    success = all(s.passed for s in sprint_results)
    return HarnessResult(success, sprint_results, (time.time() - start) * 1000)
