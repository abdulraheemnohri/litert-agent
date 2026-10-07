"""Bounded self-management: health, diagnostics, learning, maintenance and safe recovery.

This subsystem never changes model weights, security policy, or provider identity.
It proposes maintenance actions; policy/approval remains authoritative.
"""

import json
import platform
import sys
import time
from pathlib import Path
from litert_agent.self.evolution import EvolutionManager
from litert_agent.self.learning import LearningEngine
from litert_agent.self.skills import SelfSkillManager
from litert_agent.self.autonomy import AutonomousSelfController

import psutil


class SelfManager:
    """Operational self-awareness and bounded self-improvement coordinator."""

    VERSION = 1

    def __init__(self, config, orchestrator=None):
        self.config = config
        self.orchestrator = orchestrator
        self.started_at = time.time()
        self.last_diagnostics: dict = {}
        self.last_reflection: dict = {}
        self.evolution = EvolutionManager()
        self.learning = None
        self.self_skills = None
        self.autonomy = AutonomousSelfController(self)

    def identity(self) -> dict:
        return {
            "name": self.config.agent.name,
            "version": self.VERSION,
            "mission": "local-first autonomous agent powered only by LiteRT-LM CLI",
            "provider": "litert-cli",
            "platform": platform.platform(),
            "python": sys.version.split()[0],
        }

    def capabilities(self) -> dict:
        if not self.orchestrator:
            return {}
        provider = self.orchestrator.model_provider
        discovery = provider.discovery_info or {}
        return {
            "model": discovery,
            "tools": self.orchestrator.tool_registry.list_tools(),
            "safe_mode": self.config.agent.safe_mode,
            "offline_mode": self.config.agent.offline_mode,
        }

    def resources(self) -> dict:
        vm = psutil.virtual_memory()
        disk = psutil.disk_usage(str(self.config.agent.workspace_dir))
        return {
            "cpu_percent": psutil.cpu_percent(interval=0.05),
            "memory_percent": vm.percent,
            "memory_available_mb": round(vm.available / 1024 / 1024),
            "disk_percent": disk.percent,
            "disk_free_gb": round(disk.free / 1024 / 1024 / 1024, 2),
        }

    def diagnose(self) -> dict:
        checks = {}
        home = Path(self.config.agent.home_dir)
        workspace = Path(self.config.agent.workspace_dir)
        checks["home"] = home.exists()
        checks["workspace"] = workspace.exists()
        checks["database"] = (home / "agent.db").exists()
        if self.orchestrator:
            info = self.orchestrator.model_provider.discovery_info or {}
            checks["litert_cli"] = bool(info.get("available"))
            checks["litert_prompt_interface"] = bool(info.get("supports_prompt"))
            checks["tools"] = len(self.orchestrator.tool_registry.list_tools()) > 0
        resources = self.resources()
        warnings = []
        if resources["memory_percent"] >= 90:
            warnings.append("memory_pressure")
        if resources["disk_percent"] >= 95:
            warnings.append("disk_pressure")
        if not checks.get("litert_cli", False):
            warnings.append("litert_lm_unavailable")
        if not checks.get("litert_prompt_interface", False):
            warnings.append("litert_lm_prompt_interface_not_detected")
        report = {"ok": not warnings, "checks": checks, "resources": resources, "warnings": warnings}
        self.last_diagnostics = report
        return report

    def safe_concurrency(self) -> int:
        r = self.resources()
        if r["memory_percent"] >= 90:
            return 1
        if r["memory_percent"] >= 75:
            return 1
        return max(1, min(self.config.scheduler.workers, 4))

    def reflect(self, task_id: str, success: bool, summary: str, lesson: str = "") -> dict:
        result = {
            "task_id": task_id,
            "success": success,
            "summary": summary[:2000],
            "lesson": lesson[:2000],
            "created_at": time.time(),
        }
        self.last_reflection = result
        if self.orchestrator and lesson:
            try:
                import asyncio
                coro = self.orchestrator.memory.lessons.add_lesson("self_reflection", lesson)
                if asyncio.iscoroutine(coro):
                    try:
                        asyncio.get_running_loop().create_task(coro)
                    except RuntimeError:
                        pass
            except Exception:
                pass
        return result

    def maintenance_plan(self) -> list[dict]:
        d = self.last_diagnostics or self.diagnose()
        actions = []
        if "memory_pressure" in d["warnings"]:
            actions.append({"action": "reduce_concurrency", "reason": "high memory usage"})
        if "disk_pressure" in d["warnings"]:
            actions.append({"action": "archive_logs", "reason": "low disk space"})
        if not d["ok"]:
            actions.append({"action": "run_doctor", "reason": "diagnostic warnings present"})
        return actions

    def initialize_learning(self):
        if self.orchestrator:
            self.learning = LearningEngine(self.orchestrator.memory, self.orchestrator.skill_registry, self.evolution)
            self.self_skills = SelfSkillManager(self.orchestrator.skill_registry, self.orchestrator.skill_validator, self.evolution)

    def self_cycle(self) -> dict:
        return self.autonomy.tick()

    def snapshot(self) -> dict:
        return {
            "identity": self.identity(),
            "capabilities": self.capabilities(),
            "resources": self.resources(),
            "diagnostics": self.last_diagnostics or self.diagnose(),
            "maintenance": self.maintenance_plan(),
            "uptime_seconds": round(time.time() - self.started_at, 2),
        }

    def export_snapshot(self, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.snapshot(), indent=2, default=str), encoding="utf-8")
        return path
