import asyncio
import json

import pytest

from agents_service.models import TaskResultStatus
from evals.judge_agents.final_report_evaluator import evaluator as report_evaluator
from evals.prompts import REPORT_EVAL_PROMPT

PASSING_THRESHOLD = 0.6


def _build_section_findings(report_outline, task_results) -> str:
    sections = []
    for section in sorted(report_outline.sections, key=lambda s: s.order):
        findings = []
        for task_id in section.relevant_task_ids:
            result = task_results.get(task_id)
            if result is None or result.status == TaskResultStatus.FAILED:
                continue
            for f in result.key_findings:
                findings.append(f.point)
        sections.append(
            {
                "section_title": section.title,
                "findings": findings,
            }
        )
    return json.dumps(sections, indent=2)


def _run_report_eval(query, final_report, report_outline, task_results):
    prompt = REPORT_EVAL_PROMPT.format(
        query=query,
        report=final_report.content,
        section_findings=_build_section_findings(report_outline, task_results),
    )
    result = asyncio.run(report_evaluator.run(prompt))
    return result.output


class TestReport:
    # ── Deterministic ─────────────────────────────────────────

    def test_report_exists(self, final_report):
        assert final_report is not None, "Pipeline produced no final report"

    def test_report_not_empty(self, final_report):
        assert final_report.content.strip() != "", "Report content is empty"

    def test_report_has_title(self, final_report):
        assert final_report.title.strip() != "", "Report has no title"

    def test_report_min_word_count(self, final_report, expected):
        min_words = expected.get("report_min_words", 300)
        word_count = len(final_report.content.split())
        assert word_count >= min_words, (
            f"Report has {word_count} words, expected at least {min_words}"
        )

    def test_all_sections_present(self, report_outline, final_report):
        missing = [
            s.title
            for s in report_outline.sections
            if s.title not in final_report.content
        ]
        assert not missing, f"Sections missing from report: {missing}"

    def test_diagram_embeds_present(self, report_outline, final_report):
        failures = []
        for section in report_outline.sections:
            for diagram in section.diagrams:
                if diagram.url is None:
                    continue
                if diagram.url not in final_report.content:
                    failures.append(
                        f"Section '{section.title}': "
                        f"diagram '{diagram.caption}' not embedded"
                    )
        assert not failures, "\n".join(failures)

    # ── LLM Graded ───────────────────────────────────────────

    @pytest.fixture(scope="class")
    def eval_score(self, query, final_report, report_outline, task_results):
        """Run report evaluator once, reuse across all LLM-graded tests."""
        return _run_report_eval(query, final_report, report_outline, task_results)

    def test_query_satisfaction(self, eval_score):
        score = eval_score.query_satisfaction.score
        reason = eval_score.query_satisfaction.reason
        assert score >= PASSING_THRESHOLD, (
            f"Query satisfaction {score:.2f} below threshold.\nReason: {reason}"
        )

    def test_factual_specificity(self, eval_score):
        score = eval_score.factual_specificity.score
        reason = eval_score.factual_specificity.reason
        assert score >= PASSING_THRESHOLD, (
            f"Factual specificity {score:.2f} below threshold.\nReason: {reason}"
        )

    def test_structure_and_coherence(self, eval_score):
        score = eval_score.structure_and_coherence.score
        reason = eval_score.structure_and_coherence.reason
        assert score >= PASSING_THRESHOLD, (
            f"Structure and coherence {score:.2f} below threshold.\nReason: {reason}"
        )

    def test_depth_of_coverage(self, eval_score):
        score = eval_score.depth_of_coverage.score
        reason = eval_score.depth_of_coverage.reason
        assert score >= PASSING_THRESHOLD, (
            f"Depth of coverage {score:.2f} below threshold.\nReason: {reason}"
        )

    def test_diagram_integration(self, eval_score, report_outline):
        has_diagrams = any(d.url for s in report_outline.sections for d in s.diagrams)
        if not has_diagrams:
            pytest.skip("No diagrams generated — skipping diagram integration test")
        assert eval_score.diagram_integration is not None
        score = eval_score.diagram_integration.score
        reason = eval_score.diagram_integration.reason
        assert score >= PASSING_THRESHOLD, (
            f"Diagram integration {score:.2f} below threshold.\nReason: {reason}"
        )

    def test_section_faithfulness(self, eval_score):
        failures = []
        for section_score in eval_score.section_faithfulness:
            if section_score.score.score < PASSING_THRESHOLD:
                failures.append(
                    f"Section '{section_score.section_title}': "
                    f"{section_score.score.score:.2f} — "
                    f"{section_score.score.reason}"
                )
        assert not failures, "\n".join(failures)
