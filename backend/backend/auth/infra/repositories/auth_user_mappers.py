from fief_client import FiefAccessTokenInfo

from backend.auth.domain.auth_user import AuthUser, AuthRole


class AuthUserMapper:
    @staticmethod
    def access_token_to_auth_user(token_info: FiefAccessTokenInfo) -> AuthUser:
        auth_user_id = token_info["id"]
        roles = set(x for x in token_info["permissions"] if x in AuthRole)
        auth_user = AuthUser(
            id=auth_user_id,
            roles=roles,
        )
        return auth_user
