"""Approval manager for tool calls requiring confirmation."""

import uuid
from datetime import datetime


class ApprovalManager:
    """Tracks pending approvals, session approvals and audited history."""

    def __init__(self, auto_approve: bool = False, audit_logger=None):
        self.auto_approve = auto_approve
        self.session_approvals: set[str] = set()
        self.pending: list[dict] = []
        self.history: list[dict] = []
        self.audit_logger = audit_logger

    def _record(self, approval: dict, decision: str):
        approval["status"] = decision
        approval["decided_at"] = datetime.utcnow().isoformat()
        self.history.append(approval)
        if self.audit_logger is not None:
            try:
                self.audit_logger.log("approval", approval["tool"], approval["args"], decision, "ASK")
            except Exception:
                pass

    async def request_approval(self, tool_name: str, action: str, args: dict, risk_reason: str) -> bool:
        if self.auto_approve:
            return True
        key = f"{tool_name}:{action}"
        if key in self.session_approvals:
            return True

        approval = {
            "id": str(uuid.uuid4()),
            "tool": tool_name,
            "action": action,
            "args": args,
            "risk": "HIGH" if tool_name == "terminal" else "MEDIUM",
            "reason": risk_reason,
            "status": "WAITING",
        }
        self.pending.append(approval)
        # Non-interactive runtimes: not yet decided -> not approved.
        # Interactive frontends call decide() (Allow Once / Allow Session / Deny).
        return False

    def decide(self, approval_id: str, decision: str) -> dict | None:
        """decision: allow_once | allow | deny"""
        for approval in self.pending:
            if approval["id"] == approval_id:
                self.pending.remove(approval)
                if decision == "deny":
                    self._record(approval, "DENY")
                    return approval
                if decision == "allow":
                    self.session_approvals.add(f"{approval['tool']}:{approval['action']}")
                self._record(approval, "ALLOW")
                return approval
        return None

    def list_pending(self) -> list[dict]:
        return list(self.pending)

    def list_history(self) -> list[dict]:
        return list(self.history)
