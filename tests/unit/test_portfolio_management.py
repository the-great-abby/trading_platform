"""
Portfolio Management Tests

Tests for portfolio management functionality including:
- Position management (buy/sell)
- P&L tracking
- Cash management
- Portfolio summary
- Risk metrics
"""

import pytest
from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, patch

from src.models.portfolio import Portfolio, Position
from src.utils.config import Config


class TestPortfolioInitialization:
    """Test portfolio initialization"""
    
    def test_portfolio_init_defaults(self):
        """Test portfolio initialization with default config"""
        config = Config()
        portfolio = Portfolio(config)
        
        assert portfolio.config == config
        assert portfolio.initial_capital == config.initial_capital
        assert portfolio.cash == config.initial_capital
        assert portfolio.positions == {}
        assert portfolio.trade_history == []
        assert portfolio.total_pnl == 0.0
        assert portfolio.daily_pnl == 0.0
        assert portfolio.max_drawdown == 0.0
        assert portfolio.peak_value == config.initial_capital
    
    def test_portfolio_init_custom_capital(self):
        """Test portfolio initialization with custom capital"""
        config = Config()
        config.initial_capital = 50000.0
        portfolio = Portfolio(config)
        
        assert portfolio.initial_capital == 50000.0
        assert portfolio.cash == 50000.0
        assert portfolio.peak_value == 50000.0


class TestPortfolioProperties:
    """Test portfolio properties"""
    
    @pytest.fixture
    def portfolio(self):
        """Create portfolio fixture"""
        config = Config()
        config.initial_capital = 100000.0
        return Portfolio(config)
    
    def test_total_value_no_positions(self, portfolio):
        """Test total value calculation with no positions"""
        assert portfolio.total_value == 100000.0  # Just cash
    
    def test_total_value_with_positions(self, portfolio):
        """Test total value calculation with positions"""
        # Add a position
        portfolio.positions["AAPL"] = Position(
            symbol="AAPL",
            quantity=100,
            entry_price=150.0,
            current_price=160.0,
            entry_time=datetime.now(),
            strategy="momentum"
        )
        
        expected_value = 100000.0 + (100 * 160.0)  # Cash + position value
        assert portfolio.total_value == expected_value
    
    def test_total_pnl_percentage_no_pnl(self, portfolio):
        """Test P&L percentage with no P&L"""
        assert portfolio.total_pnl_percentage == 0.0
    
    def test_total_pnl_percentage_with_pnl(self, portfolio):
        """Test P&L percentage with positive P&L"""
        portfolio.total_pnl = 5000.0  # 5% gain on 100k
        assert portfolio.total_pnl_percentage == 5.0
    
    def test_total_pnl_percentage_negative(self, portfolio):
        """Test P&L percentage with negative P&L"""
        portfolio.total_pnl = -3000.0  # -3% loss on 100k
        assert portfolio.total_pnl_percentage == -3.0
    
    def test_total_pnl_percentage_zero_capital(self):
        """Test P&L percentage with zero initial capital"""
        config = Config()
        config.initial_capital = 0.0
        portfolio = Portfolio(config)
        portfolio.total_pnl = 1000.0
        
        assert portfolio.total_pnl_percentage == 0.0


class TestPortfolioPositionManagement:
    """Test portfolio position management"""
    
    @pytest.fixture
    def portfolio(self):
        """Create portfolio fixture"""
        config = Config()
        config.initial_capital = 100000.0
        return Portfolio(config)
    
    @pytest.mark.asyncio
    async def test_buy_new_position(self, portfolio):
        """Test buying a new position"""
        trade = {
            "symbol": "AAPL",
            "action": "BUY",
            "quantity": 100,
            "price": 150.0,
            "strategy": "momentum"
        }
        
        await portfolio.update_position(trade)
        
        assert "AAPL" in portfolio.positions
        pos = portfolio.positions["AAPL"]
        assert pos.symbol == "AAPL"
        assert pos.quantity == 100
        assert pos.entry_price == 150.0
        assert pos.current_price == 150.0
        assert pos.strategy == "momentum"
        assert portfolio.cash == 85000.0  # 100k - (100 * 150)
        assert len(portfolio.trade_history) == 1
    
    @pytest.mark.asyncio
    async def test_buy_additional_position(self, portfolio):
        """Test buying additional shares of existing position"""
        # First buy
        trade1 = {
            "symbol": "AAPL",
            "action": "BUY",
            "quantity": 100,
            "price": 150.0,
            "strategy": "momentum"
        }
        await portfolio.update_position(trade1)
        
        # Second buy at different price
        trade2 = {
            "symbol": "AAPL",
            "action": "BUY",
            "quantity": 50,
            "price": 160.0,
            "strategy": "momentum"
        }
        await portfolio.update_position(trade2)
        
        pos = portfolio.positions["AAPL"]
        assert pos.quantity == 150
        # Average price should be (100*150 + 50*160) / 150 = 153.33
        assert pos.entry_price == pytest.approx(153.33, rel=0.01)
        assert portfolio.cash == 77000.0  # 100k - (100*150 + 50*160)
    
    @pytest.mark.asyncio
    async def test_buy_insufficient_cash(self, portfolio):
        """Test buying with insufficient cash"""
        trade = {
            "symbol": "AAPL",
            "action": "BUY",
            "quantity": 1000,
            "price": 150.0,
            "strategy": "momentum"
        }
        
        with pytest.raises(ValueError, match="Insufficient cash"):
            await portfolio.update_position(trade)
    
    @pytest.mark.asyncio
    async def test_sell_partial_position(self, portfolio):
        """Test selling part of a position"""
        # First buy
        buy_trade = {
            "symbol": "AAPL",
            "action": "BUY",
            "quantity": 100,
            "price": 150.0,
            "strategy": "momentum"
        }
        await portfolio.update_position(buy_trade)
        
        # Then sell part
        sell_trade = {
            "symbol": "AAPL",
            "action": "SELL",
            "quantity": 30,
            "price": 160.0,
            "strategy": "momentum"
        }
        await portfolio.update_position(sell_trade)
        
        pos = portfolio.positions["AAPL"]
        assert pos.quantity == 70
        assert pos.pnl == 300.0  # (160-150) * 30
        assert pos.pnl_percentage == pytest.approx(6.67, rel=0.01)  # (160-150)/150 * 100
        assert portfolio.cash == 89800.0  # 85k + (30 * 160)
        assert portfolio.total_pnl == 300.0
        assert portfolio.daily_pnl == 300.0
    
    @pytest.mark.asyncio
    async def test_sell_full_position(self, portfolio):
        """Test selling entire position"""
        # First buy
        buy_trade = {
            "symbol": "AAPL",
            "action": "BUY",
            "quantity": 100,
            "price": 150.0,
            "strategy": "momentum"
        }
        await portfolio.update_position(buy_trade)
        
        # Then sell all
        sell_trade = {
            "symbol": "AAPL",
            "action": "SELL",
            "quantity": 100,
            "price": 160.0,
            "strategy": "momentum"
        }
        await portfolio.update_position(sell_trade)
        
        assert "AAPL" not in portfolio.positions  # Position removed
        assert portfolio.cash == 101000.0  # Original + profit from sale
        assert portfolio.total_pnl == 1000.0  # (160-150) * 100
        assert portfolio.daily_pnl == 1000.0
    
    @pytest.mark.asyncio
    async def test_sell_nonexistent_position(self, portfolio):
        """Test selling a position that doesn't exist"""
        trade = {
            "symbol": "AAPL",
            "action": "SELL",
            "quantity": 100,
            "price": 160.0,
            "strategy": "momentum"
        }
        
        with pytest.raises(ValueError, match="No position in AAPL to sell"):
            await portfolio.update_position(trade)
    
    @pytest.mark.asyncio
    async def test_sell_more_than_owned(self, portfolio):
        """Test selling more shares than owned"""
        # First buy
        buy_trade = {
            "symbol": "AAPL",
            "action": "BUY",
            "quantity": 100,
            "price": 150.0,
            "strategy": "momentum"
        }
        await portfolio.update_position(buy_trade)
        
        # Then try to sell more
        sell_trade = {
            "symbol": "AAPL",
            "action": "SELL",
            "quantity": 150,
            "price": 160.0,
            "strategy": "momentum"
        }
        
        with pytest.raises(ValueError, match="Cannot sell more AAPL than owned"):
            await portfolio.update_position(sell_trade)


class TestPortfolioValuation:
    """Test portfolio valuation updates"""
    
    @pytest.fixture
    def portfolio(self):
        """Create portfolio with positions"""
        config = Config()
        config.initial_capital = 100000.0
        portfolio = Portfolio(config)
        
        # Add some positions
        portfolio.positions["AAPL"] = Position(
            symbol="AAPL",
            quantity=100,
            entry_price=150.0,
            current_price=160.0,
            entry_time=datetime.now(),
            strategy="momentum"
        )
        
        portfolio.positions["GOOGL"] = Position(
            symbol="GOOGL",
            quantity=50,
            entry_price=2800.0,
            current_price=2900.0,
            entry_time=datetime.now(),
            strategy="momentum"
        )
        
        return portfolio
    
    @pytest.mark.asyncio
    async def test_update_valuations(self, portfolio):
        """Test updating position valuations"""
        await portfolio.update_valuations()
        
        aapl_pos = portfolio.positions["AAPL"]
        googl_pos = portfolio.positions["GOOGL"]
        
        assert aapl_pos.pnl == 1000.0  # (160-150) * 100
        assert aapl_pos.pnl_percentage == pytest.approx(6.67, rel=0.01)
        assert googl_pos.pnl == 5000.0  # (2900-2800) * 50
        assert googl_pos.pnl_percentage == pytest.approx(3.57, rel=0.01)
        assert portfolio.total_pnl == 6000.0  # 1000 + 5000


class TestPortfolioSummary:
    """Test portfolio summary functionality"""
    
    @pytest.fixture
    def portfolio(self):
        """Create portfolio with positions"""
        config = Config()
        config.initial_capital = 100000.0
        portfolio = Portfolio(config)
        
        # Add positions
        portfolio.positions["AAPL"] = Position(
            symbol="AAPL",
            quantity=100,
            entry_price=150.0,
            current_price=160.0,
            entry_time=datetime.now(),
            strategy="momentum",
            pnl=1000.0,
            pnl_percentage=6.67
        )
        
        portfolio.positions["GOOGL"] = Position(
            symbol="GOOGL",
            quantity=50,
            entry_price=2800.0,
            current_price=2900.0,
            entry_time=datetime.now(),
            strategy="momentum",
            pnl=5000.0,
            pnl_percentage=3.57
        )
        
        portfolio.total_pnl = 6000.0
        portfolio.daily_pnl = 1000.0
        portfolio.max_drawdown = 0.05
        
        return portfolio
    
    def test_get_portfolio_summary(self, portfolio):
        """Test portfolio summary generation"""
        summary = portfolio.get_portfolio_summary()
        
        assert summary["total_value"] == 100000.0 + (100 * 160) + (50 * 2900)
        assert summary["cash"] == 100000.0
        assert summary["total_pnl"] == 6000.0
        assert summary["total_pnl_percentage"] == 6.0
        assert summary["daily_pnl"] == 1000.0
        assert summary["max_drawdown"] == 0.05
        assert summary["num_positions"] == 2
        
        # Check positions
        positions = summary["positions"]
        assert len(positions) == 2
        
        aapl_pos = next(p for p in positions if p["symbol"] == "AAPL")
        assert aapl_pos["quantity"] == 100
        assert aapl_pos["entry_price"] == 150.0
        assert aapl_pos["current_price"] == 160.0
        assert aapl_pos["pnl"] == 1000.0
        assert aapl_pos["pnl_percentage"] == 6.67
        assert aapl_pos["strategy"] == "momentum"
        
        googl_pos = next(p for p in positions if p["symbol"] == "GOOGL")
        assert googl_pos["quantity"] == 50
        assert googl_pos["entry_price"] == 2800.0
        assert googl_pos["current_price"] == 2900.0
        assert googl_pos["pnl"] == 5000.0
        assert googl_pos["pnl_percentage"] == 3.57
        assert googl_pos["strategy"] == "momentum"


class TestPortfolioRiskMetrics:
    """Test portfolio risk metrics"""
    
    @pytest.fixture
    def portfolio(self):
        """Create portfolio fixture"""
        config = Config()
        config.initial_capital = 100000.0
        return Portfolio(config)
    
    @pytest.mark.asyncio
    async def test_drawdown_calculation(self, portfolio):
        """Test drawdown calculation"""
        # Initial state
        assert portfolio.max_drawdown == 0.0
        assert portfolio.peak_value == 100000.0
        
        # First, buy a position to establish a higher peak value
        buy_trade = {
            "symbol": "AAPL",
            "action": "BUY",
            "quantity": 100,
            "price": 150.0,
            "strategy": "momentum"
        }
        await portfolio.update_position(buy_trade)
        
        # Now sell at a significant loss to trigger drawdown
        sell_trade = {
            "symbol": "AAPL",
            "action": "SELL",
            "quantity": 100,
            "price": 120.0,  # 20% loss
            "strategy": "momentum"
        }
        await portfolio.update_position(sell_trade)
        
        # The drawdown should be calculated during the sell operation
        assert portfolio.max_drawdown > 0.0
        # The drawdown should reflect the loss from the position
        assert portfolio.max_drawdown > 0.01  # At least 1% drawdown
    
    def test_reset_daily_pnl(self, portfolio):
        """Test resetting daily P&L"""
        portfolio.daily_pnl = 1000.0
        portfolio.reset_daily_pnl()
        assert portfolio.daily_pnl == 0.0


class TestPortfolioEdgeCases:
    """Test portfolio edge cases"""
    
    @pytest.fixture
    def portfolio(self):
        """Create portfolio fixture"""
        config = Config()
        config.initial_capital = 100000.0
        return Portfolio(config)
    
    @pytest.mark.asyncio
    async def test_zero_quantity_trade(self, portfolio):
        """Test trade with zero quantity"""
        trade = {
            "symbol": "AAPL",
            "action": "BUY",
            "quantity": 0,
            "price": 150.0,
            "strategy": "momentum"
        }
        
        await portfolio.update_position(trade)
        assert "AAPL" in portfolio.positions  # Position created with zero quantity
        assert portfolio.positions["AAPL"].quantity == 0  # But quantity is zero
        assert portfolio.cash == 100000.0  # Cash unchanged
    
    @pytest.mark.asyncio
    async def test_zero_price_trade(self, portfolio):
        """Test trade with zero price"""
        trade = {
            "symbol": "AAPL",
            "action": "BUY",
            "quantity": 100,
            "price": 0.0,
            "strategy": "momentum"
        }
        
        await portfolio.update_position(trade)
        pos = portfolio.positions["AAPL"]
        assert pos.entry_price == 0.0
        assert pos.current_price == 0.0
        assert portfolio.cash == 100000.0  # No cash spent
    
    def test_total_value_with_zero_price_positions(self, portfolio):
        """Test total value calculation with zero price positions"""
        portfolio.positions["AAPL"] = Position(
            symbol="AAPL",
            quantity=100,
            entry_price=0.0,
            current_price=0.0,
            entry_time=datetime.now(),
            strategy="momentum"
        )
        
        assert portfolio.total_value == 100000.0  # Just cash
    
    def test_pnl_percentage_with_zero_initial_capital(self):
        """Test P&L percentage with zero initial capital"""
        config = Config()
        config.initial_capital = 0.0
        portfolio = Portfolio(config)
        
        assert portfolio.total_pnl_percentage == 0.0


class TestPortfolioIntegration:
    """Test portfolio integration scenarios"""
    
    @pytest.fixture
    def portfolio(self):
        """Create portfolio fixture"""
        config = Config()
        config.initial_capital = 100000.0
        return Portfolio(config)
    
    @pytest.mark.asyncio
    async def test_complete_trading_scenario(self, portfolio):
        """Test complete trading scenario"""
        # Day 1: Buy AAPL
        trade1 = {
            "symbol": "AAPL",
            "action": "BUY",
            "quantity": 100,
            "price": 150.0,
            "strategy": "momentum"
        }
        await portfolio.update_position(trade1)
        
        # Day 2: Buy more AAPL at higher price
        trade2 = {
            "symbol": "AAPL",
            "action": "BUY",
            "quantity": 50,
            "price": 160.0,
            "strategy": "momentum"
        }
        await portfolio.update_position(trade2)
        
        # Day 3: Buy GOOGL
        trade3 = {
            "symbol": "GOOGL",
            "action": "BUY",
            "quantity": 10,
            "price": 2800.0,
            "strategy": "momentum"
        }
        await portfolio.update_position(trade3)
        
        # Day 4: Sell part of AAPL
        trade4 = {
            "symbol": "AAPL",
            "action": "SELL",
            "quantity": 30,
            "price": 170.0,
            "strategy": "momentum"
        }
        await portfolio.update_position(trade4)
        
        # Verify final state
        assert len(portfolio.positions) == 2
        assert "AAPL" in portfolio.positions
        assert "GOOGL" in portfolio.positions
        
        aapl_pos = portfolio.positions["AAPL"]
        assert aapl_pos.quantity == 120  # 100 + 50 - 30
        assert aapl_pos.entry_price == pytest.approx(153.33, rel=0.01)  # Average price
        
        googl_pos = portfolio.positions["GOOGL"]
        assert googl_pos.quantity == 10
        assert googl_pos.entry_price == 2800.0
        
        assert len(portfolio.trade_history) == 4
        assert portfolio.total_pnl > 0  # Should have profit from AAPL sale
    
    @pytest.mark.asyncio
    async def test_portfolio_rebalancing_scenario(self, portfolio):
        """Test portfolio rebalancing scenario"""
        # Initial positions
        portfolio.positions["AAPL"] = Position(
            symbol="AAPL",
            quantity=100,
            entry_price=150.0,
            current_price=180.0,  # 20% gain
            entry_time=datetime.now(),
            strategy="momentum"
        )
        
        portfolio.positions["GOOGL"] = Position(
            symbol="GOOGL",
            quantity=50,
            entry_price=2800.0,
            current_price=2900.0,  # 3.6% gain
            entry_time=datetime.now(),
            strategy="momentum"
        )
        
        # Update valuations
        await portfolio.update_valuations()
        
        # Verify P&L calculations
        aapl_pos = portfolio.positions["AAPL"]
        googl_pos = portfolio.positions["GOOGL"]
        
        assert aapl_pos.pnl == 3000.0  # (180-150) * 100
        assert googl_pos.pnl == 5000.0  # (2900-2800) * 50
        assert portfolio.total_pnl == 8000.0
        
        # Get summary
        summary = portfolio.get_portfolio_summary()
        assert summary["total_pnl"] == 8000.0
        assert summary["total_pnl_percentage"] == 8.0  # 8k on 100k
        assert summary["num_positions"] == 2 