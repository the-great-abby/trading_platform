#!/usr/bin/env python3
"""
LLM Post-Processing for Backtest Trades
======================================
Loads trades from trades_for_llm.csv, evaluates each with the LLM, and saves results.
"""
import os
import pandas as pd
import logging
from src.services.ai.trade_evaluator import TradeEvaluator
from src.utils.enhanced_logging import get_trading_logger

logger = get_trading_logger()

OLLAMA_URL = os.environ.get('OLLAMA_BASE_URL', 'http://192.168.0.18:11434')
os.environ['OLLAMA_BASE_URL'] = OLLAMA_URL
os.environ['OLLAMA_TIMEOUT'] = '120.0'
os.environ['OLLAMA_MAX_RETRIES'] = '3'
os.environ['OLLAMA_BASE_DELAY'] = '5.0'
os.environ['OLLAMA_MAX_DELAY'] = '60.0'

logger.info(f"🔗 Using Ollama at {OLLAMA_URL}")

def main():
    logger.info("🤖 Starting LLM post-processing of trades...")
    if not os.path.exists('trades_for_llm.csv'):
        logger.error("❌ trades_for_llm.csv not found. Run the fast backtest first.")
        return
    df = pd.read_csv('trades_for_llm.csv')
    logger.info(f"📥 Loaded {len(df)} trades for LLM evaluation.")
    evaluator = TradeEvaluator()
    results = []
    for i, row in df.iterrows():
        signal = {
            'strategy': row['strategy'],
            'symbol': row['symbol'],
            'action': row['action'],
            'entry_price': row['entry_price'],
            'exit_price': row['exit_price'],
            'profit_loss': row['profit_loss'],
            'confidence': row.get('confidence', 0.8),
            'timestamp': row.get('timestamp', None)
        }
        try:
            llm_result = evaluator.evaluate_trade_signal(signal)
            results.append({**signal, **llm_result})
            logger.info(f"[{i+1}/{len(df)}] {signal['strategy']} {signal['symbol']} {signal['action']} -> Approved: {llm_result['approved']}, Confidence: {llm_result.get('confidence', 'N/A')}")
        except Exception as e:
            logger.warning(f"⚠️ LLM evaluation failed for {signal['strategy']} {signal['symbol']}: {str(e)}")
            results.append({**signal, 'approved': None, 'llm_error': str(e)})
    out_df = pd.DataFrame(results)
    out_df.to_csv('trades_with_llm_results.csv', index=False)
    logger.info(f"💾 Saved LLM-evaluated trades to trades_with_llm_results.csv")

if __name__ == "__main__":
    main() 