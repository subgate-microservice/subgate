from fief_client import FiefAccessTokenInfo

from backend.auth.domain.auth_user import AuthUser, AuthRole


class AuthUserMapper:
    @staticmethod
    def access_token_to_auth_user(token_info: FiefAccessTokenInfo) -> AuthUser:
        auth_user_id = token_info["id"]
        auth_user = AuthUser(
            id=auth_user_id,
        )
        return auth_user
