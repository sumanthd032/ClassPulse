"""merge feature heads

Revision ID: c9d2e7f4a1b0
Revises: a1b2c3d4e5f6, f1a2b3c4d5e6
Create Date: 2026-04-15 12:35:00.000000
"""
from typing import Sequence, Union


# revision identifiers, used by Alembic.
revision: str = "c9d2e7f4a1b0"
down_revision: Union[str, Sequence[str], None] = ("a1b2c3d4e5f6", "f1a2b3c4d5e6")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
