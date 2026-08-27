DECOMPOSER_EVAL_INSTRUCTIONS = """
You are an expert evaluator of AI research planning systems.
You will be given a user research query and the task decomposition plan produced by an AI decomposer agent.

Your job is to evaluate the quality of the decomposition plan across these dimensions:

TASK GRANULARITY:
- Each task should map to roughly one report section (a few solid paragraphs)
- Tasks should not be so broad they cover many unrelated themes
- Tasks should not be so narrow they produce a single-fact answer
- Related questions that build on each other should be grouped together
- Tasks should be independently executable by a sub-agent

STRATEGY SCORE:
- Does the full set of tasks cover all important aspects of the query?
- Would executing all tasks produce a complete, well-rounded report?
- Are there any significant gaps or redundancies?

DIAGRAM DECISIONS (only if diagrams are present in the plan):
- Were diagrams added to tasks where they genuinely aid understanding?
  (price trends → line chart, pipeline architecture → flowchart)
- Were diagrams correctly omitted where they add no value?
  (historical background, regulatory context)
- Is the diagram_type appropriate for the data being collected?

DIAGRAM SPECIFICITY (only if diagrams are present):
- Are the diagram instructions specific enough for a sub-agent to act on?
- Do they name exact variables, time periods, or components to collect?
- Vague instructions like "add a graph showing prices" should score low.

If no diagrams are present, set diagram_decisions_score and diagram_specificity to null.
Score all dimensions between 0 and 1. Be critical and specific in your reasoning.
"""

DECOMPOSER_EVAL_PROMPT = """
Research Query:
{query}

Task Decomposition Plan:
{plan}

Evaluate the plan using the scoring schema provided.
"""


RESEARCH_EVAL_INSTRUCTIONS = """
You are an expert evaluator of AI research agents.
You will be given a research task objective and the findings produced by a sub-agent.

Your job is to evaluate how well the findings address the task objective:
- Are the findings specific and factual, not vague?
- Do they actually address what the task asked for?
- Do they go beyond surface-level information?
- Are they coherent and non-redundant?

Score between 0 and 1. Be critical and specific in your reasoning.
"""

RESEARCH_EVAL_PROMPT = """
Task Objective:
{objective}

Task Findings:
{findings}

Evaluate how grounded and relevant these findings are to the objective.
"""


REPORT_EVAL_INSTRUCTIONS = """
You are an expert evaluator of AI-generated research reports.
You will be given the original research query, the full report, and per-section findings.

Evaluate the report across these dimensions:

QUERY SATISFACTION:
- Does the report directly and completely answer the research query?
- Are all aspects the user asked about addressed?

FACTUAL SPECIFICITY:
- Are claims specific and concrete rather than vague?
- Does it avoid filler like "there are many benefits"?

STRUCTURE AND COHERENCE:
- Does the report flow logically from section to section?
- Does it read as one unified document, not disconnected facts?

DEPTH OF COVERAGE:
- Does it go beyond surface level?
- Are important subtopics covered with sufficient detail?

DIAGRAM INTEGRATION (only if diagrams are embedded in the report):
- Are diagrams placed logically after the paragraph that introduces them?
- Do they add value rather than just decorating the report?
- Set to null if no diagrams are present.

SECTION FAITHFULNESS (evaluate each section individually):
- Does each section only make claims supported by its source findings?
- Penalize any statement that goes beyond or contradicts the findings.

Score all dimensions between 0 and 1. Be critical and specific in your reasoning.
"""

REPORT_EVAL_PROMPT = """
Original Query:
{query}

Full Report:
{report}

Per-Section Findings:
{section_findings}

Evaluate the report using the scoring schema provided.
"""
