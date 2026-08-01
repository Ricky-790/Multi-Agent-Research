import asyncio

from aiolimiter import AsyncLimiter
from pydantic_ai.exceptions import ModelHTTPError

from custom_logger import get_logger

logger = get_logger()

# Shared across ALL Gemini calls in the pipeline
gemini_rate_limiter = AsyncLimiter(max_rate=10, time_period=60)


def extract_retry_delay(error: ModelHTTPError) -> float | None:
    try:
        details = error.body.get("error", {}).get("details", [])
        for d in details:
            if d.get("@type", "").endswith("RetryInfo"):
                return float(d.get("retryDelay", "").rstrip("s"))
    except Exception:
        pass
    return None


async def run_with_retry(coro_fn, *args, max_retries: int = 4, **kwargs):
    """
    Runs an async callable under the shared rate limiter, retrying on 429s using the
    provider's suggested delay. coro_fn should be a no-arg-bound async function
    (e.g. a partial, or call this with args/kwargs to pass through).
    """
    last_error: Exception | None = None

    for attempt in range(max_retries):
        try:
            async with gemini_rate_limiter:
                return await coro_fn(*args, **kwargs)
        except ModelHTTPError as e:
            last_error = e
            if e.status_code == 429 and attempt < max_retries - 1:
                wait = extract_retry_delay(e) or 45
                logger.warning(
                    f"Rate limited (attempt {attempt + 1}/{max_retries}), retrying in {wait:.0f}s"
                )
                await asyncio.sleep(wait)
                continue
            raise

    if last_error is not None:
       raise last_error
