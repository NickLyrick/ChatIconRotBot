"""Add chats.timezone: the IANA zone admins enter and read dates in.

Existing chats keep Moscow time, which every date was entered in until now.

Revision ID: 5e2b8c41d7a9
Revises: c3f1a9d27e54
Create Date: 2026-11-07 12:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5e2b8c41d7a9'
down_revision: Union[str, None] = 'c3f1a9d27e54'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'chats',
        sa.Column(
            'timezone',
            sa.Text(),
            server_default=sa.text("'Europe/Moscow'"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column('chats', 'timezone')
