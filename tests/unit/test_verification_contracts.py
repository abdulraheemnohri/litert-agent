from litert_agent.cognition.verifier import VerificationContract, Verifier
from litert_agent.tools.base import ToolResult


def test_verification_contract_contains():
    verifier = Verifier()
    ok, failures = verifier.verify_contract(
        ToolResult(success=True, output="created file successfully"),
        VerificationContract.from_requests(["contains:created"]),
    )
    assert ok
    assert failures == []


def test_verification_contract_rejects_missing_and_unknown():
    verifier = Verifier()
    ok, failures = verifier.verify_contract(
        ToolResult(success=True, output="done"),
        VerificationContract.from_requests(["contains:expected", "unsupported request"]),
    )
    assert not ok
    assert len(failures) == 2


def test_verification_contract_invalid_regex_is_safe():
    verifier = Verifier()
    ok, failures = verifier.verify_contract(
        ToolResult(success=True, output="done"),
        VerificationContract.from_requests(["regex:["]),
    )
    assert not ok
    assert "invalid regex" in failures[0]
