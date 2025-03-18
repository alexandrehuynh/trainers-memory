"""rename workout_type to type in workouts table

Revision ID: d849247becff
Revises: 84a1af88ca3b
Create Date: 2025-03-18 10:17:46.279286

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'd849247becff'
down_revision = '84a1af88ca3b'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Check if the type column already exists
    conn = op.get_bind()
    result = conn.execute("SELECT EXISTS (SELECT FROM information_schema.columns WHERE table_name = 'workouts' AND column_name = 'type')")
    type_exists = result.scalar()
    
    # Check if workout_type column exists
    result = conn.execute("SELECT EXISTS (SELECT FROM information_schema.columns WHERE table_name = 'workouts' AND column_name = 'workout_type')")
    workout_type_exists = result.scalar()
    
    # Only proceed if type doesn't exist but workout_type does
    if not type_exists and workout_type_exists:
        # Get the column type information
        result = conn.execute("SELECT data_type FROM information_schema.columns WHERE table_name = 'workouts' AND column_name = 'workout_type'")
        data_type = result.scalar()
        
        # Rename the column from workout_type to type
        op.alter_column('workouts', 'workout_type', new_column_name='type', existing_type=sa.String(255), nullable=False)
        print("Successfully renamed 'workout_type' column to 'type' in workouts table")
    elif type_exists:
        print("The 'type' column already exists in workouts table")
    else:
        print("The 'workout_type' column doesn't exist in workouts table")


def downgrade() -> None:
    # Rename the column back to workout_type
    conn = op.get_bind()
    result = conn.execute("SELECT EXISTS (SELECT FROM information_schema.columns WHERE table_name = 'workouts' AND column_name = 'type')")
    type_exists = result.scalar()
    
    if type_exists:
        op.alter_column('workouts', 'type', new_column_name='workout_type', existing_type=sa.String(255), nullable=False)
        print("Successfully renamed 'type' column back to 'workout_type' in workouts table") 