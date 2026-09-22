"""add nation/rank metadata to athletes

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-22

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("athletes", sa.Column("nation", sa.String(length=100), nullable=True))
    op.add_column("athletes", sa.Column("nation_code", sa.String(length=3), nullable=True))
    op.add_column("athletes", sa.Column("gender", sa.String(length=1), nullable=True))
    op.add_column("athletes", sa.Column("wrl_rank", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("athletes", "wrl_rank")
    op.drop_column("athletes", "gender")
    op.drop_column("athletes", "nation_code")
    op.drop_column("athletes", "nation")
