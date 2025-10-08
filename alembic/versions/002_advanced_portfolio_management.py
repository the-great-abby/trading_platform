"""Advanced Portfolio Management System

Revision ID: 002_advanced_portfolio_management
Revises: 001_initial_setup
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002_advanced_portfolio_management'
down_revision = '001_initial_setup'
branch_labels = None
depends_on = None


def upgrade():
    """Create advanced portfolio management tables"""
    
    # Create portfolios table
    op.create_table('portfolios',
        sa.Column('portfolio_id', sa.String(50), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('owner_id', sa.String(50), nullable=False),
        sa.Column('base_currency', sa.String(3), nullable=False, default='USD'),
        sa.Column('risk_tolerance', sa.String(20), nullable=False, default='MODERATE'),
        sa.Column('rebalancing_frequency', sa.String(20), nullable=False, default='MONTHLY'),
        sa.Column('max_single_asset_weight', sa.Float, nullable=False, default=0.10),
        sa.Column('max_sector_weight', sa.Float, nullable=False, default=0.30),
        sa.Column('long_only', sa.Boolean, nullable=False, default=True),
        sa.Column('total_value', sa.Float, nullable=False, default=0.0),
        sa.Column('cash_balance', sa.Float, nullable=False, default=0.0),
        sa.Column('creation_date', sa.DateTime, nullable=False),
        sa.Column('last_updated', sa.DateTime, nullable=False, default=sa.func.now()),
        sa.Column('status', sa.String(20), nullable=False, default='ACTIVE'),
        sa.Index('idx_portfolios_owner_id', 'owner_id'),
        sa.Index('idx_portfolios_status', 'status'),
        sa.Index('idx_portfolios_creation_date', 'creation_date')
    )
    
    # Create assets table
    op.create_table('assets',
        sa.Column('asset_id', sa.String(50), primary_key=True),
        sa.Column('symbol', sa.String(20), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('sector', sa.String(100)),
        sa.Column('asset_type', sa.String(50), nullable=False, default='EQUITY'),
        sa.Column('currency', sa.String(3), nullable=False, default='USD'),
        sa.Column('exchange', sa.String(20)),
        sa.Column('country', sa.String(50)),
        sa.Column('market_cap', sa.Float),
        sa.Column('beta', sa.Float),
        sa.Column('dividend_yield', sa.Float),
        sa.Column('pe_ratio', sa.Float),
        sa.Column('pb_ratio', sa.Float),
        sa.Column('debt_to_equity', sa.Float),
        sa.Column('return_on_equity', sa.Float),
        sa.Column('created_at', sa.DateTime, nullable=False, default=sa.func.now()),
        sa.Column('last_updated', sa.DateTime, nullable=False, default=sa.func.now()),
        sa.Index('idx_assets_symbol', 'symbol'),
        sa.Index('idx_assets_sector', 'sector'),
        sa.Index('idx_assets_asset_type', 'asset_type')
    )
    
    # Create portfolio_positions table
    op.create_table('portfolio_positions',
        sa.Column('position_id', sa.String(50), primary_key=True),
        sa.Column('portfolio_id', sa.String(50), nullable=False),
        sa.Column('asset_id', sa.String(50), nullable=False),
        sa.Column('quantity', sa.Float, nullable=False),
        sa.Column('average_cost', sa.Float, nullable=False),
        sa.Column('current_price', sa.Float),
        sa.Column('market_value', sa.Float),
        sa.Column('unrealized_pnl', sa.Float, default=0.0),
        sa.Column('created_at', sa.DateTime, nullable=False, default=sa.func.now()),
        sa.Column('last_updated', sa.DateTime, nullable=False, default=sa.func.now()),
        sa.ForeignKeyConstraint(['portfolio_id'], ['portfolios.portfolio_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['asset_id'], ['assets.asset_id'], ondelete='CASCADE'),
        sa.Index('idx_portfolio_positions_portfolio_id', 'portfolio_id'),
        sa.Index('idx_portfolio_positions_asset_id', 'asset_id'),
        sa.UniqueConstraint('portfolio_id', 'asset_id', name='uq_portfolio_asset')
    )
    
    # Create optimization_results table
    op.create_table('optimization_results',
        sa.Column('optimization_id', sa.String(50), primary_key=True),
        sa.Column('portfolio_id', sa.String(50), nullable=False),
        sa.Column('optimization_type', sa.String(50), nullable=False),
        sa.Column('optimization_date', sa.DateTime, nullable=False),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('expected_return', sa.Float),
        sa.Column('expected_volatility', sa.Float),
        sa.Column('sharpe_ratio', sa.Float),
        sa.Column('risk_free_rate', sa.Float, default=0.02),
        sa.Column('convergence_achieved', sa.Boolean, default=False),
        sa.Column('iterations', sa.Integer),
        sa.Column('computation_time', sa.Float),
        sa.Column('constraints', sa.JSON),
        sa.Column('metadata', sa.JSON),
        sa.ForeignKeyConstraint(['portfolio_id'], ['portfolios.portfolio_id'], ondelete='CASCADE'),
        sa.Index('idx_optimization_results_portfolio_id', 'portfolio_id'),
        sa.Index('idx_optimization_results_type', 'optimization_type'),
        sa.Index('idx_optimization_results_date', 'optimization_date')
    )
    
    # Create optimization_weights table
    op.create_table('optimization_weights',
        sa.Column('optimization_id', sa.String(50), nullable=False),
        sa.Column('asset_id', sa.String(50), nullable=False),
        sa.Column('weight', sa.Float, nullable=False),
        sa.ForeignKeyConstraint(['optimization_id'], ['optimization_results.optimization_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['asset_id'], ['assets.asset_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('optimization_id', 'asset_id'),
        sa.Index('idx_optimization_weights_optimization_id', 'optimization_id'),
        sa.Index('idx_optimization_weights_asset_id', 'asset_id')
    )
    
    # Create market_views table
    op.create_table('market_views',
        sa.Column('market_view_id', sa.String(50), primary_key=True),
        sa.Column('portfolio_id', sa.String(50), nullable=False),
        sa.Column('view_type', sa.String(20), nullable=False),
        sa.Column('view_description', sa.Text, nullable=False),
        sa.Column('target_asset_id', sa.String(50)),
        sa.Column('expected_return', sa.Float),
        sa.Column('outperforming_asset_id', sa.String(50)),
        sa.Column('underperforming_asset_id', sa.String(50)),
        sa.Column('relative_return', sa.Float),
        sa.Column('confidence_level', sa.Float, nullable=False, default=0.5),
        sa.Column('created_at', sa.DateTime, nullable=False, default=sa.func.now()),
        sa.Column('last_updated', sa.DateTime, nullable=False, default=sa.func.now()),
        sa.Column('is_active', sa.Boolean, nullable=False, default=True),
        sa.ForeignKeyConstraint(['portfolio_id'], ['portfolios.portfolio_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['target_asset_id'], ['assets.asset_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['outperforming_asset_id'], ['assets.asset_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['underperforming_asset_id'], ['assets.asset_id'], ondelete='CASCADE'),
        sa.Index('idx_market_views_portfolio_id', 'portfolio_id'),
        sa.Index('idx_market_views_type', 'view_type'),
        sa.Index('idx_market_views_active', 'is_active')
    )
    
    # Create rebalancing_recommendations table
    op.create_table('rebalancing_recommendations',
        sa.Column('rebalancing_id', sa.String(50), primary_key=True),
        sa.Column('portfolio_id', sa.String(50), nullable=False),
        sa.Column('recommendation_date', sa.DateTime, nullable=False),
        sa.Column('rebalancing_strategy', sa.String(50), nullable=False),
        sa.Column('target_weights', sa.JSON),
        sa.Column('current_weights', sa.JSON),
        sa.Column('total_trades', sa.Integer, default=0),
        sa.Column('total_trade_value', sa.Float, default=0.0),
        sa.Column('estimated_transaction_costs', sa.Float, default=0.0),
        sa.Column('estimated_tax_cost', sa.Float, default=0.0),
        sa.Column('drift_from_target', sa.Float),
        sa.Column('rebalancing_urgency', sa.String(20)),
        sa.Column('status', sa.String(20), default='PENDING'),
        sa.Column('execution_date', sa.DateTime),
        sa.Column('metadata', sa.JSON),
        sa.ForeignKeyConstraint(['portfolio_id'], ['portfolios.portfolio_id'], ondelete='CASCADE'),
        sa.Index('idx_rebalancing_portfolio_id', 'portfolio_id'),
        sa.Index('idx_rebalancing_date', 'recommendation_date'),
        sa.Index('idx_rebalancing_status', 'status')
    )
    
    # Create trade_recommendations table
    op.create_table('trade_recommendations',
        sa.Column('trade_id', sa.String(50), primary_key=True),
        sa.Column('rebalancing_id', sa.String(50), nullable=False),
        sa.Column('asset_id', sa.String(50), nullable=False),
        sa.Column('action', sa.String(10), nullable=False),  # BUY, SELL
        sa.Column('quantity', sa.Float, nullable=False),
        sa.Column('current_price', sa.Float),
        sa.Column('trade_value', sa.Float),
        sa.Column('weight_change', sa.Float),
        sa.Column('tax_implications', sa.JSON),
        sa.Column('priority', sa.Integer, default=1),
        sa.Column('status', sa.String(20), default='PENDING'),
        sa.Column('execution_date', sa.DateTime),
        sa.Column('executed_price', sa.Float),
        sa.Column('executed_value', sa.Float),
        sa.Column('transaction_cost', sa.Float),
        sa.ForeignKeyConstraint(['rebalancing_id'], ['rebalancing_recommendations.rebalancing_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['asset_id'], ['assets.asset_id'], ondelete='CASCADE'),
        sa.Index('idx_trade_recommendations_rebalancing_id', 'rebalancing_id'),
        sa.Index('idx_trade_recommendations_asset_id', 'asset_id'),
        sa.Index('idx_trade_recommendations_status', 'status')
    )
    
    # Create risk_metrics table
    op.create_table('risk_metrics',
        sa.Column('risk_metrics_id', sa.String(50), primary_key=True),
        sa.Column('portfolio_id', sa.String(50), nullable=False),
        sa.Column('calculation_date', sa.DateTime, nullable=False),
        sa.Column('lookback_period', sa.Integer, nullable=False, default=252),
        sa.Column('var_95', sa.Float),
        sa.Column('var_99', sa.Float),
        sa.Column('cvar_95', sa.Float),
        sa.Column('cvar_99', sa.Float),
        sa.Column('systematic_risk', sa.Float),
        sa.Column('idiosyncratic_risk', sa.Float),
        sa.Column('market_beta', sa.Float),
        sa.Column('average_correlation', sa.Float),
        sa.Column('max_correlation', sa.Float),
        sa.Column('min_correlation', sa.Float),
        sa.Column('created_at', sa.DateTime, nullable=False, default=sa.func.now()),
        sa.ForeignKeyConstraint(['portfolio_id'], ['portfolios.portfolio_id'], ondelete='CASCADE'),
        sa.Index('idx_risk_metrics_portfolio_id', 'portfolio_id'),
        sa.Index('idx_risk_metrics_date', 'calculation_date')
    )
    
    # Create risk_contributions table
    op.create_table('risk_contributions',
        sa.Column('risk_metrics_id', sa.String(50), nullable=False),
        sa.Column('asset_id', sa.String(50), nullable=False),
        sa.Column('risk_contribution', sa.Float, nullable=False),
        sa.ForeignKeyConstraint(['risk_metrics_id'], ['risk_metrics.risk_metrics_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['asset_id'], ['assets.asset_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('risk_metrics_id', 'asset_id'),
        sa.Index('idx_risk_contributions_risk_metrics_id', 'risk_metrics_id'),
        sa.Index('idx_risk_contributions_asset_id', 'asset_id')
    )
    
    # Create portfolio_performance_history table (for time series data)
    op.create_table('portfolio_performance_history',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('portfolio_id', sa.String(50), nullable=False),
        sa.Column('calculation_date', sa.Date, nullable=False),
        sa.Column('total_value', sa.Float, nullable=False),
        sa.Column('cash_balance', sa.Float, nullable=False),
        sa.Column('unrealized_pnl', sa.Float, default=0.0),
        sa.Column('total_return', sa.Float),
        sa.Column('daily_return', sa.Float),
        sa.Column('volatility', sa.Float),
        sa.Column('sharpe_ratio', sa.Float),
        sa.Column('max_drawdown', sa.Float),
        sa.Column('created_at', sa.DateTime, nullable=False, default=sa.func.now()),
        sa.ForeignKeyConstraint(['portfolio_id'], ['portfolios.portfolio_id'], ondelete='CASCADE'),
        sa.Index('idx_portfolio_performance_portfolio_id', 'portfolio_id'),
        sa.Index('idx_portfolio_performance_date', 'calculation_date'),
        sa.UniqueConstraint('portfolio_id', 'calculation_date', name='uq_portfolio_performance_date')
    )
    
    # Create backtest_results table
    op.create_table('backtest_results',
        sa.Column('backtest_id', sa.String(50), primary_key=True),
        sa.Column('portfolio_id', sa.String(50), nullable=False),
        sa.Column('strategy_name', sa.String(100), nullable=False),
        sa.Column('backtest_date', sa.DateTime, nullable=False),
        sa.Column('start_date', sa.Date, nullable=False),
        sa.Column('end_date', sa.Date, nullable=False),
        sa.Column('initial_capital', sa.Float, nullable=False),
        sa.Column('final_value', sa.Float),
        sa.Column('total_return', sa.Float),
        sa.Column('annualized_return', sa.Float),
        sa.Column('volatility', sa.Float),
        sa.Column('sharpe_ratio', sa.Float),
        sa.Column('sortino_ratio', sa.Float),
        sa.Column('calmar_ratio', sa.Float),
        sa.Column('max_drawdown', sa.Float),
        sa.Column('var_95', sa.Float),
        sa.Column('cvar_95', sa.Float),
        sa.Column('benchmark_return', sa.Float),
        sa.Column('excess_return', sa.Float),
        sa.Column('information_ratio', sa.Float),
        sa.Column('alpha', sa.Float),
        sa.Column('beta', sa.Float),
        sa.Column('r_squared', sa.Float),
        sa.Column('status', sa.String(20), default='COMPLETED'),
        sa.Column('metadata', sa.JSON),
        sa.ForeignKeyConstraint(['portfolio_id'], ['portfolios.portfolio_id'], ondelete='CASCADE'),
        sa.Index('idx_backtest_results_portfolio_id', 'portfolio_id'),
        sa.Index('idx_backtest_results_strategy', 'strategy_name'),
        sa.Index('idx_backtest_results_date', 'backtest_date')
    )


def downgrade():
    """Drop advanced portfolio management tables"""
    
    # Drop tables in reverse order (respecting foreign key constraints)
    op.drop_table('backtest_results')
    op.drop_table('portfolio_performance_history')
    op.drop_table('risk_contributions')
    op.drop_table('risk_metrics')
    op.drop_table('trade_recommendations')
    op.drop_table('rebalancing_recommendations')
    op.drop_table('market_views')
    op.drop_table('optimization_weights')
    op.drop_table('optimization_results')
    op.drop_table('portfolio_positions')
    op.drop_table('assets')
    op.drop_table('portfolios')
























