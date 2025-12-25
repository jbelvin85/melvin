"""Add preferred_model field to users

Revision ID: 002_add_user_model_preference
Revises: 001_add_psychographic_profiles
Create Date: 2025-12-25 09:55:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "002_add_user_model_preference"
down_revision = "001_add_psychographic_profiles"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("preferred_model", sa.String(length=128), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "preferred_model")
