"""
Risk Management Worker - Processes risk management jobs from RabbitMQ
"""

import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import logging
from loguru import logger

from ..queue.rabbitmq_service import JobMessage, RabbitMQService
from ...risk.risk_manager import RiskManager
from ...utils.config import Config
from ...utils.risk_config import get_risk_config, RiskProfile
from ...core.types import TradeSignal
from ...models.portfolio import Portfolio


class RiskWorker:
    """Worker for processing risk management jobs"""
    
    def __init__(self, config: Config, risk_profile: RiskProfile = RiskProfile.MODERATE):
        self.config = config
        self.risk_profile = risk_profile
        self.rabbitmq = RabbitMQService(config)
        self.risk_manager = RiskManager(config)
        self.risk_config = get_risk_config(risk_profile, config.get('ACCOUNT_SIZE', 1000.0))
        self.is_running = False
        
        # Job handlers
        self.job_handlers = {
            'risk_check': self._handle_risk_check,
            'portfolio_risk_assessment': self._handle_portfolio_risk_assessment,
            'position_risk_check': self._handle_position_risk_check,
            'stress_test': self._handle_stress_test,
            'risk_alert': self._handle_risk_alert,
            'risk_metrics_update': self._handle_risk_metrics_update
        }
        
        logger.info(f"🚀 Risk Worker initialized with {risk_profile.value} risk profile")
        
    async def start(self):
        """Start the risk worker"""
        try:
            logger.info("🛡️ Starting Risk Worker...")
            
            # Connect to RabbitMQ
            await self.rabbitmq.connect()
            
            # Register job handlers
            for job_type, handler in self.job_handlers.items():
                self.rabbitmq.register_job_handler(job_type, handler)
            
            # Start consuming jobs
            await self.rabbitmq.start_consuming()
            
            self.is_running = True
            logger.info("✅ Risk Worker started successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to start Risk Worker: {e}")
            raise
    
    async def stop(self):
        """Stop the risk worker"""
        self.is_running = False
        await self.rabbitmq.disconnect()
        logger.info("🛑 Risk Worker stopped")
    
    async def _handle_risk_check(self, job: JobMessage):
        """Handle risk check job"""
        try:
            logger.info(f"🔍 Processing risk check job: {job.job_id}")
            
            # Extract job parameters
            signal_data = job.payload.get('signal', {})
            portfolio_data = job.payload.get('portfolio', {})
            market_conditions = job.payload.get('market_conditions', {})
            
            # Create TradeSignal and Portfolio objects
            signal = TradeSignal(**signal_data)
            portfolio = Portfolio(**portfolio_data)
            
            # Perform comprehensive risk validation
            is_valid, risk_assessment = await self.risk_manager.validate_signal(signal, portfolio)
            
            # Add market condition adjustments
            if market_conditions:
                adjusted_position_size = self.risk_config.get_adjusted_position_size(
                    signal.quantity, market_conditions
                )
                risk_assessment['market_adjustments'] = {
                    'original_position_size': signal.quantity,
                    'adjusted_position_size': adjusted_position_size,
                    'market_conditions': market_conditions
                }
            
            # Publish result to portfolio update queue
            result_job = JobMessage(
                job_id=f"{job.job_id}_result",
                job_type='portfolio_update',
                payload={
                    'signal': signal_data,
                    'risk_assessment': risk_assessment,
                    'approved': is_valid,
                    'original_job_id': job.job_id,
                    'risk_profile': self.risk_profile.value
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
    
    async def _handle_portfolio_risk_assessment(self, job: JobMessage):
        """Handle portfolio risk assessment job"""
        try:
            logger.info(f"📊 Processing portfolio risk assessment job: {job.job_id}")
            
            # Extract portfolio data
            portfolio_data = job.payload.get('portfolio', {})
            portfolio = Portfolio(**portfolio_data)
            
            # Calculate comprehensive risk metrics
            risk_metrics = await self.risk_manager._calculate_risk_metrics(portfolio)
            
            # Generate risk report
            risk_report = {
                'portfolio_id': portfolio_data.get('portfolio_id', 'unknown'),
                'timestamp': datetime.now().isoformat(),
                'risk_metrics': {
                    'total_risk_score': risk_metrics.total_risk_score,
                    'var_95': risk_metrics.var_95,
                    'var_99': risk_metrics.var_99,
                    'expected_shortfall': risk_metrics.expected_shortfall,
                    'sharpe_ratio': risk_metrics.sharpe_ratio,
                    'max_drawdown': risk_metrics.max_drawdown,
                    'volatility': risk_metrics.volatility,
                    'beta': risk_metrics.beta,
                    'concentration_risk': risk_metrics.concentration_risk,
                    'correlation_risk': risk_metrics.correlation_risk,
                    'sector_concentration': risk_metrics.sector_concentration,
                    'leverage': risk_metrics.leverage,
                    'cash_ratio': risk_metrics.cash_ratio,
                    'daily_loss': risk_metrics.daily_loss,
                    'daily_trades': risk_metrics.daily_trades,
                    'position_count': risk_metrics.position_count,
                    'avg_position_size': risk_metrics.avg_position_size
                },
                'risk_limits': self.risk_config.to_dict(),
                'recommendations': self._generate_risk_recommendations(risk_metrics)
            }
            
            # Publish risk report to notification queue
            report_job = JobMessage(
                job_id=f"{job.job_id}_report",
                job_type='notification',
                payload={
                    'type': 'portfolio_risk_report',
                    'risk_report': risk_report,
                    'priority': 'medium'
                },
                priority=job.priority
            )
            
            await self.rabbitmq.publish_job(
                report_job,
                self.rabbitmq.queues['notification']
            )
            
            logger.info(f"✅ Portfolio risk assessment completed for {risk_report['portfolio_id']}")
            
        except Exception as e:
            logger.error(f"❌ Error processing portfolio risk assessment: {e}")
            raise
    
    async def _handle_position_risk_check(self, job: JobMessage):
        """Handle position-specific risk check"""
        try:
            logger.info(f"📈 Processing position risk check job: {job.job_id}")
            
            # Extract position data
            position_data = job.payload.get('position', {})
            portfolio_data = job.payload.get('portfolio', {})
            
            symbol = position_data.get('symbol', 'UNKNOWN')
            quantity = position_data.get('quantity', 0)
            price = position_data.get('price', 0)
            portfolio_value = portfolio_data.get('total_value', 0)
            
            # Calculate position risk metrics
            position_value = quantity * price
            position_ratio = position_value / portfolio_value if portfolio_value > 0 else 0
            
            # Check against risk limits
            max_position_ratio = self.risk_config.position_limits.max_position_size
            max_position_value = self.risk_config.position_limits.max_position_value
            
            is_acceptable = position_ratio <= max_position_ratio and position_value <= max_position_value
            
            risk_level = "high" if position_ratio > max_position_ratio * 0.8 else "medium" if position_ratio > max_position_ratio * 0.5 else "low"
            
            position_risk_assessment = {
                'symbol': symbol,
                'position_value': position_value,
                'position_ratio': position_ratio,
                'max_allowed_ratio': max_position_ratio,
                'max_allowed_value': max_position_value,
                'is_acceptable': is_acceptable,
                'risk_level': risk_level,
                'recommendation': 'reject' if not is_acceptable else 'accept',
                'timestamp': datetime.now().isoformat()
            }
            
            # Publish position risk assessment
            assessment_job = JobMessage(
                job_id=f"{job.job_id}_assessment",
                job_type='notification',
                payload={
                    'type': 'position_risk_assessment',
                    'position_risk': position_risk_assessment,
                    'priority': 'high' if risk_level == 'high' else 'medium'
                },
                priority=job.priority
            )
            
            await self.rabbitmq.publish_job(
                assessment_job,
                self.rabbitmq.queues['notification']
            )
            
            logger.info(f"✅ Position risk check completed for {symbol}: {position_risk_assessment['recommendation']}")
            
        except Exception as e:
            logger.error(f"❌ Error processing position risk check: {e}")
            raise
    
    async def _handle_stress_test(self, job: JobMessage):
        """Handle stress testing job"""
        try:
            logger.info(f"🧪 Processing stress test job: {job.job_id}")
            
            # Extract stress test parameters
            portfolio_data = job.payload.get('portfolio', {})
            stress_scenarios = job.payload.get('scenarios', [
                'market_crash_20',
                'volatility_spike_50',
                'correlation_breakdown',
                'liquidity_crisis'
            ])
            
            portfolio = Portfolio(**portfolio_data)
            
            # Perform stress tests
            stress_test_results = {}
            
            for scenario in stress_scenarios:
                scenario_result = await self._run_stress_scenario(portfolio, scenario)
                stress_test_results[scenario] = scenario_result
            
            # Generate stress test report
            stress_report = {
                'portfolio_id': portfolio_data.get('portfolio_id', 'unknown'),
                'timestamp': datetime.now().isoformat(),
                'stress_scenarios': stress_test_results,
                'overall_risk_score': self._calculate_stress_risk_score(stress_test_results),
                'recommendations': self._generate_stress_recommendations(stress_test_results)
            }
            
            # Publish stress test report
            report_job = JobMessage(
                job_id=f"{job.job_id}_stress_report",
                job_type='notification',
                payload={
                    'type': 'stress_test_report',
                    'stress_report': stress_report,
                    'priority': 'high'
                },
                priority=job.priority
            )
            
            await self.rabbitmq.publish_job(
                report_job,
                self.rabbitmq.queues['notification']
            )
            
            logger.info(f"✅ Stress test completed for {stress_report['portfolio_id']}")
            
        except Exception as e:
            logger.error(f"❌ Error processing stress test: {e}")
            raise
    
    async def _handle_risk_alert(self, job: JobMessage):
        """Handle risk alert job"""
        try:
            logger.info(f"🚨 Processing risk alert job: {job.job_id}")
            
            # Extract alert data
            alert_data = job.payload.get('alert', {})
            alert_type = alert_data.get('type', 'unknown')
            alert_level = alert_data.get('level', 'medium')
            
            # Process alert based on type
            if alert_type == 'position_limit_breach':
                await self._handle_position_limit_alert(alert_data)
            elif alert_type == 'daily_loss_limit_breach':
                await self._handle_daily_loss_alert(alert_data)
            elif alert_type == 'concentration_risk_alert':
                await self._handle_concentration_alert(alert_data)
            elif alert_type == 'volatility_spike_alert':
                await self._handle_volatility_alert(alert_data)
            else:
                await self._handle_generic_alert(alert_data)
            
            logger.info(f"✅ Risk alert processed: {alert_type} ({alert_level})")
            
        except Exception as e:
            logger.error(f"❌ Error processing risk alert: {e}")
            raise
    
    async def _handle_risk_metrics_update(self, job: JobMessage):
        """Handle risk metrics update job"""
        try:
            logger.info(f"📊 Processing risk metrics update job: {job.job_id}")
            
            # Extract metrics data
            metrics_data = job.payload.get('metrics', {})
            
            # Update risk manager metrics
            if 'daily_loss' in metrics_data:
                self.risk_manager.update_daily_loss(metrics_data['daily_loss'])
            
            # Get updated risk metrics
            current_metrics = self.risk_manager.get_risk_metrics()
            
            # Publish updated metrics
            metrics_job = JobMessage(
                job_id=f"{job.job_id}_updated_metrics",
                job_type='notification',
                payload={
                    'type': 'risk_metrics_update',
                    'metrics': current_metrics,
                    'timestamp': datetime.now().isoformat(),
                    'priority': 'low'
                },
                priority=job.priority
            )
            
            await self.rabbitmq.publish_job(
                metrics_job,
                self.rabbitmq.queues['notification']
            )
            
            logger.info(f"✅ Risk metrics updated")
            
        except Exception as e:
            logger.error(f"❌ Error processing risk metrics update: {e}")
            raise
    
    def _generate_risk_recommendations(self, risk_metrics) -> List[Dict[str, Any]]:
        """Generate risk recommendations based on metrics"""
        recommendations = []
        
        # Check concentration risk
        if risk_metrics.concentration_risk > 0.3:
            recommendations.append({
                'type': 'concentration_risk',
                'priority': 'high',
                'message': 'Portfolio concentration is too high. Consider diversifying positions.',
                'action': 'reduce_largest_positions'
            })
        
        # Check leverage
        if risk_metrics.leverage > 1.2:
            recommendations.append({
                'type': 'leverage_risk',
                'priority': 'medium',
                'message': 'Portfolio leverage is elevated. Consider reducing position sizes.',
                'action': 'reduce_position_sizes'
            })
        
        # Check cash ratio
        if risk_metrics.cash_ratio < 0.1:
            recommendations.append({
                'type': 'cash_reserve',
                'priority': 'medium',
                'message': 'Cash reserve is below recommended level. Consider holding more cash.',
                'action': 'increase_cash_reserve'
            })
        
        # Check daily loss
        if risk_metrics.daily_loss > self.risk_config.trading_limits.max_daily_loss * 0.8:
            recommendations.append({
                'type': 'daily_loss_limit',
                'priority': 'high',
                'message': 'Approaching daily loss limit. Consider stopping trading for the day.',
                'action': 'stop_trading'
            })
        
        return recommendations
    
    async def _run_stress_scenario(self, portfolio: Portfolio, scenario: str) -> Dict[str, Any]:
        """Run a specific stress test scenario"""
        try:
            if scenario == 'market_crash_20':
                # Simulate 20% market crash
                portfolio_value_after = portfolio.total_value * 0.8
                max_loss = portfolio.total_value - portfolio_value_after
                
                return {
                    'scenario': scenario,
                    'portfolio_value_before': portfolio.total_value,
                    'portfolio_value_after': portfolio_value_after,
                    'max_loss': max_loss,
                    'loss_percentage': 0.20,
                    'risk_level': 'high' if max_loss > self.risk_config.trading_limits.max_daily_loss else 'medium'
                }
            
            elif scenario == 'volatility_spike_50':
                # Simulate 50% volatility spike
                volatility_impact = portfolio.total_value * 0.15  # 15% impact from volatility
                
                return {
                    'scenario': scenario,
                    'volatility_impact': volatility_impact,
                    'risk_level': 'medium'
                }
            
            elif scenario == 'correlation_breakdown':
                # Simulate correlation breakdown
                correlation_impact = portfolio.total_value * 0.10  # 10% impact from correlation breakdown
                
                return {
                    'scenario': scenario,
                    'correlation_impact': correlation_impact,
                    'risk_level': 'medium'
                }
            
            elif scenario == 'liquidity_crisis':
                # Simulate liquidity crisis
                liquidity_impact = portfolio.total_value * 0.25  # 25% impact from liquidity crisis
                
                return {
                    'scenario': scenario,
                    'liquidity_impact': liquidity_impact,
                    'risk_level': 'high'
                }
            
            else:
                return {
                    'scenario': scenario,
                    'error': 'Unknown stress scenario'
                }
                
        except Exception as e:
            logger.error(f"❌ Error running stress scenario {scenario}: {e}")
            return {
                'scenario': scenario,
                'error': str(e)
            }
    
    def _calculate_stress_risk_score(self, stress_results: Dict[str, Any]) -> float:
        """Calculate overall stress test risk score"""
        total_risk = 0
        scenario_count = 0
        
        for scenario, result in stress_results.items():
            if 'risk_level' in result:
                scenario_count += 1
                if result['risk_level'] == 'high':
                    total_risk += 1.0
                elif result['risk_level'] == 'medium':
                    total_risk += 0.5
                else:
                    total_risk += 0.1
        
        return total_risk / scenario_count if scenario_count > 0 else 0.0
    
    def _generate_stress_recommendations(self, stress_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate recommendations based on stress test results"""
        recommendations = []
        
        for scenario, result in stress_results.items():
            if result.get('risk_level') == 'high':
                recommendations.append({
                    'scenario': scenario,
                    'priority': 'high',
                    'message': f'High risk in {scenario} scenario. Consider risk mitigation strategies.',
                    'action': 'implement_hedging'
                })
        
        return recommendations
    
    async def _handle_position_limit_alert(self, alert_data: Dict[str, Any]):
        """Handle position limit breach alert"""
        # Implementation for position limit alerts
        pass
    
    async def _handle_daily_loss_alert(self, alert_data: Dict[str, Any]):
        """Handle daily loss limit breach alert"""
        # Implementation for daily loss alerts
        pass
    
    async def _handle_concentration_alert(self, alert_data: Dict[str, Any]):
        """Handle concentration risk alert"""
        # Implementation for concentration alerts
        pass
    
    async def _handle_volatility_alert(self, alert_data: Dict[str, Any]):
        """Handle volatility spike alert"""
        # Implementation for volatility alerts
        pass
    
    async def _handle_generic_alert(self, alert_data: Dict[str, Any]):
        """Handle generic risk alert"""
        # Implementation for generic alerts
        pass
    
    async def publish_risk_check(self, signal: TradeSignal, portfolio: Portfolio, 
                                market_conditions: Dict[str, Any] = None) -> bool:
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
                    },
                    'market_conditions': market_conditions or {}
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