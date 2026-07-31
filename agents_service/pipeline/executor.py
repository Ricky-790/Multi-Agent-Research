import asyncio

from aiolimiter import AsyncLimiter
from pydantic_ai.exceptions import ModelHTTPError

from agents_service.agents.subagent import execute_task
from agents_service.models import (
    ResearchPlan,
    Task,
    TaskResult,
    TaskResultStatus,
)
from custom_logger import get_logger

logger = get_logger()

rate_limiter = AsyncLimiter(max_rate=10, time_period=60)  # Limit to 10 RPM


async def _execute_task_with_retry(
    task: Task,
    results_so_far: dict[str, TaskResult],
    max_retries: int = 3,
) -> TaskResult:
    last_error: Exception | None = None

    for attempt in range(max_retries):
        try:
            async with rate_limiter:
                return await execute_task(task, results_so_far)
        except ModelHTTPError as e:
            last_error = e
            if e.status_code == 429 and attempt < max_retries - 1:
                wait = _extract_retry_delay(e) or 45
                logger.warning(
                    f"Rate limited on {task.id} (attempt {attempt + 1}/{max_retries}), "
                    f"retrying in {wait}s"
                )
                await asyncio.sleep(wait)
                continue
            break
        except Exception as e:
            last_error = e
            break

    logger.exception(f"Task {task.id} failed after retries")
    return TaskResult(
        task_id=task.id,
        status=TaskResultStatus.FAILED,
        summary=f"Task failed after {max_retries} attempts: {last_error}",
        key_findings=[],
        sources=[],
        notes=str(last_error),
    )


def _extract_retry_delay(error: ModelHTTPError) -> float | None:
    try:
        details = error.body.get("error", {}).get("details", [])
        for d in details:
            if d.get("@type", "").endswith("RetryInfo"):
                delay_str = d.get("retryDelay", "")  # e.g. "41s"
                return float(delay_str.rstrip("s"))
    except Exception:
        pass
    return None


async def execute_research_phase(
    plan: ResearchPlan,
    max_concurrency: int = 2,  # Can increase with higher RPM cap
) -> dict[str, TaskResult]:
    """
    Executes all tasks in a ResearchPlan's DAG, respecting dependencies, using
    topological batching (Kahn's algorithm). Tasks with no unmet dependencies run
    concurrently, bounded by max_concurrency AND a shared rate limiter to stay
    within provider RPM limits.
    """
    semaphore = asyncio.Semaphore(max_concurrency)
    done: dict[str, TaskResult] = {}
    remaining: dict[str, Task] = {t.id: t for t in plan.tasks}

    async def run_with_limit(task: Task) -> TaskResult:
        async with semaphore:
            logger.info(f"Starting task {task.id}: {task.name}")
            result = await _execute_task_with_retry(task, done)
            logger.info(f"Finished task {task.id} with status={result.status}")
            return result

    while remaining:
        ready = [
            t for t in remaining.values() if all(dep in done for dep in t.depends_on)
        ]

        if not ready:
            stuck_ids = list(remaining.keys())
            raise RuntimeError(
                f"DAG execution stalled — remaining tasks {stuck_ids} have "
                f"unresolvable dependencies (possible cycle or missing task id)."
            )

        results = await asyncio.gather(*[run_with_limit(t) for t in ready])

        for t, r in zip(ready, results):
            done[t.id] = r
            del remaining[t.id]

    return done
