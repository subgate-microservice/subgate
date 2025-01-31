from typing import Optional

import aiohttp


class FiefBaseRepo:
    def __init__(
            self,
            base_url: str,
            admin_api_key: str,
    ):
        self._base_url = f"{base_url}/admin/api"
        self._headers = {
            "Authorization": f"Bearer {admin_api_key}",
            "Content-Type": "application/json",
        }

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
