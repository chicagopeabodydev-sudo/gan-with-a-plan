import time
from claude_code_sdk import query, ClaudeCodeOptions
from .types import HarnessConfig, CallMetrics

PLANNER_SYSTEM_PROMPT = """
You are a software architect. Given a user prompt, produce a detailed spec.md file
in the working directory that describes what needs to be built, acceptance criteria,
and suggested sprint breakdown.
"""

def _get_usage(msg) -> tuple[int, int]:
    u = getattr(msg, "usage", None)
    return (getattr(u, "input_tokens", 0), getattr(u, "output_tokens", 0)) if u else (0, 0)

async def run_planner(config: HarnessConfig) -> tuple[str, CallMetrics]:
    options = ClaudeCodeOptions(
        cwd=config.work_dir,
        system_prompt=PLANNER_SYSTEM_PROMPT,
        permission_mode="bypassPermissions",
        allowed_tools=["Read", "Write"],
        model=config.planner_model,
        max_turns=20,
    )
    full_response = ""
    turn_count = 0
    input_tokens = output_tokens = 0
    t0 = time.monotonic()
    async for message in query(prompt=config.user_prompt, options=options):
        if message.type == "assistant":
            turn_count += 1
            for block in message.message.content:
                if block.type == "text":
                    full_response += block.text
        elif message.type == "result":
            input_tokens, output_tokens = _get_usage(message)
            break
    duration_ms = (time.monotonic() - t0) * 1000
    return full_response, CallMetrics(input_tokens, output_tokens, turn_count, duration_ms)
