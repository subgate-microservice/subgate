from typing import Optional

import aiohttp

from backend.auth.domain.auth_user import AuthUser, AuthId, AuthRole
from backend.auth.application.auth_usecases import AuthUserCreate
from backend.auth.domain.auth_user_repo import AuthUserRepo


class AuthUserFiefRepo(AuthUserRepo):
    def __init__(
            self,
            base_url: str,
            admin_api_key: str,
            tenant_id: str,
            client_id: str,
    ):
        self._base_url = f"{base_url}/admin/api"
        self._tenant_id = tenant_id
        self._headers = {
            "Authorization": f"Bearer {admin_api_key}",
            "Content-Type": "application/json",
        }
        self._client_id = client_id

    async def _request(self, method: str, endpoint: str, **kwargs) -> Optional[dict]:
        url = f"{self._base_url}{endpoint}"
        headers = self._headers | kwargs.pop("headers", {})
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.request(method, url, **kwargs) as response:
                response.raise_for_status()
                if response.status == 204:
                    return None
                if not response.content or response.content == b'':  # Empty body
                    return None
                try:
                    return await response.json()
                except aiohttp.ContentTypeError:
                    return None

    async def _get_auth_user_roles(self, auth_id: AuthId) -> set[AuthRole]:
        _user_permission_data = await self._request("GET", f"/users/{auth_id}/permissions")
        raise NotImplemented

    async def add_one(self, data: AuthUserCreate) -> AuthId:
        json_data = {
            "email": data.email,
            "email_verified": data.email_verified,
            "is_active": True,
            "tenant_id": self._tenant_id,
            "password": data.password,
            "fields": {},
        }
        response_data = await self._request("POST", f"/users", json=json_data)
        return response_data["id"]

    async def get_one_by_id(self, item_id: AuthId) -> AuthUser:
        user_data = await self._request("GET", f"/users/{item_id}")
        permissions, roles = await self._get_auth_user_roles(item_id)
        auth_user = AuthUser(id=user_data["id"], permissions=permissions, roles=roles)
        return auth_user

    async def update_one(self, item: AuthUser) -> None:
        raise NotImplemented

    async def delete_one(self, item: AuthUser) -> None:
        await self._request("DELETE", f"/users/{item.id}")
