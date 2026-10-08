"""Persistent, auditable approval workflow.

Approval state never grants permission by itself: every resumed execution is
re-evaluated by SecurityPolicy.
"""

import uuid
from datetime import datetime, timedelta, timezone


class ApprovalManager:
    """Tracks pending approvals with stable IDs and bounded expiry."""

    def __init__(self, auto_approve: bool = False, audit_logger=None, ttl_seconds: int = 900):
        self.auto_approve = auto_approve
        self.session_approvals: set[str] = set()
        self.pending: dict[str, dict] = {}
        self.history: list[dict] = []
        self.audit_logger = audit_logger
        self.ttl_seconds = max(30, min(ttl_seconds, 86400))

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    def _record(self, approval: dict, decision: str):
        approval = dict(approval)
        approval["status"] = decision
        approval["decided_at"] = self._now().isoformat()
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
        approval_id = str(uuid.uuid4())
        now = self._now()
        approval = {
            "id": approval_id, "tool": tool_name, "action": action,
            "args": dict(args or {}), "risk": "HIGH" if tool_name == "terminal" else "MEDIUM",
            "reason": risk_reason, "status": "WAITING",
            "created_at": now.isoformat(),
            "expires_at": (now + timedelta(seconds=self.ttl_seconds)).isoformat(),
        }
        self.pending[approval_id] = approval
        return False

    def _expire(self, approval: dict) -> None:
        self.pending.pop(approval["id"], None)
        self._record(approval, "EXPIRED")

    def decide(self, approval_id: str, decision: str) -> dict | None:
        approval = self.pending.get(approval_id)
        if approval is None:
            return None
        if self._now() >= datetime.fromisoformat(approval["expires_at"]):
            self._expire(approval)
            return approval
        if decision not in {"allow_once", "allow", "deny"}:
            return None
        self.pending.pop(approval_id, None)
        if decision == "deny":
            self._record(approval, "DENY")
            return approval
        if decision == "allow":
            self.session_approvals.add(f"{approval['tool']}:{approval['action']}")
        self._record(approval, "ALLOW")
        approval["decision"] = decision
        return approval

    def consume(self, approval_id: str) -> bool:
        return any(item.get("id") == approval_id and item.get("status") == "ALLOW"
                   for item in reversed(self.history))

    def expire_pending(self) -> int:
        count = 0
        for approval in list(self.pending.values()):
            if self._now() >= datetime.fromisoformat(approval["expires_at"]):
                self._expire(approval)
                count += 1
        return count

    def list_pending(self) -> list[dict]:
        self.expire_pending()
        return list(self.pending.values())

    def list_history(self) -> list[dict]:
        return list(self.history)
