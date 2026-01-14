"""initial_schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create campaigns table
    op.create_table(
        'campaigns',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('external_id', sa.String(255), nullable=False),
        sa.Column('name', sa.String(500), nullable=False),
        sa.Column('source', sa.String(50), nullable=False),
        sa.Column('status', sa.String(50)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.UniqueConstraint('external_id', name='uq_campaigns_external_id')
    )
    op.create_index('ix_campaigns_external_id', 'campaigns', ['external_id'])
    op.create_index('ix_campaigns_source', 'campaigns', ['source'])

    # Create daily_metrics table
    op.create_table(
        'daily_metrics',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('campaign_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('source', sa.String(50), nullable=False),
        sa.Column('impressions', sa.BigInteger(), server_default='0'),
        sa.Column('clicks', sa.Integer(), server_default='0'),
        sa.Column('spend', sa.Numeric(12, 2), server_default='0'),
        sa.Column('conversions', sa.Integer(), server_default='0'),
        sa.Column('revenue', sa.Numeric(12, 2), server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['campaign_id'], ['campaigns.id']),
        sa.UniqueConstraint('date', 'campaign_id', 'source', name='uq_daily_metrics')
    )
    op.create_index('ix_daily_metrics_date', 'daily_metrics', ['date'])
    op.create_index('ix_daily_metrics_campaign_id', 'daily_metrics', ['campaign_id'])
    op.create_index('ix_daily_metrics_source', 'daily_metrics', ['source'])

    # Create weekly_metrics table
    op.create_table(
        'weekly_metrics',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('week_start', sa.Date(), nullable=False),
        sa.Column('campaign_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('source', sa.String(50), nullable=False),
        sa.Column('impressions', sa.BigInteger()),
        sa.Column('clicks', sa.Integer()),
        sa.Column('spend', sa.Numeric(12, 2)),
        sa.Column('conversions', sa.Integer()),
        sa.Column('revenue', sa.Numeric(12, 2)),
        sa.Column('roas', sa.Numeric(10, 4)),
        sa.Column('ctr', sa.Numeric(10, 4)),
        sa.Column('cpc', sa.Numeric(10, 4)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['campaign_id'], ['campaigns.id']),
        sa.UniqueConstraint('week_start', 'campaign_id', 'source', name='uq_weekly_metrics')
    )
    op.create_index('ix_weekly_metrics_week_start', 'weekly_metrics', ['week_start'])
    op.create_index('ix_weekly_metrics_campaign_id', 'weekly_metrics', ['campaign_id'])
    op.create_index('ix_weekly_metrics_source', 'weekly_metrics', ['source'])

    # Create agent_runs table
    op.create_table(
        'agent_runs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('run_type', sa.String(50), nullable=False),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('completed_at', sa.DateTime(timezone=True)),
        sa.Column('input_params', postgresql.JSONB()),
        sa.Column('output', postgresql.JSONB()),
        sa.Column('error_message', sa.Text())
    )
    op.create_index('ix_agent_runs_run_type', 'agent_runs', ['run_type'])
    op.create_index('ix_agent_runs_status', 'agent_runs', ['status'])

    # Create insights table
    op.create_table(
        'insights',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('agent_run_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('insight_type', sa.String(50), nullable=False),
        sa.Column('campaign_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('metric', sa.String(50), nullable=False),
        sa.Column('change_percent', sa.Numeric(10, 2)),
        sa.Column('description', sa.Text()),
        sa.Column('severity', sa.String(20)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['agent_run_id'], ['agent_runs.id']),
        sa.ForeignKeyConstraint(['campaign_id'], ['campaigns.id'])
    )
    op.create_index('ix_insights_agent_run_id', 'insights', ['agent_run_id'])
    op.create_index('ix_insights_campaign_id', 'insights', ['campaign_id'])

    # Create actions table
    op.create_table(
        'actions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('agent_run_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('action_type', sa.String(50), nullable=False),
        sa.Column('campaign_id', postgresql.UUID(as_uuid=True)),
        sa.Column('description', sa.Text()),
        sa.Column('priority', sa.String(20)),
        sa.Column('status', sa.String(50), server_default='pending'),
        sa.Column('approved_by', sa.String(255)),
        sa.Column('approved_at', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['agent_run_id'], ['agent_runs.id']),
        sa.ForeignKeyConstraint(['campaign_id'], ['campaigns.id'])
    )
    op.create_index('ix_actions_agent_run_id', 'actions', ['agent_run_id'])
    op.create_index('ix_actions_campaign_id', 'actions', ['campaign_id'])
    op.create_index('ix_actions_status', 'actions', ['status'])

    # Create creatives table
    op.create_table(
        'creatives',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('agent_run_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('action_id', postgresql.UUID(as_uuid=True)),
        sa.Column('platform', sa.String(50), nullable=False),
        sa.Column('creative_type', sa.String(50)),
        sa.Column('headline', sa.Text()),
        sa.Column('primary_text', sa.Text()),
        sa.Column('description', sa.Text()),
        sa.Column('call_to_action', sa.String(100)),
        sa.Column('status', sa.String(50), server_default='draft'),
        sa.Column('approved_by', sa.String(255)),
        sa.Column('approved_at', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['agent_run_id'], ['agent_runs.id']),
        sa.ForeignKeyConstraint(['action_id'], ['actions.id'])
    )
    op.create_index('ix_creatives_agent_run_id', 'creatives', ['agent_run_id'])
    op.create_index('ix_creatives_action_id', 'creatives', ['action_id'])
    op.create_index('ix_creatives_status', 'creatives', ['status'])


def downgrade() -> None:
    # Drop tables in reverse order (respecting foreign key constraints)
    op.drop_table('creatives')
    op.drop_table('actions')
    op.drop_table('insights')
    op.drop_table('agent_runs')
    op.drop_table('weekly_metrics')
    op.drop_table('daily_metrics')
    op.drop_table('campaigns')

