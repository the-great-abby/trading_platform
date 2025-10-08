"""
Tax Optimizer Service
Service for tax-loss harvesting and tax-aware portfolio optimization
"""
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple
import uuid

from ..models import Portfolio, Position, RebalancingRecommendation


class TaxOptimizer:
    """Service for tax optimization and loss harvesting"""
    
    def __init__(self, repository=None, market_data_service=None):
        """Initialize tax optimizer with dependencies"""
        self.repository = repository
        self.market_data_service = market_data_service
    
    def identify_tax_loss_harvesting(self,
                                   portfolio: Portfolio,
                                   min_loss_threshold: float = 0.05,
                                   wash_sale_period: int = 30,
                                   max_tracking_error: float = 0.02) -> List[Dict[str, Any]]:
        """Identify tax-loss harvesting opportunities"""
        
        opportunities = []
        
        for position in portfolio.positions:
            if self._is_tax_loss_candidate(position, min_loss_threshold, wash_sale_period):
                # Find replacement asset
                replacement_asset = self._find_replacement_asset(
                    position, portfolio, max_tracking_error
                )
                
                if replacement_asset:
                    tax_savings = self._calculate_tax_savings(position)
                    tracking_error_risk = self._estimate_tracking_error(position, replacement_asset)
                    
                    opportunity = {
                        "asset_id": position.asset_id,
                        "unrealized_loss": position.unrealized_pnl,
                        "unrealized_loss_pct": position.unrealized_pnl_pct,
                        "estimated_tax_savings": tax_savings,
                        "replacement_asset_id": replacement_asset,
                        "tracking_error_risk": tracking_error_risk,
                        "wash_sale_period_compliant": True,
                        "position": position
                    }
                    
                    opportunities.append(opportunity)
        
        # Sort by tax savings potential
        opportunities.sort(key=lambda x: x["estimated_tax_savings"], reverse=True)
        
        return opportunities
    
    def execute_tax_loss_harvesting(self,
                                   portfolio: Portfolio,
                                   opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """Execute tax-loss harvesting trade"""
        
        position = opportunity["position"]
        replacement_asset = opportunity["replacement_asset_id"]
        
        try:
            # Execute sale of losing position
            sale_result = self._execute_sale(position, portfolio)
            
            # Execute purchase of replacement asset
            purchase_result = self._execute_replacement_purchase(
                replacement_asset, position, portfolio
            )
            
            # Calculate actual tax savings
            actual_tax_savings = self._calculate_tax_savings(position)
            
            # Calculate tracking error
            tracking_error = self._estimate_tracking_error(position, replacement_asset)
            
            return {
                "success": True,
                "tax_savings": actual_tax_savings,
                "tracking_error": tracking_error,
                "sale_result": sale_result,
                "purchase_result": purchase_result,
                "wash_sale_compliance": True
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def optimize_tax_aware_rebalancing(self,
                                     portfolio: Portfolio,
                                     target_weights: Dict[str, float],
                                     tax_rates: Dict[str, float] = None) -> Dict[str, Any]:
        """Optimize rebalancing with tax considerations"""
        
        if tax_rates is None:
            tax_rates = {"short_term": 0.25, "long_term": 0.20}
        
        # Identify tax-loss harvesting opportunities first
        tax_opportunities = self.identify_tax_loss_harvesting(portfolio)
        
        # Calculate current weights
        current_weights = portfolio.calculate_portfolio_weights()
        
        # Create tax-aware rebalancing plan
        recommended_trades = []
        total_tax_cost = 0.0
        total_tax_savings = 0.0
        
        for asset_id in set(current_weights.keys()) | set(target_weights.keys()):
            current_weight = current_weights.get(asset_id, 0.0)
            target_weight = target_weights.get(asset_id, 0.0)
            weight_change = target_weight - current_weight
            
            if abs(weight_change) < 0.01:  # Skip small changes
                continue
            
            position = next((p for p in portfolio.positions if p.asset_id == asset_id), None)
            
            if position:
                # Calculate tax implications
                if weight_change < 0:  # Selling
                    tax_cost = self._calculate_tax_cost(position, abs(weight_change), tax_rates)
                    total_tax_cost += tax_cost
                    
                    # Check if this is a tax-loss harvesting opportunity
                    is_tax_loss = self._is_tax_loss_candidate(position)
                    if is_tax_loss:
                        tax_savings = self._calculate_tax_savings(position)
                        total_tax_savings += tax_savings
                
                # Create trade recommendation
                trade = {
                    "asset_id": asset_id,
                    "action": "SELL" if weight_change < 0 else "BUY",
                    "weight_change": weight_change,
                    "tax_cost": tax_cost if weight_change < 0 else 0.0,
                    "tax_savings": tax_savings if is_tax_loss else 0.0,
                    "is_tax_loss_harvest": is_tax_loss
                }
                recommended_trades.append(trade)
        
        # Calculate net tax impact
        net_tax_impact = total_tax_cost - total_tax_savings
        
        return {
            "recommended_trades": recommended_trades,
            "total_tax_cost": total_tax_cost,
            "total_tax_savings": total_tax_savings,
            "net_tax_impact": net_tax_impact,
            "tax_opportunities": len(tax_opportunities)
        }
    
    def check_wash_sale_violations(self,
                                 portfolio: Portfolio,
                                 recent_purchases: List[Dict[str, Any]],
                                 wash_sale_period: int = 30) -> List[Dict[str, Any]]:
        """Check for wash sale rule violations"""
        
        violations = []
        cutoff_date = datetime.now() - timedelta(days=wash_sale_period)
        
        for position in portfolio.positions:
            # Check recent purchases of the same asset
            for purchase in recent_purchases:
                if (purchase["asset_id"] == position.asset_id and 
                    purchase["purchase_date"] > cutoff_date):
                    
                    violation = {
                        "asset_id": position.asset_id,
                        "violation_type": "recent_purchase",
                        "violation_date": purchase["purchase_date"],
                        "days_remaining": (purchase["purchase_date"] + timedelta(days=wash_sale_period) - datetime.now()).days,
                        "position": position,
                        "purchase": purchase
                    }
                    violations.append(violation)
        
        return violations
    
    def get_tax_lots(self, portfolio_id: str) -> List[Dict[str, Any]]:
        """Get tax lots for portfolio"""
        
        if not self.repository:
            return []
        
        portfolio = self.repository.get_portfolio(portfolio_id)
        if not portfolio:
            return []
        
        tax_lots = []
        for position in portfolio.positions:
            tax_lot = position.get_tax_lot_info()
            tax_lot["position_id"] = position.position_id
            tax_lot["market_value"] = position.market_value
            tax_lots.append(tax_lot)
        
        return tax_lots
    
    def _is_tax_loss_candidate(self, position: Position, min_loss_threshold: float = 0.05, wash_sale_period: int = 30) -> bool:
        """Check if position is a tax-loss harvesting candidate"""
        
        # Must have unrealized loss
        if position.unrealized_pnl >= 0:
            return False
        
        # Loss must exceed threshold
        if abs(position.unrealized_pnl_pct) < min_loss_threshold:
            return False
        
        # Check wash sale compliance
        if not self._check_wash_sale_compliance(position, wash_sale_period):
            return False
        
        return True
    
    def _check_wash_sale_compliance(self, position: Position, wash_sale_period: int) -> bool:
        """Check wash sale rule compliance"""
        
        if not position.last_sale_date:
            return True
        
        # Check if last sale was within wash sale period
        cutoff_date = datetime.now() - timedelta(days=wash_sale_period)
        return position.last_sale_date < cutoff_date
    
    def _find_replacement_asset(self, position: Position, portfolio: Portfolio, max_tracking_error: float) -> Optional[str]:
        """Find suitable replacement asset for tax-loss harvesting"""
        
        if not self.market_data_service:
            return None
        
        # Get similar assets (same sector, similar characteristics)
        similar_assets = self.market_data_service.get_similar_assets(
            position.asset_id, portfolio.positions
        )
        
        for asset_id in similar_assets:
            tracking_error = self._estimate_tracking_error(position, asset_id)
            if tracking_error <= max_tracking_error:
                return asset_id
        
        return None
    
    def _estimate_tracking_error(self, position: Position, replacement_asset: str) -> float:
        """Estimate tracking error between position and replacement asset"""
        
        if not self.market_data_service:
            return 0.02  # Default 2% tracking error
        
        try:
            correlation = self.market_data_service.get_correlation(
                position.asset_id, replacement_asset
            )
            
            # Higher correlation = lower tracking error
            tracking_error = 0.05 * (1 - correlation)  # Scale correlation to tracking error
            return min(tracking_error, 0.10)  # Cap at 10%
            
        except Exception:
            return 0.05  # Default 5% tracking error
    
    def _calculate_tax_savings(self, position: Position) -> float:
        """Calculate tax savings from selling losing position"""
        
        if position.unrealized_pnl >= 0:
            return 0.0
        
        # Tax rate based on holding period
        tax_rate = 0.20 if position.is_long_term else 0.25
        
        # Tax savings = loss amount * tax rate
        tax_savings = abs(position.unrealized_pnl) * tax_rate
        
        return tax_savings
    
    def _calculate_tax_cost(self, position: Position, weight_change: float, tax_rates: Dict[str, float]) -> float:
        """Calculate tax cost of selling position"""
        
        if position.unrealized_pnl <= 0:
            return 0.0  # No tax on losses
        
        # Calculate amount being sold
        sale_amount = weight_change * position.market_value
        
        # Tax rate based on holding period
        tax_rate = tax_rates.get("long_term" if position.is_long_term else "short_term", 0.25)
        
        # Tax cost = gain amount * tax rate
        gain_percentage = position.unrealized_pnl / position.cost_basis
        tax_cost = sale_amount * gain_percentage * tax_rate
        
        return tax_cost
    
    def _execute_sale(self, position: Position, portfolio: Portfolio) -> Dict[str, Any]:
        """Execute sale of position"""
        
        try:
            # Calculate realized P&L
            realized_pnl = position.close_position()
            
            # Remove from portfolio
            portfolio.positions.remove(position)
            
            # Update portfolio value
            portfolio.total_value = portfolio.calculate_total_value()
            
            return {
                "success": True,
                "realized_pnl": realized_pnl,
                "message": f"Sold {position.asset_id} for tax-loss harvesting"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _execute_replacement_purchase(self, replacement_asset: str, original_position: Position, portfolio: Portfolio) -> Dict[str, Any]:
        """Execute purchase of replacement asset"""
        
        try:
            # Calculate purchase amount (same as original position value)
            purchase_amount = original_position.market_value
            
            # Get current price
            current_price = self._get_current_price(replacement_asset)
            if current_price is None:
                raise ValueError(f"Unable to get price for {replacement_asset}")
            
            # Calculate quantity
            quantity = purchase_amount / current_price
            
            # Create new position
            new_position = Position(
                portfolio_id=portfolio.portfolio_id,
                asset_id=replacement_asset,
                quantity=quantity,
                average_cost=current_price,
                current_price=current_price
            )
            
            portfolio.positions.append(new_position)
            
            # Update portfolio value
            portfolio.total_value = portfolio.calculate_total_value()
            
            return {
                "success": True,
                "quantity": quantity,
                "price": current_price,
                "message": f"Purchased {replacement_asset} as replacement"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _get_current_price(self, asset_id: str) -> Optional[float]:
        """Get current price for asset"""
        if self.market_data_service:
            return self.market_data_service.get_current_price(asset_id)
        return None























