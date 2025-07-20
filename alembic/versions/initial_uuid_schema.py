"""initial_uuid_schema

Revision ID: initial_uuid_schema
Revises: 
Create Date: 2025-07-20 16:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'initial_uuid_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create users table with UUID primary key
    op.create_table('users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(length=64), nullable=False),
        sa.Column('first_name', sa.String(length=50), nullable=True),
        sa.Column('last_name', sa.String(length=50), nullable=True),
        sa.Column('avatar_url', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('last_login_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    
    # Create oauth_accounts table with UUID primary key
    op.create_table('oauth_accounts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('provider', sa.Enum('GOOGLE', 'LINKEDIN', name='oauthproviderenum'), nullable=False),
        sa.Column('provider_sub', sa.String(), nullable=False),
        sa.Column('provider_email', sa.String(length=255), nullable=True),
        sa.Column('provider_name', sa.String(length=100), nullable=True),
        sa.Column('access_token_enc', sa.Text(), nullable=True),
        sa.Column('refresh_token_enc', sa.Text(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('scope', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('provider', 'provider_sub', name='unique_provider_user')
    )


def downgrade() -> None:
    op.drop_table('oauth_accounts')
    op.drop_table('users')
    op.execute('DROP TYPE oauthproviderenum') 