import asyncio
import uuid
from collections import defaultdict
from typing import Callable

import pytest
import pytest_asyncio
import uvicorn
from fastapi import FastAPI

from backend.bootstrap import get_container
from backend.shared.utils import get_current_datetime
from backend.webhook.application.telegraph import Telegraph
from backend.webhook.domain.delivery_task import Message, DeliveryTask

container = get_container()

HOST = "localhost"
PORT = 5678
DELAY = 0.2

app = FastAPI()


class MessageStore:
    def __init__(self):
        self._messages: list[Message] = []

    def add_message(self, msg: Message):
        self._messages.append(msg)

    def get_all_messages(self):
        return self._messages

    def get_grouped_by_partkey(self) -> dict[str, list[Message]]:
        result = defaultdict(list)
        for msg in self._messages:
            partkey = msg.payload["partkey"]
            result[partkey].append(msg)
        return result

    def clear(self):
        self._messages = []


store = MessageStore()


@pytest.fixture(autouse=True)
def clear_store():
    store.clear()


@app.post("/message-handler")
async def message_handler(msg: Message) -> str:
    await asyncio.sleep(DELAY)
    store.add_message(msg)
    return "OK"


@app.post("/bad-message-handler")
async def bad_message_handler(_msg: Message):
    raise NotImplemented


@pytest_asyncio.fixture(scope="module", autouse=True)
async def fastapi_server():
    config = uvicorn.Config(app, host=HOST, port=PORT, log_config=None)
    server = uvicorn.Server(config)
    task = asyncio.create_task(server.serve())
    await asyncio.sleep(1)  # Ждем запуска сервера
    yield
    await server.shutdown()
    task.cancel()


async def create_deliveries(count: int, url: str, partkey_func: Callable[[], str], delays=(0, 0, 0,)):
    deliveries = []
    for i in range(count):
        partkey = partkey_func()
        msg = Message(
            type="event",
            event_code=f"code_{i}",
            occurred_at=get_current_datetime(),
            payload={"partkey": partkey, "number": i},
        )
        delivery = DeliveryTask(
            url=url,
            data=msg,
            delays=delays,
            partkey=partkey,
        )
        deliveries.append(delivery)

    async with container.unit_of_work_factory().create_uow() as uow:
        await uow.delivery_task_repo().add_many(deliveries)
        await uow.commit()

    return deliveries


@pytest_asyncio.fixture()
async def deliveries_with_the_same_partkey():
    yield await create_deliveries(
        20,
        f"http://{HOST}:{PORT}/message-handler",
        lambda: "Hello"
    )


@pytest_asyncio.fixture()
async def deliveries_with_different_partkeys():
    yield await create_deliveries(
        20,
        f"http://{HOST}:{PORT}/message-handler",
        lambda: str(uuid.uuid4())
    )


@pytest_asyncio.fixture()
async def deliveries_with_wrong_url():
    yield await create_deliveries(
        3,
        "http://very-bad-url.com",
        lambda: str(uuid.uuid4())
    )


@pytest_asyncio.fixture()
async def deliveries_with_bad_handler():
    yield await create_deliveries(
        3,
        f"http://{HOST}:{PORT}/bad-message-handler",
        lambda: str(uuid.uuid4())
    )


async def telegraph_worker():
    telegraph = Telegraph(container.unit_of_work_factory(), sleep_time=0.1)

    async def stop_task():
        while True:
            await asyncio.sleep(0.3)
            async with container.unit_of_work_factory().create_uow() as uow:
                deliveries = await uow.delivery_task_repo().get_deliveries_for_send()
                if not deliveries:
                    break
        telegraph.stop_worker()

    _task = asyncio.create_task(stop_task())
    await telegraph.run_worker()


@pytest.mark.asyncio
async def test_sequential_deliveries_with_the_same_partkey(deliveries_with_the_same_partkey):
    await telegraph_worker()
    assert len(store.get_all_messages()) == len(deliveries_with_the_same_partkey)
    messages = store.get_all_messages()
    sorted_messages = list(sorted(messages, key=lambda x: x.payload["number"]))
    assert messages == sorted_messages


@pytest.mark.asyncio
async def test_concurrency_deliveries_with_different_partkeys(deliveries_with_different_partkeys):
    await telegraph_worker()
    assert len(store.get_all_messages()) == len(deliveries_with_different_partkeys)
    messages = store.get_all_messages()
    sorted_messages = list(sorted(messages, key=lambda x: x.payload["number"]))
    assert messages != sorted_messages


@pytest.mark.asyncio
async def test_deliveries_with_bad_url(deliveries_with_wrong_url):
    await telegraph_worker()
    async with container.unit_of_work_factory().create_uow() as uow:
        deliveries = await uow.delivery_task_repo().get_all()
        assert len(deliveries) == 3
        for delivery in deliveries:
            assert delivery.retries == 3
            assert delivery.status == "failed_sent"


@pytest.mark.asyncio
async def test_deliveries_with_bad_handler(deliveries_with_bad_handler):
    await telegraph_worker()
    async with container.unit_of_work_factory().create_uow() as uow:
        deliveries = await uow.delivery_task_repo().get_all()
        assert len(deliveries) == 3
        for delivery in deliveries:
            assert delivery.retries == 3
            assert delivery.status == "failed_sent"
