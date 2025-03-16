"""merge workout_templates migration

Revision ID: 1bdbb4eb815d
Revises: a0b1c2d3e4f5, f2b1c25117bf
Create Date: 2025-03-15 20:18:51.128052

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1bdbb4eb815d'
down_revision = ('a0b1c2d3e4f5', 'f2b1c25117bf')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass 