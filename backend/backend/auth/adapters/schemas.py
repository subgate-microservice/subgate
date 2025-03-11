from backend.shared.base_models import MyBase


class ApikeyCreateSchema(MyBase):
    title: str


class PasswordUpdateSchema(MyBase):
    old_password: str
    new_password: str
