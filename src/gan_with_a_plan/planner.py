import time
from claude_code_sdk import ClaudeCodeOptions, AssistantMessage, ResultMessage, TextBlock
from .types import HarnessConfig, CallMetrics
from .sdk_utils import safe_query

PLANNER_SYSTEM_PROMPT = """
You are a software architect. Given a user prompt, produce a detailed spec.md file
in the working directory that describes what needs to be built, acceptance criteria,
and suggested sprint breakdown.
"""

def _get_usage(msg) -> tuple[int, int]:
    u = getattr(msg, "usage", None)
    if not u:
        return (0, 0)
    if isinstance(u, dict):
        return (u.get("input_tokens", 0), u.get("output_tokens", 0))
    return (getattr(u, "input_tokens", 0), getattr(u, "output_tokens", 0))

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
    async for message in safe_query(prompt=config.user_prompt, options=options):
        if isinstance(message, AssistantMessage):
            turn_count += 1
            for block in message.content:
                if isinstance(block, TextBlock):
                    full_response += block.text
        elif isinstance(message, ResultMessage):
            if not full_response and message.result:
                full_response = message.result
            input_tokens, output_tokens = _get_usage(message)
            break
    duration_ms = (time.monotonic() - t0) * 1000
    return full_response, CallMetrics(input_tokens, output_tokens, turn_count, duration_ms)
