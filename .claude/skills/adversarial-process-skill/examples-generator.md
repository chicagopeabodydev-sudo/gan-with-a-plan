# Adversarial Process Skill — Python Examples: Generator

## generator.py

```python
from claude_code_sdk import query, ClaudeCodeOptions
from .types import HarnessConfig, SprintContract, EvalResult

def build_generator_prompt(contract: SprintContract, feedback: EvalResult | None) -> str:
    base = f"Sprint {contract['sprintNumber']} contract:\n{contract}"
    if feedback:
        base += f"\n\nPrevious evaluation feedback:\n{feedback['overallSummary']}"
    return base

async def run_generator(
    contract: SprintContract,
    config: HarnessConfig,
    previous_feedback: EvalResult | None = None,
    session_id: str | None = None,
) -> tuple[str, str | None]:  # (response, session_id)
    options = ClaudeCodeOptions(
        cwd=config.work_dir,
        system_prompt=build_generator_prompt(contract, previous_feedback),
        permission_mode="bypassPermissions",
        tools=["Read", "Write", "Edit", "Bash", "Glob", "Grep"],
        model=config.model,
        max_turns=40,
        persist_session=True,
        session_id=session_id,  # resumes prior session on retries
    )
    full_response, new_session_id = "", None
    async for message in query(prompt="Implement the sprint contract.", options=options):
        if message.type == "assistant":
            for block in message.message.content:
                if block.type == "text":
                    full_response += block.text
        elif message.type == "result":
            new_session_id = message.session_id
            break
    return full_response, new_session_id

async def run_generator_plan_only(
    contract: SprintContract,
    config: HarnessConfig,
    previous_plan_feedback: EvalResult | None = None,
) -> str:
    """Plan-gated variant: proposes an approach without writing any code."""
    options = ClaudeCodeOptions(
        cwd=config.work_dir,
        system_prompt=build_generator_prompt(contract, previous_plan_feedback),
        permission_mode="bypassPermissions",
        tools=["Read", "Glob", "Grep"],  # read-only — no code writing
        model=config.model,
        max_turns=20,
        # persist_session not set — plan proposals are stateless
    )
    full_response = ""
    async for message in query(prompt="Propose a plan for the sprint contract. Do not write any code.", options=options):
        if message.type == "assistant":
            for block in message.message.content:
                if block.type == "text":
                    full_response += block.text
        elif message.type == "result":
            break
    return full_response
```

- `persist_session=True` and `session_id` resumption are exclusive to `run_generator` — the Generator maintains session state so retries have full context.
- `run_generator_plan_only` uses read-only tools and no `persist_session` — plan proposals are isolated.
- `session_id` from the `result` message is passed back by the Harness on the next retry call.
