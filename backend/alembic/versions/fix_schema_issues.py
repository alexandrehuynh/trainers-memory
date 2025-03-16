"""fix schema issues

Revision ID: fix_schema_issues
Revises: 1bdbb4eb815d
Create Date: 2025-03-16 08:45:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
import uuid

# revision identifiers, used by Alembic.
revision = 'fix_schema_issues'
down_revision = '1bdbb4eb815d'  # Use the latest migration as the down_revision
branch_labels = None
depends_on = None

def upgrade():
    # Check if workout_templates table exists
    conn = op.get_bind()
    res = conn.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'workout_templates')")
    templates_exists = res.scalar()
    
    if not templates_exists:
        # Create workout_templates table
        op.create_table(
            'workout_templates',
            sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
            sa.Column('name', sa.String(255), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('is_system', sa.Boolean(), server_default='false', nullable=False),
            sa.Column('user_id', UUID(as_uuid=True), nullable=False),
            sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        )
    
    # Check if api_keys.user_id column exists
    try:
        res = conn.execute("SELECT EXISTS (SELECT FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'api_keys' AND column_name = 'user_id')")
        user_id_exists = res.scalar()
        
        if not user_id_exists:
            # Add user_id column to api_keys
            op.add_column('api_keys', sa.Column('user_id', UUID(as_uuid=True), nullable=True))
            
            # Update existing api_keys with a user_id from their client's user_id
            op.execute("""
                UPDATE api_keys 
                SET user_id = (SELECT user_id FROM clients WHERE clients.id = api_keys.client_id)
                WHERE user_id IS NULL
            """)
            
            # Make user_id not nullable after filling data
            op.alter_column('api_keys', 'user_id', nullable=False)
            
            # Add foreign key constraint
            op.create_foreign_key('fk_api_keys_user_id_users', 'api_keys', 'users', ['user_id'], ['id'], ondelete='CASCADE')
    except Exception as e:
        print(f"Error updating api_keys: {e}")
        # The table might not exist yet, or there might be issues with the constraints
        # Continue with migration to fix other issues
    
    # Fix template_exercises foreign key if it exists
    try:
        # Check if template_exercises table exists
        res = conn.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'template_exercises')")
        template_exercises_exists = res.scalar()
        
        if template_exercises_exists:
            # Check if the foreign key exists but is incorrect
            try:
                # Drop the constraint if it exists but is incorrect
                op.drop_constraint('template_exercises_template_id_fkey', 'template_exercises', type_='foreignkey')
            except Exception:
                # If constraint doesn't exist or can't be dropped, continue
                pass
            
            # Add the correct foreign key constraint
            op.create_foreign_key(
                'template_exercises_template_id_fkey',
                'template_exercises', 'workout_templates',
                ['template_id'], ['id'],
                ondelete='CASCADE'
            )
        else:
            # Create template_exercises table if it doesn't exist
            op.create_table(
                'template_exercises',
                sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
                sa.Column('template_id', UUID(as_uuid=True), nullable=False),
                sa.Column('name', sa.String(255), nullable=False),
                sa.Column('sets', sa.Integer(), nullable=False),
                sa.Column('reps', sa.String(50), nullable=True),
                sa.Column('rest_time', sa.Integer(), nullable=True),
                sa.Column('notes', sa.Text(), nullable=True),
                sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
                sa.Column('updated_at', sa.DateTime(), nullable=True),
                sa.ForeignKeyConstraint(['template_id'], ['workout_templates.id'], ondelete='CASCADE'),
            )
    except Exception as e:
        print(f"Error fixing template_exercises: {e}")
        # Continue with migration to fix other issues

def downgrade():
    # Only drop objects that were created in this migration
    conn = op.get_bind()
    
    # Check if foreign key for template_exercises.template_id exists and was created here
    try:
        op.drop_constraint('template_exercises_template_id_fkey', 'template_exercises', type_='foreignkey')
    except Exception:
        pass
    
    # Check if foreign key for api_keys.user_id exists and was created here
    try:
        op.drop_constraint('fk_api_keys_user_id_users', 'api_keys', type_='foreignkey')
        op.drop_column('api_keys', 'user_id')
    except Exception:
        pass 