from claude_code_sdk import query, ClaudeCodeOptions
from .types import HarnessConfig

PLANNER_SYSTEM_PROMPT = """
You are a software architect. Given a user prompt, produce a detailed spec.md file
in the working directory that describes what needs to be built, acceptance criteria,
and suggested sprint breakdown.
"""

async def run_planner(config: HarnessConfig) -> str:
    options = ClaudeCodeOptions(
        cwd=config.work_dir,
        system_prompt=PLANNER_SYSTEM_PROMPT,
        permission_mode="bypassPermissions",
        allowed_tools=["Read", "Write"],
        model=config.planner_model,
        max_turns=20,
    )
    full_response = ""
    async for message in query(prompt=config.user_prompt, options=options):
        if message.type == "assistant":
            for block in message.message.content:
                if block.type == "text":
                    full_response += block.text
        elif message.type == "result":
            break
    return full_response
