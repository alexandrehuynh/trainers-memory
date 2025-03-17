"""Add user_id columns for multi-tenant support

Revision ID: 87a42b50e912
Revises: fix_api_keys_user_id
Create Date: 2025-03-17 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = '87a42b50e912'
down_revision = 'fix_api_keys_user_id'
branch_labels = None
depends_on = None


def upgrade():
    # Create a temporary default user_id for existing data
    # This will need to be updated with real user IDs later
    default_user_id = "00000000-0000-0000-0000-000000000000"
    
    # Add user_id to workouts table if it doesn't exist
    op.execute('SELECT column_name FROM information_schema.columns WHERE table_name=\'workouts\' AND column_name=\'user_id\'')
    result = op.get_bind().fetchone()
    if not result:
        op.add_column('workouts', sa.Column('user_id', sa.String(), nullable=True))
        op.create_index(op.f('ix_workouts_user_id'), 'workouts', ['user_id'], unique=False)
        
        # Set default user_id based on client's user_id
        op.execute(f"""
            UPDATE workouts w
            SET user_id = c.user_id
            FROM clients c
            WHERE w.client_id = c.id
        """)
        
        # Set any remaining nulls to default
        op.execute(f"""
            UPDATE workouts
            SET user_id = '{default_user_id}'
            WHERE user_id IS NULL
        """)
        
        # Make the column non-nullable
        op.alter_column('workouts', 'user_id', nullable=False)
    
    # Add user_id to exercises table if it doesn't exist
    op.execute('SELECT column_name FROM information_schema.columns WHERE table_name=\'exercises\' AND column_name=\'user_id\'')
    result = op.get_bind().fetchone()
    if not result:
        op.add_column('exercises', sa.Column('user_id', sa.String(), nullable=True))
        op.create_index(op.f('ix_exercises_user_id'), 'exercises', ['user_id'], unique=False)
        
        # Set user_id based on workout's user_id
        op.execute(f"""
            UPDATE exercises e
            SET user_id = w.user_id
            FROM workouts w
            WHERE e.workout_id = w.id
        """)
        
        # Set any remaining nulls to default
        op.execute(f"""
            UPDATE exercises
            SET user_id = '{default_user_id}'
            WHERE user_id IS NULL
        """)
        
        # Make the column non-nullable
        op.alter_column('exercises', 'user_id', nullable=False)
    
    # Add user_id to workout_templates table if it doesn't exist
    op.execute('SELECT column_name FROM information_schema.columns WHERE table_name=\'workout_templates\' AND column_name=\'user_id\'')
    result = op.get_bind().fetchone()
    if not result:
        op.add_column('workout_templates', sa.Column('user_id', sa.String(), nullable=True))
        op.create_index(op.f('ix_workout_templates_user_id'), 'workout_templates', ['user_id'], unique=False)
        
        # Set default user_id
        op.execute(f"""
            UPDATE workout_templates
            SET user_id = '{default_user_id}'
            WHERE user_id IS NULL
        """)
        
        # Make the column non-nullable
        op.alter_column('workout_templates', 'user_id', nullable=False)
    
    # Add user_id to template_exercises table if it doesn't exist
    op.execute('SELECT column_name FROM information_schema.columns WHERE table_name=\'template_exercises\' AND column_name=\'user_id\'')
    result = op.get_bind().fetchone()
    if not result:
        op.add_column('template_exercises', sa.Column('user_id', sa.String(), nullable=True))
        op.create_index(op.f('ix_template_exercises_user_id'), 'template_exercises', ['user_id'], unique=False)
        
        # Set user_id based on template's user_id
        op.execute(f"""
            UPDATE template_exercises te
            SET user_id = wt.user_id
            FROM workout_templates wt
            WHERE te.template_id = wt.id
        """)
        
        # Set any remaining nulls to default
        op.execute(f"""
            UPDATE template_exercises
            SET user_id = '{default_user_id}'
            WHERE user_id IS NULL
        """)
        
        # Make the column non-nullable
        op.alter_column('template_exercises', 'user_id', nullable=False)


def downgrade():
    # Remove indices and user_id columns from all tables
    op.drop_index(op.f('ix_template_exercises_user_id'), table_name='template_exercises')
    op.drop_column('template_exercises', 'user_id')
    
    op.drop_index(op.f('ix_workout_templates_user_id'), table_name='workout_templates')
    op.drop_column('workout_templates', 'user_id')
    
    op.drop_index(op.f('ix_exercises_user_id'), table_name='exercises')
    op.drop_column('exercises', 'user_id')
    
    op.drop_index(op.f('ix_workouts_user_id'), table_name='workouts')
    op.drop_column('workouts', 'user_id') 