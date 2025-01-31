import asyncio
from datetime import timedelta
from unittest.mock import patch

import pytest
import pytest_asyncio
from loguru import logger

from backend.bootstrap import get_container
from backend.shared.unit_of_work.uow import UnitOfWork
from backend.shared.utils import get_current_datetime
from backend.webhook.application.telegraph import Telegraph, safe_commit
from backend.webhook.domain.telegram import Telegram, SentErrorInfo

container = get_container()


def mocked_get_next_retry(self):
    if self.retries + 1 >= self.max_retries:
        return None
    return get_current_datetime() + timedelta(seconds=0.1)


async def mocked_request_without_error(*_args, **_kwargs):
    return None


async def mocked_request_with_mix_error_and_success(*_args, **kwargs):
    message_data: str = kwargs["data"]
    number = int(message_data)
    return SentErrorInfo(status_code=404, detail="Not found") if number % 2 == 0 else None


async def mocked_safe_commit(uow: UnitOfWork, msg: Telegram):
    if int(msg.data) != 3:
        await safe_commit(uow, msg)
    else:
        logger.error(f"Any error in safe_commit was occurred with processing Message #{msg.data}")


@pytest_asyncio.fixture()
async def messages():
    messages = []
    for i in range(10):
        msg = Telegram(
            url="correct_url",
            data=f"{i}",
            next_retry_at=get_current_datetime() - timedelta(seconds=1),
            max_retries=3,
        )
        messages.append(msg)

    async with container.unit_of_work_factory().create_uow() as uow:
        await uow.telegram_repo().add_many(messages)
        await uow.commit()
    yield messages


@pytest.mark.asyncio
async def test_send_messages_with_success(messages):
    with patch("backend.webhook.application.telegraph.safe_request", mocked_request_without_error):
        # Отправляем успешные вебхуки
        telegraph = container.telegraph()
        task = asyncio.create_task(telegraph.run_worker())
        await asyncio.sleep(0.1)
        telegraph.stop_worker()
        await asyncio.gather(task)

        # Проверяем статусы сообщений
        async with container.unit_of_work_factory().create_uow() as uow:
            real = await uow.telegram_repo().get_all()
            assert len(real) == len(messages) and len(real) > 0
            for msg in real:
                assert msg.status == "success_sent"
                assert msg.next_retry_at is None
                assert msg.retries == 1


@pytest.mark.asyncio
async def test_send_messages_with_error(messages):
    async def mocked_request_with_error(*_args, **kwargs):
        message_data: str = kwargs["data"]
        logger.error(f"Message #{message_data}: any exception while request occurred")
        return SentErrorInfo(status_code=404, detail="Not found")

    with (patch("backend.webhook.application.telegraph.safe_request", mocked_request_with_error),
          patch("backend.webhook.domain.telegram.Telegram._get_next_retry", mocked_get_next_retry),
          ):
        # Отправляем провалившиеся вебхуки
        telegraph = Telegraph(container.unit_of_work_factory(), sleep_time=0.1)
        task = asyncio.create_task(telegraph.run_worker())
        await asyncio.sleep(3)
        telegraph.stop_worker()
        await asyncio.gather(task)

        # Проверяем статусы сообщений
        async with container.unit_of_work_factory().create_uow() as uow:
            real = await uow.telegram_repo().get_all()
            assert len(real) == len(messages) and len(real) > 0
            for msg in real:
                assert msg.status == "failed_sent"
                assert msg.retries == 3
                assert msg.next_retry_at is None


@pytest.mark.asyncio
async def test_send_messages_with_success_and_error(messages):
    with (patch("backend.webhook.application.telegraph.safe_request", mocked_request_with_mix_error_and_success),
          patch("backend.webhook.domain.telegram.Telegram._get_next_retry", mocked_get_next_retry),
          ):
        # Отправляем вебхуки
        telegraph = Telegraph(container.unit_of_work_factory(), sleep_time=0.1)
        task = asyncio.create_task(telegraph.run_worker())
        await asyncio.sleep(3)
        telegraph.stop_worker()
        await asyncio.gather(task)

        # Проверяем статусы сообщений
        async with container.unit_of_work_factory().create_uow() as uow:
            real = await uow.telegram_repo().get_all()
            assert len(real) == len(messages) and len(real) > 0
            success = [x for x in messages if x.status == "success_sent"]
            failed = [x for x in messages if x.status == "failed_sent"]

            assert len(success) == len(failed)
            for msg in success:
                assert msg.status == "success_sent"
                assert msg.retries == 1
                assert msg.next_retry_at is None

            for msg in failed:
                assert msg.status == "failed_sent"
                assert msg.retries == 3
                assert msg.next_retry_at is None


@pytest.mark.asyncio
async def test_logic_when_save_data_in_database_failed(messages):
    # Вообще если что-то случается с записью задачи в базу данных, то это беда
    # В этом тесте мы проверяем, что если беда случилась, то она случилась только с одной задачей
    with (patch("backend.webhook.application.telegraph.safe_request", mocked_request_without_error),
          patch("backend.webhook.application.telegraph.safe_commit", mocked_safe_commit),
          patch("backend.webhook.domain.telegram.Telegram._get_next_retry", mocked_get_next_retry),
          ):
        # Отправляем вебхуки, записываем результат, эмулируем ошибку записи результата под номером три
        telegraph = Telegraph(container.unit_of_work_factory(), sleep_time=0.1)
        task = asyncio.create_task(telegraph.run_worker())
        await asyncio.sleep(3)
        telegraph.stop_worker()
        await asyncio.gather(task)

        # Проверяем статусы сообщений (сообщение 3 в базу не сохранилось)
        async with container.unit_of_work_factory().create_uow() as uow:
            real = await uow.telegram_repo().get_all()
            assert len(real) == len(messages) and len(real) > 0
            for msg in real:
                if msg.data == "3":
                    assert msg.status == "unprocessed"
                    assert msg.retries == 0
                else:
                    assert msg.status == "success_sent"
                    assert msg.retries == 1
                    assert msg.next_retry_at is None
