"""Add chats.survey_period: the month whose survey results were last published.

Revision ID: c3f1a9d27e54
Revises: bbd72dbf4178
Create Date: 2026-11-03 15:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3f1a9d27e54'
down_revision: Union[str, None] = 'bbd72dbf4178'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('chats', sa.Column('survey_period', sa.Date(), nullable=True))
    # Until now the in-process scheduler published each survey on the 1st at
    # 12:00 UTC. Mark the latest month that has passed that point as done, so
    # the first tick does not publish the same results a second time.
    op.execute(
        "UPDATE chats SET survey_period = "
        "date_trunc('month', now() AT TIME ZONE 'UTC' - interval '12 hours')::date"
    )


def downgrade() -> None:
    op.drop_column('chats', 'survey_period')
