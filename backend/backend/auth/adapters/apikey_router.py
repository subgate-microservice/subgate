from fastapi import APIRouter, Depends, Header, HTTPException

from backend.auth.application.apikey_service import ApikeyService
from backend.auth.domain.apikey import ApikeyId, Apikey, ApikeySby
from backend.auth.domain.auth_user import AuthUser
from backend.bootstrap import get_container, auth_closure
from backend.shared.base_models import MyBase


class ApikeyCreate(MyBase):
    title: str


apikey_router = APIRouter(
    prefix="/apikey",
    tags=["Apikey"]
)

container = get_container()


@apikey_router.post("/")
async def create_one(data: ApikeyCreate, auth_user: AuthUser = Depends(auth_closure)) -> tuple[dict, str]:
    async with container.unit_of_work_factory().create_uow() as uow:
        apikey = Apikey(title=data.title, auth_user=auth_user)
        apikey_service = ApikeyService(uow)
        await apikey_service.create_one(apikey)
        await uow.commit()
    return apikey.to_light_bson(), apikey.value


@apikey_router.get("/")
async def get_selected(auth_user: AuthUser = Depends(auth_closure)) -> list[dict]:
    sby = ApikeySby(auth_ids={auth_user.id})
    async with container.unit_of_work_factory().create_uow() as uow:
        apikeys = await uow.apikey_repo().get_selected(sby)
        lights = [x.to_light_bson() for x in apikeys]
    return lights


@apikey_router.delete("/{apikey_id}")
async def delete_one_by_id(apikey_id: ApikeyId, auth_user: AuthUser = Depends(auth_closure)) -> str:
    async with container.unit_of_work_factory().create_uow() as uow:
        service = ApikeyService(uow)
        target = await service.get_one_by_id(apikey_id)
        assert target.id == auth_user.id
        await service.delete_one(target)
        await uow.commit()
    return "Ok"


@apikey_router.get("/get-auth-user")
async def get_auth_user_by_apikey_value(apikey_value: str = Header(None, alias="Apikey")) -> AuthUser:
    async with container.unit_of_work_factory().create_uow() as uow:
        apikey = await uow.apikey_repo().get_apikey_by_value(apikey_value)
        if not apikey:
            raise HTTPException(status_code=404, detail="API key not found")
    return apikey.auth_user
