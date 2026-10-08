from litert_agent.cognition.decision import DecisionEngine
from litert_agent.model.parser import ProtocolParser


def test_structured_execute_task_is_normalized():
    msg = ProtocolParser.parse(
        '{"intent":"execute_task","goal":"inspect repo","tool":"terminal","action":"execute","arguments":{"command":"pwd"}}'
    )
    assert msg.type == "tool_call"
    assert msg.tool == "terminal"
    assert msg.arguments["command"] == "pwd"


def test_structured_final_is_normalized():
    msg = ProtocolParser.parse('{"intent":"complete","content":"done"}')
    assert msg.type == "final"
    assert msg.content == "done"


def test_plain_model_text_cannot_complete_task():
    msg = ProtocolParser.parse("I think the task is complete.")
    assert msg.type == "thought"
    assert DecisionEngine().decide(msg) == "CONTINUE"


def test_malformed_tool_payload_is_non_executable():
    msg = ProtocolParser.parse('TOOL: terminal ARGS: {"command":')
    assert msg.type == "thought"
    assert DecisionEngine().decide(msg) == "CONTINUE"


def test_plan_message_is_update_only():
    msg = ProtocolParser.parse(
        '{"type":"plan","goal":"x","plan_steps":["inspect","verify"]}'
    )
    assert DecisionEngine().decide(msg) == "UPDATE_PLAN"
