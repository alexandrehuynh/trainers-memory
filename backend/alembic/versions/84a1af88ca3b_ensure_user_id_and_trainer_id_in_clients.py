"""ensure user_id and trainer_id in clients

Revision ID: 84a1af88ca3b
Revises: 54f3692145b7
Create Date: 2025-03-18 09:39:46.965999

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '84a1af88ca3b'
down_revision = '54f3692145b7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Check if trainer_id exists in clients table
    conn = op.get_bind()
    result = conn.execute("SELECT EXISTS (SELECT FROM information_schema.columns WHERE table_name = 'clients' AND column_name = 'trainer_id')")
    trainer_id_exists = result.scalar()
    
    # Add trainer_id column if it doesn't exist
    if not trainer_id_exists:
        op.add_column('clients', sa.Column('trainer_id', postgresql.UUID(as_uuid=True), nullable=True))
        # Create index for trainer_id
        op.create_index('ix_clients_trainer_id', 'clients', ['trainer_id'], unique=False, schema='public')
        # Add foreign key
        op.create_foreign_key('fk_clients_trainer_id', 'clients', 'users', ['trainer_id'], ['id'], source_schema='public', referent_schema='public')
    
    # Rest of autogenerated migration
    op.add_column('api_keys', sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False))
    op.create_index('ix_api_keys_user_id', 'api_keys', ['user_id'], unique=False, schema='public')
    op.drop_constraint('api_keys_client_id_fkey', 'api_keys', type_='foreignkey')
    op.create_foreign_key(None, 'api_keys', 'clients', ['client_id'], ['id'], source_schema='public', referent_schema='public', ondelete='CASCADE')
    op.create_foreign_key(None, 'api_keys', 'users', ['user_id'], ['id'], source_schema='public', referent_schema='public', ondelete='CASCADE')
    op.alter_column('clients', 'user_id',
               existing_type=postgresql.UUID(),
               nullable=False)
    op.drop_constraint('clients_email_key', 'clients', type_='unique')
    op.create_index('ix_clients_user_id', 'clients', ['user_id'], unique=False, schema='public')
    op.create_unique_constraint('uq_client_email_per_user', 'clients', ['user_id', 'email'], schema='public')
    op.create_foreign_key(None, 'clients', 'users', ['user_id'], ['id'], source_schema='public', referent_schema='public', ondelete='CASCADE')
    op.drop_constraint('exercises_workout_id_fkey', 'exercises', type_='foreignkey')
    op.create_foreign_key(None, 'exercises', 'workouts', ['workout_id'], ['id'], source_schema='public', referent_schema='public', ondelete='CASCADE')
    op.drop_constraint('template_exercises_template_id_fkey', 'template_exercises', type_='foreignkey')
    op.create_foreign_key(None, 'template_exercises', 'workout_templates', ['template_id'], ['id'], source_schema='public', referent_schema='public', ondelete='CASCADE')
    op.drop_constraint('workout_templates_user_id_fkey', 'workout_templates', type_='foreignkey')
    op.create_foreign_key(None, 'workout_templates', 'users', ['user_id'], ['id'], source_schema='public', referent_schema='public', ondelete='CASCADE')
    op.add_column('workouts', sa.Column('type', sa.String(length=255), nullable=False))
    op.drop_constraint('workouts_client_id_fkey', 'workouts', type_='foreignkey')
    op.create_foreign_key(None, 'workouts', 'clients', ['client_id'], ['id'], source_schema='public', referent_schema='public', ondelete='CASCADE')
    op.drop_column('workouts', 'workout_type')


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('workouts', sa.Column('workout_type', sa.VARCHAR(length=255), autoincrement=False, nullable=False))
    op.drop_constraint(None, 'workouts', schema='public', type_='foreignkey')
    op.create_foreign_key('workouts_client_id_fkey', 'workouts', 'clients', ['client_id'], ['id'], ondelete='CASCADE')
    op.drop_column('workouts', 'type')
    op.drop_constraint(None, 'workout_templates', schema='public', type_='foreignkey')
    op.create_foreign_key('workout_templates_user_id_fkey', 'workout_templates', 'users', ['user_id'], ['id'], ondelete='CASCADE')
    op.drop_constraint(None, 'template_exercises', schema='public', type_='foreignkey')
    op.create_foreign_key('template_exercises_template_id_fkey', 'template_exercises', 'workout_templates', ['template_id'], ['id'], ondelete='CASCADE')
    op.drop_constraint(None, 'exercises', schema='public', type_='foreignkey')
    op.create_foreign_key('exercises_workout_id_fkey', 'exercises', 'workouts', ['workout_id'], ['id'], ondelete='CASCADE')
    op.drop_constraint(None, 'clients', schema='public', type_='foreignkey')
    op.drop_constraint('uq_client_email_per_user', 'clients', schema='public', type_='unique')
    op.drop_index('ix_clients_user_id', table_name='clients', schema='public')
    op.create_unique_constraint('clients_email_key', 'clients', ['email'])
    op.alter_column('clients', 'user_id',
               existing_type=postgresql.UUID(),
               nullable=True)
    op.drop_constraint(None, 'api_keys', schema='public', type_='foreignkey')
    op.drop_constraint(None, 'api_keys', schema='public', type_='foreignkey')
    op.create_foreign_key('api_keys_client_id_fkey', 'api_keys', 'clients', ['client_id'], ['id'], ondelete='CASCADE')
    op.drop_index('ix_api_keys_user_id', table_name='api_keys', schema='public')
    op.drop_column('api_keys', 'user_id')
    # Remove trainer_id indexes and foreign keys if added in upgrade
    try:
        op.drop_constraint('fk_clients_trainer_id', 'clients', schema='public', type_='foreignkey')
        op.drop_index('ix_clients_trainer_id', table_name='clients', schema='public')
    except:
        pass
    # ### end Alembic commands ### 