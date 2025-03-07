from fastapi import APIRouter, Depends

from backend.auth.application.apikey_service import ApikeyCreate, ApikeyManager
from backend.auth.domain.apikey import ApikeySby
from backend.auth.domain.auth_user import AuthUser
from backend.bootstrap import get_container, auth_closure

apikey_router = APIRouter(
    prefix="/apikey",
    tags=["Apikey"]
)

container = get_container()


@apikey_router.post("/")
async def create_one(data: ApikeyCreate, auth_user: AuthUser = Depends(auth_closure)) -> tuple[dict, str]:
    async with container.unit_of_work_factory().create_uow() as uow:
        manager = ApikeyManager(uow)
        await manager.create(data)
        await uow.commit()
    return {"public_id": data.public_id, "title": data.title}, data.secret


@apikey_router.get("/")
async def get_selected(auth_user: AuthUser = Depends(auth_closure)) -> list[dict]:
    sby = ApikeySby(auth_ids={auth_user.id})
    async with container.unit_of_work_factory().create_uow() as uow:
        apikeys = await uow.apikey_repo().get_selected(sby)
        lights = [{"public_id": x.public_id, "title": x.title} for x in apikeys]
    return lights


@apikey_router.delete("/{public_id}")
async def delete_one_by_id(public_id: str, auth_user: AuthUser = Depends(auth_closure)) -> str:
    async with container.unit_of_work_factory().create_uow() as uow:
        target = await uow.apikey_repo().get_one_by_public_id(public_id)
        assert target.auth_user.id == auth_user.id
        await uow.apikey_repo().delete_one(target)
        await uow.commit()
    cache_manager = container.cache_manager()
    cache_manager.pop(public_id)
    return "Ok"
