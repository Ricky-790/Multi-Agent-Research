import asyncio
import json

import pytest

from evals.judge_agents.decompose_task_evaluator import (
    evaluator as decomposer_evaluator,
)
from evals.prompts import DECOMPOSER_EVAL_PROMPT

PASSING_THRESHOLD = 0.6


def _plan_to_str(research_plan) -> str:
    tasks = []
    for task in research_plan.tasks:
        tasks.append(
            {
                "id": task.id,
                "name": task.name,
                "objective": task.objective,
                "depends_on": task.depends_on,
                "diagram_plan": (
                    {
                        "diagram_type": task.diagram_plan.diagram_type.value,
                        "instruction": task.diagram_plan.instruction,
                    }
                    if task.diagram_plan
                    else None
                ),
            }
        )
    return json.dumps(tasks, indent=2)


def _run_decomposer_eval(query: str, research_plan):
    prompt = DECOMPOSER_EVAL_PROMPT.format(
        query=query,
        plan=_plan_to_str(research_plan),
    )
    result = asyncio.run(decomposer_evaluator.run(prompt))
    return result.output


class TestDecomposer:
    @pytest.fixture(scope="class")
    def eval_score(self, query, research_plan):
        """Run evaluator once, reuse across all tests in this class."""
        return _run_decomposer_eval(query, research_plan)

    def test_task_granularity(self, eval_score):
        score = eval_score.task_granularity.score
        reason = eval_score.task_granularity.reason
        assert score >= PASSING_THRESHOLD, (
            f"Task granularity score {score:.2f} below threshold "
            f"{PASSING_THRESHOLD}.\nReason: {reason}"
        )

    def test_strategy_coverage(self, eval_score):
        score = eval_score.strategy_score.score
        reason = eval_score.strategy_score.reason
        assert score >= PASSING_THRESHOLD, (
            f"Strategy coverage score {score:.2f} below threshold "
            f"{PASSING_THRESHOLD}.\nReason: {reason}"
        )

    def test_diagram_decisions(self, eval_score, research_plan):
        has_diagrams = any(t.diagram_plan for t in research_plan.tasks)
        if not has_diagrams:
            pytest.skip("No diagrams in this plan — skipping diagram decision test")
        assert eval_score.diagram_decisions_score is not None, (
            "Plan has diagrams but evaluator returned no diagram_decisions_score"
        )
        score = eval_score.diagram_decisions_score.score
        reason = eval_score.diagram_decisions_score.reason
        assert score >= PASSING_THRESHOLD, (
            f"Diagram decisions score {score:.2f} below threshold "
            f"{PASSING_THRESHOLD}.\nReason: {reason}"
        )

    def test_diagram_specificity(self, eval_score, research_plan):
        has_diagrams = any(t.diagram_plan for t in research_plan.tasks)
        if not has_diagrams:
            pytest.skip("No diagrams in this plan — skipping diagram specificity test")
        assert eval_score.diagram_specificity is not None, (
            "Plan has diagrams but evaluator returned no diagram_specificity score"
        )
        score = eval_score.diagram_specificity.score
        reason = eval_score.diagram_specificity.reason
        assert score >= PASSING_THRESHOLD, (
            f"Diagram specificity score {score:.2f} below threshold "
            f"{PASSING_THRESHOLD}.\nReason: {reason}"
        )
