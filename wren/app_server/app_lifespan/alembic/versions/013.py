"""Add execution_status column to conversation_metadata

Revision ID: 013
Revises: 012
Create Date: 2026-06-15 11:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '013'
down_revision: Union[str, None] = '012'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('conversation_metadata') as batch_op:
        batch_op.add_column(
            sa.Column(
                'execution_status',
                sa.String(),
                nullable=True,
            )
        )
        # Create index for efficient dashboard queries - FIXED STRING TO LIST
        batch_op.create_index(
            'ix_conversation_metadata_execution_status',
            ['execution_status'],
            unique=False,
        )


def downgrade() -> None:
    with op.batch_alter_table('conversation_metadata') as batch_op:
        batch_op.drop_index('ix_conversation_metadata_execution_status')
        batch_op.drop_column('execution_status')
