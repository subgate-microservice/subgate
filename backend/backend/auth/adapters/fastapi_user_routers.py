from fastapi import FastAPI

from backend.auth.infra.fastapi_users.manager import auth_backend
from backend.auth.infra.fastapi_users.schemas import UserRead, UserCreate, UserUpdate
from backend.bootstrap import get_container

container = get_container()
fastapi_users = container.fastapi_users()


def include_fastapi_users_routers(app: FastAPI):
    app.include_router(
        fastapi_users.get_auth_router(auth_backend),
        prefix="/api/v1/auth/jwt",
        tags=["auth"],
    )
    app.include_router(
        fastapi_users.get_register_router(UserRead, UserCreate),
        prefix="/api/v1/auth",
        tags=["auth"],
    )
    app.include_router(
        fastapi_users.get_reset_password_router(),
        prefix="/api/v1/auth",
        tags=["auth"],
    )
    app.include_router(
        fastapi_users.get_verify_router(UserRead),
        prefix="/api/v1/auth",
        tags=["auth"],
    )
    app.include_router(
        fastapi_users.get_users_router(UserRead, UserUpdate),
        prefix="/api/v1/users",
        tags=["users"],
    )
