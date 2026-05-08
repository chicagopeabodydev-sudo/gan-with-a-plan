import re, json, time
from claude_code_sdk import query, ClaudeCodeOptions
from .types import HarnessConfig, SprintContract, EvalResult, CallMetrics

def build_evaluator_prompt(contract: SprintContract, mode: str) -> str:
    modes = {
        "contract": "Review the proposed sprint contract for clarity, testability, and feasibility.",
        "plan": "Evaluate the generator's proposed plan against the sprint contract criteria.",
        "implementation": "Evaluate the implemented code against the sprint contract criteria.",
    }
    return f"{modes[mode]}\n\nContract:\n{contract}\n\nReturn a JSON EvalResult."

def _get_usage(msg) -> tuple[int, int]:
    u = getattr(msg, "usage", None)
    return (getattr(u, "input_tokens", 0), getattr(u, "output_tokens", 0)) if u else (0, 0)

async def run_evaluator(
    contract: SprintContract,
    config: HarnessConfig,
    evaluation_mode: str = "implementation",  # "plan" | "contract" | "implementation"
) -> tuple[EvalResult, CallMetrics]:
    options = ClaudeCodeOptions(
        cwd=config.work_dir,
        system_prompt=build_evaluator_prompt(contract, evaluation_mode),
        permission_mode="bypassPermissions",
        allowed_tools=["Read", "Bash", "Glob", "Grep"],
        model=config.evaluator_model,
        max_turns=20,
    )
    raw = ""
    turn_count = 0
    input_tokens = output_tokens = 0
    t0 = time.monotonic()
    async for message in query(prompt="Evaluate per the contract criteria.", options=options):
        if message.type == "assistant":
            turn_count += 1
            for block in message.message.content:
                if block.type == "text":
                    raw += block.text
        elif message.type == "result":
            input_tokens, output_tokens = _get_usage(message)
            break
    duration_ms = (time.monotonic() - t0) * 1000
    result = _extract_eval_result(raw)
    result["passed"] = all(f["score"] >= config.pass_threshold for f in result["feedback"])
    return result, CallMetrics(input_tokens, output_tokens, turn_count, duration_ms)

def _extract_eval_result(raw: str) -> EvalResult:
    # Pass 1: fenced code block
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.DOTALL)
    if m:
        return json.loads(m.group(1))
    # Pass 2: brace-balanced substring
    start = raw.find("{")
    if start != -1:
        depth, end = 0, -1
        for i, ch in enumerate(raw[start:], start):
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    end = i
                    break
        if end != -1:
            return json.loads(raw[start:end + 1])
    # Pass 3: raw parse (raises on failure)
    return json.loads(raw)
