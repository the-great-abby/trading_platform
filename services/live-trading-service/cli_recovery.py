#!/usr/bin/env python3
"""
Trade Recovery CLI Tool

Lightweight command-line tool for trade recovery operations.
Zero persistent resource usage - runs on-demand only.
"""

import asyncio
import argparse
import json
import logging
import sys
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.services.live_trading.recovery_service import RecoveryService
from src.services.live_trading.recovery_models import (
    RecoverySessionCreate, RecoveryType, AssignmentReason
)
from src.services.live_trading.database import init_database, close_database, async_session_maker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TradeRecoveryCLI:
    """Command-line interface for trade recovery operations"""
    
    def __init__(self):
        """Initialize CLI"""
        self.db_session = None
    
    async def initialize(self):
        """Initialize database connection"""
        try:
            await init_database()
            self.db_session = async_session_maker()
            logger.info("Database connection initialized")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    async def cleanup(self):
        """Cleanup database connection"""
        try:
            if self.db_session:
                await self.db_session.close()
            await close_database()
            logger.info("Database connection closed")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    async def detect_trades(self, account_id: str, include_closed: bool = False) -> List[Dict[str, Any]]:
        """Detect active trades for an account"""
        try:
            async with self.db_session() as db:
                recovery_service = RecoveryService(db)
                trades = await recovery_service.detect_active_trades(account_id, include_closed)
                
                return [
                    {
                        "id": trade.id,
                        "symbol": trade.symbol,
                        "side": trade.side.value,
                        "quantity": float(trade.quantity),
                        "entry_price": float(trade.entry_price),
                        "current_price": float(trade.current_price) if trade.current_price else None,
                        "unrealized_pnl": float(trade.unrealized_pnl) if trade.unrealized_pnl else None,
                        "entry_time": trade.entry_time.isoformat(),
                        "position_type": trade.position_type.value
                    }
                    for trade in trades
                ]
                
        except Exception as e:
            logger.error(f"Failed to detect trades: {e}")
            raise
    
    async def create_session(self, account_id: str, recovery_type: str, description: str = "") -> str:
        """Create a recovery session"""
        try:
            async with self.db_session() as db:
                recovery_service = RecoveryService(db)
                
                session_data = RecoverySessionCreate(
                    account_id=account_id,
                    recovery_type=RecoveryType(recovery_type),
                    description=description
                )
                
                session = await recovery_service.create_recovery_session(session_data)
                return session.id
                
        except Exception as e:
            logger.error(f"Failed to create recovery session: {e}")
            raise
    
    async def match_strategies(self, trade_id: str, session_id: str) -> List[Dict[str, Any]]:
        """Match strategies for a trade"""
        try:
            async with self.db_session() as db:
                recovery_service = RecoveryService(db)
                matches = await recovery_service.match_strategies_for_trade(trade_id, session_id)
                
                return [
                    {
                        "strategy_id": match.strategy_id,
                        "strategy_name": match.strategy_name,
                        "confidence_score": match.confidence_score,
                        "match_reason": match.match_reason,
                        "market_conditions": match.market_conditions
                    }
                    for match in matches
                ]
                
        except Exception as e:
            logger.error(f"Failed to match strategies: {e}")
            raise
    
    async def assign_strategy(self, session_id: str, trade_id: str, strategy_id: str, 
                           strategy_name: str, confidence_score: float, auto_assign: bool = True) -> str:
        """Assign a strategy to a trade"""
        try:
            async with self.db_session() as db:
                recovery_service = RecoveryService(db)
                
                assignment_request = StrategyAssignmentRequest(
                    session_id=session_id,
                    trade_id=trade_id,
                    strategy_id=strategy_id,
                    strategy_name=strategy_name,
                    confidence_score=confidence_score,
                    assignment_reason=AssignmentReason.HIGH_CONFIDENCE_MATCH,
                    auto_assigned=auto_assign
                )
                
                assignment = await recovery_service.assign_strategy_to_trade(assignment_request)
                
                if not assignment:
                    raise Exception("Failed to create assignment")
                
                return assignment.id
                
        except Exception as e:
            logger.error(f"Failed to assign strategy: {e}")
            raise
    
    async def bulk_assign(self, session_id: str, auto_assign: bool = True) -> Dict[str, Any]:
        """Bulk assign strategies to all trades in a session"""
        try:
            async with self.db_session() as db:
                recovery_service = RecoveryService(db)
                results = await recovery_service.bulk_assign_strategies(session_id, auto_assign)
                
                return {
                    "total_processed": len(results),
                    "successful": len([r for r in results if r.get("success", False)]),
                    "failed": len([r for r in results if not r.get("success", False)]),
                    "results": results
                }
                
        except Exception as e:
            logger.error(f"Failed to bulk assign strategies: {e}")
            raise
    
    async def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """Get recovery session status"""
        try:
            async with self.db_session() as db:
                recovery_service = RecoveryService(db)
                status = await recovery_service.get_recovery_session_status(session_id)
                
                if not status:
                    raise Exception("Session not found")
                
                return {
                    "session_id": status.session_id,
                    "status": status.status.value,
                    "progress": {
                        "total_trades_detected": status.progress.total_trades_detected,
                        "trades_processed": status.progress.trades_processed,
                        "trades_assigned": status.progress.trades_assigned,
                        "completion_percentage": status.progress.completion_percentage
                    },
                    "last_updated": status.last_updated.isoformat()
                }
                
        except Exception as e:
            logger.error(f"Failed to get session status: {e}")
            raise
    
    async def interactive_mode(self, account_id: str):
        """Interactive recovery mode"""
        print(f"\n🔧 Trade Recovery Interactive Mode")
        print(f"Account: {account_id}")
        print("=" * 50)
        
        try:
            # Step 1: Detect trades
            print("\n1️⃣ Detecting active trades...")
            trades = await self.detect_trades(account_id)
            
            if not trades:
                print("❌ No active trades found")
                return
            
            print(f"✅ Found {len(trades)} active trades:")
            for i, trade in enumerate(trades, 1):
                print(f"   {i}. {trade['symbol']} - {trade['side']} {trade['quantity']} @ ${trade['entry_price']}")
            
            # Step 2: Create recovery session
            print("\n2️⃣ Creating recovery session...")
            session_id = await self.create_session(
                account_id, 
                "MANUAL_RECOVERY", 
                f"Interactive recovery for {len(trades)} trades"
            )
            print(f"✅ Created session: {session_id}")
            
            # Step 3: Match strategies
            print("\n3️⃣ Matching strategies...")
            for trade in trades:
                matches = await self.match_strategies(trade['id'], session_id)
                if matches:
                    best_match = max(matches, key=lambda m: m['confidence_score'])
                    print(f"   {trade['symbol']}: {best_match['strategy_name']} (confidence: {best_match['confidence_score']:.2f})")
                else:
                    print(f"   {trade['symbol']}: No matches found")
            
            # Step 4: Ask for confirmation
            print("\n4️⃣ Strategy Assignment")
            response = input("Do you want to auto-assign strategies? (y/n): ").lower().strip()
            auto_assign = response in ['y', 'yes']
            
            if auto_assign:
                print("🔄 Auto-assigning strategies...")
                results = await self.bulk_assign(session_id, auto_assign=True)
                print(f"✅ Assigned strategies to {results['successful']}/{results['total_processed']} trades")
            else:
                print("⏭️ Skipping auto-assignment")
            
            # Step 5: Show final status
            print("\n5️⃣ Final Status")
            status = await self.get_session_status(session_id)
            print(f"Session Status: {status['status']}")
            print(f"Progress: {status['progress']['completion_percentage']:.1f}%")
            print(f"Trades Detected: {status['progress']['total_trades_detected']}")
            print(f"Trades Assigned: {status['progress']['trades_assigned']}")
            
            print(f"\n✅ Recovery session completed: {session_id}")
            
        except Exception as e:
            print(f"❌ Error in interactive mode: {e}")
            raise


async def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description="Trade Recovery CLI Tool")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Detect trades command
    detect_parser = subparsers.add_parser('detect', help='Detect active trades')
    detect_parser.add_argument('--account', required=True, help='Account ID')
    detect_parser.add_argument('--include-closed', action='store_true', help='Include closed trades')
    detect_parser.add_argument('--output', help='Output file (JSON)')
    
    # Create session command
    session_parser = subparsers.add_parser('session', help='Create recovery session')
    session_parser.add_argument('--account', required=True, help='Account ID')
    session_parser.add_argument('--type', default='MANUAL_RECOVERY', help='Recovery type')
    session_parser.add_argument('--description', default='', help='Session description')
    
    # Match strategies command
    match_parser = subparsers.add_parser('match', help='Match strategies for trade')
    match_parser.add_argument('--trade-id', required=True, help='Trade ID')
    match_parser.add_argument('--session-id', required=True, help='Session ID')
    
    # Assign strategy command
    assign_parser = subparsers.add_parser('assign', help='Assign strategy to trade')
    assign_parser.add_argument('--session-id', required=True, help='Session ID')
    assign_parser.add_argument('--trade-id', required=True, help='Trade ID')
    assign_parser.add_argument('--strategy-id', required=True, help='Strategy ID')
    assign_parser.add_argument('--strategy-name', required=True, help='Strategy name')
    assign_parser.add_argument('--confidence', type=float, required=True, help='Confidence score')
    assign_parser.add_argument('--auto-assign', action='store_true', help='Auto assign')
    
    # Bulk assign command
    bulk_parser = subparsers.add_parser('bulk', help='Bulk assign strategies')
    bulk_parser.add_argument('--session-id', required=True, help='Session ID')
    bulk_parser.add_argument('--auto-assign', action='store_true', help='Auto assign')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Get session status')
    status_parser.add_argument('--session-id', required=True, help='Session ID')
    
    # Interactive command
    interactive_parser = subparsers.add_parser('interactive', help='Interactive recovery mode')
    interactive_parser.add_argument('--account', required=True, help='Account ID')
    
    # Recover command (full workflow)
    recover_parser = subparsers.add_parser('recover', help='Full recovery workflow')
    recover_parser.add_argument('--account', required=True, help='Account ID')
    recover_parser.add_argument('--session-id', help='Existing session ID')
    recover_parser.add_argument('--auto-assign', action='store_true', help='Auto assign strategies')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    cli = TradeRecoveryCLI()
    
    try:
        await cli.initialize()
        
        if args.command == 'detect':
            trades = await cli.detect_trades(args.account, args.include_closed)
            output = json.dumps(trades, indent=2, default=str)
            
            if args.output:
                with open(args.output, 'w') as f:
                    f.write(output)
                print(f"✅ Trades saved to {args.output}")
            else:
                print(output)
        
        elif args.command == 'session':
            session_id = await cli.create_session(args.account, args.type, args.description)
            print(f"✅ Created recovery session: {session_id}")
        
        elif args.command == 'match':
            matches = await cli.match_strategies(args.trade_id, args.session_id)
            print(json.dumps(matches, indent=2, default=str))
        
        elif args.command == 'assign':
            assignment_id = await cli.assign_strategy(
                args.session_id, args.trade_id, args.strategy_id, 
                args.strategy_name, args.confidence, args.auto_assign
            )
            print(f"✅ Created assignment: {assignment_id}")
        
        elif args.command == 'bulk':
            results = await cli.bulk_assign(args.session_id, args.auto_assign)
            print(f"✅ Bulk assignment completed:")
            print(f"   Total: {results['total_processed']}")
            print(f"   Successful: {results['successful']}")
            print(f"   Failed: {results['failed']}")
        
        elif args.command == 'status':
            status = await cli.get_session_status(args.session_id)
            print(json.dumps(status, indent=2, default=str))
        
        elif args.command == 'interactive':
            await cli.interactive_mode(args.account)
        
        elif args.command == 'recover':
            # Full recovery workflow
            print(f"🔧 Starting recovery for account: {args.account}")
            
            # Detect trades
            trades = await cli.detect_trades(args.account)
            if not trades:
                print("❌ No active trades found")
                return
            
            print(f"✅ Found {len(trades)} active trades")
            
            # Create or use existing session
            if args.session_id:
                session_id = args.session_id
                print(f"📋 Using existing session: {session_id}")
            else:
                session_id = await cli.create_session(args.account, "MANUAL_RECOVERY")
                print(f"✅ Created session: {session_id}")
            
            # Bulk assign strategies
            if args.auto_assign:
                print("🔄 Auto-assigning strategies...")
                results = await cli.bulk_assign(session_id, auto_assign=True)
                print(f"✅ Assigned strategies to {results['successful']}/{results['total_processed']} trades")
            
            # Show final status
            status = await cli.get_session_status(session_id)
            print(f"\n📊 Final Status:")
            print(f"   Session: {session_id}")
            print(f"   Status: {status['status']}")
            print(f"   Progress: {status['progress']['completion_percentage']:.1f}%")
            print(f"   Trades Assigned: {status['progress']['trades_assigned']}")
        
    except Exception as e:
        logger.error(f"CLI error: {e}")
        print(f"❌ Error: {e}")
        sys.exit(1)
    
    finally:
        await cli.cleanup()


if __name__ == "__main__":
    asyncio.run(main())


















