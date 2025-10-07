"""
Database migration: Add advanced strategy types to StrategyType enum

Adds support for all the advanced strategies from the main strategy system.
"""

from alembic import op
import sqlalchemy as sa


def upgrade():
    """Add advanced strategy types to the StrategyType enum."""
    
    # Add new strategy types to the existing enum
    op.execute("""
        ALTER TYPE strategytype ADD VALUE 'VOLATILITY_TRADING';
        ALTER TYPE strategytype ADD VALUE 'VOLATILITY_BREAKOUT';
        ALTER TYPE strategytype ADD VALUE 'MARKET_REGIME_ADAPTIVE';
        ALTER TYPE strategytype ADD VALUE 'REGIME_SWITCHING';
        ALTER TYPE strategytype ADD VALUE 'ELLIOTT_WAVE_CORRECTIVE';
        ALTER TYPE strategytype ADD VALUE 'ELLIOTT_WAVE_IMPULSE';
        ALTER TYPE strategytype ADD VALUE 'SECTOR_ROTATION';
        ALTER TYPE strategytype ADD VALUE 'NEWS_ENHANCED';
        ALTER TYPE strategytype ADD VALUE 'RSI_AI_ENHANCED';
        ALTER TYPE strategytype ADD VALUE 'QUANTUM_MOMENTUM';
        ALTER TYPE strategytype ADD VALUE 'COVERED_CALL';
        ALTER TYPE strategytype ADD VALUE 'CASH_SECURED_PUT';
        ALTER TYPE strategytype ADD VALUE 'STRADDLE';
        ALTER TYPE strategytype ADD VALUE 'STRANGLE';
        ALTER TYPE strategytype ADD VALUE 'DIAGONAL_SPREAD';
        ALTER TYPE strategytype ADD VALUE 'EARNINGS_STRATEGY';
        ALTER TYPE strategytype ADD VALUE 'GREEKS_ENHANCED';
        ALTER TYPE strategytype ADD VALUE 'ENHANCED_IRON_CONDOR';
        ALTER TYPE strategytype ADD VALUE 'OPTIONS_WHEEL';
    """)


def downgrade():
    """Remove advanced strategy types from the StrategyType enum."""
    
    # Note: PostgreSQL doesn't support removing enum values directly
    # This would require recreating the enum type and updating all references
    # For now, we'll leave the values in place for safety
    
    # If you really need to remove them, you would need to:
    # 1. Create a new enum without the values
    # 2. Update all columns to use the new enum
    # 3. Drop the old enum
    # 4. Rename the new enum to the original name
    
    pass


















