import asyncio
import logging
from typing import List, Awaitable, Any

logger = logging.getLogger(__name__)


class ConcurrencyLimiter:
    def __init__(self, max_concurrent: int):
        self.semaphore = asyncio.Semaphore(max_concurrent)

    async def limit(self, task: Awaitable) -> Any:
        async with self.semaphore:
            try:
                return await task
            except Exception as e:
                logger.error(f"Task failed with error: {e}")
                return e

    async def execute(self, tasks: List[Awaitable]) -> List[Any]:
        wrapped_tasks = [self.limit(task) for task in tasks]
        return await asyncio.gather(*wrapped_tasks)
