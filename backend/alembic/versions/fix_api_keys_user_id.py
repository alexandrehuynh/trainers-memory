"""Fix api_keys user_id column

Revision ID: fix_api_keys_user_id
Revises: f2b1c25117bf
Create Date: 2025-03-16 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
import uuid

# revision identifiers, used by Alembic.
revision = 'fix_api_keys_user_id'
down_revision = 'f2b1c25117bf'
branch_labels = None
depends_on = None


def upgrade():
    # Get a connection to check existing tables and columns
    conn = op.get_bind()
    
    # Check if the api_keys table exists
    result = conn.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'api_keys')")
    table_exists = result.scalar()
    
    if not table_exists:
        print("api_keys table doesn't exist, skipping migration")
        return
    
    # Check if the user_id column exists
    result = conn.execute("SELECT EXISTS (SELECT FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'api_keys' AND column_name = 'user_id')")
    user_id_exists = result.scalar()
    
    if not user_id_exists:
        print("Adding user_id column to api_keys table")
        
        # Add the user_id column
        op.add_column(
            'api_keys',
            sa.Column('user_id', UUID(as_uuid=True), nullable=True),
            schema='public'
        )
        
        # Create index for user_id
        op.create_index('ix_api_keys_user_id', 'api_keys', ['user_id'], schema='public')
        
        # Update existing keys with the admin user ID
        # We use a default admin user with a fixed UUID for existing records
        op.execute("""
            UPDATE public.api_keys SET user_id = '00000000-0000-0000-0000-000000000001'
            WHERE user_id IS NULL
        """)
        
        # Alternatively, try to use client's user_id if available:
        op.execute("""
            UPDATE public.api_keys 
            SET user_id = (
                SELECT user_id FROM public.clients 
                WHERE clients.id = api_keys.client_id
            )
            WHERE user_id IS NULL AND EXISTS (
                SELECT 1 FROM public.clients 
                WHERE clients.id = api_keys.client_id 
                AND clients.user_id IS NOT NULL
            )
        """)
        
        # Make user_id not nullable
        op.alter_column('api_keys', 'user_id', nullable=False, schema='public')
        
        # Add foreign key constraint
        op.create_foreign_key(
            'fk_api_keys_user_id', 'api_keys', 'users',
            ['user_id'], ['id'], source_schema='public', referent_schema='public',
            ondelete='CASCADE'
        )
        
        print("Successfully added user_id column to api_keys table")
    else:
        print("user_id column already exists in api_keys table")


def downgrade():
    # This is a critical column, so we don't provide a downgrade path
    pass 