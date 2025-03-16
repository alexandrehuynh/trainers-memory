"""create workout_templates table

Revision ID: a0b1c2d3e4f5
Revises: 
Create Date: 2025-03-16

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
import uuid

# revision identifiers
revision = 'a0b1c2d3e4f5'  # Unique identifier for this migration
down_revision = None  # Set this to the previous migration's revision ID if there is one
branch_labels = None
depends_on = None

def upgrade():
    # Create workout_templates table
    op.create_table(
        'workout_templates',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('type', sa.String(50), nullable=True),
        sa.Column('difficulty', sa.String(20), nullable=True),
        sa.Column('duration_minutes', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Check if template_exercises table exists, and create it if it doesn't
    # This ensures we have both tables for the relationship
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if 'template_exercises' not in inspector.get_table_names():
        op.create_table(
            'template_exercises',
            sa.Column('id', sa.String(), primary_key=True),
            sa.Column('template_id', sa.String(), nullable=False),
            sa.Column('exercise_name', sa.String(100), nullable=False),
            sa.Column('sets', sa.Integer(), nullable=True),
            sa.Column('reps', sa.Integer(), nullable=True),
            sa.Column('weight', sa.Float(), nullable=True),
            sa.Column('duration_seconds', sa.Integer(), nullable=True),
            sa.Column('order', sa.Integer(), nullable=True),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.ForeignKeyConstraint(['template_id'], ['workout_templates.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        
        # Create an index on template_id
        op.create_index('ix_template_exercises_template_id', 'template_exercises', ['template_id'])
    else:
        # If template_exercises exists but doesn't have the FK constraint, add it
        try:
            op.drop_constraint('fk_template_exercises_template_id', 'template_exercises', type_='foreignkey')
        except Exception:
            # Constraint might not exist or have a different name, continue anyway
            pass
            
        # Create the foreign key constraint
        op.create_foreign_key(
            'fk_template_exercises_template_id',
            'template_exercises', 'workout_templates',
            ['template_id'], ['id'],
            ondelete='CASCADE'
        )

def downgrade():
    # Remove the foreign key constraint first
    try:
        op.drop_constraint('fk_template_exercises_template_id', 'template_exercises', type_='foreignkey')
    except Exception:
        pass
    
    # Then drop the tables in reverse order
    op.drop_table('template_exercises')
    op.drop_table('workout_templates') 