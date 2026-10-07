"""Self-test and doctor checks for all local subsystems."""

from pathlib import Path


class SelfDoctor:
    def __init__(self, config, orchestrator):
        self.config = config
        self.orchestrator = orchestrator

    async def run(self) -> dict:
        await self.orchestrator.initialize()
        provider = self.orchestrator.model_provider
        info = provider.discovery_info or {}
        checks = {
            "litert_lm_executable": bool(info.get("available")),
            "litert_lm_prompt_interface": bool(info.get("supports_prompt")),
            "database": Path(self.config.agent.home_dir / "agent.db").exists(),
            "workspace": Path(self.config.agent.workspace_dir).exists(),
            "tools": len(self.orchestrator.tool_registry.list_tools()) > 0,
            "security": self.orchestrator.policy is not None,
            "approvals": self.orchestrator.approval_manager is not None,
            "checkpoints": self.orchestrator.checkpoint_manager is not None,
            "crash_recovery": self.orchestrator.crash_recovery is not None,
        }
        return {"ok": all(checks.values()), "checks": checks, "model": info}
