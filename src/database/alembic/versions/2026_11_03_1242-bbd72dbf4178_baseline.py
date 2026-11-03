"""Baseline: the schema of the production database as of 2026-11-03.

Revision ID: bbd72dbf4178
Revises: 
Create Date: 2026-11-03 12:42:58.220992

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bbd72dbf4178'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('chats',
    sa.Column('chat_id', sa.BigInteger(), autoincrement=False, nullable=False),
    sa.Column('date', sa.DateTime(timezone=True), nullable=False),
    sa.Column('delta', sa.Integer(), nullable=False),
    sa.PrimaryKeyConstraint('chat_id'),
    comment='Chat table where the bot is running'
    )
    op.create_table('history',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=True), autoincrement=True, nullable=False),
    sa.Column('chat_id', sa.BigInteger(), nullable=False),
    sa.Column('hunter', sa.Text(), nullable=False),
    sa.Column('game', sa.Text(), nullable=False),
    sa.Column('date', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('platform', sa.Text(), server_default=sa.text("'Playstation'"), nullable=True),
    sa.Column('user_id', sa.BigInteger(), nullable=True),
    sa.Column('avatar_date', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('platinum',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=True), autoincrement=True, nullable=False, comment='Unique ID'),
    sa.Column('chat_id', sa.BigInteger(), nullable=False),
    sa.Column('hunter', sa.Text(), nullable=False),
    sa.Column('game', sa.Text(), nullable=False),
    sa.Column('platform', sa.Text(), server_default=sa.text("'Playstation'"), nullable=True),
    sa.Column('photo_id', sa.Text(), nullable=False),
    sa.Column('user_id', sa.BigInteger(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('scores',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=True), autoincrement=True, nullable=False),
    sa.Column('trophy_id', sa.BigInteger(), nullable=False),
    sa.Column('user_id', sa.BigInteger(), nullable=False),
    sa.Column('picture', sa.Integer(), nullable=True),
    sa.Column('game', sa.Integer(), nullable=True),
    sa.Column('difficulty', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['trophy_id'], ['history.id'], name='history'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('surveys',
    sa.Column('trophy_id', sa.BigInteger(), autoincrement=False, nullable=False),
    sa.Column('picture', sa.REAL(), nullable=True),
    sa.Column('game', sa.REAL(), nullable=True),
    sa.Column('difficulty', sa.REAL(), nullable=True),
    sa.ForeignKeyConstraint(['trophy_id'], ['history.id'], name='trophy'),
    sa.PrimaryKeyConstraint('trophy_id')
    )


def downgrade() -> None:
    op.drop_table('surveys')
    op.drop_table('scores')
    op.drop_table('platinum')
    op.drop_table('history')
    op.drop_table('chats')
