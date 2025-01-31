import asyncio
import datetime
import functools
from typing import Iterable

from loguru import logger


def get_current_datetime():
    return datetime.datetime.now(datetime.UTC).replace(microsecond=0)


def run_sync(coro):
    try:
        _loop = asyncio.get_running_loop()
    except RuntimeError:
        # Если цикла нет, создаем его и запускаем
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(coro)
    else:
        # Если цикл запущен, создаем задачу в существующем цикле
        return asyncio.ensure_future(coro)


def repeat(
        exceptions: tuple[type[Exception]] | type[Exception] = Exception,
        delays: Iterable[float] = None
):
    if delays is None:
        delays = (0, 0.1, 0.25, 0.5, 1, 2, 3)

    def decorator(fn):
        @functools.wraps(fn)
        async def wrapper(*args, **kwargs):
            last_err = None
            for i, delay in enumerate(delays):
                try:
                    if last_err:
                        await asyncio.sleep(delay)
                    return await fn(*args, **kwargs)
                except Exception as err:
                    if isinstance(err, exceptions):
                        msg = f"function: {fn.__name__} | repeat_count: {i} | error: {err}"
                        logger.warning(msg)
                        last_err = err
                    else:
                        raise err
            raise last_err

        return wrapper

    return decorator
