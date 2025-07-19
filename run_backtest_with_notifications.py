#!/usr/bin/env python3
"""
Backtest Runner with Email Notifications
"""

import os
import sys
import asyncio
import httpx
from datetime import datetime
from loguru import logger

# Add src to path
sys.path.append('/app/src')

from backtesting.engine.backtest_engine import BacktestEngine
from utils.config import get_config
from services.market_data.market_data_provider import MarketDataProvider
from services.market_data.cached_market_data_manager import CachedMarketDataManager

async def send_completion_notification(job_id: str, results: dict, user_email: str, notification_service_url: str):
    """Send completion notification to user"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{notification_service_url}/api/send-notification",
                json={
                    "job_id": job_id,
                    "user_email": user_email,
                    "notification_type": "backtest_completion",
                    "results": results
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                logger.info(f"✅ Email notification sent successfully to {user_email}")
            else:
                logger.error(f"❌ Failed to send email notification: {response.status_code} - {response.text}")
                
    except Exception as e:
        logger.error(f"❌ Error sending email notification: {e}")

async def main():
    """Main backtest execution with notifications"""
    
    # Get configuration
    config = get_config()
    
    # Check if email notifications are enabled
    enable_notifications = os.getenv('ENABLE_EMAIL_NOTIFICATIONS', 'false').lower() in ('true', '1', 'yes')
    user_email = os.getenv('USER_EMAIL', '')
    notification_service_url = os.getenv('NOTIFICATION_SERVICE_URL', 'http://notification-service:80')
    
    # Get job ID from environment or generate one
    job_id = os.getenv('JOB_NAME', f"backtest-{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    
    logger.info(f"🚀 Starting backtest with notifications enabled: {enable_notifications}")
    if enable_notifications:
        logger.info(f"📧 Email notifications will be sent to: {user_email}")
    
    try:
        # Initialize backtest engine
        engine = BacktestEngine()
        
        # Get backtest parameters from environment
        symbols = os.getenv('BACKTEST_SYMBOLS', 'AAPL,GOOGL,MSFT').split(',')
        start_date = os.getenv('BACKTEST_START_DATE', '2023-01-01')
        end_date = os.getenv('BACKTEST_END_DATE', '2025-01-01')
        initial_capital = float(os.getenv('BACKTEST_INITIAL_CAPITAL', '100000'))
        risk_profile = os.getenv('BACKTEST_RISK_PROFILE', 'moderate')
        strategies = os.getenv('BACKTEST_STRATEGIES', 'BollingerBands,RSI,MACD').split(',')
        
        logger.info(f"📊 Running backtest with parameters:")
        logger.info(f"   Symbols: {symbols}")
        logger.info(f"   Date Range: {start_date} to {end_date}")
        logger.info(f"   Initial Capital: ${initial_capital:,.2f}")
        logger.info(f"   Risk Profile: {risk_profile}")
        logger.info(f"   Strategies: {strategies}")
        
        # Run backtest
        results = await engine.run_backtest(
            symbols=symbols,
            start_date=start_date,
            end_date=end_date,
            initial_capital=initial_capital,
            risk_profile=risk_profile,
            strategies=strategies
        )
        
        # Store results
        await engine.store_results(
            results=results,
            symbols=symbols,
            start_date=start_date,
            end_date=end_date,
            database_only=os.getenv('DATABASE_ONLY', 'false').lower() in ('true', '1', 'yes')
        )
        
        # Prepare results summary for email
        results_summary = {
            "total_return_pct": 0.0,
            "sharpe_ratio": 0.0,
            "max_drawdown_pct": 0.0,
            "total_trades": 0,
            "win_rate": 0.0,
            "strategies": strategies,
            "symbols": symbols
        }
        
        # Extract metrics from results
        if results:
            for strategy_name, result in results.items():
                if hasattr(result, 'total_return_pct'):
                    results_summary["total_return_pct"] = result.total_return_pct
                if hasattr(result, 'sharpe_ratio'):
                    results_summary["sharpe_ratio"] = result.sharpe_ratio
                if hasattr(result, 'max_drawdown_pct'):
                    results_summary["max_drawdown_pct"] = result.max_drawdown_pct
                if hasattr(result, 'total_trades'):
                    results_summary["total_trades"] = result.total_trades
                if hasattr(result, 'win_rate'):
                    results_summary["win_rate"] = result.win_rate
                break  # Use first result for summary
        
        logger.info(f"✅ Backtest completed successfully!")
        logger.info(f"   Total Return: {results_summary['total_return_pct']:.2f}%")
        logger.info(f"   Sharpe Ratio: {results_summary['sharpe_ratio']:.2f}")
        logger.info(f"   Max Drawdown: {results_summary['max_drawdown_pct']:.2f}%")
        logger.info(f"   Total Trades: {results_summary['total_trades']}")
        logger.info(f"   Win Rate: {results_summary['win_rate']:.1%}")
        
        # Send email notification if enabled
        if enable_notifications and user_email:
            await send_completion_notification(
                job_id=job_id,
                results=results_summary,
                user_email=user_email,
                notification_service_url=notification_service_url
            )
        else:
            logger.info("📧 Email notifications not enabled or no email provided")
            
    except Exception as e:
        logger.error(f"❌ Backtest failed: {e}")
        
        # Send failure notification if enabled
        if enable_notifications and user_email:
            try:
                await send_completion_notification(
                    job_id=job_id,
                    results={
                        "total_return_pct": 0.0,
                        "sharpe_ratio": 0.0,
                        "max_drawdown_pct": 0.0,
                        "total_trades": 0,
                        "win_rate": 0.0,
                        "strategies": strategies,
                        "symbols": symbols,
                        "error": str(e)
                    },
                    user_email=user_email,
                    notification_service_url=notification_service_url
                )
            except Exception as notify_error:
                logger.error(f"❌ Failed to send failure notification: {notify_error}")
        
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 