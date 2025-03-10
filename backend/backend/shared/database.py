import asyncpg
from loguru import logger
from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import create_async_engine

metadata = MetaData()


class DatabaseManager:
    def __init__(
            self,
            host: str,
            port: int,
            db_name: str,
            username: str,
            password: str,
    ):
        self._db_name = db_name
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._async_engine = create_async_engine(
            f"postgresql+asyncpg://{username}:{password}@{host}:{port}/{db_name}",
            echo=False
        )

    async def _execute_db_command(self, command: str) -> None:
        conn = await asyncpg.connect(
            user=self._username, password=self._password,
            host=self._host, port=self._port, database="postgres"
        )
        try:
            await conn.execute(command)
        finally:
            await conn.close()

    async def drop_and_create_database(self) -> None:
        await self._execute_db_command(f"DROP DATABASE IF EXISTS {self._db_name}")
        await self._execute_db_command(f"CREATE DATABASE {self._db_name}")
        logger.info(f"Database {self._db_name} created")

    async def create_database_if_not_exist(self) -> None:
        conn = await asyncpg.connect(
            user=self._username, password=self._password,
            host=self._host, port=self._port, database="postgres"
        )
        try:
            result = await conn.fetchval(
                "SELECT 1 FROM pg_database WHERE datname=$1", self._db_name
            )
            if result is None:
                await conn.execute(f"CREATE DATABASE {self._db_name}")
                logger.info(f"Database {self._db_name} created")
            else:
                logger.info(f"Database {self._db_name} already exists")
        finally:
            await conn.close()

    async def drop_and_create_tables(self) -> None:
        async with self._async_engine.begin() as conn:
            await conn.run_sync(metadata.drop_all)
            await conn.run_sync(metadata.create_all)
            await conn.commit()
        logger.info("Postgres tables were recreated.")

    async def create_tables_if_not_exist(self) -> None:
        async with self._async_engine.begin() as conn:
            await conn.run_sync(metadata.create_all)
            await conn.commit()
        logger.info(f"Tables in {self._db_name} are ready")
