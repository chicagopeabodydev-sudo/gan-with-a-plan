import re, json, time
from claude_code_sdk import ClaudeCodeOptions, AssistantMessage, ResultMessage, TextBlock
from .types import HarnessConfig, SprintContract, EvalResult, CallMetrics
from .sdk_utils import safe_query

def build_evaluator_prompt(contract: SprintContract, mode: str) -> str:
    modes = {
        "contract": "Review the proposed sprint contract for clarity, testability, and feasibility.",
        "plan": "Evaluate the generator's proposed plan against the sprint contract criteria.",
        "implementation": "Evaluate the implemented code against the sprint contract criteria.",
    }
    schema = '''{
  "feedback": [
    {"criterion": "<name>", "score": <0-10 float>, "details": "<explanation>"}
  ],
  "overallSummary": "<one paragraph summary>"
}'''
    return f"{modes[mode]}\n\nContract:\n{contract}\n\nRespond with ONLY a JSON object matching this exact schema:\n{schema}"

def _get_usage(msg) -> tuple[int, int]:
    u = getattr(msg, "usage", None)
    if not u:
        return (0, 0)
    if isinstance(u, dict):
        return (u.get("input_tokens", 0), u.get("output_tokens", 0))
    return (getattr(u, "input_tokens", 0), getattr(u, "output_tokens", 0))

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
    async for message in safe_query(prompt="Evaluate per the contract criteria.", options=options):
        if isinstance(message, AssistantMessage):
            turn_count += 1
            for block in message.content:
                if isinstance(block, TextBlock):
                    raw += block.text
        elif isinstance(message, ResultMessage):
            if not raw and message.result:
                raw = message.result
            input_tokens, output_tokens = _get_usage(message)
            break
    duration_ms = (time.monotonic() - t0) * 1000
    import sys
    print(f"\n[evaluator raw ({evaluation_mode})]: {raw[:500]!r}", file=sys.stderr)
    result = _extract_eval_result(raw)
    print(f"[evaluator parsed]: {result}", file=sys.stderr)
    scores = [f["score"] for f in result["feedback"]]
    if evaluation_mode == "contract":
        # Use average score for contract gate — individual criteria will vary widely
        avg = sum(scores) / len(scores) if scores else 0
        result["passed"] = avg >= config.pass_threshold
        print(f"[evaluator passed={result['passed']} avg={avg:.2f} threshold={config.pass_threshold}]", file=sys.stderr)
    else:
        result["passed"] = all(s >= config.pass_threshold for s in scores)
        print(f"[evaluator passed={result['passed']} threshold={config.pass_threshold}]", file=sys.stderr)
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
