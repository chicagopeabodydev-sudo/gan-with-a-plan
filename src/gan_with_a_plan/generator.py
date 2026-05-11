import time
from claude_code_sdk import ClaudeCodeOptions, AssistantMessage, ResultMessage, TextBlock
from .types import HarnessConfig, SprintContract, EvalResult, CallMetrics
from .sdk_utils import safe_query

def build_generator_prompt(contract: SprintContract, feedback: EvalResult | None) -> str:
    sprint_num = contract.get("sprintNumber") or contract.get("sprint_number", "?")
    base = f"Sprint {sprint_num} contract:\n{contract}"
    if feedback:
        base += f"\n\nPrevious evaluation feedback:\n{feedback['overallSummary']}"
    return base

def _get_usage(msg) -> tuple[int, int]:
    u = getattr(msg, "usage", None)
    if not u:
        return (0, 0)
    if isinstance(u, dict):
        return (u.get("input_tokens", 0), u.get("output_tokens", 0))
    return (getattr(u, "input_tokens", 0), getattr(u, "output_tokens", 0))

async def run_generator(
    contract: SprintContract,
    config: HarnessConfig,
    previous_feedback: EvalResult | None = None,
    session_id: str | None = None,
) -> tuple[str, str | None, CallMetrics]:
    options = ClaudeCodeOptions(
        cwd=config.work_dir,
        system_prompt=build_generator_prompt(contract, previous_feedback),
        permission_mode="bypassPermissions",
        allowed_tools=["Read", "Write", "Edit", "Bash", "Glob", "Grep"],
        model=config.generator_model,
        max_turns=40,
        resume=session_id,
    )
    full_response, new_session_id = "", None
    turn_count = 0
    input_tokens = output_tokens = 0
    t0 = time.monotonic()
    async for message in safe_query(prompt="Implement the sprint contract.", options=options):
        if isinstance(message, AssistantMessage):
            turn_count += 1
            for block in message.content:
                if isinstance(block, TextBlock):
                    full_response += block.text
        elif isinstance(message, ResultMessage):
            if not full_response and message.result:
                full_response = message.result
            new_session_id = message.session_id
            input_tokens, output_tokens = _get_usage(message)
            break
    duration_ms = (time.monotonic() - t0) * 1000
    return full_response, new_session_id, CallMetrics(input_tokens, output_tokens, turn_count, duration_ms)

async def run_generator_plan_only(
    contract: SprintContract,
    config: HarnessConfig,
    previous_plan_feedback: EvalResult | None = None,
) -> tuple[str, CallMetrics]:
    """Plan-gated variant: proposes an approach without writing any code."""
    options = ClaudeCodeOptions(
        cwd=config.work_dir,
        system_prompt=build_generator_prompt(contract, previous_plan_feedback),
        permission_mode="bypassPermissions",
        allowed_tools=["Read", "Glob", "Grep"],
        model=config.generator_model,
        max_turns=20,
    )
    full_response = ""
    turn_count = 0
    input_tokens = output_tokens = 0
    t0 = time.monotonic()
    async for message in safe_query(prompt="Propose a plan for the sprint contract. Do not write any code.", options=options):
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
