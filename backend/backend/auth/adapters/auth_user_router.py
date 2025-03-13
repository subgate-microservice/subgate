from fastapi import FastAPI, APIRouter, Depends

from backend.auth.adapters.schemas import PasswordUpdateSchema, EmailUpdateSchema, ProfileDeleteSchema
from backend.auth.application.auth_usecases import AuthUserPasswordUpdate, AuthUserEmailUpdate, AuthUserDelete
from backend.auth.domain.auth_user import AuthUser
from backend.auth.infra.fastapi_users.manager import auth_backend
from backend.auth.infra.fastapi_users.schemas import UserRead, UserCreate
from backend.bootstrap import get_container, auth_closure

container = get_container()

current_user_router = APIRouter()


@current_user_router.get("/me")
async def get_current_user(auth_user=Depends(auth_closure)) -> AuthUser:
    return AuthUser(id=auth_user.id)


@current_user_router.patch("/me/update-email")
async def update_email(data: EmailUpdateSchema, auth_user=Depends(auth_closure)):
    data = AuthUserEmailUpdate(id=auth_user.id, new_email=data.new_email, password=data.password)
    await container.auth_usecase().update_email(data)
    return "Ok"


@current_user_router.patch("/me/update-password")
async def update_password(data: PasswordUpdateSchema, auth_user: UserRead = Depends(auth_closure)) -> str:
    data = AuthUserPasswordUpdate(old_password=data.old_password, new_password=data.new_password, id=auth_user.id)
    await container.auth_usecase().update_password(data)
    return "Ok"


@current_user_router.delete("/me")
async def delete_profile(data: ProfileDeleteSchema, auth_user: UserRead = Depends(auth_closure)):
    data = AuthUserDelete(id=auth_user.id, password=data.password)
    await container.auth_usecase().delete_auth_user(data)
    return "Ok"


def include_fastapi_users_routers(app: FastAPI, prefix="/api/v1"):
    app.include_router(
        container.fastapi_users().get_auth_router(auth_backend),
        prefix=f"{prefix}/auth/jwt",
        tags=["auth"],
    )
    app.include_router(
        container.fastapi_users().get_register_router(UserRead, UserCreate),
        prefix=f"{prefix}/auth",
        tags=["auth"],
    )
    # app.include_router(
    #     container.fastapi_users().get_reset_password_router(),
    #     prefix=f"{prefix}/auth",
    #     tags=["auth"],
    # )
    app.include_router(
        container.fastapi_users().get_verify_router(UserRead),
        prefix=f"{prefix}/auth",
        tags=["auth"],
    )
    app.include_router(
        current_user_router,
        prefix=f"{prefix}/users",
        tags=["users"],
    )
