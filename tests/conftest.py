import pytest
from unittest.mock import AsyncMock, MagicMock

@pytest.fixture
def fake_sdk_query(monkeypatch):
    """Patches claude_code_sdk.query to yield a fake assistant message then a result message."""
    def make_query(assistant_text="ok", session_id="test-session"):
        async def _fake_query(prompt, options):
            msg = MagicMock()
            msg.type = "assistant"
            block = MagicMock()
            block.type = "text"
            block.text = assistant_text
            msg.message = MagicMock()
            msg.message.content = [block]
            yield msg

            result = MagicMock()
            result.type = "result"
            result.session_id = session_id
            yield result

        return _fake_query

    return make_query
