"""add similarity columns to submissions

Adds `similarity_score` (float) and `similarity_flagged` (bool) to the
submissions table so the plagiarism check worker can persist its findings.

Revision ID: a1b2c3d4e5f6
Revises: 98566dd7c071
Create Date: 2026-04-13 00:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "98566dd7c071"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # similarity_score: highest TF-IDF cosine similarity found (0.0 – 1.0)
    op.add_column(
        "submissions",
        sa.Column("similarity_score", sa.Float(), nullable=True),
    )
    # similarity_flagged: True when score >= 0.80 (the plagiarism threshold)
    op.add_column(
        "submissions",
        sa.Column(
            "similarity_flagged",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )


def downgrade() -> None:
    op.drop_column("submissions", "similarity_flagged")
    op.drop_column("submissions", "similarity_score")
