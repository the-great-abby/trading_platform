"""Add portfolio management tables

Revision ID: 002_portfolio_tables
Revises: 001_initial_schema
Create Date: 2025-01-27 10:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002_portfolio_tables'
down_revision = '001_initial_schema'  # Adjust based on your existing schema
branch_labels = None
depends_on = None


def upgrade():
    """Create portfolio management tables"""
    
    # Core portfolio table
    op.create_table('portfolios',
        sa.Column('portfolio_id', sa.VARCHAR(50), primary_key=True),
        sa.Column('name', sa.VARCHAR(255), nullable=False),
        sa.Column('description', sa.TEXT),
        sa.Column('owner_id', sa.VARCHAR(50), nullable=False),
        sa.Column('creation_date', sa.TIMESTAMP, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('last_updated', sa.TIMESTAMP, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('status', sa.VARCHAR(20), server_default='ACTIVE'),
        sa.Column('base_currency', sa.VARCHAR(3), server_default='USD'),
        sa.Column('rebalancing_frequency', sa.VARCHAR(20), server_default='MONTHLY'),
        sa.Column('risk_tolerance', sa.VARCHAR(20), server_default='MODERATE'),
        sa.Column('max_single_asset_weight', sa.DECIMAL(5,4), server_default=sa.text('0.10')),
        sa.Column('max_sector_weight', sa.DECIMAL(5,4), server_default=sa.text('0.30')),
        sa.Column('min_liquidity_requirement', sa.BIGINT, server_default=sa.text('1000000000')),
        sa.Column('long_only', sa.BOOLEAN, server_default=sa.text('TRUE')),
        sa.Column('total_value', sa.DECIMAL(15,2), server_default=sa.text('0.00')),
        sa.Column('cash_balance', sa.DECIMAL(15,2), server_default=sa.text('0.00')),
        sa.Column('total_invested', sa.DECIMAL(15,2), server_default=sa.text('0.00')),
        sa.Column('unrealized_pnl', sa.DECIMAL(15,2), server_default=sa.text('0.00')),
        sa.Column('realized_pnl', sa.DECIMAL(15,2), server_default=sa.text('0.00')),
        sa.Column('total_return', sa.DECIMAL(10,6), server_default=sa.text('0.00')),
        sa.Column('annualized_return', sa.DECIMAL(10,6), server_default=sa.text('0.00')),
        sa.Column('volatility', sa.DECIMAL(10,6), server_default=sa.text('0.00')),
        sa.Column('sharpe_ratio', sa.DECIMAL(10,6), server_default=sa.text('0.00')),
        sa.Column('max_drawdown', sa.DECIMAL(10,6), server_default=sa.text('0.00')),
        sa.Column('calmar_ratio', sa.DECIMAL(10,6), server_default=sa.text('0.00'))
    )

    # Portfolio positions
    op.create_table('portfolio_positions',
        sa.Column('position_id', sa.VARCHAR(50), primary_key=True),
        sa.Column('portfolio_id', sa.VARCHAR(50), sa.ForeignKey('portfolios.portfolio_id')),
        sa.Column('asset_id', sa.VARCHAR(50), nullable=False),
        sa.Column('quantity', sa.DECIMAL(15,6), nullable=False),
        sa.Column('average_cost', sa.DECIMAL(10,4), nullable=False),
        sa.Column('current_price', sa.DECIMAL(10,4), nullable=False),
        sa.Column('market_value', sa.DECIMAL(15,2), nullable=False),
        sa.Column('cost_basis', sa.DECIMAL(15,2), nullable=False),
        sa.Column('unrealized_pnl', sa.DECIMAL(15,2), server_default=sa.text('0.00')),
        sa.Column('unrealized_pnl_pct', sa.DECIMAL(10,6), server_default=sa.text('0.00')),
        sa.Column('weight', sa.DECIMAL(8,6), server_default=sa.text('0.00')),
        sa.Column('holding_period', sa.INTEGER, server_default=sa.text('0')),
        sa.Column('is_long_term', sa.BOOLEAN, server_default=sa.text('FALSE')),
        sa.Column('tax_lot_id', sa.VARCHAR(50)),
        sa.Column('first_purchase_date', sa.TIMESTAMP),
        sa.Column('last_purchase_date', sa.TIMESTAMP),
        sa.Column('last_sale_date', sa.TIMESTAMP),
        sa.Column('created_at', sa.TIMESTAMP, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.TIMESTAMP, server_default=sa.text('CURRENT_TIMESTAMP'))
    )

    # Optimization results
    op.create_table('optimization_results',
        sa.Column('optimization_id', sa.VARCHAR(50), primary_key=True),
        sa.Column('portfolio_id', sa.VARCHAR(50), sa.ForeignKey('portfolios.portfolio_id')),
        sa.Column('optimization_method', sa.VARCHAR(50), nullable=False),
        sa.Column('risk_free_rate', sa.DECIMAL(8,6), server_default=sa.text('0.02')),
        sa.Column('optimization_date', sa.TIMESTAMP, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('expected_return', sa.DECIMAL(10,6), nullable=False),
        sa.Column('expected_volatility', sa.DECIMAL(10,6), nullable=False),
        sa.Column('sharpe_ratio', sa.DECIMAL(10,6), nullable=False),
        sa.Column('portfolio_var', sa.DECIMAL(10,6)),
        sa.Column('portfolio_cvar', sa.DECIMAL(10,6)),
        sa.Column('max_drawdown', sa.DECIMAL(10,6)),
        sa.Column('beta', sa.DECIMAL(10,6)),
        sa.Column('convergence_status', sa.BOOLEAN, server_default=sa.text('FALSE')),
        sa.Column('optimization_time', sa.DECIMAL(10,3)),
        sa.Column('iteration_count', sa.INTEGER),
        sa.Column('constraint_violations', postgresql.ARRAY(sa.TEXT))
    )

    # Asset weights from optimization
    op.create_table('optimization_weights',
        sa.Column('weight_id', sa.VARCHAR(50), primary_key=True),
        sa.Column('optimization_id', sa.VARCHAR(50), sa.ForeignKey('optimization_results.optimization_id')),
        sa.Column('asset_id', sa.VARCHAR(50), nullable=False),
        sa.Column('optimal_weight', sa.DECIMAL(8,6), nullable=False),
        sa.Column('risk_contribution', sa.DECIMAL(8,6)),
        sa.Column('expected_return', sa.DECIMAL(10,6)),
        sa.Column('expected_volatility', sa.DECIMAL(10,6))
    )

    # Market views for Black-Litterman
    op.create_table('market_views',
        sa.Column('view_id', sa.VARCHAR(50), primary_key=True),
        sa.Column('portfolio_id', sa.VARCHAR(50), sa.ForeignKey('portfolios.portfolio_id')),
        sa.Column('view_type', sa.VARCHAR(20), nullable=False),
        sa.Column('view_description', sa.TEXT),
        sa.Column('target_asset_id', sa.VARCHAR(50)),
        sa.Column('expected_return', sa.DECIMAL(10,6)),
        sa.Column('outperforming_asset_id', sa.VARCHAR(50)),
        sa.Column('underperforming_asset_id', sa.VARCHAR(50)),
        sa.Column('relative_return', sa.DECIMAL(10,6)),
        sa.Column('confidence_level', sa.DECIMAL(5,4), nullable=False),
        sa.Column('view_date', sa.TIMESTAMP, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('expiry_date', sa.TIMESTAMP),
        sa.Column('is_active', sa.BOOLEAN, server_default=sa.text('TRUE'))
    )

    # Rebalancing recommendations
    op.create_table('rebalancing_recommendations',
        sa.Column('recommendation_id', sa.VARCHAR(50), primary_key=True),
        sa.Column('portfolio_id', sa.VARCHAR(50), sa.ForeignKey('portfolios.portfolio_id')),
        sa.Column('optimization_id', sa.VARCHAR(50), sa.ForeignKey('optimization_results.optimization_id')),
        sa.Column('recommendation_date', sa.TIMESTAMP, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('target_rebalancing_date', sa.TIMESTAMP, nullable=False),
        sa.Column('priority', sa.VARCHAR(20), server_default='MEDIUM'),
        sa.Column('total_trades', sa.INTEGER, server_default=sa.text('0')),
        sa.Column('estimated_transaction_cost', sa.DECIMAL(15,2), server_default=sa.text('0.00')),
        sa.Column('estimated_market_impact', sa.DECIMAL(15,2), server_default=sa.text('0.00')),
        sa.Column('tracking_error_reduction', sa.DECIMAL(10,6), server_default=sa.text('0.00')),
        sa.Column('expected_risk_reduction', sa.DECIMAL(10,6), server_default=sa.text('0.00')),
        sa.Column('expected_return_improvement', sa.DECIMAL(10,6), server_default=sa.text('0.00')),
        sa.Column('rebalancing_urgency', sa.DECIMAL(5,4), server_default=sa.text('0.00')),
        sa.Column('is_executed', sa.BOOLEAN, server_default=sa.text('FALSE')),
        sa.Column('execution_date', sa.TIMESTAMP),
        sa.Column('execution_cost', sa.DECIMAL(15,2))
    )

    # Trade recommendations
    op.create_table('trade_recommendations',
        sa.Column('trade_id', sa.VARCHAR(50), primary_key=True),
        sa.Column('recommendation_id', sa.VARCHAR(50), sa.ForeignKey('rebalancing_recommendations.recommendation_id')),
        sa.Column('asset_id', sa.VARCHAR(50), nullable=False),
        sa.Column('action', sa.VARCHAR(10), nullable=False),
        sa.Column('current_quantity', sa.DECIMAL(15,6), nullable=False),
        sa.Column('target_quantity', sa.DECIMAL(15,6), nullable=False),
        sa.Column('trade_quantity', sa.DECIMAL(15,6), nullable=False),
        sa.Column('current_weight', sa.DECIMAL(8,6), nullable=False),
        sa.Column('target_weight', sa.DECIMAL(8,6), nullable=False),
        sa.Column('weight_change', sa.DECIMAL(8,6), nullable=False),
        sa.Column('current_price', sa.DECIMAL(10,4), nullable=False),
        sa.Column('estimated_execution_price', sa.DECIMAL(10,4)),
        sa.Column('estimated_cost', sa.DECIMAL(15,2), server_default=sa.text('0.00')),
        sa.Column('estimated_market_impact', sa.DECIMAL(15,2), server_default=sa.text('0.00')),
        sa.Column('is_tax_loss_harvest', sa.BOOLEAN, server_default=sa.text('FALSE')),
        sa.Column('tax_lot_id', sa.VARCHAR(50)),
        sa.Column('estimated_tax_savings', sa.DECIMAL(15,2)),
        sa.Column('priority', sa.INTEGER, server_default=sa.text('1')),
        sa.Column('is_executed', sa.BOOLEAN, server_default=sa.text('FALSE')),
        sa.Column('execution_date', sa.TIMESTAMP),
        sa.Column('actual_execution_price', sa.DECIMAL(10,4))
    )

    # Risk metrics
    op.create_table('risk_metrics',
        sa.Column('risk_metrics_id', sa.VARCHAR(50), primary_key=True),
        sa.Column('portfolio_id', sa.VARCHAR(50), sa.ForeignKey('portfolios.portfolio_id')),
        sa.Column('calculation_date', sa.TIMESTAMP, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('lookback_period', sa.INTEGER, server_default=sa.text('252')),
        sa.Column('var_95', sa.DECIMAL(10,6)),
        sa.Column('var_99', sa.DECIMAL(10,6)),
        sa.Column('cvar_95', sa.DECIMAL(10,6)),
        sa.Column('cvar_99', sa.DECIMAL(10,6)),
        sa.Column('systematic_risk', sa.DECIMAL(10,6)),
        sa.Column('idiosyncratic_risk', sa.DECIMAL(10,6)),
        sa.Column('market_beta', sa.DECIMAL(10,6)),
        sa.Column('size_factor_exposure', sa.DECIMAL(10,6)),
        sa.Column('value_factor_exposure', sa.DECIMAL(10,6)),
        sa.Column('momentum_factor_exposure', sa.DECIMAL(10,6)),
        sa.Column('quality_factor_exposure', sa.DECIMAL(10,6)),
        sa.Column('average_correlation', sa.DECIMAL(8,6)),
        sa.Column('max_correlation', sa.DECIMAL(8,6)),
        sa.Column('min_correlation', sa.DECIMAL(8,6)),
        sa.Column('information_ratio', sa.DECIMAL(10,6)),
        sa.Column('tracking_error', sa.DECIMAL(10,6)),
        sa.Column('max_drawdown', sa.DECIMAL(10,6)),
        sa.Column('calmar_ratio', sa.DECIMAL(10,6)),
        sa.Column('sortino_ratio', sa.DECIMAL(10,6))
    )

    # Risk contributions by asset
    op.create_table('risk_contributions',
        sa.Column('contribution_id', sa.VARCHAR(50), primary_key=True),
        sa.Column('risk_metrics_id', sa.VARCHAR(50), sa.ForeignKey('risk_metrics.risk_metrics_id')),
        sa.Column('asset_id', sa.VARCHAR(50), nullable=False),
        sa.Column('risk_contribution', sa.DECIMAL(8,6), nullable=False),
        sa.Column('marginal_risk', sa.DECIMAL(8,6)),
        sa.Column('component_risk', sa.DECIMAL(8,6))
    )

    # Create indexes for performance
    op.create_index('idx_portfolios_owner_id', 'portfolios', ['owner_id'])
    op.create_index('idx_portfolios_status', 'portfolios', ['status'])
    op.create_index('idx_portfolio_positions_portfolio_id', 'portfolio_positions', ['portfolio_id'])
    op.create_index('idx_optimization_results_portfolio_id', 'optimization_results', ['portfolio_id'])
    op.create_index('idx_market_views_portfolio_id', 'market_views', ['portfolio_id'])
    op.create_index('idx_risk_metrics_portfolio_id', 'risk_metrics', ['portfolio_id'])


def downgrade():
    """Drop portfolio management tables"""
    
    # Drop indexes
    op.drop_index('idx_risk_metrics_portfolio_id')
    op.drop_index('idx_market_views_portfolio_id')
    op.drop_index('idx_optimization_results_portfolio_id')
    op.drop_index('idx_portfolio_positions_portfolio_id')
    op.drop_index('idx_portfolios_status')
    op.drop_index('idx_portfolios_owner_id')
    
    # Drop tables in reverse order
    op.drop_table('risk_contributions')
    op.drop_table('risk_metrics')
    op.drop_table('trade_recommendations')
    op.drop_table('rebalancing_recommendations')
    op.drop_table('market_views')
    op.drop_table('optimization_weights')
    op.drop_table('optimization_results')
    op.drop_table('portfolio_positions')
    op.drop_table('portfolios')
























