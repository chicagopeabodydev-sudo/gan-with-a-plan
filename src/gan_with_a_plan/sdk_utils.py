from claude_code_sdk import ClaudeCodeOptions, AssistantMessage, ResultMessage, TextBlock
from claude_code_sdk._internal.transport.subprocess_cli import SubprocessCLITransport
from claude_code_sdk._internal.message_parser import parse_message

_SKIP_TYPES = {"rate_limit_event"}

async def safe_query(prompt: str, options: ClaudeCodeOptions):
    """Query the Claude CLI, skipping unrecognized message types instead of crashing."""
    transport = SubprocessCLITransport(prompt=prompt, options=options)
    await transport.connect()
    try:
        async for data in transport.read_messages():
            if data.get("type") in _SKIP_TYPES:
                continue
            try:
                yield parse_message(data)
            except Exception:
                continue
    finally:
        await transport.close()
