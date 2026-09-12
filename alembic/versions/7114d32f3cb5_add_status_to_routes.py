"""add_status_to_routes

Revision ID: 7114d32f3cb5
Revises: 8555a33fc6cc
Create Date: 2026-09-12 17:11:21.883689

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7114d32f3cb5'
down_revision: Union[str, Sequence[str], None] = '8555a33fc6cc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    route_status = sa.Enum('active', 'inactive', name='route_status')
    route_status.create(op.get_bind(), checkfirst=True)
    op.add_column('routes', sa.Column('status', route_status, server_default='active', nullable=False))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('routes', 'status')
    sa.Enum('active', 'inactive', name='route_status').drop(op.get_bind(), checkfirst=True)
