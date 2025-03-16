"""add_rest_time_to_template_exercises

Revision ID: 6163696ad6f4
Revises: fix_schema_issues
Create Date: 2025-03-15 20:48:26.811018

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6163696ad6f4'
down_revision = 'fix_schema_issues'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add rest_time column to template_exercises table
    op.add_column('template_exercises', sa.Column('rest_time', sa.Integer(), nullable=True))


def downgrade() -> None:
    # Remove rest_time column from template_exercises table
    op.drop_column('template_exercises', 'rest_time') 