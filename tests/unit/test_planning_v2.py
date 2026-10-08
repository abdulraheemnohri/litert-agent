from pytest import raises

from litert_agent.cognition.planner import (
    DependencyResolver,
    PlanStep,
    PlanValidationError,
    Planner,
    RiskEstimator,
)


def test_planner_builds_dependency_aware_proposal():
    proposal = Planner().create_plan_proposal("create a project and run tests")
    assert proposal.steps[0].id == "inspect"
    assert proposal.steps[-1].id == "verify"
    assert proposal.overall_risk in {"low", "medium", "high", "critical"}
    assert proposal.estimated_cost > 0


def test_dependency_resolver_rejects_missing_dependency():
    steps = [PlanStep(id="a", description="A", depends_on=["missing"])]
    with raises(PlanValidationError, match="missing dependencies"):
        DependencyResolver.order(steps)


def test_dependency_resolver_rejects_cycles():
    steps = [
        PlanStep(id="a", description="A", depends_on=["b"]),
        PlanStep(id="b", description="B", depends_on=["a"]),
    ]
    with raises(PlanValidationError, match="cycle"):
        DependencyResolver.order(steps)


def test_risk_estimator_is_conservative():
    assert RiskEstimator.estimate("push changes", "git") == "high"
    assert RiskEstimator.estimate("write a file", "filesystem") == "medium"
    assert RiskEstimator.estimate("inspect status", "terminal") == "low"


def test_replan_does_not_disable_policy():
    proposal = Planner().create_plan_proposal("inspect repository")
    recovery = Planner().replan(proposal, "inspect", "temporary failure")
    assert recovery.steps[-1].capability == "recovery"
    assert recovery.steps[-1].risk == "medium"
