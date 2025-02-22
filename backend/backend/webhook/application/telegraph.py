import asyncio
from typing import Optional

import aiohttp
from loguru import logger

from backend.shared.unit_of_work.uow import UnitOfWorkFactory, UnitOfWork
from backend.webhook.domain.telegram import SentErrorInfo, Telegram


async def safe_request(method: str, url: str, **kwargs) -> Optional[SentErrorInfo]:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.request(method, url, **kwargs) as response:
                if response.status >= 400:
                    return SentErrorInfo(status_code=response.status, detail="Request error")
                return None
    except Exception as err:
        return SentErrorInfo(status_code=500, detail=str(err))


async def safe_commit(uow: UnitOfWork, msg: Telegram):
    try:
        await uow.telegram_repo().update_one(msg)
        await uow.commit()
    except Exception as err:
        logger.error(err)


class Telegraph:
    def __init__(self, uow_factory: UnitOfWorkFactory, sleep_time=10):
        self._uow_factory = uow_factory
        self._STOP_FLAG = False
        self._wake_event = asyncio.Event()  # Событие для пробуждения
        self._sleep_time = sleep_time

    def stop_worker(self):
        self._STOP_FLAG = True
        self.wake_worker()

    def wake_worker(self):
        self._wake_event.set()

    async def run_worker(self):
        self._STOP_FLAG = False

        while True:
            if self._STOP_FLAG:
                break

            try:
                async with self._uow_factory.create_uow() as uow:
                    messages = await uow.telegram_repo().get_messages_for_send()
                    logger.info(f"Need to send {len(messages)} telegrams")
                    for msg in messages:
                        error_info = await safe_request("POST", msg.url, json=msg.data)
                        updated_msg = msg.failed_sent(error_info) if error_info else msg.success_sent()
                        await safe_commit(uow, updated_msg)
            except Exception as err:
                logger.exception(err)
            finally:
                try:
                    await asyncio.wait_for(self._wake_event.wait(), timeout=self._sleep_time)
                except asyncio.TimeoutError:
                    pass
                finally:
                    self._wake_event.clear()
