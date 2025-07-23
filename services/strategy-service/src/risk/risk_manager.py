"""
Comprehensive Risk Management System for CQRS Trading Platform
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from decimal import Decimal
import numpy as np
from loguru import logger

from ..core.types import TradeSignal
from ..models.portfolio import Portfolio
from ..utils.config import Config
from ..services.queue.rabbitmq_service import RabbitMQService, JobMessage
from ..utils.dynamic_position_sizing import DynamicPositionSizer


@dataclass
class RiskMetrics:
    """Comprehensive risk metrics"""
    # Portfolio-level metrics
    total_risk_score: float
    var_95: float  # Value at Risk (95%)
    var_99: float  # Value at Risk (99%)
    expected_shortfall: float
    sharpe_ratio: float
    max_drawdown: float
    volatility: float
    beta: float
    
    # Position-level metrics
    concentration_risk: float
    correlation_risk: float
    sector_concentration: Dict[str, float]
    leverage: float
    cash_ratio: float
    
    # Trading metrics
    daily_loss: float
    daily_trades: int
    max_daily_loss_remaining: float
    position_count: int
    avg_position_size: float


@dataclass
class RiskLimits:
    """Risk limits configuration"""
    # Position limits
    max_position_size: float = 0.15  # 15% max per position
    max_sector_concentration: float = 0.30  # 30% max per sector
    max_correlation: float = 0.70  # 70% max correlation
    
    # Portfolio limits
    max_portfolio_leverage: float = 1.5  # 150% max leverage
    min_cash_reserve: float = 0.10  # 10% min cash reserve
    max_drawdown: float = 0.25  # 25% max drawdown
    
    # Trading limits
    max_daily_loss: float = 100.0  # $100 max daily loss
    max_daily_trades: int = 10  # 10 max trades per day
    max_positions: int = 5  # 5 max concurrent positions
    
    # Risk thresholds
    var_limit: float = 0.02  # 2% VaR limit
    volatility_limit: float = 0.30  # 30% volatility limit
    beta_limit: float = 1.5  # 1.5 beta limit


class RiskManager:
    """Comprehensive risk management system with CQRS integration"""
    
    def __init__(self, config: Config):
        self.config = config
        self.rabbitmq = RabbitMQService(config)
        
        # Risk tracking
        self.daily_loss = 0.0
        self.daily_trades = 0
        self.last_reset_date = datetime.now().date()
        self.risk_history: List[Dict[str, Any]] = []
        
        # Position sizing
        self.position_sizer = DynamicPositionSizer()
        
        # Risk limits
        self.risk_limits = RiskLimits()
        
        # Market data cache
        self.market_data_cache: Dict[str, Dict[str, Any]] = {}
        
        # Risk alerts
        self.risk_alerts: List[Dict[str, Any]] = []
        
        logger.info("🚀 Risk Manager initialized with comprehensive risk controls")
    
    async def start(self):
        """Start the risk manager"""
        try:
            logger.info("🛡️ Starting Risk Manager...")
            
            # Connect to RabbitMQ
            await self.rabbitmq.connect()
            
            # Register risk check handler
            self.rabbitmq.register_job_handler('risk_check', self._handle_risk_check)
            
            # Start consuming risk check jobs
            await self.rabbitmq.start_consuming()
            
            logger.info("✅ Risk Manager started successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to start Risk Manager: {e}")
            raise
    
    async def stop(self):
        """Stop the risk manager"""
        await self.rabbitmq.disconnect()
        logger.info("🛑 Risk Manager stopped")
    
    async def validate_signal(self, signal: TradeSignal, portfolio: Portfolio) -> Tuple[bool, Dict[str, Any]]:
        """
        Comprehensive signal validation against risk rules
        
        Returns:
            Tuple[bool, Dict]: (is_valid, risk_assessment)
        """
        try:
            logger.info(f"🔍 Validating signal for {signal.symbol}")
            
            # Calculate comprehensive risk metrics
            risk_metrics = await self._calculate_risk_metrics(portfolio)
            
            # Perform risk checks
            risk_assessment = {
                'signal_id': signal.signal_id,
                'symbol': signal.symbol,
                'timestamp': datetime.now().isoformat(),
                'checks': {},
                'overall_risk_score': 0.0,
                'recommendation': 'reject'
            }
            
            # 1. Daily loss limit check
            daily_loss_check = self._check_daily_loss_limit()
            risk_assessment['checks']['daily_loss'] = {
                'passed': daily_loss_check,
                'current_loss': self.daily_loss,
                'limit': self.risk_limits.max_daily_loss
            }
            
            # 2. Position size check
            position_size_check = self._check_position_size(signal, portfolio)
            risk_assessment['checks']['position_size'] = {
                'passed': position_size_check,
                'position_value': signal.quantity * signal.price,
                'max_allowed': portfolio.total_value * self.risk_limits.max_position_size
            }
            
            # 3. Maximum positions check
            max_positions_check = self._check_max_positions(portfolio)
            risk_assessment['checks']['max_positions'] = {
                'passed': max_positions_check,
                'current_positions': len(portfolio.positions),
                'max_positions': self.risk_limits.max_positions
            }
            
            # 4. Portfolio concentration check
            concentration_check = self._check_concentration(signal, portfolio)
            risk_assessment['checks']['concentration'] = {
                'passed': concentration_check,
                'concentration_risk': risk_metrics.concentration_risk,
                'max_concentration': self.risk_limits.max_sector_concentration
            }
            
            # 5. Correlation check
            correlation_check = self._check_correlation(signal, portfolio)
            risk_assessment['checks']['correlation'] = {
                'passed': correlation_check,
                'correlation_risk': risk_metrics.correlation_risk,
                'max_correlation': self.risk_limits.max_correlation
            }
            
            # 6. Volatility check
            volatility_check = self._check_volatility(signal)
            risk_assessment['checks']['volatility'] = {
                'passed': volatility_check,
                'current_volatility': risk_metrics.volatility,
                'volatility_limit': self.risk_limits.volatility_limit
            }
            
            # 7. VaR check
            var_check = self._check_var(risk_metrics)
            risk_assessment['checks']['var'] = {
                'passed': var_check,
                'var_95': risk_metrics.var_95,
                'var_limit': self.risk_limits.var_limit
            }
            
            # Calculate overall risk score
            passed_checks = sum(1 for check in risk_assessment['checks'].values() if check['passed'])
            total_checks = len(risk_assessment['checks'])
            risk_assessment['overall_risk_score'] = (total_checks - passed_checks) / total_checks
            
            # Determine recommendation
            all_checks_passed = all(check['passed'] for check in risk_assessment['checks'].values())
            risk_assessment['recommendation'] = 'accept' if all_checks_passed else 'reject'
            
            # Log risk assessment
            logger.info(f"📊 Risk assessment for {signal.symbol}: {risk_assessment['recommendation']} (score: {risk_assessment['overall_risk_score']:.2f})")
            
            # Store risk assessment
            self.risk_history.append(risk_assessment)
            
            # Send risk alert if high risk
            if risk_assessment['overall_risk_score'] > 0.5:
                await self._send_risk_alert(risk_assessment)
            
            return all_checks_passed, risk_assessment
            
        except Exception as e:
            logger.error(f"❌ Error validating signal: {e}")
            return False, {'error': str(e)}
    
    async def _handle_risk_check(self, job: JobMessage):
        """Handle risk check job from RabbitMQ"""
        try:
            logger.info(f"🔍 Processing risk check job: {job.job_id}")
            
            # Extract job data
            signal_data = job.payload.get('signal', {})
            portfolio_data = job.payload.get('portfolio', {})
            
            # Create TradeSignal and Portfolio objects
            signal = TradeSignal(**signal_data)
            portfolio = Portfolio(**portfolio_data)
            
            # Perform risk validation
            is_valid, risk_assessment = await self.validate_signal(signal, portfolio)
            
            # Publish result to portfolio update queue
            result_job = JobMessage(
                job_id=str(job.job_id) + "_result",
                job_type='portfolio_update',
                payload={
                    'signal': signal_data,
                    'risk_assessment': risk_assessment,
                    'approved': is_valid,
                    'original_job_id': job.job_id
                },
                priority=job.priority + 1
            )
            
            await self.rabbitmq.publish_job(
                result_job,
                self.rabbitmq.queues['portfolio_update']
            )
            
            logger.info(f"✅ Risk check completed for {signal.symbol}: {'approved' if is_valid else 'rejected'}")
            
        except Exception as e:
            logger.error(f"❌ Error processing risk check job: {e}")
            raise
    
    async def _calculate_risk_metrics(self, portfolio: Portfolio) -> RiskMetrics:
        """Calculate comprehensive risk metrics"""
        try:
            # Basic portfolio metrics
            total_position_value = sum(pos.value for pos in portfolio.positions.values())
            portfolio_value = portfolio.total_value
            cash_ratio = portfolio.cash / portfolio_value if portfolio_value > 0 else 0
            leverage = total_position_value / portfolio_value if portfolio_value > 0 else 0
            
            # Calculate concentration risk (Herfindahl index)
            concentration_risk = 0
            sector_concentration = {}
            
            for position in portfolio.positions.values():
                position_ratio = position.value / portfolio_value if portfolio_value > 0 else 0
                concentration_risk += position_ratio ** 2
                
                # Sector concentration
                sector = position.sector if hasattr(position, 'sector') else 'unknown'
                sector_concentration[sector] = sector_concentration.get(sector, 0) + position_ratio
            
            # Calculate correlation risk (simplified)
            correlation_risk = 0.0
            if len(portfolio.positions) > 1:
                # Simple correlation estimate based on sector overlap
                tech_positions = sum(1 for pos in portfolio.positions.values() 
                                   if getattr(pos, 'sector', '') == 'technology')
                if tech_positions > 1:
                    correlation_risk = (tech_positions - 1) / len(portfolio.positions)
            
            # Calculate volatility (simplified)
            volatility = 0.15  # Default volatility, would be calculated from historical data
            
            # Calculate VaR (simplified)
            var_95 = portfolio_value * 0.02  # 2% VaR
            var_99 = portfolio_value * 0.03  # 3% VaR
            expected_shortfall = portfolio_value * 0.025  # 2.5% expected shortfall
            
            # Calculate Sharpe ratio (simplified)
            sharpe_ratio = 1.2  # Would be calculated from historical returns
            
            # Calculate beta (simplified)
            beta = 1.1  # Would be calculated from market correlation
            
            # Calculate max drawdown (simplified)
            max_drawdown = 0.08  # Would be calculated from historical data
            
            # Calculate average position size
            avg_position_size = total_position_value / len(portfolio.positions) if portfolio.positions else 0
            
            # Calculate overall risk score
            total_risk_score = min(100, (
                concentration_risk * 30 +
                correlation_risk * 20 +
                max(0, leverage - 1) * 25 +
                max(0, 0.1 - cash_ratio) * 15 +
                (self.daily_loss / self.risk_limits.max_daily_loss) * 10
            ))
            
            return RiskMetrics(
                total_risk_score=total_risk_score,
                var_95=var_95,
                var_99=var_99,
                expected_shortfall=expected_shortfall,
                sharpe_ratio=sharpe_ratio,
                max_drawdown=max_drawdown,
                volatility=volatility,
                beta=beta,
                concentration_risk=concentration_risk,
                correlation_risk=correlation_risk,
                sector_concentration=sector_concentration,
                leverage=leverage,
                cash_ratio=cash_ratio,
                daily_loss=self.daily_loss,
                daily_trades=self.daily_trades,
                max_daily_loss_remaining=self.risk_limits.max_daily_loss - self.daily_loss,
                position_count=len(portfolio.positions),
                avg_position_size=avg_position_size
            )
            
        except Exception as e:
            logger.error(f"❌ Error calculating risk metrics: {e}")
            raise
    
    def _check_daily_loss_limit(self) -> bool:
        """Check if daily loss limit is exceeded"""
        current_date = datetime.now().date()
        
        # Reset daily metrics if it's a new day
        if current_date > self.last_reset_date:
            self.daily_loss = 0.0
            self.daily_trades = 0
            self.last_reset_date = current_date
        
        return self.daily_loss <= self.risk_limits.max_daily_loss
    
    def _check_position_size(self, signal: TradeSignal, portfolio: Portfolio) -> bool:
        """Check if position size is within limits"""
        position_value = signal.quantity * signal.price
        max_position_value = portfolio.total_value * self.risk_limits.max_position_size
        
        return position_value <= max_position_value
    
    def _check_max_positions(self, portfolio: Portfolio) -> bool:
        """Check if maximum number of positions is reached"""
        return len(portfolio.positions) < self.risk_limits.max_positions
    
    def _check_concentration(self, signal: TradeSignal, portfolio: Portfolio) -> bool:
        """Check portfolio concentration limits"""
        new_position_value = signal.quantity * signal.price
        total_portfolio_value = portfolio.total_value + new_position_value
        
        # Check if any single position would exceed concentration limit
        return new_position_value / total_portfolio_value <= self.risk_limits.max_sector_concentration
    
    def _check_correlation(self, signal: TradeSignal, portfolio: Portfolio) -> bool:
        """Check correlation limits"""
        # Simplified correlation check
        # In a real implementation, this would calculate actual correlations
        return True  # Placeholder
    
    def _check_volatility(self, signal: TradeSignal) -> bool:
        """Check volatility limits"""
        # Simplified volatility check
        # In a real implementation, this would use actual volatility data
        return True  # Placeholder
    
    def _check_var(self, risk_metrics: RiskMetrics) -> bool:
        """Check VaR limits"""
        return risk_metrics.var_95 <= self.risk_limits.var_limit
    
    async def _send_risk_alert(self, risk_assessment: Dict[str, Any]):
        """Send risk alert notification"""
        try:
            alert_job = JobMessage(
                job_id=f"risk_alert_{datetime.now().timestamp()}",
                job_type='notification',
                payload={
                    'type': 'risk_alert',
                    'risk_assessment': risk_assessment,
                    'timestamp': datetime.now().isoformat(),
                    'priority': 'high' if risk_assessment['overall_risk_score'] > 0.7 else 'medium'
                },
                priority=9  # High priority
            )
            
            await self.rabbitmq.publish_job(
                alert_job,
                self.rabbitmq.queues['notification']
            )
            
            logger.warning(f"🚨 Risk alert sent for {risk_assessment.get('symbol', 'unknown')}")
            
        except Exception as e:
            logger.error(f"❌ Error sending risk alert: {e}")
    
    def update_daily_loss(self, pnl: float):
        """Update daily loss tracking"""
        self.daily_loss += abs(pnl) if pnl < 0 else 0
        self.daily_trades += 1
        
        logger.info(f"📊 Updated daily loss: ${self.daily_loss:.2f} (${self.risk_limits.max_daily_loss - self.daily_loss:.2f} remaining)")
    
    def get_risk_metrics(self) -> Dict[str, Any]:
        """Get current risk metrics"""
        return {
            "daily_loss": self.daily_loss,
            "daily_trades": self.daily_trades,
            "max_daily_loss": self.risk_limits.max_daily_loss,
            "daily_loss_remaining": self.risk_limits.max_daily_loss - self.daily_loss,
            "risk_history_count": len(self.risk_history),
            "risk_alerts_count": len(self.risk_alerts)
        }
    
    async def publish_risk_check(self, signal: TradeSignal, portfolio: Portfolio) -> bool:
        """Publish risk check job to RabbitMQ"""
        try:
            risk_check_job = JobMessage(
                job_id=f"risk_check_{signal.signal_id}",
                job_type='risk_check',
                payload={
                    'signal': {
                        'signal_id': signal.signal_id,
                        'symbol': signal.symbol,
                        'action': signal.action,
                        'quantity': signal.quantity,
                        'price': signal.price,
                        'strategy': signal.strategy,
                        'confidence': signal.confidence,
                        'metadata': signal.metadata
                    },
                    'portfolio': {
                        'total_value': portfolio.total_value,
                        'cash': portfolio.cash,
                        'positions': {symbol: {
                            'quantity': pos.quantity,
                            'avg_price': pos.avg_price,
                            'value': pos.value,
                            'sector': getattr(pos, 'sector', 'unknown')
                        } for symbol, pos in portfolio.positions.items()}
                    }
                },
                priority=8  # High priority for risk checks
            )
            
            success = await self.rabbitmq.publish_job(
                risk_check_job,
                self.rabbitmq.queues['risk_check']
            )
            
            if success:
                logger.info(f"✅ Risk check job published for {signal.symbol}")
            else:
                logger.error(f"❌ Failed to publish risk check job for {signal.symbol}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Error publishing risk check job: {e}")
            return False 