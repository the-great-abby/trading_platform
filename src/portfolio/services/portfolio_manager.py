"""
Portfolio Manager Service
Core service for portfolio management operations
"""
from datetime import datetime
from typing import List, Dict, Any, Optional
import uuid
from dataclasses import asdict

from ..models import (
    Portfolio, Position, Asset, OptimizationResult, MarketView,
    RebalancingRecommendation, RiskMetrics,
    PortfolioStatus, RiskTolerance, RebalancingFrequency
)


class PortfolioManager:
    """Core service for portfolio management operations"""
    
    def __init__(self, repository=None, market_data_service=None):
        """Initialize portfolio manager with dependencies"""
        self.repository = repository
        self.market_data_service = market_data_service
    
    def create_portfolio(self, 
                        name: str,
                        description: str = "",
                        owner_id: str = "",
                        base_currency: str = "USD",
                        risk_tolerance: RiskTolerance = RiskTolerance.MODERATE,
                        rebalancing_frequency: RebalancingFrequency = RebalancingFrequency.MONTHLY,
                        max_single_asset_weight: float = 0.10,
                        max_sector_weight: float = 0.30,
                        long_only: bool = True,
                        **kwargs) -> Portfolio:
        """Create a new portfolio"""
        
        portfolio = Portfolio(
            name=name,
            description=description,
            owner_id=owner_id,
            base_currency=base_currency,
            risk_tolerance=risk_tolerance,
            rebalancing_frequency=rebalancing_frequency,
            max_single_asset_weight=max_single_asset_weight,
            max_sector_weight=max_sector_weight,
            long_only=long_only,
            **kwargs
        )
        
        # Save to repository if available
        if self.repository:
            self.repository.save_portfolio(portfolio)
        
        return portfolio
    
    def get_portfolio(self, portfolio_id: str) -> Optional[Portfolio]:
        """Get portfolio by ID"""
        if not self.repository:
            return None
        
        return self.repository.get_portfolio(portfolio_id)
    
    def get_portfolios(self, owner_id: str = None, status: PortfolioStatus = None) -> List[Portfolio]:
        """Get portfolios with optional filtering"""
        if not self.repository:
            return []
        
        return self.repository.get_portfolios(owner_id=owner_id, status=status)
    
    def update_portfolio(self, portfolio_id: str, updates: Dict[str, Any]) -> Optional[Portfolio]:
        """Update portfolio with new values"""
        portfolio = self.get_portfolio(portfolio_id)
        if not portfolio:
            return None
        
        # Update allowed fields
        allowed_fields = [
            'name', 'description', 'risk_tolerance', 'rebalancing_frequency',
            'max_single_asset_weight', 'max_sector_weight', 'long_only'
        ]
        
        for field, value in updates.items():
            if field in allowed_fields and hasattr(portfolio, field):
                setattr(portfolio, field, value)
        
        portfolio.update_last_modified()
        
        if self.repository:
            self.repository.save_portfolio(portfolio)
        
        return portfolio
    
    def delete_portfolio(self, portfolio_id: str) -> bool:
        """Delete portfolio"""
        if not self.repository:
            return False
        
        return self.repository.delete_portfolio(portfolio_id)
    
    def add_position(self, 
                    portfolio_id: str,
                    asset_id: str,
                    quantity: float,
                    average_cost: float,
                    current_price: Optional[float] = None) -> Optional[Position]:
        """Add position to portfolio"""
        portfolio = self.get_portfolio(portfolio_id)
        if not portfolio:
            return None
        
        # Get current price if not provided
        if current_price is None and self.market_data_service:
            current_price = self.market_data_service.get_current_price(asset_id)
        
        if current_price is None:
            current_price = average_cost
        
        # Create position
        position = Position(
            portfolio_id=portfolio_id,
            asset_id=asset_id,
            quantity=quantity,
            average_cost=average_cost,
            current_price=current_price
        )
        
        # Add to portfolio
        portfolio.positions.append(position)
        
        # Update portfolio value
        portfolio.total_value = portfolio.calculate_total_value()
        
        # Save changes
        if self.repository:
            self.repository.save_portfolio(portfolio)
            self.repository.save_position(position)
        
        return position
    
    def update_position_price(self, position_id: str, new_price: float) -> Optional[Position]:
        """Update position price and recalculate metrics"""
        if not self.repository:
            return None
        
        position = self.repository.get_position(position_id)
        if not position:
            return None
        
        position.update_price(new_price)
        
        # Update portfolio
        portfolio = self.get_portfolio(position.portfolio_id)
        if portfolio:
            portfolio.total_value = portfolio.calculate_total_value()
            
            if self.repository:
                self.repository.save_portfolio(portfolio)
                self.repository.save_position(position)
        
        return position
    
    def remove_position(self, position_id: str) -> bool:
        """Remove position from portfolio"""
        if not self.repository:
            return False
        
        position = self.repository.get_position(position_id)
        if not position:
            return False
        
        portfolio = self.get_portfolio(position.portfolio_id)
        if portfolio:
            # Remove from portfolio
            portfolio.positions = [p for p in portfolio.positions if p.position_id != position_id]
            portfolio.total_value = portfolio.calculate_total_value()
            
            if self.repository:
                self.repository.save_portfolio(portfolio)
                self.repository.delete_position(position_id)
        
        return True
    
    def get_portfolio_positions(self, portfolio_id: str) -> List[Position]:
        """Get all positions for a portfolio"""
        portfolio = self.get_portfolio(portfolio_id)
        if not portfolio:
            return []
        
        return portfolio.positions
    
    def calculate_portfolio_performance(self, portfolio_id: str) -> Dict[str, Any]:
        """Calculate comprehensive portfolio performance metrics"""
        portfolio = self.get_portfolio(portfolio_id)
        if not portfolio:
            return {}
        
        # Update all position prices
        if self.market_data_service:
            for position in portfolio.positions:
                current_price = self.market_data_service.get_current_price(position.asset_id)
                if current_price:
                    position.update_price(current_price)
        
        # Recalculate portfolio value
        portfolio.total_value = portfolio.calculate_total_value()
        
        # Calculate performance metrics
        total_invested = sum(pos.cost_basis for pos in portfolio.positions)
        total_unrealized_pnl = sum(pos.unrealized_pnl for pos in portfolio.positions)
        
        portfolio.total_invested = total_invested
        portfolio.unrealized_pnl = total_unrealized_pnl
        
        if total_invested > 0:
            portfolio.total_return = total_unrealized_pnl / total_invested
        
        # Calculate weights
        weights = portfolio.calculate_portfolio_weights()
        for position in portfolio.positions:
            position.weight = weights.get(position.asset_id, 0.0)
        
        # Save updated portfolio
        if self.repository:
            self.repository.save_portfolio(portfolio)
        
        return {
            "total_value": portfolio.total_value,
            "total_invested": portfolio.total_invested,
            "unrealized_pnl": portfolio.unrealized_pnl,
            "total_return": portfolio.total_return,
            "positions": [pos.to_dict() for pos in portfolio.positions],
            "weights": weights
        }
    
    def add_market_view(self, market_view: MarketView) -> MarketView:
        """Add market view to portfolio"""
        portfolio = self.get_portfolio(market_view.portfolio_id)
        if not portfolio:
            raise ValueError(f"Portfolio {market_view.portfolio_id} not found")
        
        # Validate view
        market_view.validate_market_view()
        
        # Save view
        if self.repository:
            self.repository.save_market_view(market_view)
        
        return market_view
    
    def get_market_views(self, portfolio_id: str, active_only: bool = True) -> List[MarketView]:
        """Get market views for portfolio"""
        if not self.repository:
            return []
        
        views = self.repository.get_market_views(portfolio_id)
        
        if active_only:
            views = [view for view in views if view.is_valid()]
        
        return views
    
    def get_optimization_results(self, portfolio_id: str) -> List[OptimizationResult]:
        """Get optimization results for portfolio"""
        if not self.repository:
            return []
        
        return self.repository.get_optimization_results(portfolio_id)
    
    def get_rebalancing_recommendations(self, portfolio_id: str) -> List[RebalancingRecommendation]:
        """Get rebalancing recommendations for portfolio"""
        if not self.repository:
            return []
        
        return self.repository.get_rebalancing_recommendations(portfolio_id)
    
    def get_risk_metrics(self, portfolio_id: str) -> Optional[RiskMetrics]:
        """Get latest risk metrics for portfolio"""
        if not self.repository:
            return None
        
        return self.repository.get_latest_risk_metrics(portfolio_id)
    
    def validate_portfolio_constraints(self, portfolio_id: str) -> List[str]:
        """Validate portfolio constraints and return violations"""
        portfolio = self.get_portfolio(portfolio_id)
        if not portfolio:
            return ["Portfolio not found"]
        
        violations = portfolio.check_constraints()
        
        # Additional validations
        if not portfolio.validate_weights():
            violations.append("Portfolio weights do not sum to 1.0")
        
        # Check for duplicate assets
        asset_ids = [pos.asset_id for pos in portfolio.positions]
        if len(asset_ids) != len(set(asset_ids)):
            violations.append("Duplicate assets found in portfolio")
        
        return violations
    
    def get_portfolio_summary(self, portfolio_id: str) -> Dict[str, Any]:
        """Get comprehensive portfolio summary"""
        portfolio = self.get_portfolio(portfolio_id)
        if not portfolio:
            return {}
        
        # Calculate current performance
        performance = self.calculate_portfolio_performance(portfolio_id)
        
        # Get optimization results
        optimization_results = self.get_optimization_results(portfolio_id)
        latest_optimization = optimization_results[-1] if optimization_results else None
        
        # Get rebalancing recommendations
        recommendations = self.get_rebalancing_recommendations(portfolio_id)
        pending_recommendations = [r for r in recommendations if not r.is_executed]
        
        # Get risk metrics
        risk_metrics = self.get_risk_metrics(portfolio_id)
        
        # Get market views
        market_views = self.get_market_views(portfolio_id, active_only=True)
        
        return {
            "portfolio": portfolio.to_dict(),
            "performance": performance,
            "latest_optimization": latest_optimization.to_dict() if latest_optimization else None,
            "pending_rebalancing": len(pending_recommendations),
            "risk_metrics": risk_metrics.to_dict() if risk_metrics else None,
            "active_views": len(market_views),
            "constraint_violations": self.validate_portfolio_constraints(portfolio_id)
        }

