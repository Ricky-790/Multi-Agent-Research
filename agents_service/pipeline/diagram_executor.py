import asyncio

from e2b_code_interpreter import Sandbox
from pydantic_ai import Agent

from agents_service.models import DiagramAgentOutput, DiagramData
from agents_service.pipeline.rate_limiting import nvidia_rate_limiter

_sandbox_semaphore = asyncio.Semaphore(3)


async def execute_diagram(
    diagram_data: DiagramData,
    diagram_agent: Agent,
) -> bytes:
    """
    Acquires a sandbox slot, generates code with retry loop, returns PNG bytes.
    Blocks if 3 sandboxes are already running.
    """
    async with _sandbox_semaphore:  # blocks here if 3 already in use
        return await _run_diagram_in_sandbox(diagram_data, diagram_agent)
