"""Initial database schema

Revision ID: 001
Revises: 
Create Date: 2024-04-19 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create user_profiles table (if it doesn't exist)
    op.create_table('user_profiles',
        sa.Column('uid', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=True),
        sa.Column('display_name', sa.String(), nullable=True),
        sa.Column('photo_url', sa.String(), nullable=True),
        sa.Column('plan', sa.String(), nullable=True, server_default='free'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('uid')
    )

    # Create knowledge_bases table
    op.create_table('knowledge_bases',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['user_profiles.uid'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'name', name='uq_user_kb_name')
    )

    # Create sources table
    op.create_table('sources',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('kb_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('kb_name', sa.String(), nullable=False),
        sa.Column('url', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=True),
        sa.Column('source_type', sa.String(), nullable=True, server_default='youtube'),
        sa.Column('status', sa.String(), nullable=True, server_default='pending'),
        sa.Column('video_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('chunk_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('intro_cache', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['kb_id'], ['knowledge_bases.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['user_profiles.uid'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create chat_sessions table
    op.create_table('chat_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('source_id', sa.String(), nullable=False),
        sa.Column('kb_name', sa.String(), nullable=False),
        sa.Column('source_title', sa.String(), nullable=True),
        sa.Column('messages', sa.JSON(), nullable=True, server_default='[]'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['source_id'], ['sources.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['user_profiles.uid'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create usage_logs table
    op.create_table('usage_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('action', sa.String(), nullable=False),
        sa.Column('resource_id', sa.String(), nullable=True),
        sa.Column('event_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['user_profiles.uid'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create user_subscriptions table
    op.create_table('user_subscriptions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('plan_type', sa.String(), nullable=False, server_default='free'),
        sa.Column('status', sa.String(), nullable=False, server_default='active'),
        sa.Column('stripe_customer_id', sa.String(), nullable=True),
        sa.Column('stripe_subscription_id', sa.String(), nullable=True),
        sa.Column('current_period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('current_period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.CheckConstraint("plan_type IN ('free', 'pro', 'enterprise')", name='ck_plan_type'),
        sa.CheckConstraint("status IN ('active', 'cancelled', 'expired', 'past_due')", name='ck_subscription_status'),
        sa.ForeignKeyConstraint(['user_id'], ['user_profiles.uid'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )

    # Create daily_usage table
    op.create_table('daily_usage',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('videos_ingested', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('questions_asked', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('summaries_generated', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['user_profiles.uid'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'date', name='uq_user_date')
    )

    # Create plan_features table
    op.create_table('plan_features',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('plan_type', sa.String(), nullable=False),
        sa.Column('feature_name', sa.String(), nullable=False),
        sa.Column('feature_value', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('plan_type', 'feature_name', name='uq_plan_feature')
    )

    # Create indexes
    op.create_index('idx_knowledge_bases_user_id', 'knowledge_bases', ['user_id'])
    op.create_index('idx_sources_user_id', 'sources', ['user_id'])
    op.create_index('idx_sources_kb_id', 'sources', ['kb_id'])
    op.create_index('idx_chat_sessions_user_id', 'chat_sessions', ['user_id'])
    op.create_index('idx_chat_sessions_source_id', 'chat_sessions', ['source_id'])
    op.create_index('idx_usage_logs_user_id', 'usage_logs', ['user_id'])
    op.create_index('idx_usage_logs_action_date', 'usage_logs', ['user_id', 'action', 'created_at'])
    op.create_index('idx_user_subscriptions_user_id', 'user_subscriptions', ['user_id'])
    op.create_index('idx_daily_usage_user_date', 'daily_usage', ['user_id', 'date'])

    # Insert default plan features
    plan_features_data = [
        # Free plan
        ('free', 'videos_per_day', '3'),
        ('free', 'questions_per_day', '20'),
        ('free', 'history_retention_days', '7'),
        ('free', 'max_concurrent_videos', '5'),
        ('free', 'advanced_features', 'false'),
        ('free', 'priority_processing', 'false'),
        ('free', 'export_enabled', 'false'),
        
        # Pro plan
        ('pro', 'videos_per_day', '50'),
        ('pro', 'questions_per_day', '500'),
        ('pro', 'history_retention_days', '365'),
        ('pro', 'max_concurrent_videos', '100'),
        ('pro', 'advanced_features', 'true'),
        ('pro', 'priority_processing', 'true'),
        ('pro', 'export_enabled', 'true'),
        
        # Enterprise plan
        ('enterprise', 'videos_per_day', '1000'),
        ('enterprise', 'questions_per_day', '10000'),
        ('enterprise', 'history_retention_days', '-1'),
        ('enterprise', 'max_concurrent_videos', '1000'),
        ('enterprise', 'advanced_features', 'true'),
        ('enterprise', 'priority_processing', 'true'),
        ('enterprise', 'export_enabled', 'true'),
    ]
    
    # Insert plan features
    plan_features_table = sa.table('plan_features',
        sa.column('plan_type', sa.String),
        sa.column('feature_name', sa.String),
        sa.column('feature_value', sa.String)
    )
    
    for plan_type, feature_name, feature_value in plan_features_data:
        op.execute(
            plan_features_table.insert().values(
                plan_type=plan_type,
                feature_name=feature_name,
                feature_value=feature_value
            )
        )


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_daily_usage_user_date', table_name='daily_usage')
    op.drop_index('idx_user_subscriptions_user_id', table_name='user_subscriptions')
    op.drop_index('idx_usage_logs_action_date', table_name='usage_logs')
    op.drop_index('idx_usage_logs_user_id', table_name='usage_logs')
    op.drop_index('idx_chat_sessions_source_id', table_name='chat_sessions')
    op.drop_index('idx_chat_sessions_user_id', table_name='chat_sessions')
    op.drop_index('idx_sources_kb_id', table_name='sources')
    op.drop_index('idx_sources_user_id', table_name='sources')
    op.drop_index('idx_knowledge_bases_user_id', table_name='knowledge_bases')
    
    # Drop tables in reverse order (respecting foreign key constraints)
    op.drop_table('plan_features')
    op.drop_table('daily_usage')
    op.drop_table('user_subscriptions')
    op.drop_table('usage_logs')
    op.drop_table('chat_sessions')
    op.drop_table('sources')
    op.drop_table('knowledge_bases')
    op.drop_table('user_profiles')