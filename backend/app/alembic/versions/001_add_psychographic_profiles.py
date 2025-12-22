"""Add psychographic profile tables and user relationship

Revision ID: 001_add_psychographic_profiles
Revises: 
Create Date: 2024-12-22 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001_add_psychographic_profiles'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add profile relationship to users table
    op.add_column('users', sa.Column('profile_id', sa.Integer(), nullable=True))
    
    # Create player_profiles table
    op.create_table(
        'player_profiles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('primary_type', sa.Enum('timmy_tammy', 'johnny_jenny', 'spike_sheila', 'vorthos', 'melvin', name='psychographictype'), nullable=False),
        sa.Column('primary_score', sa.Float(), nullable=False),
        sa.Column('secondary_type', sa.Enum('timmy_tammy', 'johnny_jenny', 'spike_sheila', 'vorthos', 'melvin', name='psychographictype'), nullable=True),
        sa.Column('secondary_score', sa.Float(), nullable=True),
        sa.Column('subtype', sa.Enum('power_gamer', 'social_gamer', 'adrenaline_gamer', 'combo_builder', 'offbeat_builder', 'architect', 'competitive', 'technical', 'meta_analyst', 'lore_enthusiast', 'mechanics_enthusiast', name='psychographicsubtype'), nullable=True),
        sa.Column('subtype_score', sa.Float(), nullable=True),
        sa.Column('total_questions_answered', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('assessment_version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('prefers_big_plays', sa.Float(), nullable=False, server_default='0.5'),
        sa.Column('prefers_originality', sa.Float(), nullable=False, server_default='0.5'),
        sa.Column('prefers_optimization', sa.Float(), nullable=False, server_default='0.5'),
        sa.Column('enjoys_lore', sa.Float(), nullable=False, server_default='0.5'),
        sa.Column('enjoys_mechanics', sa.Float(), nullable=False, server_default='0.5'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('last_assessment_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.UniqueConstraint('user_id'),
        sa.Index('ix_player_profiles_user_id', 'user_id'),
    )
    
    # Create psychographic_questions table
    op.create_table(
        'psychographic_questions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('question_text', sa.Text(), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('assessment_version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('order', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('ix_psychographic_questions_order', 'order'),
    )
    
    # Create question_options table
    op.create_table(
        'question_options',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('question_id', sa.Integer(), nullable=False),
        sa.Column('option_text', sa.Text(), nullable=False),
        sa.Column('order', sa.Integer(), nullable=False),
        sa.Column('timmy_weight', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('johnny_weight', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('spike_weight', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('vorthos_weight', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('melvin_weight', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('power_gamer_weight', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('social_gamer_weight', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('adrenaline_weight', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('combo_builder_weight', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('offbeat_builder_weight', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('architect_weight', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('competitive_weight', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('technical_weight', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('meta_analyst_weight', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('lore_weight', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('mechanics_weight', sa.Float(), nullable=False, server_default='0.0'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['question_id'], ['psychographic_questions.id'], ),
    )
    
    # Create assessment_responses table
    op.create_table(
        'assessment_responses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('profile_id', sa.Integer(), nullable=False),
        sa.Column('question_id', sa.Integer(), nullable=False),
        sa.Column('selected_option_id', sa.Integer(), nullable=False),
        sa.Column('answered_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['profile_id'], ['player_profiles.id'], ),
        sa.ForeignKeyConstraint(['question_id'], ['psychographic_questions.id'], ),
        sa.ForeignKeyConstraint(['selected_option_id'], ['question_options.id'], ),
    )


def downgrade() -> None:
    # Drop tables in reverse order of creation
    op.drop_table('assessment_responses')
    op.drop_table('question_options')
    op.drop_table('psychographic_questions')
    op.drop_column('users', 'profile_id')
    op.drop_table('player_profiles')
