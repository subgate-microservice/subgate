import asyncio
from collections import defaultdict

import pytest
import pytest_asyncio
import uvicorn
from fastapi import FastAPI
from loguru import logger

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


@pytest_asyncio.fixture(scope="module", autouse=True)
async def fastapi_server():
    config = uvicorn.Config(app, host=HOST, port=PORT, log_config=None)
    server = uvicorn.Server(config)
    task = asyncio.create_task(server.serve())
    await asyncio.sleep(1)  # Ждем запуска сервера
    yield
    await server.shutdown()
    task.cancel()


@pytest_asyncio.fixture()
async def deliveries():
    deliveries = []
    for i in range(120):
        partkey = str(i % 3)
        msg = Message(
            type="event",
            event_code=f"code_{i}",
            occurred_at=get_current_datetime(),
            payload={"partkey": partkey, "number": i},
        )
        delivery = DeliveryTask(
            url=f"http://{HOST}:{PORT}/message-handler",
            data=msg,
            delays=(0, 1, 2),
            partkey=partkey,
        )
        deliveries.append(delivery)

    async with container.unit_of_work_factory().create_uow() as uow:
        await uow.delivery_task_repo().add_many(deliveries)
        await uow.commit()

    yield deliveries


@pytest.mark.asyncio
async def test_sequential_deliveries_with_the_same_partkey(deliveries):
    telegraph = Telegraph(container.unit_of_work_factory())

    async def stop_task():
        await asyncio.sleep(DELAY * 2)
        telegraph.stop_worker()

    _task = asyncio.create_task(stop_task())
    await telegraph.run_worker()

    assert len(store.get_all_messages()) == len(deliveries)
    for partkey, messages in store.get_grouped_by_partkey().items():
        number = messages[0].payload["number"]
        for msg in messages[1:]:
            assert msg.payload["number"] > number
            number = msg.payload["number"]
