#!/usr/bin/env python3
"""
🚀 Event-Driven Trading System Demo

This demo shows how to set up and use the event-driven architecture
with decision tree for automated trading decisions.
"""

import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List
from dataclasses import dataclass
from enum import Enum
from loguru import logger

# Configure logging
logger.add("logs/event_driven_demo.log", rotation="1 day", retention="7 days")

# Event Types
class EventType(Enum):
    MARKET_DATA = "market_data"
    NEWS_EVENT = "news_event"
    USER_COMMAND = "user_command"
    TIME_EVENT = "time_event"

@dataclass
class Event:
    event_id: str
    event_type: EventType
    data: Dict[str, Any]
    timestamp: datetime
    source: str
    priority: int = 1

@dataclass
class AnalysisResult:
    signal_type: str
    confidence: float
    action: str
    metadata: Dict[str, Any]
    timestamp: datetime

@dataclass
class DecisionResult:
    approved: bool
    action: str
    confidence: float
    reasoning: str
    metadata: Dict[str, Any]

class EventGateway:
    """Simplified event gateway for demo"""
    
    def __init__(self):
        self.event_handlers: Dict[EventType, List] = {}
        self.event_queue = asyncio.Queue()
        self.is_running = False
        
    async def start(self):
        """Start the event gateway"""
        self.is_running = True
        logger.info("🚀 Event Gateway started")
        asyncio.create_task(self._process_events())
        
    async def stop(self):
        """Stop the event gateway"""
        self.is_running = False
        logger.info("🛑 Event Gateway stopped")
        
    async def publish_event(self, event: Event):
        """Publish an event"""
        await self.event_queue.put(event)
        logger.info(f"📡 Event published: {event.event_type.value} - {event.event_id}")
        
    async def _process_events(self):
        """Process events"""
        while self.is_running:
            try:
                event = await asyncio.wait_for(self.event_queue.get(), timeout=1.0)
                await self._route_event(event)
                self.event_queue.task_done()
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error processing event: {e}")
                
    async def _route_event(self, event: Event):
        """Route event to handlers"""
        handlers = self.event_handlers.get(event.event_type, [])
        for handler in handlers:
            try:
                await handler(event)
            except Exception as e:
                logger.error(f"Error in event handler: {e}")
                
    def register_handler(self, event_type: EventType, handler):
        """Register event handler"""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
        logger.info(f"📝 Registered handler for {event_type.value}")

class AnalysisEngine:
    """Simplified analysis engine for demo"""
    
    def __init__(self):
        self.technical_weights = {
            'rsi': 0.3,
            'macd': 0.3,
            'bollinger_bands': 0.2,
            'sma': 0.2
        }
        
    async def analyze_event(self, event: Event) -> AnalysisResult:
        """Analyze event and generate signal"""
        
        if event.event_type == EventType.MARKET_DATA:
            return await self._analyze_market_data(event)
        elif event.event_type == EventType.NEWS_EVENT:
            return await self._analyze_news_event(event)
        else:
            return None
            
    async def _analyze_market_data(self, event: Event) -> AnalysisResult:
        """Analyze market data event"""
        data = event.data
        
        # Simulate technical analysis
        technical_score = self._calculate_technical_score(data)
        
        # Simulate AI analysis
        ai_score = self._calculate_ai_score(data)
        
        # Combine scores
        combined_confidence = (technical_score * 0.6) + (ai_score * 0.4)
        
        # Determine action
        if combined_confidence > 0.7:
            action = "BUY"
        elif combined_confidence < 0.3:
            action = "SELL"
        else:
            action = "HOLD"
            
        return AnalysisResult(
            signal_type="market_analysis",
            confidence=combined_confidence,
            action=action,
            metadata={
                'technical_score': technical_score,
                'ai_score': ai_score,
                'price': data.get('price', 0),
                'volume': data.get('volume', 0)
            },
            timestamp=datetime.now()
        )
        
    async def _analyze_news_event(self, event: Event) -> AnalysisResult:
        """Analyze news event"""
        data = event.data
        
        # Simulate sentiment analysis
        sentiment_score = data.get('sentiment', 0)
        
        # Determine action based on sentiment
        if sentiment_score > 0.5:
            action = "BUY"
            confidence = sentiment_score
        elif sentiment_score < -0.5:
            action = "SELL"
            confidence = abs(sentiment_score)
        else:
            action = "HOLD"
            confidence = 0.5
            
        return AnalysisResult(
            signal_type="news_analysis",
            confidence=confidence,
            action=action,
            metadata={
                'sentiment_score': sentiment_score,
                'news_impact': data.get('impact', 'medium'),
                'headline': data.get('headline', '')
            },
            timestamp=datetime.now()
        )
        
    def _calculate_technical_score(self, data: Dict[str, Any]) -> float:
        """Calculate technical analysis score"""
        # Simulate technical indicators
        price = data.get('price', 100)
        volume = data.get('volume', 1000000)
        
        # Simple scoring based on price and volume
        price_score = min(price / 100, 1.0)  # Normalize to 0-1
        volume_score = min(volume / 1000000, 1.0)  # Normalize to 0-1
        
        return (price_score + volume_score) / 2
        
    def _calculate_ai_score(self, data: Dict[str, Any]) -> float:
        """Calculate AI analysis score"""
        # Simulate AI analysis
        import random
        return random.uniform(0.3, 0.9)

class DecisionTreeEngine:
    """Simplified decision tree engine for demo"""
    
    def __init__(self):
        self.confidence_thresholds = {
            'signal_quality': 0.3,
            'technical_analysis': 0.4,
            'ai_analysis': 0.5,
            'risk_assessment': 0.6,
            'final_decision': 0.7
        }
        
    async def evaluate_signal(self, analysis_result: AnalysisResult, context: Dict[str, Any]) -> DecisionResult:
        """Evaluate signal through decision tree"""
        
        reasoning = []
        metadata = {}
        
        # Layer 1: Signal Quality Check
        if analysis_result.confidence < self.confidence_thresholds['signal_quality']:
            return DecisionResult(
                approved=False,
                action="REJECT",
                confidence=analysis_result.confidence,
                reasoning="Signal confidence too low",
                metadata={}
            )
        reasoning.append("Signal quality: PASS")
        
        # Layer 2: Technical Analysis
        technical_score = analysis_result.metadata.get('technical_score', 0)
        if technical_score < self.confidence_thresholds['technical_analysis']:
            return DecisionResult(
                approved=False,
                action="REJECT",
                confidence=analysis_result.confidence,
                reasoning="Technical analysis too weak",
                metadata={}
            )
        reasoning.append("Technical analysis: PASS")
        
        # Layer 3: AI Analysis
        ai_score = analysis_result.metadata.get('ai_score', 0)
        if ai_score < self.confidence_thresholds['ai_analysis']:
            return DecisionResult(
                approved=False,
                action="REJECT",
                confidence=analysis_result.confidence,
                reasoning="AI analysis confidence too low",
                metadata={}
            )
        reasoning.append("AI analysis: PASS")
        
        # Layer 4: Risk Assessment
        risk_result = await self._assess_risk(analysis_result, context)
        if not risk_result['approved']:
            return DecisionResult(
                approved=False,
                action="REJECT",
                confidence=analysis_result.confidence,
                reasoning=f"Risk assessment failed: {risk_result['reason']}",
                metadata={}
            )
        reasoning.append("Risk assessment: PASS")
        
        # Layer 5: Final Decision
        if analysis_result.confidence >= self.confidence_thresholds['final_decision']:
            return DecisionResult(
                approved=True,
                action=analysis_result.action,
                confidence=analysis_result.confidence,
                reasoning=" -> ".join(reasoning),
                metadata=metadata
            )
        else:
            return DecisionResult(
                approved=False,
                action="WAIT",
                confidence=analysis_result.confidence,
                reasoning="Insufficient confidence for execution",
                metadata={}
            )
            
    async def _assess_risk(self, analysis_result: AnalysisResult, context: Dict[str, Any]) -> Dict[str, Any]:
        """Assess risk for the signal"""
        # Simulate risk assessment
        symbol = context.get('symbol', 'UNKNOWN')
        
        # Simple risk check - reject if symbol is too volatile
        if symbol in ['TSLA', 'NVDA']:  # High volatility stocks
            return {
                'approved': False,
                'reason': f"Symbol {symbol} too volatile"
            }
            
        return {
            'approved': True,
            'reason': "Risk assessment passed"
        }

class ExecutionEngine:
    """Simplified execution engine for demo"""
    
    def __init__(self):
        self.trade_count = 0
        
    async def execute_trade(self, decision_result: DecisionResult, context: Dict[str, Any]):
        """Execute trade based on decision"""
        
        if decision_result.approved:
            self.trade_count += 1
            logger.info(f"✅ EXECUTING TRADE #{self.trade_count}")
            logger.info(f"   Symbol: {context.get('symbol', 'UNKNOWN')}")
            logger.info(f"   Action: {decision_result.action}")
            logger.info(f"   Confidence: {decision_result.confidence:.2f}")
            logger.info(f"   Reasoning: {decision_result.reasoning}")
            
            # Simulate trade execution
            await asyncio.sleep(0.1)  # Simulate execution time
            
            logger.info(f"✅ Trade #{self.trade_count} executed successfully")
        else:
            logger.info(f"❌ Trade rejected: {decision_result.reasoning}")

class TradingSystem:
    """Main trading system orchestrator"""
    
    def __init__(self):
        self.event_gateway = EventGateway()
        self.analysis_engine = AnalysisEngine()
        self.decision_tree = DecisionTreeEngine()
        self.execution_engine = ExecutionEngine()
        
        # Register event handlers
        self._register_handlers()
        
    def _register_handlers(self):
        """Register event handlers"""
        self.event_gateway.register_handler(EventType.MARKET_DATA, self._handle_market_data)
        self.event_gateway.register_handler(EventType.NEWS_EVENT, self._handle_news_event)
        self.event_gateway.register_handler(EventType.USER_COMMAND, self._handle_user_command)
        
    async def start(self):
        """Start the trading system"""
        logger.info("🚀 Starting Event-Driven Trading System...")
        await self.event_gateway.start()
        logger.info("✅ Trading System started")
        
    async def stop(self):
        """Stop the trading system"""
        logger.info("🛑 Stopping Trading System...")
        await self.event_gateway.stop()
        logger.info("✅ Trading System stopped")
        
    async def _handle_market_data(self, event: Event):
        """Handle market data events"""
        logger.info(f"📊 Processing market data for {event.data.get('symbol', 'UNKNOWN')}")
        
        # Analyze market data
        analysis_result = await self.analysis_engine.analyze_event(event)
        
        if analysis_result:
            # Evaluate through decision tree
            context = {
                'symbol': event.data.get('symbol'),
                'current_price': event.data.get('price'),
                'timestamp': event.timestamp
            }
            
            decision_result = await self.decision_tree.evaluate_signal(
                analysis_result, context
            )
            
            # Execute trade if approved
            await self.execution_engine.execute_trade(decision_result, context)
            
    async def _handle_news_event(self, event: Event):
        """Handle news events"""
        logger.info(f"📰 Processing news event: {event.data.get('headline', 'No headline')}")
        
        # Analyze news impact
        analysis_result = await self.analysis_engine.analyze_event(event)
        
        if analysis_result:
            # Evaluate through decision tree
            context = {
                'symbol': event.data.get('symbol'),
                'news_impact': event.data.get('impact'),
                'timestamp': event.timestamp
            }
            
            decision_result = await self.decision_tree.evaluate_signal(
                analysis_result, context
            )
            
            # Execute trade if approved
            await self.execution_engine.execute_trade(decision_result, context)
            
    async def _handle_user_command(self, event: Event):
        """Handle user commands"""
        command = event.data.get('command')
        logger.info(f"👤 User command: {command}")
        
        if command == 'status':
            logger.info("📊 System Status: Running")
        elif command == 'stop':
            logger.info("🛑 User requested system stop")
            await self.stop()

async def generate_demo_events(trading_system: TradingSystem):
    """Generate demo events to test the system"""
    
    symbols = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA']
    
    # Generate market data events
    for i in range(10):
        symbol = symbols[i % len(symbols)]
        price = 100 + (i * 5) + (i % 3 * 10)  # Varying prices
        volume = 1000000 + (i * 100000)
        
        event = Event(
            event_id=str(uuid.uuid4()),
            event_type=EventType.MARKET_DATA,
            data={
                'symbol': symbol,
                'price': price,
                'volume': volume,
                'timestamp': datetime.now()
            },
            timestamp=datetime.now(),
            source='demo_market_data'
        )
        
        await trading_system.event_gateway.publish_event(event)
        await asyncio.sleep(1)  # Wait between events
        
    # Generate news events
    news_events = [
        {
            'symbol': 'AAPL',
            'headline': 'Apple reports strong Q4 earnings',
            'sentiment': 0.8,
            'impact': 'high'
        },
        {
            'symbol': 'TSLA',
            'headline': 'Tesla faces regulatory challenges',
            'sentiment': -0.6,
            'impact': 'medium'
        },
        {
            'symbol': 'GOOGL',
            'headline': 'Google announces new AI breakthrough',
            'sentiment': 0.7,
            'impact': 'high'
        }
    ]
    
    for news in news_events:
        event = Event(
            event_id=str(uuid.uuid4()),
            event_type=EventType.NEWS_EVENT,
            data=news,
            timestamp=datetime.now(),
            source='demo_news'
        )
        
        await trading_system.event_gateway.publish_event(event)
        await asyncio.sleep(2)  # Wait between news events

async def main():
    """Main demo function"""
    logger.info("🚀 Starting Event-Driven Trading System Demo")
    
    # Create trading system
    trading_system = TradingSystem()
    
    try:
        # Start the system
        await trading_system.start()
        
        # Generate demo events
        logger.info("📡 Generating demo events...")
        await generate_demo_events(trading_system)
        
        # Wait for events to be processed
        logger.info("⏳ Waiting for event processing...")
        await asyncio.sleep(5)
        
        # Send status command
        status_event = Event(
            event_id=str(uuid.uuid4()),
            event_type=EventType.USER_COMMAND,
            data={'command': 'status'},
            timestamp=datetime.now(),
            source='demo_user'
        )
        await trading_system.event_gateway.publish_event(status_event)
        
        # Wait a bit more
        await asyncio.sleep(2)
        
        logger.info("✅ Demo completed successfully!")
        
    except KeyboardInterrupt:
        logger.info("🛑 Demo interrupted by user")
    except Exception as e:
        logger.error(f"❌ Demo error: {e}")
    finally:
        # Stop the system
        await trading_system.stop()

if __name__ == "__main__":
    # Run the demo
    asyncio.run(main()) 