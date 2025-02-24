import asyncio

import httpx
from loguru import logger

from backend.shared.unit_of_work.uow import UnitOfWorkFactory, UnitOfWork
from backend.webhook.domain.telegram import SentErrorInfo, Telegram


class RequestClient:
    def __init__(self):
        self.client = httpx.AsyncClient()

    async def safe_request(self, telegram: Telegram) -> Telegram:
        payload = telegram.data.model_dump(mode="json")
        error = None
        try:
            response = await self.client.request("POST", telegram.url, json=payload)
            if response.status_code >= 400:
                error = SentErrorInfo(
                    status_code=response.status_code,
                    detail="request_error",
                )
        except Exception as err:
            error = SentErrorInfo(
                status_code=500,
                detail=str(err),
            )

        if error:
            msg = (
                f"SendError(telegram_id={telegram.id}, status={error.status_code},"
                f" retry_count={telegram.retries}, detail={error.detail})"
            )
            logger.error(msg)

        return telegram.failed_sent(error) if error else telegram.success_sent()


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
        self._client = RequestClient()

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
                    updated_telegrams = []
                    tasks = []
                    for msg in messages:
                        task = asyncio.create_task(self._client.safe_request(msg))
                        task.add_done_callback(lambda x: updated_telegrams.append(x.result()))
                        tasks.append(task)
                    await asyncio.gather(*tasks)
                    await uow.telegram_repo().update_many(updated_telegrams)
                    await uow.commit()
            except Exception as err:
                logger.error(err)
            finally:
                try:
                    await asyncio.wait_for(self._wake_event.wait(), timeout=self._sleep_time)
                except asyncio.TimeoutError:
                    pass
                finally:
                    self._wake_event.clear()
