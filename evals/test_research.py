import asyncio
import json

import pytest

from agents_service.models import TaskResultStatus
from evals.judge_agents.research_evaluator import evaluator as research_evaluator
from evals.prompts import RESEARCH_EVAL_PROMPT

PASSING_THRESHOLD = 0.6


def _findings_to_str(result) -> str:
    return json.dumps(
        {
            "summary": result.summary,
            "key_findings": [
                {
                    "point": f.point,
                    "supporting_detail": f.supporting_detail,
                    "source_urls": f.source_urls,
                }
                for f in result.key_findings
            ],
            "notes": result.notes,
        },
        indent=2,
    )


def _get_objective(task_id: str, research_plan) -> str:
    for task in research_plan.tasks:
        if task.id == task_id:
            return task.objective
    return ""


class TestResearch:
    # ── Deterministic ─────────────────────────────────────────

    def test_all_tasks_have_results(self, research_plan, task_results):
        missing = [t.id for t in research_plan.tasks if t.id not in task_results]
        assert not missing, f"Missing results for tasks: {missing}"

    def test_no_failed_tasks(self, task_results):
        failed = [
            tid
            for tid, r in task_results.items()
            if r.status == TaskResultStatus.FAILED
        ]
        assert not failed, f"Tasks failed: {failed}"

    def test_findings_not_empty(self, task_results):
        empty = [
            tid
            for tid, r in task_results.items()
            if r.status == TaskResultStatus.SUCCESS and len(r.key_findings) == 0
        ]
        assert not empty, f"Tasks succeeded but returned no findings: {empty}"

    def test_findings_have_sources(self, task_results):
        failures = []
        for tid, result in task_results.items():
            for finding in result.key_findings:
                if not finding.source_urls:
                    failures.append(
                        f"Task {tid}: finding has no sources: {finding.point[:60]}"
                    )
        assert not failures, "\n".join(failures)

    def test_diagram_data_populated_where_required(self, research_plan, task_results):
        missing = [
            t.id
            for t in research_plan.tasks
            if t.diagram_plan
            and (t.id not in task_results or task_results[t.id].diagram_data is None)
        ]
        assert not missing, f"Tasks required diagram data but none returned: {missing}"

    def test_diagram_type_matches_plan(self, research_plan, task_results):
        mismatches = []
        for task in research_plan.tasks:
            if not task.diagram_plan:
                continue
            result = task_results.get(task.id)
            if result and result.diagram_data:
                if result.diagram_data.diagram_type != task.diagram_plan.diagram_type:
                    mismatches.append(
                        f"Task {task.id}: expected "
                        f"{task.diagram_plan.diagram_type}, "
                        f"got {result.diagram_data.diagram_type}"
                    )
        assert not mismatches, "\n".join(mismatches)

    # ── LLM Graded ───────────────────────────────────────────

    def test_findings_grounded_in_objective(self, research_plan, task_results):
        failures = []
        for task_id, result in task_results.items():
            if result.status == TaskResultStatus.FAILED:
                continue
            objective = _get_objective(task_id, research_plan)
            prompt = RESEARCH_EVAL_PROMPT.format(
                objective=objective,
                findings=_findings_to_str(result),
            )
            eval_result = asyncio.run(research_evaluator.run(prompt))
            score_obj = eval_result.output
            if score_obj.score.score < PASSING_THRESHOLD:
                failures.append(
                    f"Task {task_id}: score {score_obj.score.score:.2f} "
                    f"— {score_obj.score.reason}"
                )
        assert not failures, "\n".join(failures)
