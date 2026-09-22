"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-09-22

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("pin", sa.String(length=10), nullable=True),
        sa.UniqueConstraint("name"),
    )

    op.create_table(
        "weight_classes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("kampfbeginn", sa.DateTime(), nullable=False),
        sa.Column("tag", sa.Date(), nullable=False),
    )

    op.create_table(
        "athletes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column(
            "weight_class_id", sa.Integer(), sa.ForeignKey("weight_classes.id"), nullable=True
        ),
    )

    op.create_table(
        "tips",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column(
            "weight_class_id", sa.Integer(), sa.ForeignKey("weight_classes.id"), nullable=True
        ),
        sa.Column("platz_1", sa.Integer(), sa.ForeignKey("athletes.id"), nullable=True),
        sa.Column("platz_2", sa.Integer(), sa.ForeignKey("athletes.id"), nullable=True),
        sa.Column("platz_3a", sa.Integer(), sa.ForeignKey("athletes.id"), nullable=True),
        sa.Column("platz_3b", sa.Integer(), sa.ForeignKey("athletes.id"), nullable=True),
        sa.UniqueConstraint("user_id", "weight_class_id"),
    )

    op.create_table(
        "results",
        sa.Column(
            "weight_class_id",
            sa.Integer(),
            sa.ForeignKey("weight_classes.id"),
            primary_key=True,
        ),
        sa.Column("platz_1", sa.Integer(), sa.ForeignKey("athletes.id"), nullable=True),
        sa.Column("platz_2", sa.Integer(), sa.ForeignKey("athletes.id"), nullable=True),
        sa.Column("platz_3a", sa.Integer(), sa.ForeignKey("athletes.id"), nullable=True),
        sa.Column("platz_3b", sa.Integer(), sa.ForeignKey("athletes.id"), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("results")
    op.drop_table("tips")
    op.drop_table("athletes")
    op.drop_table("weight_classes")
    op.drop_table("users")
