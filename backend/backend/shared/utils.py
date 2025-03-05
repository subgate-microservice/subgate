import datetime
import secrets
from typing import Optional, Union

from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher
from pwdlib.hashers.bcrypt import BcryptHasher


def get_current_datetime():
    return datetime.datetime.now(datetime.UTC)


class PasswordHelper:
    def __init__(self, password_hash: Optional[PasswordHash] = None) -> None:
        if password_hash is None:
            self.password_hash = PasswordHash(
                (
                    Argon2Hasher(),
                    BcryptHasher(),
                )
            )
        else:
            self.password_hash = password_hash  # pragma: no cover

    def verify_and_update(
            self, plain_password: str, hashed_password: str
    ) -> tuple[bool, Union[str, None]]:
        return self.password_hash.verify_and_update(plain_password, hashed_password)

    def verify(self, plain_password: str, hashed_password: str) -> bool:
        return self.password_hash.verify(plain_password, hashed_password)

    def hash(self, password: str) -> str:
        return self.password_hash.hash(password)

    @staticmethod
    def generate() -> str:
        return secrets.token_urlsafe()
