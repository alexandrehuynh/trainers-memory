"""add user_id to api_keys

Revision ID: 32a96dcc6138
Revises: d849247becff
Create Date: 2025-03-18 10:33:06.718087

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers, used by Alembic.
revision = '32a96dcc6138'
down_revision = 'd849247becff'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Check if the user_id column already exists
    conn = op.get_bind()
    result = conn.execute("SELECT EXISTS (SELECT FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'api_keys' AND column_name = 'user_id')")
    column_exists = result.scalar()
    
    if not column_exists:
        # Add the user_id column
        op.add_column('api_keys', sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True))
        
        # Add an index for user_id
        op.create_index('ix_api_keys_user_id', 'api_keys', ['user_id'], unique=False, schema='public')
        
        # Initialize user_id with client owners
        op.execute("""
            UPDATE api_keys 
            SET user_id = (
                SELECT user_id FROM clients 
                WHERE clients.id = api_keys.client_id
            )
            WHERE user_id IS NULL
        """)
        
        # For any remaining NULL user_ids, set to a default admin user
        op.execute("""
            UPDATE api_keys
            SET user_id = '00000000-0000-0000-0000-000000000001'
            WHERE user_id IS NULL
        """)
        
        # Add foreign key constraint
        op.create_foreign_key(
            'fk_api_keys_user_id', 'api_keys', 'users',
            ['user_id'], ['id'], source_schema='public', referent_schema='public',
            ondelete='CASCADE'
        )
        
        # Make the user_id column not nullable
        op.alter_column('api_keys', 'user_id', nullable=False, schema='public')
        
        print("Successfully added user_id column to api_keys table")
    else:
        print("user_id column already exists in api_keys table")


def downgrade() -> None:
    # Remove foreign key constraint
    conn = op.get_bind()
    result = conn.execute("SELECT EXISTS (SELECT FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'api_keys' AND column_name = 'user_id')")
    column_exists = result.scalar()
    
    if column_exists:
        op.drop_constraint('fk_api_keys_user_id', 'api_keys', type_='foreignkey', schema='public')
        op.drop_index('ix_api_keys_user_id', table_name='api_keys', schema='public')
        op.drop_column('api_keys', 'user_id', schema='public')
        print("Successfully removed user_id column from api_keys table")
    else:
        print("user_id column doesn't exist in api_keys table") 