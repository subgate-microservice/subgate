import asyncio
import datetime

import pytest
from loguru import logger

from tests.conftest import apikey_client, client


class TestApikeyAuthenticationPerformance:
    @pytest.mark.asyncio
    async def test_get_myself_without_concurrency(self, apikey_client):
        start = datetime.datetime.now()
        for i in range(1_000):
            response = await apikey_client.get(f"/users/me")
            response.raise_for_status()
        end = datetime.datetime.now()
        logger.debug(f"Total time is {(end - start)}")

    @pytest.mark.asyncio
    async def test_get_myself_without_with_concurrency(self, apikey_client):
        start = datetime.datetime.now()

        tasks = []
        for i in range(1_000):
            coro = apikey_client.get(f"/users/me")
            task = asyncio.create_task(coro)
            tasks.append(task)
        await asyncio.gather(*tasks)

        end = datetime.datetime.now()
        logger.debug(f"Total time is {(end - start)}")


class TestTokenAuthenticationPerformance:
    @pytest.mark.asyncio
    async def test_get_myself_without_concurrency(self, client):
        start = datetime.datetime.now()
        for i in range(1_000):
            response = await client.get(f"/users/me")
            response.raise_for_status()
        end = datetime.datetime.now()
        logger.debug(f"Total time is {(end - start)}")
