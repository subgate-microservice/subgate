from fastapi import FastAPI, APIRouter, Depends

from backend.auth.infra.fastapi_users.manager import auth_backend
from backend.auth.infra.fastapi_users.schemas import UserRead, UserCreate
from backend.bootstrap import get_container, auth_closure

container = get_container()
fastapi_users = container.fastapi_users()

current_user_router = APIRouter()


@current_user_router.get("/me")
async def get_current_user(auth_user=Depends(auth_closure)) -> UserRead:
    return auth_user


# @current_user_router.patch("/me/update-email")
# async def update_email():
#     pass
#
#
@current_user_router.patch("/me/update-password")
async def update_password(auth_user: UserRead = Depends(auth_closure)) -> str:
    manager = fastapi_users.get_user_manager()
    return "Ok"


#
#
# @current_user_router.patch("/me/delete-profile")
# async def delete_profile():
#     pass


def include_fastapi_users_routers(app: FastAPI, prefix="/api/v1"):
    app.include_router(
        fastapi_users.get_auth_router(auth_backend),
        prefix=f"{prefix}/auth/jwt",
        tags=["auth"],
    )
    app.include_router(
        fastapi_users.get_register_router(UserRead, UserCreate),
        prefix=f"{prefix}/auth",
        tags=["auth"],
    )
    app.include_router(
        fastapi_users.get_reset_password_router(),
        prefix=f"{prefix}/auth",
        tags=["auth"],
    )
    app.include_router(
        fastapi_users.get_verify_router(UserRead),
        prefix=f"{prefix}/auth",
        tags=["auth"],
    )
    app.include_router(
        current_user_router,
        prefix=f"{prefix}/users",
        tags=["users"],
    )
