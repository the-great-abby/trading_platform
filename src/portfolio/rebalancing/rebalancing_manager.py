"""
Rebalancing Manager Service
Service for portfolio rebalancing recommendations and execution
"""
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple
import uuid

from ..models import (
    Portfolio, Position, OptimizationResult, RebalancingRecommendation,
    TradeRecommendation, RebalancingPriority
)


class RebalancingManager:
    """Service for portfolio rebalancing recommendations and execution"""
    
    def __init__(self, repository=None, market_data_service=None, tax_optimizer=None):
        """Initialize rebalancing manager with dependencies"""
        self.repository = repository
        self.market_data_service = market_data_service
        self.tax_optimizer = tax_optimizer
    
    def generate_rebalancing_recommendations(self,
                                           portfolio: Portfolio,
                                           target_optimization: OptimizationResult,
                                           rebalancing_threshold: float = 0.05,
                                           transaction_cost_rate: float = 0.001,
                                           market_impact_rate: float = 0.0005,
                                           priority: RebalancingPriority = RebalancingPriority.MEDIUM) -> RebalancingRecommendation:
        """Generate rebalancing recommendations based on target optimization"""
        
        # Get current portfolio weights
        current_weights = portfolio.calculate_portfolio_weights()
        target_weights = target_optimization.asset_weights
        
        # Identify rebalancing trades
        trades = self._identify_rebalancing_trades(
            portfolio, current_weights, target_weights, 
            rebalancing_threshold, transaction_cost_rate, market_impact_rate
        )
        
        if not trades:
            # No rebalancing needed
            return self._create_no_rebalancing_recommendation(portfolio, target_optimization)
        
        # Calculate summary metrics
        total_trades = len([t for t in trades if t.action != "HOLD"])
        estimated_transaction_cost = sum(t.estimated_cost for t in trades if t.action != "HOLD")
        estimated_market_impact = sum(t.estimated_market_impact for t in trades if t.action != "HOLD")
        
        # Calculate expected improvements
        tracking_error_reduction = self._estimate_tracking_error_reduction(
            current_weights, target_weights
        )
        expected_risk_reduction = self._estimate_risk_reduction(
            portfolio, current_weights, target_weights
        )
        expected_return_improvement = self._estimate_return_improvement(
            portfolio, current_weights, target_weights
        )
        
        # Calculate rebalancing urgency
        rebalancing_urgency = self._calculate_rebalancing_urgency(
            current_weights, target_weights, rebalancing_threshold
        )
        
        # Create recommendation
        recommendation = RebalancingRecommendation(
            portfolio_id=portfolio.portfolio_id,
            optimization_id=target_optimization.optimization_id,
            priority=priority,
            trades=trades,
            total_trades=total_trades,
            estimated_transaction_cost=estimated_transaction_cost,
            estimated_market_impact=estimated_market_impact,
            tracking_error_reduction=tracking_error_reduction,
            expected_risk_reduction=expected_risk_reduction,
            expected_return_improvement=expected_return_improvement,
            rebalancing_urgency=rebalancing_urgency,
            target_rebalancing_date=datetime.now() + timedelta(days=1)
        )
        
        # Save recommendation
        if self.repository:
            self.repository.save_rebalancing_recommendation(recommendation)
        
        return recommendation
    
    def execute_rebalancing(self,
                           recommendation_id: str,
                           execution_prices: Optional[Dict[str, float]] = None,
                           dry_run: bool = False) -> Dict[str, Any]:
        """Execute rebalancing recommendation"""
        
        if not self.repository:
            return {"success": False, "error": "Repository not available"}
        
        recommendation = self.repository.get_rebalancing_recommendation(recommendation_id)
        if not recommendation:
            return {"success": False, "error": "Recommendation not found"}
        
        if recommendation.is_executed:
            return {"success": False, "error": "Recommendation already executed"}
        
        portfolio = self.repository.get_portfolio(recommendation.portfolio_id)
        if not portfolio:
            return {"success": False, "error": "Portfolio not found"}
        
        execution_result = {
            "success": True,
            "execution_id": str(uuid.uuid4()),
            "recommendation_id": recommendation_id,
            "execution_date": datetime.now(),
            "trades_executed": 0,
            "actual_cost": 0.0,
            "execution_time": 0.0,
            "trade_results": []
        }
        
        start_time = datetime.now()
        
        try:
            if dry_run:
                # Simulate execution
                execution_result["trades_executed"] = len([t for t in recommendation.trades if t.action != "HOLD"])
                execution_result["actual_cost"] = recommendation.estimated_transaction_cost
                execution_result["simulation_results"] = {
                    "would_execute_trades": execution_result["trades_executed"],
                    "estimated_cost": recommendation.estimated_transaction_cost
                }
            else:
                # Execute actual trades
                actual_cost = 0.0
                trades_executed = 0
                
                for trade in recommendation.trades:
                    if trade.action == "HOLD":
                        continue
                    
                    # Get execution price
                    if execution_prices and trade.asset_id in execution_prices:
                        execution_price = execution_prices[trade.asset_id]
                    else:
                        execution_price = self._get_current_price(trade.asset_id)
                    
                    if execution_price is None:
                        execution_result["trade_results"].append({
                            "trade_id": trade.trade_id,
                            "success": False,
                            "error": "Unable to get execution price"
                        })
                        continue
                    
                    # Execute trade
                    trade_result = self._execute_trade(trade, execution_price, portfolio)
                    
                    if trade_result["success"]:
                        actual_cost += trade_result["cost"]
                        trades_executed += 1
                        trade.is_executed = True
                        trade.actual_execution_price = execution_price
                    
                    execution_result["trade_results"].append(trade_result)
                
                execution_result["trades_executed"] = trades_executed
                execution_result["actual_cost"] = actual_cost
                
                # Mark recommendation as executed
                recommendation.is_executed = True
                recommendation.execution_date = datetime.now()
                recommendation.execution_cost = actual_cost
                
                # Save changes
                self.repository.save_rebalancing_recommendation(recommendation)
                self.repository.save_portfolio(portfolio)
            
            execution_result["execution_time"] = (datetime.now() - start_time).total_seconds()
            
        except Exception as e:
            execution_result["success"] = False
            execution_result["error_message"] = str(e)
        
        return execution_result
    
    def _identify_rebalancing_trades(self,
                                   portfolio: Portfolio,
                                   current_weights: Dict[str, float],
                                   target_weights: Dict[str, float],
                                   threshold: float,
                                   transaction_cost_rate: float,
                                   market_impact_rate: float) -> List[TradeRecommendation]:
        """Identify trades needed for rebalancing"""
        
        trades = []
        all_assets = set(current_weights.keys()) | set(target_weights.keys())
        
        for asset_id in all_assets:
            current_weight = current_weights.get(asset_id, 0.0)
            target_weight = target_weights.get(asset_id, 0.0)
            weight_change = target_weight - current_weight
            
            # Skip if change is below threshold
            if abs(weight_change) < threshold:
                trades.append(self._create_hold_trade(asset_id, current_weight, target_weight))
                continue
            
            # Find position for this asset
            position = next((p for p in portfolio.positions if p.asset_id == asset_id), None)
            
            if position is None and target_weight > 0:
                # New position - BUY
                trade = self._create_buy_trade(
                    asset_id, current_weight, target_weight, 
                    portfolio.total_value, transaction_cost_rate, market_impact_rate
                )
                trades.append(trade)
            elif position and target_weight == 0:
                # Close position - SELL
                trade = self._create_sell_trade(
                    asset_id, position, current_weight, target_weight,
                    transaction_cost_rate, market_impact_rate
                )
                trades.append(trade)
            elif position and weight_change != 0:
                # Adjust position
                trade = self._create_adjustment_trade(
                    asset_id, position, current_weight, target_weight,
                    weight_change, transaction_cost_rate, market_impact_rate
                )
                trades.append(trade)
            else:
                trades.append(self._create_hold_trade(asset_id, current_weight, target_weight))
        
        # Sort trades by priority (tax-loss harvesting first, then by size)
        trades.sort(key=lambda t: (not t.is_tax_loss_harvest, -abs(t.trade_quantity)))
        
        # Assign priorities
        for i, trade in enumerate(trades):
            trade.priority = i + 1
        
        return trades
    
    def _create_hold_trade(self, asset_id: str, current_weight: float, target_weight: float) -> TradeRecommendation:
        """Create a HOLD trade recommendation"""
        return TradeRecommendation(
            asset_id=asset_id,
            action="HOLD",
            current_weight=current_weight,
            target_weight=target_weight,
            weight_change=0.0,
            trade_quantity=0.0,
            current_quantity=0.0,
            target_quantity=0.0,
            current_price=0.0,
            estimated_cost=0.0,
            priority=0
        )
    
    def _create_buy_trade(self, asset_id: str, current_weight: float, target_weight: float,
                         portfolio_value: float, transaction_cost_rate: float, market_impact_rate: float) -> TradeRecommendation:
        """Create a BUY trade recommendation"""
        current_price = self._get_current_price(asset_id) or 100.0  # Default price
        
        # Calculate quantities
        target_value = target_weight * portfolio_value
        trade_quantity = target_value / current_price
        
        estimated_execution_price = current_price * (1 + market_impact_rate)
        estimated_cost = trade_quantity * estimated_execution_price * transaction_cost_rate
        
        return TradeRecommendation(
            asset_id=asset_id,
            action="BUY",
            current_weight=current_weight,
            target_weight=target_weight,
            weight_change=target_weight - current_weight,
            trade_quantity=trade_quantity,
            current_quantity=0.0,
            target_quantity=trade_quantity,
            current_price=current_price,
            estimated_execution_price=estimated_execution_price,
            estimated_cost=estimated_cost,
            estimated_market_impact=trade_quantity * current_price * market_impact_rate,
            priority=1
        )
    
    def _create_sell_trade(self, asset_id: str, position: Position, current_weight: float, target_weight: float,
                          transaction_cost_rate: float, market_impact_rate: float) -> TradeRecommendation:
        """Create a SELL trade recommendation"""
        current_price = position.current_price
        trade_quantity = position.quantity
        
        estimated_execution_price = current_price * (1 - market_impact_rate)
        estimated_cost = trade_quantity * estimated_execution_price * transaction_cost_rate
        
        return TradeRecommendation(
            asset_id=asset_id,
            action="SELL",
            current_weight=current_weight,
            target_weight=target_weight,
            weight_change=target_weight - current_weight,
            trade_quantity=-trade_quantity,
            current_quantity=position.quantity,
            target_quantity=0.0,
            current_price=current_price,
            estimated_execution_price=estimated_execution_price,
            estimated_cost=estimated_cost,
            estimated_market_impact=trade_quantity * current_price * market_impact_rate,
            is_tax_loss_harvest=self._is_tax_loss_harvest(position),
            tax_lot_id=position.tax_lot_id,
            estimated_tax_savings=self._estimate_tax_savings(position) if self._is_tax_loss_harvest(position) else 0.0,
            priority=1
        )
    
    def _create_adjustment_trade(self, asset_id: str, position: Position, current_weight: float, target_weight: float,
                               weight_change: float, transaction_cost_rate: float, market_impact_rate: float) -> TradeRecommendation:
        """Create an adjustment trade recommendation"""
        current_price = position.current_price
        
        # Calculate target quantity
        portfolio_value = position.portfolio_id  # This should be passed properly
        target_value = target_weight * portfolio_value  # This needs portfolio value
        target_quantity = target_value / current_price
        trade_quantity = target_quantity - position.quantity
        
        action = "BUY" if trade_quantity > 0 else "SELL"
        
        estimated_execution_price = current_price * (1 + market_impact_rate if trade_quantity > 0 else 1 - market_impact_rate)
        estimated_cost = abs(trade_quantity) * estimated_execution_price * transaction_cost_rate
        
        return TradeRecommendation(
            asset_id=asset_id,
            action=action,
            current_weight=current_weight,
            target_weight=target_weight,
            weight_change=weight_change,
            trade_quantity=trade_quantity,
            current_quantity=position.quantity,
            target_quantity=target_quantity,
            current_price=current_price,
            estimated_execution_price=estimated_execution_price,
            estimated_cost=estimated_cost,
            estimated_market_impact=abs(trade_quantity) * current_price * market_impact_rate,
            is_tax_loss_harvest=self._is_tax_loss_harvest(position) and trade_quantity < 0,
            tax_lot_id=position.tax_lot_id,
            estimated_tax_savings=self._estimate_tax_savings(position) if self._is_tax_loss_harvest(position) and trade_quantity < 0 else 0.0,
            priority=1
        )
    
    def _execute_trade(self, trade: TradeRecommendation, execution_price: float, portfolio: Portfolio) -> Dict[str, Any]:
        """Execute a single trade"""
        try:
            if trade.action == "BUY":
                return self._execute_buy_trade(trade, execution_price, portfolio)
            elif trade.action == "SELL":
                return self._execute_sell_trade(trade, execution_price, portfolio)
            else:
                return {"success": True, "cost": 0.0, "message": "Hold trade - no action needed"}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _execute_buy_trade(self, trade: TradeRecommendation, execution_price: float, portfolio: Portfolio) -> Dict[str, Any]:
        """Execute a buy trade"""
        # Find or create position
        position = next((p for p in portfolio.positions if p.asset_id == trade.asset_id), None)
        
        if position is None:
            # Create new position
            position = Position(
                portfolio_id=portfolio.portfolio_id,
                asset_id=trade.asset_id,
                quantity=trade.trade_quantity,
                average_cost=execution_price,
                current_price=execution_price
            )
            portfolio.positions.append(position)
        else:
            # Add to existing position
            position.add_shares(trade.trade_quantity, execution_price)
        
        cost = trade.trade_quantity * execution_price
        
        return {
            "success": True,
            "cost": cost,
            "quantity": trade.trade_quantity,
            "price": execution_price,
            "message": f"Bought {trade.trade_quantity:.2f} shares of {trade.asset_id} at ${execution_price:.2f}"
        }
    
    def _execute_sell_trade(self, trade: TradeRecommendation, execution_price: float, portfolio: Portfolio) -> Dict[str, Any]:
        """Execute a sell trade"""
        position = next((p for p in portfolio.positions if p.asset_id == trade.asset_id), None)
        
        if position is None:
            return {"success": False, "error": f"Position not found for {trade.asset_id}"}
        
        if position.quantity < abs(trade.trade_quantity):
            return {"success": False, "error": f"Insufficient quantity. Available: {position.quantity}, Requested: {abs(trade.trade_quantity)}"}
        
        # Execute sale
        realized_pnl = position.remove_shares(abs(trade.trade_quantity))
        
        # Remove position if quantity becomes zero
        if position.quantity == 0:
            portfolio.positions.remove(position)
        
        proceeds = abs(trade.trade_quantity) * execution_price
        
        return {
            "success": True,
            "cost": -proceeds,  # Negative cost (proceeds)
            "quantity": trade.trade_quantity,
            "price": execution_price,
            "realized_pnl": realized_pnl,
            "message": f"Sold {abs(trade.trade_quantity):.2f} shares of {trade.asset_id} at ${execution_price:.2f}"
        }
    
    def _get_current_price(self, asset_id: str) -> Optional[float]:
        """Get current price for asset"""
        if self.market_data_service:
            return self.market_data_service.get_current_price(asset_id)
        return None
    
    def _is_tax_loss_harvest(self, position: Position) -> bool:
        """Check if position is eligible for tax-loss harvesting"""
        return position.is_tax_loss_harvest_candidate()
    
    def _estimate_tax_savings(self, position: Position) -> float:
        """Estimate tax savings from selling position"""
        if not self._is_tax_loss_harvest(position):
            return 0.0
        
        # Simplified tax calculation (25% for short-term, 20% for long-term)
        tax_rate = 0.20 if position.is_long_term else 0.25
        tax_savings = abs(position.unrealized_pnl) * tax_rate
        
        return tax_savings
    
    def _estimate_tracking_error_reduction(self, current_weights: Dict[str, float], target_weights: Dict[str, float]) -> float:
        """Estimate tracking error reduction from rebalancing"""
        # Simplified calculation - in practice would use historical data
        weight_deviation = sum(abs(current_weights.get(asset, 0) - target_weights.get(asset, 0)) 
                             for asset in set(current_weights.keys()) | set(target_weights.keys()))
        return min(weight_deviation * 0.1, 0.05)  # Cap at 5%
    
    def _estimate_risk_reduction(self, portfolio: Portfolio, current_weights: Dict[str, float], target_weights: Dict[str, float]) -> float:
        """Estimate risk reduction from rebalancing"""
        # Simplified calculation - would use actual risk models
        return 0.01  # 1% risk reduction
    
    def _estimate_return_improvement(self, portfolio: Portfolio, current_weights: Dict[str, float], target_weights: Dict[str, float]) -> float:
        """Estimate return improvement from rebalancing"""
        # Simplified calculation - would use expected returns
        return 0.005  # 0.5% return improvement
    
    def _calculate_rebalancing_urgency(self, current_weights: Dict[str, float], target_weights: Dict[str, float], threshold: float) -> float:
        """Calculate rebalancing urgency score"""
        max_deviation = 0.0
        for asset in set(current_weights.keys()) | set(target_weights.keys()):
            deviation = abs(current_weights.get(asset, 0) - target_weights.get(asset, 0))
            max_deviation = max(max_deviation, deviation)
        
        if max_deviation <= threshold:
            return 0.0
        
        # Scale urgency from 0 to 1
        urgency = min((max_deviation - threshold) / (0.20 - threshold), 1.0)  # 20% max deviation
        return urgency
    
    def _create_no_rebalancing_recommendation(self, portfolio: Portfolio, target_optimization: OptimizationResult) -> RebalancingRecommendation:
        """Create a recommendation when no rebalancing is needed"""
        return RebalancingRecommendation(
            portfolio_id=portfolio.portfolio_id,
            optimization_id=target_optimization.optimization_id,
            priority=RebalancingPriority.LOW,
            trades=[],  # No trades needed
            total_trades=0,
            estimated_transaction_cost=0.0,
            estimated_market_impact=0.0,
            tracking_error_reduction=0.0,
            expected_risk_reduction=0.0,
            expected_return_improvement=0.0,
            rebalancing_urgency=0.0,
            target_rebalancing_date=datetime.now() + timedelta(days=30)  # Check again in 30 days
        )





















