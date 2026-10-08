"""Self-X CLI: goal, self and research commands (A-to-Z spec sections 40-43).

Exposed as the `litert-agent-self` console script so it composes with the
main CLI without touching it. All commands are local and JSON-friendly.
"""
from __future__ import annotations

import json
from typing import Optional

import typer

from litert_agent.self.curiosity import CuriosityEngine
from litert_agent.self.goals import GoalManager
from litert_agent.self.learning import LearningEngine
from litert_agent.self.report import generate_self_report
from litert_agent.research.missions import ResearchStore

app = typer.Typer(no_args_is_help=True, help="Self-X commands: goals, curiosity, learning, research.")
goal_app = typer.Typer(no_args_is_help=True, help="Autonomous goal management.")
research_app = typer.Typer(no_args_is_help=True, help="Research missions.")
app.add_typer(goal_app, name="goal")
app.add_typer(research_app, name="research")


def _echo(data, json_mode: bool) -> None:
    if json_mode:
        typer.echo(json.dumps(data, indent=2, default=str))
    else:
        typer.echo(data)


# --- goals ---------------------------------------------------------------

@goal_app.command("create")
def goal_create(title: str, description: str = "", priority: str = "NORMAL",
                risk: str = "low", json: bool = False):
    """Create a goal. High-risk goals start WAITING_APPROVAL."""
    gm = GoalManager()
    goal = gm.create_goal(title, description, priority=priority, risk=risk)
    _echo(goal.as_dict() if json else f"created goal {goal.id} [{goal.status}]", json)
    gm.close()


@goal_app.command("list")
def goal_list(status: Optional[str] = None, json: bool = False):
    gm = GoalManager()
    goals = [g.as_dict() for g in gm.list_goals(status)]
    _echo(goals if json else "\n".join(
        f"{g['id']}  {g['status']:18} {g['priority']:8} {g['title']}" for g in goals
    ) or "no goals", json)
    gm.close()


@goal_app.command("show")
def goal_show(goal_id: str, json: bool = False):
    gm = GoalManager()
    _echo(gm.get_goal(goal_id).as_dict(), json)
    gm.close()


@goal_app.command("approve")
def goal_approve(goal_id: str, json: bool = False):
    """Approve a high-risk goal that is waiting for approval."""
    gm = GoalManager()
    _echo(gm.approve_goal(goal_id).as_dict(), json)
    gm.close()


@goal_app.command("execute-next")
def goal_execute_next(json: bool = False):
    """Promote the highest-priority READY goal to ACTIVE."""
    gm = GoalManager()
    gm.find_ready_goals()
    goal = gm.execute_next_goal()
    _echo(goal.as_dict() if goal else "no ready goals", json)
    gm.close()


@goal_app.command("pause")
def goal_pause(goal_id: str, json: bool = False):
    gm = GoalManager(); _echo(gm.pause_goal(goal_id).as_dict(), json); gm.close()


@goal_app.command("resume")
def goal_resume(goal_id: str, json: bool = False):
    gm = GoalManager(); _echo(gm.resume_goal(goal_id).as_dict(), json); gm.close()


@goal_app.command("cancel")
def goal_cancel(goal_id: str, json: bool = False):
    gm = GoalManager(); _echo(gm.cancel_goal(goal_id).as_dict(), json); gm.close()


@goal_app.command("complete")
def goal_complete(goal_id: str, json: bool = False):
    gm = GoalManager(); _echo(gm.complete_goal(goal_id).as_dict(), json); gm.close()


# --- self ------------------------------------------------------------------

@app.command("report")
def self_report(json: bool = False):
    """Operational self-report: goals, curiosity, learning."""
    _echo(generate_self_report(), json)


@app.command("curiosity")
def self_curiosity(json: bool = False):
    ce = CuriosityEngine()
    _echo([c.as_dict() for c in ce.rank_curiosity()] or "no open curiosity", json)
    ce.close()


@app.command("curiosity-add")
def curiosity_add(question: str, origin: str = "observation", json: bool = False):
    ce = CuriosityEngine()
    _echo(ce.generate_curiosity(question, origin).as_dict(), json)
    ce.close()


@app.command("learn")
def self_learn(json: bool = False):
    """Recent experiences, lessons and skill proposals."""
    le = LearningEngine()
    data = {
        "recent_experiences": [e.as_dict() for e in le.list_experiences(10)],
        "lessons": le.list_lessons(),
        "skill_proposals": le.list_skill_proposals(),
        "pattern": le.derive_pattern(),
    }
    _echo(data, json)
    le.close()


# --- research ---------------------------------------------------------------

@research_app.command("create")
def research_create(question: str, json: bool = False):
    rs = ResearchStore()
    mission = rs.create_research(question)
    _echo({"id": mission.id, "question": mission.question, "status": mission.status}, json)
    rs.close()


@research_app.command("add-source")
def research_add_source(mission_id: int, url: str, json: bool = False):
    rs = ResearchStore()
    source = rs.add_source(mission_id, url)
    _echo({"id": source.id, "url": source.url, "credibility": source.credibility}, json)
    rs.close()


@research_app.command("add-claim")
def research_add_claim(mission_id: int, source_id: int, claim: str, json: bool = False):
    rs = ResearchStore()
    c = rs.add_claim(mission_id, source_id, claim)
    _echo({"id": c.id, "source_id": c.source_id, "claim": c.text, "polarity": c.polarity}, json)
    rs.close()


@research_app.command("synthesize")
def research_synthesize(mission_id: int, json: bool = False):
    rs = ResearchStore()
    synthesis = rs.synthesize(mission_id)
    contradictions = rs.detect_contradictions(mission_id)
    _echo({"synthesis": synthesis, "contradictions": contradictions}, json)
    rs.close()


@research_app.command("report")
def research_report(mission_id: int, json: bool = False):
    rs = ResearchStore()
    m = rs.get_mission(mission_id)
    _echo({
        "id": m.id, "question": m.question, "status": m.status,
        "synthesis": m.synthesis,
        "sources": [{"id": s.id, "url": s.url, "credibility": s.credibility} for s in m.sources],
        "claims": [{"id": c.id, "claim": c.text, "polarity": c.polarity} for c in m.claims],
    }, json)
    rs.close()


if __name__ == "__main__":
    app()
