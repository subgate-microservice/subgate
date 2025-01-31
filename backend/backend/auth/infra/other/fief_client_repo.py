from uuid import UUID

from backend.auth.infra.other.fief_base_repo import FiefBaseRepo
from backend.auth.infra.other.fief_schemas import FiefClientPartialUpdate, FiefClient


class FiefClientRepo(FiefBaseRepo):
    async def get_one_by_id(self, item_id: UUID) -> FiefClient:
        url = f"/clients/{item_id}"
        json_data = await self._request("GET", url)
        return FiefClient(**json_data)

    async def get_all(self) -> list[FiefClient]:
        url = f"/clients"
        json_data = await self._request("GET", url)
        return [FiefClient(**x) for x in json_data["results"]]

    async def partial_update_one(self, item: FiefClientPartialUpdate) -> None:
        url = f"/clients/{item.id}"
        data = item.model_dump(mode="json", exclude={"id"}, exclude_none=True)
        await self._request("PATCH", url, json=data)
