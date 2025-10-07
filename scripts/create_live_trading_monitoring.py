#!/usr/bin/env python3
"""
Live Trading Monitoring & Exit Strategy System
Provides comprehensive monitoring and exit strategy capabilities for live trading
"""

import logging
from pathlib import Path
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LiveTradingMonitoringSystem:
    """Create comprehensive monitoring system for live trading"""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.src_dir = self.base_dir / "src"
        self.services_dir = self.src_dir / "services"
        
    def create_live_trading_monitoring(self):
        """Create comprehensive live trading monitoring system"""
        logger.info("🔧 Creating live trading monitoring system...")
        
        # Create live trading position monitor
        self.create_position_monitor()
        
        # Create exit strategy service
        self.create_exit_strategy_service()
        
        # Create monitoring dashboard
        self.create_monitoring_dashboard()
        
        # Create monitoring API
        self.create_monitoring_api()
        
        logger.info("✅ Live trading monitoring system created")
    
    def create_position_monitor(self):
        """Create live trading position monitor"""
        logger.info("🔧 Creating live trading position monitor...")
        
        monitor_path = self.services_dir / "live_trading" / "position_monitor.py"
        
        monitor_code = '''#!/usr/bin/env python3
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
            async with get_db_session() as session:
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
        
        # Calculate unrealized P&L
        if position.action == "BUY":
            unrealized_pnl = (current_price - position.entry_price) * position.quantity
        else:  # SELL
            unrealized_pnl = (position.entry_price - current_price) * position.quantity
        
        unrealized_pnl_pct = unrealized_pnl / (position.entry_price * position.quantity)
        
        # Calculate holding period
        holding_days = (datetime.now() - position.created_at).days
        
        # Determine risk level
        risk_level = self.determine_risk_level(unrealized_pnl_pct, holding_days)
        
        return PositionMonitorData(
            position_id=str(position.position_id),
            symbol=position.symbol,
            strategy=position.strategy.value if position.strategy else "UNKNOWN",
            entry_time=position.created_at,
            entry_price=float(position.entry_price),
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
        """Get monitoring summary"""
        total_positions = len(self.monitored_positions)
        high_risk_positions = sum(1 for p in self.monitored_positions.values() if p.risk_level == "HIGH")
        
        return {
            'total_positions': total_positions,
            'high_risk_positions': high_risk_positions,
            'monitoring_active': self.is_monitoring,
            'last_update': datetime.now().isoformat(),
            'positions': [
                {
                    'symbol': p.symbol,
                    'strategy': p.strategy,
                    'pnl_pct': p.unrealized_pnl_pct,
                    'holding_days': p.holding_days,
                    'risk_level': p.risk_level
                }
                for p in self.monitored_positions.values()
            ]
        }

# Global instance
position_monitor = LiveTradingPositionMonitor()
'''
        
        monitor_path.write_text(monitor_code)
        logger.info(f"✅ Created position monitor at {monitor_path}")
    
    def create_exit_strategy_service(self):
        """Create exit strategy service"""
        logger.info("🔧 Creating exit strategy service...")
        
        service_path = self.services_dir / "live_trading" / "exit_strategy_service.py"
        
        service_code = '''#!/usr/bin/env python3
"""
Live Trading Exit Strategy Service
Provides sophisticated exit strategy management for live trading
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class ExitStrategyType(Enum):
    """Types of exit strategies"""
    TIME_BASED = "TIME_BASED"
    PROFIT_TARGET = "PROFIT_TARGET"
    STOP_LOSS = "STOP_LOSS"
    TRAILING_STOP = "TRAILING_STOP"
    VOLATILITY_BASED = "VOLATILITY_BASED"
    MOMENTUM_BASED = "MOMENTUM_BASED"
    CORRELATION_BASED = "CORRELATION_BASED"

@dataclass
class ExitStrategy:
    """Exit strategy configuration"""
    strategy_type: ExitStrategyType
    parameters: Dict[str, Any]
    is_active: bool = True
    priority: int = 1  # Higher number = higher priority
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

class LiveTradingExitStrategyService:
    """Service for managing exit strategies in live trading"""
    
    def __init__(self):
        self.exit_strategies = {}
        self.strategy_performance = {}
        
        # Default exit strategies
        self.default_strategies = {
            'conservative': [
                ExitStrategy(
                    strategy_type=ExitStrategyType.TIME_BASED,
                    parameters={'max_days': 7, 'min_hours': 4},
                    priority=3
                ),
                ExitStrategy(
                    strategy_type=ExitStrategyType.PROFIT_TARGET,
                    parameters={'target_pct': 0.10, 'min_target': 0.05},
                    priority=2
                ),
                ExitStrategy(
                    strategy_type=ExitStrategyType.STOP_LOSS,
                    parameters={'loss_pct': 0.05, 'max_loss': 0.08},
                    priority=1
                )
            ],
            'aggressive': [
                ExitStrategy(
                    strategy_type=ExitStrategyType.TIME_BASED,
                    parameters={'max_days': 14, 'min_hours': 2},
                    priority=3
                ),
                ExitStrategy(
                    strategy_type=ExitStrategyType.PROFIT_TARGET,
                    parameters={'target_pct': 0.20, 'min_target': 0.10},
                    priority=2
                ),
                ExitStrategy(
                    strategy_type=ExitStrategyType.STOP_LOSS,
                    parameters={'loss_pct': 0.08, 'max_loss': 0.12},
                    priority=1
                )
            ],
            'swing_trading': [
                ExitStrategy(
                    strategy_type=ExitStrategyType.TIME_BASED,
                    parameters={'max_days': 30, 'min_hours': 24},
                    priority=3
                ),
                ExitStrategy(
                    strategy_type=ExitStrategyType.PROFIT_TARGET,
                    parameters={'target_pct': 0.15, 'min_target': 0.08},
                    priority=2
                ),
                ExitStrategy(
                    strategy_type=ExitStrategyType.STOP_LOSS,
                    parameters={'loss_pct': 0.06, 'max_loss': 0.10},
                    priority=1
                )
            ]
        }
        
        logger.info("Live Trading Exit Strategy Service initialized")
    
    def get_exit_strategies(self, strategy_name: str) -> List[ExitStrategy]:
        """Get exit strategies for a trading strategy"""
        if strategy_name in self.exit_strategies:
            return self.exit_strategies[strategy_name]
        
        # Return default strategies based on strategy type
        if 'day' in strategy_name.lower():
            return self.default_strategies['aggressive']
        elif 'swing' in strategy_name.lower():
            return self.default_strategies['swing_trading']
        else:
            return self.default_strategies['conservative']
    
    def set_exit_strategies(self, strategy_name: str, strategies: List[ExitStrategy]):
        """Set exit strategies for a trading strategy"""
        self.exit_strategies[strategy_name] = strategies
        logger.info(f"✅ Set {len(strategies)} exit strategies for {strategy_name}")
    
    async def evaluate_exit_conditions(self, position_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Evaluate all exit conditions for a position"""
        strategy_name = position_data.get('strategy', 'UNKNOWN')
        strategies = self.get_exit_strategies(strategy_name)
        
        triggered_conditions = []
        
        for strategy in strategies:
            if not strategy.is_active:
                continue
                
            condition_result = await self.evaluate_strategy(strategy, position_data)
            if condition_result['is_triggered']:
                triggered_conditions.append(condition_result)
        
        # Sort by priority (highest first)
        triggered_conditions.sort(key=lambda x: x['priority'], reverse=True)
        
        return triggered_conditions
    
    async def evaluate_strategy(self, strategy: ExitStrategy, position_data: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate a specific exit strategy"""
        
        if strategy.strategy_type == ExitStrategyType.TIME_BASED:
            return await self.evaluate_time_based_exit(strategy, position_data)
        elif strategy.strategy_type == ExitStrategyType.PROFIT_TARGET:
            return await self.evaluate_profit_target_exit(strategy, position_data)
        elif strategy.strategy_type == ExitStrategyType.STOP_LOSS:
            return await self.evaluate_stop_loss_exit(strategy, position_data)
        elif strategy.strategy_type == ExitStrategyType.TRAILING_STOP:
            return await self.evaluate_trailing_stop_exit(strategy, position_data)
        elif strategy.strategy_type == ExitStrategyType.VOLATILITY_BASED:
            return await self.evaluate_volatility_exit(strategy, position_data)
        else:
            return {
                'strategy_type': strategy.strategy_type.value,
                'is_triggered': False,
                'priority': strategy.priority,
                'reason': 'Strategy not implemented'
            }
    
    async def evaluate_time_based_exit(self, strategy: ExitStrategy, position_data: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate time-based exit strategy"""
        params = strategy.parameters
        entry_time = position_data['entry_time']
        current_time = datetime.now()
        
        holding_days = (current_time - entry_time).days
        max_days = params.get('max_days', 30)
        
        is_triggered = holding_days >= max_days
        
        return {
            'strategy_type': strategy.strategy_type.value,
            'is_triggered': is_triggered,
            'priority': strategy.priority,
            'reason': f"Time-based exit: {holding_days} days >= {max_days} days" if is_triggered else None,
            'current_value': holding_days,
            'threshold': max_days
        }
    
    async def evaluate_profit_target_exit(self, strategy: ExitStrategy, position_data: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate profit target exit strategy"""
        params = strategy.parameters
        pnl_pct = position_data.get('unrealized_pnl_pct', 0.0)
        target_pct = params.get('target_pct', 0.10)
        
        is_triggered = pnl_pct >= target_pct
        
        return {
            'strategy_type': strategy.strategy_type.value,
            'is_triggered': is_triggered,
            'priority': strategy.priority,
            'reason': f"Profit target reached: {pnl_pct:.1%} >= {target_pct:.1%}" if is_triggered else None,
            'current_value': pnl_pct,
            'threshold': target_pct
        }
    
    async def evaluate_stop_loss_exit(self, strategy: ExitStrategy, position_data: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate stop loss exit strategy"""
        params = strategy.parameters
        pnl_pct = position_data.get('unrealized_pnl_pct', 0.0)
        loss_pct = params.get('loss_pct', 0.05)
        
        is_triggered = pnl_pct <= -loss_pct
        
        return {
            'strategy_type': strategy.strategy_type.value,
            'is_triggered': is_triggered,
            'priority': strategy.priority,
            'reason': f"Stop loss triggered: {pnl_pct:.1%} <= -{loss_pct:.1%}" if is_triggered else None,
            'current_value': pnl_pct,
            'threshold': -loss_pct
        }
    
    async def evaluate_trailing_stop_exit(self, strategy: ExitStrategy, position_data: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate trailing stop exit strategy"""
        # Placeholder implementation
        return {
            'strategy_type': strategy.strategy_type.value,
            'is_triggered': False,
            'priority': strategy.priority,
            'reason': 'Trailing stop not implemented'
        }
    
    async def evaluate_volatility_exit(self, strategy: ExitStrategy, position_data: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate volatility-based exit strategy"""
        # Placeholder implementation
        return {
            'strategy_type': strategy.strategy_type.value,
            'is_triggered': False,
            'priority': strategy.priority,
            'reason': 'Volatility exit not implemented'
        }
    
    def get_strategy_performance(self, strategy_name: str) -> Dict[str, Any]:
        """Get performance metrics for exit strategies"""
        return self.strategy_performance.get(strategy_name, {
            'total_exits': 0,
            'successful_exits': 0,
            'average_holding_time': 0,
            'average_pnl': 0.0
        })

# Global instance
exit_strategy_service = LiveTradingExitStrategyService()
'''
        
        service_path.write_text(service_code)
        logger.info(f"✅ Created exit strategy service at {service_path}")
    
    def create_monitoring_dashboard(self):
        """Create monitoring dashboard"""
        logger.info("🔧 Creating monitoring dashboard...")
        
        dashboard_path = self.services_dir / "live_trading" / "monitoring_dashboard.py"
        
        dashboard_code = '''#!/usr/bin/env python3
"""
Live Trading Monitoring Dashboard
Provides real-time monitoring interface for live trading positions
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import json

from .position_monitor import position_monitor
from .exit_strategy_service import exit_strategy_service

logger = logging.getLogger(__name__)

app = FastAPI(title="Live Trading Monitoring Dashboard")

class MonitoringDashboard:
    """Real-time monitoring dashboard for live trading"""
    
    def __init__(self):
        self.connected_clients = []
        self.monitoring_data = {}
        
    async def connect(self, websocket: WebSocket):
        """Connect a client to the dashboard"""
        await websocket.accept()
        self.connected_clients.append(websocket)
        logger.info(f"📱 Client connected to monitoring dashboard")
    
    async def disconnect(self, websocket: WebSocket):
        """Disconnect a client from the dashboard"""
        if websocket in self.connected_clients:
            self.connected_clients.remove(websocket)
        logger.info(f"📱 Client disconnected from monitoring dashboard")
    
    async def broadcast_update(self, data: Dict[str, Any]):
        """Broadcast update to all connected clients"""
        if self.connected_clients:
            message = json.dumps(data)
            for client in self.connected_clients.copy():
                try:
                    await client.send_text(message)
                except:
                    self.connected_clients.remove(client)
    
    async def start_monitoring_broadcast(self):
        """Start broadcasting monitoring data"""
        while True:
            try:
                # Get monitoring summary
                summary = await position_monitor.get_monitoring_summary()
                
                # Add exit strategy information
                summary['exit_strategies'] = {
                    'total_strategies': len(exit_strategy_service.exit_strategies),
                    'active_strategies': sum(1 for strategies in exit_strategy_service.exit_strategies.values() 
                                           for s in strategies if s.is_active)
                }
                
                # Broadcast to clients
                await self.broadcast_update({
                    'type': 'monitoring_update',
                    'data': summary,
                    'timestamp': datetime.now().isoformat()
                })
                
                await asyncio.sleep(30)  # Update every 30 seconds
                
            except Exception as e:
                logger.error(f"❌ Error in monitoring broadcast: {e}")
                await asyncio.sleep(60)

# Global dashboard instance
dashboard = MonitoringDashboard()

@app.get("/")
async def get_dashboard():
    """Get the monitoring dashboard HTML"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Live Trading Monitoring Dashboard</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
            .container { max-width: 1200px; margin: 0 auto; }
            .header { background: #2c3e50; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
            .card { background: white; padding: 20px; margin: 10px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .position { border-left: 4px solid #3498db; padding: 10px; margin: 5px 0; }
            .high-risk { border-left-color: #e74c3c; }
            .medium-risk { border-left-color: #f39c12; }
            .low-risk { border-left-color: #27ae60; }
            .status { display: inline-block; padding: 4px 8px; border-radius: 4px; font-size: 12px; }
            .status.active { background: #27ae60; color: white; }
            .status.inactive { background: #95a5a6; color: white; }
            .metric { display: inline-block; margin: 10px 20px 10px 0; }
            .metric-value { font-size: 24px; font-weight: bold; color: #2c3e50; }
            .metric-label { font-size: 12px; color: #7f8c8d; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🚀 Live Trading Monitoring Dashboard</h1>
                <p>Real-time position monitoring and exit strategy management</p>
            </div>
            
            <div class="card">
                <h2>📊 System Overview</h2>
                <div class="metric">
                    <div class="metric-value" id="total-positions">0</div>
                    <div class="metric-label">Total Positions</div>
                </div>
                <div class="metric">
                    <div class="metric-value" id="high-risk-positions">0</div>
                    <div class="metric-label">High Risk</div>
                </div>
                <div class="metric">
                    <div class="metric-value" id="monitoring-status">Inactive</div>
                    <div class="metric-label">Monitoring Status</div>
                </div>
                <div class="metric">
                    <div class="metric-value" id="last-update">Never</div>
                    <div class="metric-label">Last Update</div>
                </div>
            </div>
            
            <div class="card">
                <h2>📈 Active Positions</h2>
                <div id="positions-list">
                    <p>No active positions</p>
                </div>
            </div>
            
            <div class="card">
                <h2>🎯 Exit Strategies</h2>
                <div id="exit-strategies">
                    <p>Loading exit strategy information...</p>
                </div>
            </div>
        </div>
        
        <script>
            const ws = new WebSocket("ws://localhost:8080/ws");
            
            ws.onmessage = function(event) {
                const data = JSON.parse(event.data);
                
                if (data.type === 'monitoring_update') {
                    updateDashboard(data.data);
                }
            };
            
            function updateDashboard(data) {
                // Update system overview
                document.getElementById('total-positions').textContent = data.total_positions;
                document.getElementById('high-risk-positions').textContent = data.high_risk_positions;
                document.getElementById('monitoring-status').textContent = data.monitoring_active ? 'Active' : 'Inactive';
                document.getElementById('last-update').textContent = new Date(data.last_update).toLocaleTimeString();
                
                // Update positions list
                const positionsList = document.getElementById('positions-list');
                if (data.positions && data.positions.length > 0) {
                    positionsList.innerHTML = data.positions.map(pos => `
                        <div class="position ${pos.risk_level.toLowerCase()}-risk">
                            <strong>${pos.symbol}</strong> (${pos.strategy})<br>
                            P&L: ${(pos.pnl_pct * 100).toFixed(1)}% | 
                            Holding: ${pos.holding_days} days | 
                            Risk: ${pos.risk_level}
                        </div>
                    `).join('');
                } else {
                    positionsList.innerHTML = '<p>No active positions</p>';
                }
                
                // Update exit strategies
                const exitStrategies = document.getElementById('exit-strategies');
                exitStrategies.innerHTML = `
                    <p>Total Strategies: ${data.exit_strategies.total_strategies}</p>
                    <p>Active Strategies: ${data.exit_strategies.active_strategies}</p>
                `;
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await dashboard.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await dashboard.disconnect(websocket)

@app.get("/api/monitoring/summary")
async def get_monitoring_summary():
    """Get monitoring summary API"""
    return await position_monitor.get_monitoring_summary()

@app.get("/api/exit-strategies")
async def get_exit_strategies():
    """Get exit strategies API"""
    return {
        'strategies': exit_strategy_service.exit_strategies,
        'default_strategies': exit_strategy_service.default_strategies
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
'''
        
        dashboard_path.write_text(dashboard_code)
        logger.info(f"✅ Created monitoring dashboard at {dashboard_path}")
    
    def create_monitoring_api(self):
        """Create monitoring API"""
        logger.info("🔧 Creating monitoring API...")
        
        api_path = self.services_dir / "live_trading" / "monitoring_api.py"
        
        api_code = '''#!/usr/bin/env python3
"""
Live Trading Monitoring API
REST API for monitoring live trading positions and exit strategies
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .position_monitor import position_monitor
from .exit_strategy_service import exit_strategy_service

logger = logging.getLogger(__name__)

app = FastAPI(title="Live Trading Monitoring API", version="1.0.0")

class PositionSummary(BaseModel):
    """Position summary model"""
    symbol: str
    strategy: str
    pnl_pct: float
    holding_days: int
    risk_level: str

class MonitoringSummary(BaseModel):
    """Monitoring summary model"""
    total_positions: int
    high_risk_positions: int
    monitoring_active: bool
    last_update: str
    positions: List[PositionSummary]

class ExitStrategyConfig(BaseModel):
    """Exit strategy configuration model"""
    strategy_name: str
    strategies: List[Dict[str, Any]]

@app.get("/api/monitoring/status")
async def get_monitoring_status():
    """Get monitoring system status"""
    return {
        "monitoring_active": position_monitor.is_monitoring,
        "monitored_positions": len(position_monitor.monitored_positions),
        "exit_strategies_configured": len(exit_strategy_service.exit_strategies),
        "last_update": datetime.now().isoformat()
    }

@app.get("/api/monitoring/positions")
async def get_active_positions():
    """Get all active positions"""
    summary = await position_monitor.get_monitoring_summary()
    return summary

@app.get("/api/monitoring/positions/{symbol}")
async def get_position_by_symbol(symbol: str):
    """Get position by symbol"""
    for position in position_monitor.monitored_positions.values():
        if position.symbol == symbol:
            return position
    raise HTTPException(status_code=404, detail="Position not found")

@app.get("/api/exit-strategies")
async def get_exit_strategies():
    """Get all exit strategies"""
    return {
        "configured_strategies": exit_strategy_service.exit_strategies,
        "default_strategies": exit_strategy_service.default_strategies
    }

@app.get("/api/exit-strategies/{strategy_name}")
async def get_exit_strategies_for_strategy(strategy_name: str):
    """Get exit strategies for a specific trading strategy"""
    strategies = exit_strategy_service.get_exit_strategies(strategy_name)
    return {
        "strategy_name": strategy_name,
        "exit_strategies": [
            {
                "type": s.strategy_type.value,
                "parameters": s.parameters,
                "is_active": s.is_active,
                "priority": s.priority
            }
            for s in strategies
        ]
    }

@app.post("/api/exit-strategies/{strategy_name}")
async def set_exit_strategies_for_strategy(strategy_name: str, config: ExitStrategyConfig):
    """Set exit strategies for a specific trading strategy"""
    try:
        # Convert config to ExitStrategy objects
        strategies = []
        for strategy_data in config.strategies:
            strategy = ExitStrategy(
                strategy_type=ExitStrategyType(strategy_data['type']),
                parameters=strategy_data['parameters'],
                is_active=strategy_data.get('is_active', True),
                priority=strategy_data.get('priority', 1)
            )
            strategies.append(strategy)
        
        exit_strategy_service.set_exit_strategies(strategy_name, strategies)
        
        return {
            "message": f"Exit strategies set for {strategy_name}",
            "strategies_count": len(strategies)
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/monitoring/start")
async def start_monitoring():
    """Start position monitoring"""
    if not position_monitor.is_monitoring:
        asyncio.create_task(position_monitor.start_monitoring())
        return {"message": "Monitoring started"}
    else:
        return {"message": "Monitoring already active"}

@app.post("/api/monitoring/stop")
async def stop_monitoring():
    """Stop position monitoring"""
    await position_monitor.stop_monitoring()
    return {"message": "Monitoring stopped"}

@app.get("/api/monitoring/alerts")
async def get_monitoring_alerts():
    """Get monitoring alerts"""
    alerts = []
    
    # Check for high-risk positions
    high_risk_count = sum(1 for p in position_monitor.monitored_positions.values() if p.risk_level == "HIGH")
    if high_risk_count > 0:
        alerts.append({
            "type": "HIGH_RISK_POSITIONS",
            "message": f"{high_risk_count} high-risk positions detected",
            "severity": "HIGH",
            "timestamp": datetime.now().isoformat()
        })
    
    # Check for long-held positions
    long_held_count = sum(1 for p in position_monitor.monitored_positions.values() if p.holding_days > 20)
    if long_held_count > 0:
        alerts.append({
            "type": "LONG_HELD_POSITIONS",
            "message": f"{long_held_count} positions held for more than 20 days",
            "severity": "MEDIUM",
            "timestamp": datetime.now().isoformat()
        })
    
    return {
        "alerts": alerts,
        "total_alerts": len(alerts)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8081)
'''
        
        api_path.write_text(api_code)
        logger.info(f"✅ Created monitoring API at {api_path}")

async def main():
    system = LiveTradingMonitoringSystem()
    system.create_live_trading_monitoring()

if __name__ == "__main__":
    asyncio.run(main())




