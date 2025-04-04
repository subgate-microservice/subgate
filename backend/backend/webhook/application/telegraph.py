import asyncio
from collections import defaultdict

import httpx
from loguru import logger

from backend.shared.unit_of_work.uow import UnitOfWorkFactory, UnitOfWork
from backend.webhook.domain.delivery_task import SentErrorInfo, DeliveryTask


class RequestClient:
    def __init__(self):
        self.client = httpx.AsyncClient()

    async def safe_request(self, delivery: DeliveryTask) -> DeliveryTask:
        payload = delivery.data.model_dump(mode="json")
        error = None
        try:
            response = await self.client.request("POST", delivery.url, json=payload)
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
                f"SendError(delivery_id={delivery.id}, status={error.status_code},"
                f" retry_count={delivery.retries}, detail={error.detail})"
            )
            logger.error(msg)

        return delivery.failed_sent(error) if error else delivery.success_sent()


async def safe_commit(uow: UnitOfWork, msg: DeliveryTask):
    try:
        await uow.delivery_task_repo().update_one(msg)
        await uow.commit()
    except Exception as err:
        logger.error(err)


def group_deliveries(deliveries: list[DeliveryTask]) -> dict[str, list[DeliveryTask]]:
    result = defaultdict(list)
    for tlg in deliveries:
        result[tlg.partkey].append(tlg)
    return result


class Telegraph:
    def __init__(self, uow_factory: UnitOfWorkFactory):
        self._uow_factory = uow_factory
        self._client = RequestClient()

    async def _partkey_worker(self, deliveries: list[DeliveryTask]) -> list[DeliveryTask]:
        updated_deliveries = []
        for delivery in deliveries:
            updated = await self._client.safe_request(delivery)
            updated_deliveries.append(updated)
        return updated_deliveries

    async def notify(self):
        async with self._uow_factory.create_uow() as uow:
            deliveries = await uow.delivery_task_repo().get_deliveries_for_send()
            logger.info(f"Check delivery tasks: {len(deliveries)} need to send")

            updated_deliveries = []
            tasks = []
            for partkey, grouped_deliveries in group_deliveries(deliveries).items():
                task = asyncio.create_task(self._partkey_worker(grouped_deliveries))
                task.add_done_callback(lambda x: updated_deliveries.extend(x.result()))
                tasks.append(task)
            await asyncio.gather(*tasks)
            await uow.delivery_task_repo().update_many(updated_deliveries)
            await uow.commit()

            if updated_deliveries:
                successes = len([x for x in updated_deliveries if x.status == "success_sent"])
                fails = len(updated_deliveries) - successes
                logger.info(
                    f"{len(updated_deliveries)} DeliveryTasks were processed. {successes} success, {fails} failed"
                )
