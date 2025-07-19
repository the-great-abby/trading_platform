#!/usr/bin/env python3
"""
LLM Trade Evaluator
===================
Evaluates trade signals using LLM analysis before execution.
Tracks performance of LLM recommendations vs original signals.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd

from src.services.ai.ollama_service import OllamaService
from src.core.types import TradeSignal
from src.utils.enhanced_logging import get_trading_logger

logger = get_trading_logger()

class TradeEvaluator:
    """
    LLM-based trade signal evaluator
    
    Features:
    - Evaluates trade signals before execution
    - Tracks LLM performance vs original signals
    - Provides confidence scores and reasoning
    - Generates performance reports
    """
    
    def __init__(self, model_name: str = "gemma3:1b"):
        self.ollama_service = OllamaService(model=model_name)
        self.evaluations = []
        self.performance_stats = {
            'total_signals': 0,
            'llm_approved': 0,
            'llm_rejected': 0,
            'approved_correct': 0,
            'approved_incorrect': 0,
            'rejected_correct': 0,
            'rejected_incorrect': 0,
            'llm_accuracy': 0.0,
            'llm_confidence_avg': 0.0
        }
    
    async def evaluate_trade_signal(self, signal: TradeSignal, market_data: pd.DataFrame, 
                                  strategy_name: str) -> Dict[str, Any]:
        """
        Evaluate a trade signal using LLM analysis
        
        Args:
            signal: Trade signal to evaluate
            market_data: Recent market data for context
            strategy_name: Name of the strategy that generated the signal
            
        Returns:
            Dictionary with evaluation results
        """
        try:
            # Prepare context for LLM
            context = self._prepare_evaluation_context(signal, market_data, strategy_name)
            
            # Generate LLM prompt
            prompt = self._generate_evaluation_prompt(context)
            
            # Get LLM evaluation
            response = await self.ollama_service._call_ollama(prompt)
            
            # Parse LLM response
            evaluation = self._parse_evaluation_response(response, signal)
            
            # Store evaluation
            evaluation['timestamp'] = datetime.now()
            evaluation['signal'] = signal
            evaluation['strategy'] = strategy_name
            self.evaluations.append(evaluation)
            
            logger.info(f"🔍 LLM Evaluation: {signal.symbol} {signal.action} - "
                       f"Approved: {evaluation['approved']}, "
                       f"Confidence: {evaluation['confidence']:.2f}, "
                       f"Reason: {evaluation['reason'][:100]}...")
            
            return evaluation
            
        except Exception as e:
            logger.error(f"❌ Error evaluating trade signal: {str(e)}")
            # Default to approve if LLM fails
            return {
                'approved': True,
                'confidence': 0.5,
                'reason': f"LLM evaluation failed: {str(e)}",
                'timestamp': datetime.now(),
                'signal': signal,
                'strategy': strategy_name
            }
    
    def _prepare_evaluation_context(self, signal: TradeSignal, market_data: pd.DataFrame, 
                                  strategy_name: str) -> Dict[str, Any]:
        """Prepare context for LLM evaluation"""
        
        # Get recent price data
        recent_data = market_data.tail(20) if len(market_data) >= 20 else market_data
        
        # Calculate basic metrics
        current_price = signal.price
        price_change_1d = ((current_price - recent_data['Close'].iloc[-2]) / recent_data['Close'].iloc[-2] * 100) if len(recent_data) > 1 else 0
        price_change_5d = ((current_price - recent_data['Close'].iloc[-6]) / recent_data['Close'].iloc[-6] * 100) if len(recent_data) > 5 else 0
        volatility = recent_data['Close'].pct_change().std() * 100
        
        # Get signal metadata
        signal_metadata = signal.metadata or {}
        
        context = {
            'symbol': signal.symbol,
            'action': signal.action,
            'price': current_price,
            'quantity': signal.quantity,
            'strategy': strategy_name,
            'confidence': signal.confidence,
            'price_change_1d': price_change_1d,
            'price_change_5d': price_change_5d,
            'volatility': volatility,
            'signal_metadata': signal_metadata,
            'recent_prices': recent_data['Close'].tail(5).tolist()
        }
        
        return context
    
    def _generate_evaluation_prompt(self, context: Dict[str, Any]) -> str:
        """Generate LLM prompt for trade evaluation"""
        
        prompt = f"""
You are an expert trading analyst. Evaluate this trade signal and provide a recommendation.

TRADE SIGNAL:
- Symbol: {context['symbol']}
- Action: {context['action']}
- Price: ${context['price']:.2f}
- Quantity: {context['quantity']}
- Strategy: {context['strategy']}
- Signal Confidence: {context['confidence']:.2f}

MARKET CONTEXT:
- 1-day price change: {context['price_change_1d']:.2f}%
- 5-day price change: {context['price_change_5d']:.2f}%
- Volatility: {context['volatility']:.2f}%
- Recent prices: {context['recent_prices']}

SIGNAL METADATA:
{context['signal_metadata']}

EVALUATION TASK:
Analyze this trade signal considering:
1. Market conditions and trends
2. Signal strength and timing
3. Risk/reward ratio
4. Strategy logic

Provide your evaluation in this exact JSON format:
{{
    "approved": true/false,
    "confidence": 0.0-1.0,
    "reason": "detailed explanation",
    "risk_level": "low/medium/high",
    "expected_return": "positive/negative/neutral"
}}

RESPONSE:
"""
        return prompt
    
    def _parse_evaluation_response(self, response: str, signal: TradeSignal) -> Dict[str, Any]:
        """Parse LLM evaluation response"""
        
        try:
            # Extract JSON from response
            import json
            import re
            
            # Find JSON in response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                evaluation_data = json.loads(json_match.group())
            else:
                # Fallback parsing
                evaluation_data = {
                    'approved': 'approved' in response.lower(),
                    'confidence': 0.5,
                    'reason': response,
                    'risk_level': 'medium',
                    'expected_return': 'neutral'
                }
            
            return {
                'approved': evaluation_data.get('approved', True),
                'confidence': float(evaluation_data.get('confidence', 0.5)),
                'reason': evaluation_data.get('reason', 'No reason provided'),
                'risk_level': evaluation_data.get('risk_level', 'medium'),
                'expected_return': evaluation_data.get('expected_return', 'neutral')
            }
            
        except Exception as e:
            logger.error(f"❌ Error parsing LLM response: {str(e)}")
            return {
                'approved': True,
                'confidence': 0.5,
                'reason': f"Failed to parse LLM response: {str(e)}",
                'risk_level': 'medium',
                'expected_return': 'neutral'
            }
    
    def update_performance(self, signal_id: str, actual_pnl: float):
        """Update performance statistics after trade completion"""
        
        # Find the evaluation for this signal
        for evaluation in self.evaluations:
            if (evaluation['signal'].symbol == signal_id.split('_')[0] and 
                evaluation['signal'].timestamp == signal_id.split('_')[1]):
                
                # Update statistics
                self.performance_stats['total_signals'] += 1
                
                if evaluation['approved']:
                    self.performance_stats['llm_approved'] += 1
                    if actual_pnl > 0:
                        self.performance_stats['approved_correct'] += 1
                    else:
                        self.performance_stats['approved_incorrect'] += 1
                else:
                    self.performance_stats['llm_rejected'] += 1
                    if actual_pnl <= 0:
                        self.performance_stats['rejected_correct'] += 1
                    else:
                        self.performance_stats['rejected_incorrect'] += 1
                
                # Update accuracy
                correct = (self.performance_stats['approved_correct'] + 
                          self.performance_stats['rejected_correct'])
                total = self.performance_stats['total_signals']
                self.performance_stats['llm_accuracy'] = correct / total if total > 0 else 0.0
                
                # Update average confidence
                confidences = [e['confidence'] for e in self.evaluations if 'confidence' in e]
                self.performance_stats['llm_confidence_avg'] = sum(confidences) / len(confidences) if confidences else 0.0
                
                break
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        
        return {
            'llm_performance': self.performance_stats,
            'evaluations_summary': {
                'total_evaluations': len(self.evaluations),
                'approval_rate': (self.performance_stats['llm_approved'] / 
                                self.performance_stats['total_signals'] * 100) if self.performance_stats['total_signals'] > 0 else 0,
                'accuracy': self.performance_stats['llm_accuracy'] * 100,
                'average_confidence': self.performance_stats['llm_confidence_avg']
            },
            'recent_evaluations': self.evaluations[-10:] if self.evaluations else []
        }
    
    def reset_performance(self):
        """Reset performance statistics"""
        self.evaluations = []
        self.performance_stats = {
            'total_signals': 0,
            'llm_approved': 0,
            'llm_rejected': 0,
            'approved_correct': 0,
            'approved_incorrect': 0,
            'rejected_correct': 0,
            'rejected_incorrect': 0,
            'llm_accuracy': 0.0,
            'llm_confidence_avg': 0.0
        } 