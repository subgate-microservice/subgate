from backend.auth.domain.apikey import Apikey
from backend.auth.domain.auth_user import AuthId


def check_apikey_owner(apikey: Apikey, owner_id: AuthId) -> None:
    if apikey.auth_user.id != owner_id:
        raise PermissionError
