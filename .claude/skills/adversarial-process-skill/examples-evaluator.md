# Adversarial Process Skill — Python Examples: Evaluator

## evaluator.py

```python
import re, json
from claude_code_sdk import query, ClaudeCodeOptions
from .types import HarnessConfig, SprintContract, EvalResult

def build_evaluator_prompt(contract: SprintContract, mode: str) -> str:
    modes = {
        "contract": "Review the proposed sprint contract for clarity, testability, and feasibility.",
        "plan": "Evaluate the generator's proposed plan against the sprint contract criteria.",
        "implementation": "Evaluate the implemented code against the sprint contract criteria.",
    }
    return f"{modes[mode]}\n\nContract:\n{contract}\n\nReturn a JSON EvalResult."

async def run_evaluator(
    contract: SprintContract,
    config: HarnessConfig,
    evaluation_mode: str = "implementation",  # "plan" | "contract" | "implementation"
) -> EvalResult:
    options = ClaudeCodeOptions(
        cwd=config.work_dir,
        system_prompt=build_evaluator_prompt(contract, evaluation_mode),
        permission_mode="bypassPermissions",
        tools=["Read", "Bash", "Glob", "Grep"],
        model=config.model,
        max_turns=20,
    )
    raw = ""
    async for message in query(prompt="Evaluate per the contract criteria.", options=options):
        if message.type == "assistant":
            for block in message.message.content:
                if block.type == "text":
                    raw += block.text
        elif message.type == "result":
            break
    result = _extract_eval_result(raw)
    result["passed"] = all(f["score"] >= config.pass_threshold for f in result["feedback"])
    return result

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
```

- `_extract_eval_result` uses 3-pass JSON extraction: fenced code block → brace-balanced substring → raw parse. Handles varied Evaluator output formatting.
- `result["passed"]` is computed inside `run_evaluator` after extraction — the Evaluator agent itself does not decide pass/fail, only scores each criterion.
- The `evaluation_mode` parameter lets the same function serve all three evaluation contexts (contract, plan, implementation).
