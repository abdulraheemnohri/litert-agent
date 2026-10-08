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
from litert_agent.self.web_learning import WebLearningEngine
from litert_agent.self.research import ResearchEngine
from litert_agent.self.goals import GoalManager
from litert_agent.self.goal_execution import GoalExecutionController
from litert_agent.skills.registry import SkillRegistry
from litert_agent.skills.validator import SkillValidator

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
        self.web_learning = None
        self.research = None
        self.goals = None
        self.goal_execution = None

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
            registry = SkillRegistry(self.orchestrator.memory.db_manager)
            self.learning = LearningEngine(self.orchestrator.memory, registry, self.evolution)
            self.self_skills = SelfSkillManager(registry, SkillValidator, self.evolution, self.orchestrator.memory.db_manager)
            self.web_learning = WebLearningEngine(self.orchestrator.tool_registry.get("http"), self.orchestrator.memory)
            self.research = ResearchEngine(self.orchestrator.memory.db_manager, self.orchestrator.tool_registry.get("http"), self.orchestrator.memory)
            self.goals = GoalManager(self.orchestrator.memory.db_manager)
            self.goal_execution = GoalExecutionController(self)

    async def learn(self, task_id, success, observation, lesson=""):
        if self.learning is None:
            self.initialize_learning()
        return await self.learning.learn_from_outcome(task_id, success, observation, lesson)

    def discover_skills(self, task_description):
        if self.self_skills is None:
            self.initialize_learning()
        return self.self_skills.discover(task_description)

    async def learn_from_web(self, url, lesson):
        if self.web_learning is None:
            self.initialize_learning()
        evidence = await self.web_learning.fetch(url)
        return await self.web_learning.ingest(evidence, lesson)

    def self_cycle(self):
        return self.autonomy.tick()

    def research_mission(self, topic: str, goal: str, urls: list[str] | None = None):
        if self.research is None:
            self.initialize_learning()
        return self.research.create_mission(topic, goal, urls)

    async def collect_research(self, mission_id: str):
        if self.research is None:
            self.initialize_learning()
        return await self.research.collect_mission_sources(mission_id)

    def research_sources_for_mission(self, mission_id: str):
        if self.research is None:
            self.initialize_learning()
        return self.research.mission_urls(mission_id)

    async def research_source(self, mission_id: str, topic: str, url: str, claim: str, evidence: str = "", confidence: float = 0.5):
        if self.research is None:
            self.initialize_learning()
        source = await self.research.fetch_source(url)
        return await self.research.ingest_claim(mission_id, source, topic, claim, evidence or source.title, confidence)

    def add_goal_dependency(self, goal_id: str, depends_on_goal_id: str):
        if self.goals is None:
            self.initialize_learning()
        return self.goals.add_dependency(goal_id, depends_on_goal_id)

    def generate_curiosity(self):
        if self.goals is None:
            self.initialize_learning()
        return self.goals.generate_curiosity_from_stale(
            self.config.self.knowledge_stale_after_days * 86400
        )

    def ready_goals(self, limit: int = 3):
        if self.goal_execution is None:
            self.initialize_learning()
        return self.goal_execution.ready_goals(limit)

    async def execute_goal(self, goal_id: str):
        if self.goal_execution is None:
            self.initialize_learning()
        return await self.goal_execution.execute(goal_id)

    async def execute_next_goal(self):
        if self.goal_execution is None:
            self.initialize_learning()
        return await self.goal_execution.execute_next()

    def promote_curiosity_goal(self):
        if self.goal_execution is None:
            self.initialize_learning()
        return self.goal_execution.promote_curiosity()

    def create_goal(self, title: str, description: str, priority: str = "NORMAL", parent_id: str | None = None, goal_type: str = "user"):
        if self.goals is None:
            self.initialize_learning()
        return self.goals.create(title, description, priority, parent_id, goal_type)

    def self_overview(self) -> dict:
        if self.research is None or self.goals is None:
            self.initialize_learning()
        return {
            "snapshot": self.snapshot(),
            "research": {"missions": self.research.list_missions(), "sources": self.research.list_sources(), "findings": self.research.list_findings()},
            "goals": self.goals.list(),
            "curiosity": self.goals.peek_curiosity(),
        }


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
