"""Unit tests for model subsystem."""

import pytest
from litert_agent.model.parser import ProtocolParser
from litert_agent.model.protocol import ProtocolMessage
from litert_agent.model.litert_cli import LiteRTLMProvider

def test_protocol_parser_json():
    json_str = '{"type": "tool_call", "tool": "terminal", "arguments": {"command": "ls"}}'
    msg = ProtocolParser.parse(json_str)
    assert msg.type == "tool_call"
    assert msg.tool == "terminal"
    assert msg.arguments == {"command": "ls"}

def test_protocol_parser_heuristic():
    text = "FINAL: All tasks completed successfully."
    msg = ProtocolParser.parse(text)
    assert msg.type == "final"
    assert msg.content == "All tasks completed successfully."

@pytest.mark.asyncio
async def test_litert_provider_fallback():
    provider = LiteRTLMProvider(cli_path="nonexistent-litert-lm-bin")
    await provider.initialize()
    msg = await provider.generate("hello")
    assert msg.type in ("thought", "error")
