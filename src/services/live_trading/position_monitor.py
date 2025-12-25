#!/usr/bin/env python3
"""
Live Trading Position Monitor
Monitors active positions and provides exit strategy information
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from .models import LivePosition, LiveTrade, PositionStatus, TradeStatus
from .database import get_db_session

logger = logging.getLogger(__name__)

@dataclass
class ExitCondition:
    """Exit condition for a position"""
    condition_type: str  # TIME_BASED, PROFIT_TARGET, STOP_LOSS, VOLATILITY
    threshold: float
    current_value: float
    is_triggered: bool
    trigger_time: Optional[datetime] = None
    reason: Optional[str] = None

@dataclass
class PositionMonitorData:
    """Position monitoring data"""
    position_id: str
    symbol: str
    strategy: str
    entry_time: datetime
    entry_price: float
    current_price: float
    quantity: int
    unrealized_pnl: float
    unrealized_pnl_pct: float
    holding_days: int
    exit_conditions: List[ExitCondition]
    risk_level: str  # LOW, MEDIUM, HIGH
    next_exit_check: datetime

class LiveTradingPositionMonitor:
    """Monitor live trading positions and exit strategies"""
    
    def __init__(self):
        self.monitoring_interval = 300  # 5 minutes
        self.is_monitoring = False
        self.monitored_positions = {}
        
        # Exit strategy configuration
        self.exit_config = {
            'max_holding_days': 30,
            'profit_target_pct': 0.15,  # 15% profit target
            'stop_loss_pct': 0.08,     # 8% stop loss
            'volatility_threshold': 0.40,  # 40% volatility threshold
            'min_holding_hours': 4     # Minimum 4 hours holding
        }
        
        logger.info("Live Trading Position Monitor initialized")
    
    async def start_monitoring(self):
        """Start monitoring active positions"""
        logger.info("🚀 Starting live trading position monitoring...")
        self.is_monitoring = True
        
        while self.is_monitoring:
            try:
                await self.monitor_all_positions()
                await asyncio.sleep(self.monitoring_interval)
            except Exception as e:
                logger.error(f"❌ Error in position monitoring: {e}")
                await asyncio.sleep(60)  # Wait 1 minute on error
    
    async def stop_monitoring(self):
        """Stop monitoring"""
        logger.info("🛑 Stopping live trading position monitoring...")
        self.is_monitoring = False
    
    async def monitor_all_positions(self):
        """Monitor all active positions"""
        try:
            # Use the session maker directly instead of the generator
            from .database import async_session_maker
            async with async_session_maker() as session:
                # Get all open positions
                stmt = select(LivePosition).where(LivePosition.status == PositionStatus.OPEN)
                result = await session.execute(stmt)
                positions = result.scalars().all()
                
                logger.info(f"🔍 Monitoring {len(positions)} active positions")
                
                for position in positions:
                    await self.monitor_position(position, session)
                    
        except Exception as e:
            logger.error(f"❌ Error monitoring positions: {e}")
    
    async def monitor_position(self, position: LivePosition, session: AsyncSession):
        """Monitor a single position"""
        try:
            # Get current market data (placeholder - would integrate with real market data)
            current_price = await self.get_current_price(position.symbol)
            
            # Calculate position metrics
            monitor_data = await self.calculate_position_metrics(position, current_price)
            
            # Check exit conditions
            exit_conditions = await self.check_exit_conditions(monitor_data)
            
            # Update monitoring data
            self.monitored_positions[position.position_id] = monitor_data
            
            # Log monitoring results
            await self.log_monitoring_results(monitor_data, exit_conditions)
            
            # Check if any exit conditions are triggered
            triggered_conditions = [ec for ec in exit_conditions if ec.is_triggered]
            if triggered_conditions:
                await self.handle_exit_triggers(position, triggered_conditions, session)
                
        except Exception as e:
            logger.error(f"❌ Error monitoring position {position.position_id}: {e}")
    
    async def calculate_position_metrics(self, position: LivePosition, current_price: float) -> PositionMonitorData:
        """Calculate position monitoring metrics"""
        
        # Calculate unrealized P&L based on quantity sign
        # Positive quantity = long position, negative = short position
        unrealized_pnl = (current_price - float(position.average_price)) * position.quantity
        
        unrealized_pnl_pct = unrealized_pnl / (float(position.average_price) * abs(position.quantity))
        
        # Calculate holding period
        holding_days = (datetime.now() - position.created_at).days
        
        # Determine risk level
        risk_level = self.determine_risk_level(unrealized_pnl_pct, holding_days)
        
        return PositionMonitorData(
            position_id=str(position.position_id),
            symbol=position.symbol,
            strategy=position.strategy.value if position.strategy else "UNKNOWN",
            entry_time=position.opened_at,
            entry_price=float(position.average_price),
            current_price=current_price,
            quantity=position.quantity,
            unrealized_pnl=unrealized_pnl,
            unrealized_pnl_pct=unrealized_pnl_pct,
            holding_days=holding_days,
            exit_conditions=[],  # Will be populated by check_exit_conditions
            risk_level=risk_level,
            next_exit_check=datetime.now() + timedelta(minutes=5)
        )
    
    def determine_risk_level(self, pnl_pct: float, holding_days: int) -> str:
        """Determine position risk level"""
        if pnl_pct < -0.05 or holding_days > 20:  # 5% loss or held > 20 days
            return "HIGH"
        elif pnl_pct < -0.02 or holding_days > 10:  # 2% loss or held > 10 days
            return "MEDIUM"
        else:
            return "LOW"
    
    async def check_exit_conditions(self, monitor_data: PositionMonitorData) -> List[ExitCondition]:
        """Check all exit conditions for a position"""
        conditions = []
        
        # 1. Time-based exit
        if monitor_data.holding_days >= self.exit_config['max_holding_days']:
            conditions.append(ExitCondition(
                condition_type="TIME_BASED",
                threshold=self.exit_config['max_holding_days'],
                current_value=monitor_data.holding_days,
                is_triggered=True,
                trigger_time=datetime.now(),
                reason=f"Max holding period reached ({monitor_data.holding_days} days)"
            ))
        
        # 2. Profit target exit
        elif monitor_data.unrealized_pnl_pct >= self.exit_config['profit_target_pct']:
            conditions.append(ExitCondition(
                condition_type="PROFIT_TARGET",
                threshold=self.exit_config['profit_target_pct'],
                current_value=monitor_data.unrealized_pnl_pct,
                is_triggered=True,
                trigger_time=datetime.now(),
                reason=f"Profit target reached ({monitor_data.unrealized_pnl_pct:.1%})"
            ))
        
        # 3. Stop loss exit
        elif monitor_data.unrealized_pnl_pct <= -self.exit_config['stop_loss_pct']:
            conditions.append(ExitCondition(
                condition_type="STOP_LOSS",
                threshold=-self.exit_config['stop_loss_pct'],
                current_value=monitor_data.unrealized_pnl_pct,
                is_triggered=True,
                trigger_time=datetime.now(),
                reason=f"Stop loss triggered ({monitor_data.unrealized_pnl_pct:.1%})"
            ))
        
        # 4. Minimum holding period check
        elif monitor_data.holding_days < (self.exit_config['min_holding_hours'] / 24):
            conditions.append(ExitCondition(
                condition_type="MIN_HOLDING",
                threshold=self.exit_config['min_holding_hours'] / 24,
                current_value=monitor_data.holding_days,
                is_triggered=False,
                reason=f"Minimum holding period not met ({monitor_data.holding_days:.1f} days)"
            ))
        
        return conditions
    
    async def handle_exit_triggers(self, position: LivePosition, triggered_conditions: List[ExitCondition], session: AsyncSession):
        """Handle triggered exit conditions"""
        logger.info(f"🚨 Exit triggers detected for {position.symbol}: {len(triggered_conditions)} conditions")
        
        for condition in triggered_conditions:
            logger.info(f"   • {condition.condition_type}: {condition.reason}")
            
            # Create exit trade (placeholder - would integrate with actual trading)
            await self.create_exit_trade(position, condition, session)
    
    async def create_exit_trade(self, position: LivePosition, condition: ExitCondition, session: AsyncSession):
        """Create exit trade for triggered condition"""
        try:
            # This would integrate with the actual trading service
            logger.info(f"📤 Creating exit trade for {position.symbol} - {condition.reason}")
            
            # Update position status
            position.status = PositionStatus.CLOSED
            await session.commit()
            
            logger.info(f"✅ Position {position.position_id} closed due to {condition.condition_type}")
            
        except Exception as e:
            logger.error(f"❌ Error creating exit trade: {e}")
    
    async def get_current_price(self, symbol: str) -> float:
        """Get current market price (placeholder)"""
        # This would integrate with real market data service
        return 100.0  # Placeholder price
    
    async def log_monitoring_results(self, monitor_data: PositionMonitorData, exit_conditions: List[ExitCondition]):
        """Log monitoring results"""
        logger.info(f"📊 {monitor_data.symbol} ({monitor_data.strategy}): "
                   f"P&L: {monitor_data.unrealized_pnl_pct:.1%}, "
                   f"Holding: {monitor_data.holding_days}d, "
                   f"Risk: {monitor_data.risk_level}, "
                   f"Conditions: {len(exit_conditions)}")
    
    async def get_monitoring_summary(self) -> Dict[str, Any]:
        """Get monitoring summary with detailed exit strategy information"""
        total_positions = len(self.monitored_positions)
        high_risk_positions = sum(1 for p in self.monitored_positions.values() if p.risk_level == "HIGH")
        
        # Enhanced position data with exit strategy details
        enhanced_positions = []
        for p in self.monitored_positions.values():
            # Calculate exit strategy details
            exit_strategy_info = await self.get_position_exit_strategy_info(p)
            
            enhanced_position = {
                'symbol': p.symbol,
                'strategy': p.strategy,
                'pnl_pct': p.unrealized_pnl_pct,
                'holding_days': p.holding_days,
                'risk_level': p.risk_level,
                'entry_price': p.entry_price,
                'current_price': p.current_price,
                'quantity': p.quantity,
                'unrealized_pnl': p.unrealized_pnl,
                'exit_strategy': exit_strategy_info
            }
            enhanced_positions.append(enhanced_position)
        
        return {
            'total_positions': total_positions,
            'high_risk_positions': high_risk_positions,
            'monitoring_active': self.is_monitoring,
            'last_update': datetime.now().isoformat(),
            'positions': enhanced_positions,
            'exit_strategy_config': self.exit_config
        }
    
    async def get_position_exit_strategy_info(self, position_data: PositionMonitorData) -> Dict[str, Any]:
        """Get detailed exit strategy information for a position"""
        
        # Calculate exit timeline and distances
        max_holding_days = self.exit_config['max_holding_days']
        profit_target_pct = self.exit_config['profit_target_pct']
        stop_loss_pct = self.exit_config['stop_loss_pct']
        
        # Days until max holding period
        days_until_max_hold = max(0, max_holding_days - position_data.holding_days)
        
        # Distance to profit target
        profit_distance_pct = max(0, profit_target_pct - position_data.unrealized_pnl_pct)
        
        # Distance to stop loss
        stop_distance_pct = max(0, position_data.unrealized_pnl_pct + stop_loss_pct)
        
        # Determine which exit condition is closest
        closest_exit = self.get_closest_exit_condition(position_data)
        
        # Generate anxiety-reducing messaging
        anxiety_reduction_msg = self.generate_anxiety_reduction_message(position_data)
        
        return {
            'max_holding_days': max_holding_days,
            'profit_target_pct': profit_target_pct,
            'stop_loss_pct': stop_loss_pct,
            'min_holding_hours': self.exit_config['min_holding_hours'],
            'days_until_max_hold': days_until_max_hold,
            'profit_distance_pct': profit_distance_pct,
            'stop_distance_pct': stop_distance_pct,
            'closest_exit': closest_exit,
            'anxiety_reduction_message': anxiety_reduction_msg,
            'exit_conditions': [
                {
                    'type': 'TIME_BASED',
                    'threshold': max_holding_days,
                    'current_value': position_data.holding_days,
                    'is_triggered': position_data.holding_days >= max_holding_days,
                    'description': f"Automatic exit after {max_holding_days} days"
                },
                {
                    'type': 'PROFIT_TARGET',
                    'threshold': profit_target_pct,
                    'current_value': position_data.unrealized_pnl_pct,
                    'is_triggered': position_data.unrealized_pnl_pct >= profit_target_pct,
                    'description': f"Take profit at {profit_target_pct:.1%} gain"
                },
                {
                    'type': 'STOP_LOSS',
                    'threshold': -stop_loss_pct,
                    'current_value': position_data.unrealized_pnl_pct,
                    'is_triggered': position_data.unrealized_pnl_pct <= -stop_loss_pct,
                    'description': f"Stop loss at {stop_loss_pct:.1%} loss"
                }
            ]
        }
    
    def get_closest_exit_condition(self, position_data: PositionMonitorData) -> Dict[str, Any]:
        """Determine which exit condition is closest to being triggered"""
        max_holding_days = self.exit_config['max_holding_days']
        profit_target_pct = self.exit_config['profit_target_pct']
        stop_loss_pct = self.exit_config['stop_loss_pct']
        
        # Calculate distances
        time_distance = max_holding_days - position_data.holding_days
        profit_distance = profit_target_pct - position_data.unrealized_pnl_pct
        stop_distance = position_data.unrealized_pnl_pct + stop_loss_pct
        
        # Find minimum distance
        distances = {
            'TIME_BASED': time_distance,
            'PROFIT_TARGET': profit_distance,
            'STOP_LOSS': stop_distance
        }
        
        closest_type = min(distances, key=distances.get)
        closest_distance = distances[closest_type]
        
        return {
            'type': closest_type,
            'distance': closest_distance,
            'description': self.get_exit_description(closest_type, closest_distance)
        }
    
    def get_exit_description(self, exit_type: str, distance: float) -> str:
        """Get human-readable description of exit condition"""
        if exit_type == 'TIME_BASED':
            return f"Time-based exit in {distance:.1f} days"
        elif exit_type == 'PROFIT_TARGET':
            return f"Profit target {distance:.1%} away"
        elif exit_type == 'STOP_LOSS':
            return f"Stop loss {distance:.1%} away"
        else:
            return "Unknown exit condition"
    
    def generate_anxiety_reduction_message(self, position_data: PositionMonitorData) -> str:
        """Generate reassuring message about position protection"""
        max_holding_days = self.exit_config['max_holding_days']
        profit_target_pct = self.exit_config['profit_target_pct']
        stop_loss_pct = self.exit_config['stop_loss_pct']
        
        messages = [
            f"🛡️ Your position is protected by automated exit strategies:",
            f"   • Automatic stop-loss at {stop_loss_pct:.1%} to limit losses",
            f"   • Profit-taking at {profit_target_pct:.1%} to secure gains",
            f"   • Time-based exit after {max_holding_days} days maximum",
            f"   • Current risk level: {position_data.risk_level}"
        ]
        
        if position_data.unrealized_pnl_pct > 0:
            messages.append(f"   • Currently profitable: {position_data.unrealized_pnl_pct:.1%}")
        elif position_data.unrealized_pnl_pct < -stop_loss_pct * 0.5:
            messages.append(f"   • Stop-loss protection active: {position_data.unrealized_pnl_pct:.1%}")
        
        return "\n".join(messages)

# Global instance
position_monitor = LiveTradingPositionMonitor()
