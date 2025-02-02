from sqlalchemy import Table, Column, UUID, String, Boolean

from backend.shared.unit_of_work.base_repo_sql import metadata

auth_user_table = Table(
    "user",
    metadata,
    id=Column(UUID, primary_key=True),
    email=Column(String, nullable=False),
    hashed_password=Column(String, nullable=False),
    is_active=Column(Boolean, nullable=False),
    is_superuser=Column(Boolean, nullable=False),
    is_verified=Column(Boolean, nullable=False),
)
