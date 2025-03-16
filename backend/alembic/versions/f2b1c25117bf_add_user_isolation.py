"""add_user_isolation

Revision ID: f2b1c25117bf
Revises: 062832f6fa7c
Create Date: 2025-03-15 18:48:16.356124

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid


# revision identifiers, used by Alembic.
revision = 'f2b1c25117bf'
down_revision = '062832f6fa7c'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Get a connection to check existing tables
    conn = op.get_bind()
    
    # Check if users table exists
    inspector = sa.inspect(conn)
    users_exists = 'users' in inspector.get_table_names()
    
    if not users_exists:
        # Create users table only if it doesn't exist
        op.create_table(
            'users',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
            sa.Column('email', sa.String(255), nullable=False, unique=True),
            sa.Column('hashed_password', sa.String(255), nullable=True),
            sa.Column('role', sa.String(50), nullable=False, server_default='trainer'),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            schema='public'
        )
        op.create_index('ix_users_email', 'users', ['email'], unique=False, schema='public')
    
    # Check if workout_templates table exists
    workout_templates_exists = 'workout_templates' in inspector.get_table_names()
    
    if not workout_templates_exists:
        # Create template tables
        op.create_table(
            'workout_templates',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
            sa.Column('name', sa.String(255), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('type', sa.String(255), nullable=False),
            sa.Column('duration', sa.Integer(), nullable=False),
            sa.Column('is_system', sa.Boolean(), nullable=False, server_default='false'),
            sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['user_id'], ['public.users.id'], ondelete='CASCADE'),
            schema='public'
        )
    
    # Check if template_exercises table exists
    template_exercises_exists = 'template_exercises' in inspector.get_table_names()
    
    if not template_exercises_exists:
        op.create_table(
            'template_exercises',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
            sa.Column('template_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('name', sa.String(255), nullable=False),
            sa.Column('sets', sa.Integer(), nullable=False),
            sa.Column('reps', sa.Integer(), nullable=False),
            sa.Column('weight', sa.Float(), nullable=True),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.ForeignKeyConstraint(['template_id'], ['public.workout_templates.id'], ondelete='CASCADE'),
            schema='public'
        )
    
    # Add a default admin user to bootstrap the system if users table was just created
    if not users_exists:
        op.execute(
            """
            INSERT INTO public.users (id, email, role, is_active, created_at) 
            VALUES ('00000000-0000-0000-0000-000000000001', 'admin@trainersmemory.com', 'admin', TRUE, now())
            """
        )
    
    # Check if clients table has a unique constraint on email
    try:
        op.drop_index('clients_email_key', table_name='clients', schema='public')
    except Exception:
        # If the constraint doesn't exist, continue
        pass
    
    # Check if user_id column already exists in clients table
    columns = [c['name'] for c in inspector.get_columns('clients')]
    if 'user_id' not in columns:
        # Add user_id column to clients
        op.add_column(
            'clients', 
            sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
            schema='public'
        )
        op.create_index('ix_clients_user_id', 'clients', ['user_id'], schema='public')
        
        # Set all existing clients to be owned by admin user
        op.execute(
            """
            UPDATE public.clients SET user_id = '00000000-0000-0000-0000-000000000001'
            """
        )
        
        # Now make user_id not nullable
        op.alter_column('clients', 'user_id', nullable=False, schema='public')
        
        # Add foreign key constraint
        op.create_foreign_key(
            'fk_clients_user_id', 'clients', 'users',
            ['user_id'], ['id'], source_schema='public', referent_schema='public',
            ondelete='CASCADE'
        )
        
        # Add unique constraint for email per user
        op.create_unique_constraint(
            'uq_client_email_per_user', 'clients',
            ['user_id', 'email'], schema='public'
        )
    
    # Check if user_id column already exists in api_keys table
    columns = [c['name'] for c in inspector.get_columns('api_keys')]
    if 'user_id' not in columns:
        # Add user_id to api_keys
        op.add_column(
            'api_keys',
            sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
            schema='public'
        )
        op.create_index('ix_api_keys_user_id', 'api_keys', ['user_id'], schema='public')
        
        # Set existing API keys to admin user
        op.execute(
            """
            UPDATE public.api_keys SET user_id = '00000000-0000-0000-0000-000000000001'
            """
        )
        
        # Make user_id not nullable
        op.alter_column('api_keys', 'user_id', nullable=False, schema='public')
        
        # Add foreign key constraint
        op.create_foreign_key(
            'fk_api_keys_user_id', 'api_keys', 'users',
            ['user_id'], ['id'], source_schema='public', referent_schema='public',
            ondelete='CASCADE'
        )


def downgrade() -> None:
    # Remove foreign key constraints
    op.drop_constraint('fk_api_keys_user_id', 'api_keys', schema='public', type_='foreignkey')
    op.drop_constraint('fk_clients_user_id', 'clients', schema='public', type_='foreignkey')
    
    # Drop user_id columns
    op.drop_column('api_keys', 'user_id', schema='public')
    
    # Recreate unique constraint on client email
    op.create_index('clients_email_key', 'clients', ['email'], unique=True, schema='public')
    
    # Drop unique constraint for email per user
    op.drop_constraint('uq_client_email_per_user', 'clients', schema='public')
    
    # Drop user_id column from clients
    op.drop_column('clients', 'user_id', schema='public')
    
    # Drop template tables
    op.drop_table('template_exercises', schema='public')
    op.drop_table('workout_templates', schema='public')
    
    # Drop users table
    op.drop_table('users', schema='public') 