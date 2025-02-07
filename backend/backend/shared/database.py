from loguru import logger
from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import create_async_engine

from backend import config

metadata = MetaData()


async def drop_and_create_postgres_tables():
    async_engine = create_async_engine(config.POSTGRES_URL, echo=False)
    async with async_engine.begin() as conn:
        await conn.run_sync(metadata.drop_all)
        await conn.run_sync(metadata.create_all)
        await conn.commit()
    logger.info("Postgres tables were successfully created.")
