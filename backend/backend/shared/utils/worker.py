import asyncio
from typing import Awaitable, Callable
from uuid import uuid4

from loguru import logger


class Worker:
    def __init__(
            self,
            callback: Callable[[], Awaitable[None]],
            sleep_time=0,
            safe=False,
            task_name: str = None,
    ):
        self._callback = callback
        self._STOP_FLAG = False
        self._wake_event = asyncio.Event()
        self._safe = safe
        self._sleep_time = sleep_time
        self._task_name = task_name or str(uuid4())

    async def _run(self):
        self._STOP_FLAG = False

        while True:
            if self._STOP_FLAG:
                break

            try:
                await self._callback()
            except Exception as err:
                if self._safe:
                    logger.exception(err)
                else:
                    raise err
            finally:
                try:
                    await asyncio.wait_for(self._wake_event.wait(), timeout=self._sleep_time)
                except asyncio.TimeoutError:
                    pass
                finally:
                    self._wake_event.clear()

    def run(self):
        logger.info(f"Run {self._task_name}")
        task = asyncio.create_task(self._run())
        if self._task_name:
            task.set_name(self._task_name)

    async def run_until_complete(self):
        logger.info(f"Run {self._task_name}")
        task = asyncio.create_task(self._run())
        if self._task_name:
            task.set_name(self._task_name)
        await task

    def stop(self):
        logger.info(f"Stop {self._task_name}")
        self._STOP_FLAG = True
        self.wake()

    def wake(self):
        self._wake_event.set()
