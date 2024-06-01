"""Initial migration

Revision ID: 975320d095e9
Revises: 
Create Date: 2024-05-24 01:16:35.851222

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector


# revision identifiers, used by Alembic.
revision: str = "975320d095e9"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    existing_tables = inspector.get_table_names()

    if "chats" not in existing_tables:
        op.create_table(
            "chats",
            sa.Column("chat_id", sa.BigInteger(), nullable=False),
            sa.Column("date", sa.DateTime(timezone=True), nullable=False),
            sa.Column("delta", sa.Integer(), nullable=False),
            sa.PrimaryKeyConstraint("chat_id"),
            comment="Chat table where the bot is running",
        )

    if "history" not in existing_tables:
        op.create_table(
            "history",
            sa.Column(
                "id",
                sa.BigInteger(),
                sa.Identity(
                    always=True,
                    start=1,
                    increment=1,
                    minvalue=1,
                    maxvalue=9223372036854775807,
                    cycle=False,
                    cache=1,
                ),
                autoincrement=True,
                nullable=False,
            ),
            sa.Column("chat_id", sa.BigInteger(), nullable=False),
            sa.Column("hunter", sa.Text(), nullable=False),
            sa.Column("game", sa.Text(), nullable=False),
            sa.Column(
                "date",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.Column("platform", sa.Text(), nullable=True),
            sa.Column("user_id", sa.BigInteger(), nullable=True),
            sa.Column("avatar_date", sa.DateTime(timezone=True), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )

    if "platinum" not in existing_tables:
        op.create_table(
            "platinum",
            sa.Column(
                "id",
                sa.BigInteger(),
                sa.Identity(
                    always=True,
                    start=1,
                    increment=1,
                    minvalue=1,
                    maxvalue=9223372036854775807,
                    cycle=False,
                    cache=1,
                ),
                autoincrement=True,
                nullable=False,
                comment="Unique ID",
            ),
            sa.Column("chat_id", sa.BigInteger(), nullable=False),
            sa.Column("hunter", sa.Text(), nullable=False),
            sa.Column("game", sa.Text(), nullable=False),
            sa.Column("platform", sa.Text(), nullable=True),
            sa.Column("photo_id", sa.Text(), nullable=False),
            sa.Column("user_id", sa.BigInteger(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )

    if "scores" not in existing_tables:
        op.create_table(
            "scores",
            sa.Column(
                "id",
                sa.BigInteger(),
                sa.Identity(
                    always=True,
                    start=1,
                    increment=1,
                    minvalue=1,
                    maxvalue=9223372036854775807,
                    cycle=False,
                    cache=1,
                ),
                autoincrement=True,
                nullable=False,
            ),
            sa.Column("trophy_id", sa.BigInteger(), nullable=False),
            sa.Column("user_id", sa.BigInteger(), nullable=False),
            sa.Column("picture", sa.Integer(), nullable=True),
            sa.Column("game", sa.Integer(), nullable=True),
            sa.Column("difficulty", sa.Integer(), nullable=True),
            sa.ForeignKeyConstraint(
                ["trophy_id"],
                ["history.id"],
            ),
            sa.PrimaryKeyConstraint("id"),
        )

    if "surveys" not in existing_tables:
        op.create_table(
            "surveys",
            sa.Column("trophy_id", sa.BigInteger(), nullable=False),
            sa.Column("picture", sa.REAL(), nullable=True),
            sa.Column("game", sa.REAL(), nullable=True),
            sa.Column("difficulty", sa.REAL(), nullable=True),
            sa.ForeignKeyConstraint(
                ["trophy_id"],
                ["history.id"],
            ),
            sa.PrimaryKeyConstraint("trophy_id"),
        )


def downgrade() -> None:
    op.drop_table("surveys")
    op.drop_table("scores")
    op.drop_table("platinum")
    op.drop_table("history")
    op.drop_table("chats")
