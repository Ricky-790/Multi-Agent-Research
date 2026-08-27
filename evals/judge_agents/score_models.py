from pydantic import BaseModel, Field


class ScoreField(BaseModel):
    score: float = Field(
        ...,
        description="Score you would give to this specific output. All scores are between 0 and 1.",
        lt=1,
        ge=0,
    )
    reason: str = Field(
        ...,
        description="Your detailed reasoning for this score, why its good or why its bad, what needs working.",
    )


# DECOMPOSITION SCORE MODELS
class TaskDecompositionScore(BaseModel):
    task_granularity: ScoreField = Field(
        ...,
        description="How low level each task is, or how independent all tasks are of each other.",
        lt=1,
        ge=0,
    )
    strategy_score: ScoreField = Field(
        ...,
        description="How well the strategy proposed covers all the aspects of the topic.",
        lt=1,
        ge=0,
    )
    diagram_decisions_score: ScoreField | None = Field(
        default=None,
        description="Were diagrams added to tasks where they genuinely aid understanding? Is the diagram_type appropriate for the data being collected?",
    )
    diagram_specificity: ScoreField | None = Field(
        default=None,
        description="Are the diagram instructions specific enough for a sub-agent to act on? If no diagrams were requested in the query, evaluate only whether the plan    correctly avoided adding unnecessary diagrams.",
    )


# SUBAGENT RESEARCH/TASK-RESULTS SCORE MODELS


class FindingsGroundedScore(BaseModel):  # LLM output, rest just deterministic checks
    task_id: str = Field(..., description="unique id of the task")
    score: ScoreField = Field(
        ...,
        description="does the finding actually address the task objective? Score how grounded or relevant the final results of the task are compared to the original query and the task objective",
    )


class TaskResultScore(FindingsGroundedScore):
    task_result: dict[str, str] | None = None


class ResearchPhaseScore(BaseModel):
    # Deterministic scores | Not llm dependent
    task_id_inconsistency: float
    tasks_success_rate: float
    diagram_population_score: float
    # LLM Score
    individual_task_scores: list[TaskResultScore]


# FULL REPORT
class SectionFaithfulnessScore(BaseModel):
    section_title: str = Field(..., description="Title of the section being evaluated.")
    score: ScoreField = Field(
        ...,
        description="Does the section only make claims supported by its source findings? Penalize hallucinated or contradicted statements.",
    )


class ReportQualityScore(BaseModel):
    query_satisfaction: ScoreField = Field(
        ...,
        description="Does the report directly and completely answer the original research query? Are all aspects addressed?",
    )
    factual_specificity: ScoreField = Field(
        ...,
        description="Are claims specific and concrete? Does it avoid vague filler like 'there are many benefits'?",
    )
    structure_and_coherence: ScoreField = Field(
        ...,
        description="Does the report flow logically across sections? Does it read as one unified document?",
    )
    depth_of_coverage: ScoreField = Field(
        ...,
        description="Does the report go beyond surface level? Are important subtopics covered with enough detail?",
    )
    diagram_integration: ScoreField | None = Field(
        default=None,
        description="Are diagrams placed logically and do they add value? Null if no diagrams were generated.",
    )
    section_faithfulness: list[SectionFaithfulnessScore] = Field(
        default_factory=list,
        description="Per-section faithfulness scores — does each section stay grounded in its source findings?",
    )
