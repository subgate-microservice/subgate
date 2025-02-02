from fastapi_users_db_sqlalchemy import SQLAlchemyBaseUserTableUUID
from sqlalchemy.orm import registry

mapper_registry = registry()


@mapper_registry.mapped
class User(SQLAlchemyBaseUserTableUUID):
    pass
