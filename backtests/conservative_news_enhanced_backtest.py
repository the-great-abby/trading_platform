#!/usr/bin/env python3
"""
Conservative News-Enhanced Market Regime Strategies Backtest
News quality scoring and conservative integration for risk management
"""

import json
import random
import numpy as np
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ConservativeNewsEnhancedBacktest:
    def __init__(self):
        self.initial_capital = 4000.0
        
        self.symbols = {
            'SPY': {'volatility': 0.15, 'avg_daily_range': 0.015, 'liquidity': 'high', 'beta': 1.0},
            'QQQ': {'volatility': 0.18, 'avg_daily_range': 0.02, 'liquidity': 'high', 'beta': 1.1},
            'AAPL': {'volatility': 0.20, 'avg_daily_range': 0.025, 'liquidity': 'high', 'beta': 0.9},
            'MSFT': {'volatility': 0.18, 'avg_daily_range': 0.02, 'liquidity': 'high', 'beta': 1.0},
            'TSLA': {'volatility': 0.35, 'avg_daily_range': 0.05, 'liquidity': 'high', 'beta': 1.8},
            'NVDA': {'volatility': 0.30, 'avg_daily_range': 0.04, 'liquidity': 'high', 'beta': 1.6}
        }
        
        # Conservative strategies with minimal news dependency
        self.strategies = {
            'ElliottWaveCorrective': {
                'base_return': 0.035,
                'volatility': 0.08,
                'win_rate': 0.68,
                'avg_win': 0.065,
                'avg_loss': 0.035,
                'trade_frequency': 0.06,
                'max_loss': 0.06,
                'profit_target': 0.65,
                'trailing_stop': 0.18,
                'market_regimes': ['corrective', 'sideways', 'low_vol'],
                'news_risk_threshold': 0.7,  # Only use high-quality news for risk management
                'news_position_reduction': 0.3,  # Reduce position size on negative news
                'news_exit_threshold': 0.8  # Exit on very negative news
            },
            'ElliottWaveImpulse': {
                'base_return': 0.045,
                'volatility': 0.10,
                'win_rate': 0.62,
                'avg_win': 0.08,
                'avg_loss': 0.045,
                'trade_frequency': 0.05,
                'max_loss': 0.07,
                'profit_target': 0.75,
                'trailing_stop': 0.12,
                'market_regimes': ['impulse', 'trending', 'bull'],
                'news_risk_threshold': 0.8,  # Higher threshold for impulse waves
                'news_position_reduction': 0.4,  # More aggressive position reduction
                'news_exit_threshold': 0.9  # Higher exit threshold
            },
            'CalendarSpreads': {
                'base_return': 0.015,
                'volatility': 0.04,
                'win_rate': 0.75,
                'avg_win': 0.04,
                'avg_loss': 0.06,
                'trade_frequency': 0.06,
                'max_loss': 0.08,
                'profit_target': 0.50,
                'trailing_stop': 0.10,
                'market_regimes': ['low_vol', 'normal', 'sideways', 'corrective'],
                'news_risk_threshold': 0.6,  # Lower threshold for calendar spreads
                'news_position_reduction': 0.2,  # Minimal position reduction
                'news_exit_threshold': 0.7  # Lower exit threshold
            },
            'IronCondor': {
                'base_return': 0.025,
                'volatility': 0.06,
                'win_rate': 0.70,
                'avg_win': 0.06,
                'avg_loss': 0.15,
                'trade_frequency': 0.08,
                'max_loss': 0.15,
                'profit_target': 0.40,
                'trailing_stop': 0.15,
                'market_regimes': ['low_vol', 'normal', 'sideways'],
                'news_risk_threshold': 0.5,  # Very low threshold
                'news_position_reduction': 0.1,  # Minimal reduction
                'news_exit_threshold': 0.6  # Very low exit threshold
            }
        }
        
        # Enhanced news quality scoring system
        self.news_quality_criteria = {
            'source_reliability': {
                'tier_1': {'weight': 0.3, 'sources': ['Fed', 'SEC', 'Earnings', 'Major Banks']},
                'tier_2': {'weight': 0.2, 'sources': ['Reuters', 'Bloomberg', 'WSJ', 'CNBC']},
                'tier_3': {'weight': 0.1, 'sources': ['Social Media', 'Blogs', 'Forums']}
            },
            'impact_magnitude': {
                'high': {'weight': 0.25, 'threshold': 0.8, 'examples': ['Fed Rate Decision', 'Earnings Beat/Miss', 'Geopolitical Crisis']},
                'medium': {'weight': 0.15, 'threshold': 0.5, 'examples': ['Economic Data', 'Sector News', 'Company Updates']},
                'low': {'weight': 0.05, 'threshold': 0.2, 'examples': ['Minor Updates', 'Rumors', 'Speculation']}
            },
            'sentiment_confidence': {
                'high': {'weight': 0.2, 'threshold': 0.8, 'criteria': 'Clear positive/negative sentiment'},
                'medium': {'weight': 0.1, 'threshold': 0.5, 'criteria': 'Mixed or neutral sentiment'},
                'low': {'weight': 0.05, 'threshold': 0.2, 'criteria': 'Unclear or conflicting sentiment'}
            },
            'market_correlation': {
                'high': {'weight': 0.15, 'threshold': 0.7, 'criteria': 'Strong correlation with market movements'},
                'medium': {'weight': 0.1, 'threshold': 0.4, 'criteria': 'Moderate correlation'},
                'low': {'weight': 0.05, 'threshold': 0.1, 'criteria': 'Weak correlation'}
            }
        }
        
        # News categories with quality weights
        self.news_categories = {
            'fed_policy': {
                'base_quality': 0.9, 'impact_duration': 5, 'volatility_boost': 2.0,
                'risk_management_weight': 0.8, 'delay_hours': 2
            },
            'earnings': {
                'base_quality': 0.85, 'impact_duration': 3, 'volatility_boost': 1.5,
                'risk_management_weight': 0.7, 'delay_hours': 1
            },
            'economic_data': {
                'base_quality': 0.8, 'impact_duration': 2, 'volatility_boost': 1.3,
                'risk_management_weight': 0.6, 'delay_hours': 1
            },
            'sector_news': {
                'base_quality': 0.7, 'impact_duration': 1, 'volatility_boost': 1.2,
                'risk_management_weight': 0.5, 'delay_hours': 0.5
            },
            'geopolitical': {
                'base_quality': 0.75, 'impact_duration': 7, 'volatility_boost': 2.5,
                'risk_management_weight': 0.9, 'delay_hours': 4
            }
        }
        
        self.public_com_costs = {
            'commission_per_trade': 0.0,
            'commission_per_contract': 0.0,
            'options_rebate_per_contract': 0.06,
            'bid_ask_spread': 0.001,
            'slippage': 0.0003,
            'financing_cost': 0.0001,
            'max_daily_trades': 3,
            'min_trade_size': 100,
            'max_position_size': 0.10,
            'contracts_per_trade': 2
        }
    
    def calculate_news_quality_score(self, news_event):
        """Calculate comprehensive news quality score"""
        quality_score = 0.0
        
        # Source reliability scoring
        source_tier = self._get_source_tier(news_event.get('source', 'tier_3'))
        quality_score += self.news_quality_criteria['source_reliability'][source_tier]['weight']
        
        # Impact magnitude scoring
        impact_level = self._get_impact_level(news_event.get('impact_score', 0.5))
        quality_score += self.news_quality_criteria['impact_magnitude'][impact_level]['weight']
        
        # Sentiment confidence scoring
        sentiment_confidence = abs(news_event.get('sentiment', 0))
        if sentiment_confidence > 0.8:
            confidence_level = 'high'
        elif sentiment_confidence > 0.5:
            confidence_level = 'medium'
        else:
            confidence_level = 'low'
        quality_score += self.news_quality_criteria['sentiment_confidence'][confidence_level]['weight']
        
        # Market correlation scoring (simplified)
        correlation_level = self._get_correlation_level(news_event.get('category', 'sector_news'))
        quality_score += self.news_quality_criteria['market_correlation'][correlation_level]['weight']
        
        # Category-specific quality boost
        category = news_event.get('category', 'sector_news')
        if category in self.news_categories:
            quality_score *= self.news_categories[category]['base_quality']
        
        return min(1.0, max(0.0, quality_score))
    
    def _get_source_tier(self, source):
        """Determine source reliability tier"""
        if source in self.news_quality_criteria['source_reliability']['tier_1']['sources']:
            return 'tier_1'
        elif source in self.news_quality_criteria['source_reliability']['tier_2']['sources']:
            return 'tier_2'
        else:
            return 'tier_3'
    
    def _get_impact_level(self, impact_score):
        """Determine impact magnitude level"""
        if impact_score >= 0.8:
            return 'high'
        elif impact_score >= 0.5:
            return 'medium'
        else:
            return 'low'
    
    def _get_correlation_level(self, category):
        """Determine market correlation level"""
        if category in ['fed_policy', 'geopolitical']:
            return 'high'
        elif category in ['earnings', 'economic_data']:
            return 'medium'
        else:
            return 'low'
    
    def generate_high_quality_news_data(self, days):
        """Generate realistic high-quality news data"""
        news_data = []
        
        for day in range(days):
            daily_news = []
            
            # Fewer but higher quality news events
            num_events = np.random.poisson(1.5)  # Reduced from 2.5
            
            for _ in range(num_events):
                # Select news category with quality weighting
                categories = list(self.news_categories.keys())
                weights = [self.news_categories[cat]['base_quality'] for cat in categories]
                category = np.random.choice(categories, p=np.array(weights)/sum(weights))
                
                # Generate higher quality sentiment
                base_sentiment = np.random.normal(0, 0.2)  # Reduced volatility
                
                # Add market cycle correlation
                cycle_factor = np.sin(day / 50) * 0.15  # Reduced cycle impact
                sentiment = np.clip(base_sentiment + cycle_factor, -1, 1)
                
                # Generate higher impact scores
                impact_score = np.random.beta(3, 3)  # More centered distribution
                
                # Generate source based on category
                if category == 'fed_policy':
                    source = np.random.choice(['Fed', 'SEC', 'Major Banks'])
                elif category == 'earnings':
                    source = np.random.choice(['Earnings', 'Reuters', 'Bloomberg'])
                elif category == 'economic_data':
                    source = np.random.choice(['Reuters', 'Bloomberg', 'WSJ'])
                else:
                    source = np.random.choice(['Reuters', 'Bloomberg', 'CNBC'])
                
                news_event = {
                    'category': category,
                    'sentiment': sentiment,
                    'impact_score': impact_score,
                    'timestamp': day,
                    'symbol': np.random.choice(list(self.symbols.keys())),
                    'headline': f"{category.replace('_', ' ').title()} news",
                    'confidence': np.random.uniform(0.7, 0.95),  # Higher confidence
                    'source': source
                }
                
                # Calculate quality score
                news_event['quality_score'] = self.calculate_news_quality_score(news_event)
                
                # Only include high-quality news
                if news_event['quality_score'] >= 0.6:
                    daily_news.append(news_event)
            
            # Calculate daily aggregate sentiment (only from high-quality news)
            if daily_news:
                weighted_sentiment = sum(
                    event['sentiment'] * event['impact_score'] * event['confidence'] * event['quality_score']
                    for event in daily_news
                ) / sum(event['impact_score'] * event['confidence'] * event['quality_score'] for event in daily_news)
                
                avg_quality = np.mean([event['quality_score'] for event in daily_news])
            else:
                weighted_sentiment = 0.0
                avg_quality = 0.0
            
            news_data.append({
                'day': day,
                'events': daily_news,
                'aggregate_sentiment': weighted_sentiment,
                'avg_quality_score': avg_quality,
                'volatility_impact': sum(
                    event['impact_score'] * self.news_categories[event['category']]['volatility_boost']
                    for event in daily_news
                ) / max(1, len(daily_news))
            })
        
        return news_data
    
    def detect_market_regime_conservative(self, day, news_data):
        """Conservative market regime detection with minimal news dependency"""
        # Base regime detection (primary)
        base_regime = self.detect_base_market_regime(day)
        
        # Get recent high-quality news
        recent_news = news_data[max(0, day-3):day+1]  # Shorter lookback
        high_quality_news = [n for n in recent_news if n['avg_quality_score'] >= 0.7]
        
        if high_quality_news:
            avg_sentiment = np.mean([n['aggregate_sentiment'] for n in high_quality_news])
            avg_quality = np.mean([n['avg_quality_score'] for n in high_quality_news])
        else:
            avg_sentiment = 0.0
            avg_quality = 0.0
        
        # Conservative news adjustment (minimal impact)
        news_adjusted_regime = self._conservative_adjust_regime_for_news(base_regime, avg_sentiment, avg_quality)
        
        return news_adjusted_regime
    
    def detect_base_market_regime(self, day):
        """Base market regime detection (simplified)"""
        regime_cycle = day % 100
        
        if regime_cycle < 25:
            return {'regime': 'bull', 'confidence': 0.8, 'volatility': 0.7, 'trend': 0.03}
        elif regime_cycle < 35:
            return {'regime': 'trending', 'confidence': 0.7, 'volatility': 0.8, 'trend': 0.02}
        elif regime_cycle < 50:
            return {'regime': 'normal', 'confidence': 0.6, 'volatility': 1.0, 'trend': 0.0}
        elif regime_cycle < 65:
            return {'regime': 'sideways', 'confidence': 0.7, 'volatility': 0.9, 'trend': 0.0}
        elif regime_cycle < 75:
            return {'regime': 'corrective', 'confidence': 0.6, 'volatility': 1.1, 'trend': -0.01}
        elif regime_cycle < 85:
            return {'regime': 'low_vol', 'confidence': 0.8, 'volatility': 0.6, 'trend': 0.01}
        else:
            return {'regime': 'impulse', 'confidence': 0.7, 'volatility': 0.8, 'trend': 0.025}
    
    def _conservative_adjust_regime_for_news(self, base_regime, sentiment, quality):
        """Conservative news adjustment - minimal impact"""
        adjusted_regime = base_regime.copy()
        
        # Only adjust if news quality is very high
        if quality < 0.8:
            return adjusted_regime
        
        # Minimal volatility adjustment
        sentiment_vol_adjustment = sentiment * 0.1  # Reduced from 0.2
        adjusted_regime['volatility'] *= (1 + sentiment_vol_adjustment)
        
        # Minimal trend adjustment
        sentiment_trend_adjustment = sentiment * 0.005  # Reduced from 0.01
        adjusted_regime['trend'] += sentiment_trend_adjustment
        
        # Only change regime for very strong sentiment
        if sentiment > 0.6 and quality > 0.9:  # Very high thresholds
            if base_regime['regime'] in ['normal', 'sideways']:
                adjusted_regime['regime'] = 'trending'
        elif sentiment < -0.6 and quality > 0.9:
            if base_regime['regime'] in ['bull', 'trending']:
                adjusted_regime['regime'] = 'corrective'
        
        return adjusted_regime
    
    def is_strategy_suitable_conservative(self, strategy_name, market_regime):
        """Conservative strategy suitability - no news dependency for entry"""
        strategy_config = self.strategies[strategy_name]
        return market_regime['regime'] in strategy_config['market_regimes']
    
    def calculate_conservative_elliott_wave_confidence(self, strategy_name, market_regime, symbol_config):
        """Conservative Elliott Wave confidence - minimal news dependency"""
        if 'ElliottWave' not in strategy_name:
            return 0.8
        
        confidence = 0.5
        
        # Base Elliott Wave confidence
        if strategy_name == 'ElliottWaveCorrective':
            if market_regime['regime'] in ['corrective', 'sideways']:
                confidence += 0.3
            if market_regime['volatility'] < 1.0:
                confidence += 0.1
        
        elif strategy_name == 'ElliottWaveImpulse':
            if market_regime['regime'] in ['impulse', 'trending', 'bull']:
                confidence += 0.3
            if market_regime['trend'] > 0.01:
                confidence += 0.2
        
        # Symbol-specific adjustments
        if symbol_config['volatility'] < 0.25:
            confidence += 0.1
        
        return min(1.0, max(0.1, confidence))
    
    def apply_news_risk_management(self, position, news_sentiment, news_quality, strategy_config):
        """Apply conservative news-based risk management"""
        risk_adjustments = {
            'position_reduction': 1.0,
            'trailing_stop_adjustment': 1.0,
            'should_exit': False
        }
        
        # Only apply if news quality is high enough
        if news_quality < strategy_config['news_risk_threshold']:
            return risk_adjustments
        
        # Position reduction on negative news
        if news_sentiment < -0.3:
            reduction_factor = 1.0 - (strategy_config['news_position_reduction'] * abs(news_sentiment))
            risk_adjustments['position_reduction'] = max(0.3, reduction_factor)
        
        # Tighter trailing stops on negative news
        if news_sentiment < -0.2:
            risk_adjustments['trailing_stop_adjustment'] = 0.8  # 20% tighter stops
        
        # Exit on very negative news
        if news_sentiment < -0.5 and news_quality > strategy_config['news_exit_threshold']:
            risk_adjustments['should_exit'] = True
        
        return risk_adjustments
    
    def run_conservative_news_backtest(self, years=2):
        """Run conservative news-enhanced backtest"""
        days = years * 252
        portfolio_value = self.initial_capital
        peak_value = self.initial_capital
        daily_pnl = []
        total_trades = 0
        total_contracts = 0
        total_rebates = 0.0
        total_new_costs = 0.0
        
        active_positions = []
        monthly_returns = []
        current_month_pnl = 0
        days_in_month = 0
        
        # Generate high-quality news data
        news_data = self.generate_high_quality_news_data(days)
        
        for day in range(days):
            daily_trade_pnl = 0
            daily_trades = 0
            daily_contracts = 0
            daily_rebates = 0.0
            daily_new_costs = 0.0
            
            # Skip weekends
            if day % 7 in [5, 6]:
                daily_pnl.append(0)
                days_in_month += 1
                if days_in_month >= 21:
                    monthly_returns.append(current_month_pnl / portfolio_value)
                    current_month_pnl = 0
                    days_in_month = 0
                continue
            
            # Get current news and market regime
            current_news = news_data[day]
            market_regime = self.detect_market_regime_conservative(day, news_data)
            news_sentiment = current_news['aggregate_sentiment']
            news_quality = current_news['avg_quality_score']
            
            # Apply news-based risk management to existing positions
            positions_to_close = []
            for i, position in enumerate(active_positions):
                strategy_config = self.strategies[position['strategy']]
                
                # Apply news risk management
                risk_adjustments = self.apply_news_risk_management(
                    position, news_sentiment, news_quality, strategy_config
                )
                
                # Exit if news indicates high risk
                if risk_adjustments['should_exit']:
                    positions_to_close.append(i)
                    daily_trade_pnl += position['current_pnl']
                    logger.info(f'News-triggered exit: {position["strategy"]} - P&L: ${position["current_pnl"]:.2f}')
                    continue
                
                # Calculate position P&L
                position_pnl = self._calculate_conservative_position_pnl(position, market_regime)
                
                # Apply news-based trailing stop adjustments
                trailing_stop_multiplier = risk_adjustments['trailing_stop_adjustment']
                
                if self._check_conservative_trailing_stop(position, position_pnl, trailing_stop_multiplier):
                    positions_to_close.append(i)
                    daily_trade_pnl += position_pnl
                    logger.info(f'Position closed: {position["strategy"]} - P&L: ${position_pnl:.2f}')
                else:
                    active_positions[i]['current_pnl'] = position_pnl
                    active_positions[i]['days_held'] += 1
            
            # Close positions
            for i in reversed(positions_to_close):
                active_positions.pop(i)
            
            # Run strategies with conservative approach
            for strategy_name, strategy_config in self.strategies.items():
                # Conservative strategy suitability (no news dependency)
                if not self.is_strategy_suitable_conservative(strategy_name, market_regime):
                    continue
                
                # Check if strategy generates a signal
                base_frequency = strategy_config['trade_frequency']
                regime_multiplier = 0.5 + (market_regime['confidence'] * 1.0)
                adjusted_frequency = base_frequency * regime_multiplier
                
                if random.random() > adjusted_frequency:
                    continue
                
                # Check daily trade limit
                if daily_trades >= self.public_com_costs['max_daily_trades']:
                    break
                
                # Check if we already have a position in this strategy
                if any(pos['strategy'] == strategy_name for pos in active_positions):
                    continue
                
                # Select symbol
                symbol = random.choice(list(self.symbols.keys()))
                symbol_config = self.symbols[symbol]
                
                # Calculate conservative Elliott Wave confidence
                wave_confidence = self.calculate_conservative_elliott_wave_confidence(
                    strategy_name, market_regime, symbol_config
                )
                
                # Skip if confidence too low
                if wave_confidence < 0.6:
                    continue
                
                # Conservative position sizing
                base_size = 0.05
                confidence_multiplier = wave_confidence
                volatility_adjustment = 1.0 - (symbol_config['volatility'] - 0.15) * 0.3
                
                # Apply news-based position reduction if negative news
                news_position_multiplier = 1.0
                if news_sentiment < -0.3 and news_quality > strategy_config['news_risk_threshold']:
                    news_position_multiplier = 1.0 - (strategy_config['news_position_reduction'] * abs(news_sentiment))
                
                position_size = min(
                    self.public_com_costs['max_position_size'], 
                    max(0.02, base_size * confidence_multiplier * volatility_adjustment * news_position_multiplier)
                )
                
                # Calculate trade size
                trade_size = position_size * portfolio_value
                
                if trade_size < self.public_com_costs['min_trade_size']:
                    continue
                
                # Calculate return
                expected_return = strategy_config['base_return'] * market_regime['volatility']
                
                # Conservative win rate calculation
                base_win_rate = strategy_config['win_rate']
                
                # Regime-based adjustments
                if market_regime['regime'] == 'bear':
                    base_win_rate *= 0.5
                elif market_regime['regime'] == 'bull':
                    base_win_rate *= 1.2
                    base_win_rate = min(0.85, base_win_rate)
                elif market_regime['regime'] == 'trending':
                    base_win_rate *= 1.1
                    base_win_rate = min(0.80, base_win_rate)
                
                # Confidence-based adjustment
                base_win_rate *= wave_confidence
                
                is_win = random.random() < base_win_rate
                
                # Calculate trade return
                if is_win:
                    trade_return = max(0.003, np.random.normal(strategy_config['avg_win'], 0.005))
                else:
                    trade_return = -min(strategy_config['max_loss'], abs(np.random.normal(strategy_config['avg_loss'], 0.005)))
                
                # Calculate contracts traded
                contracts_traded = self.public_com_costs.get('contracts_per_trade', 1)
                daily_contracts += contracts_traded
                
                # Apply trading costs
                new_commission_cost = self.public_com_costs['commission_per_trade']
                new_contract_cost = self.public_com_costs['commission_per_contract'] * contracts_traded
                new_rebate = self.public_com_costs['options_rebate_per_contract'] * contracts_traded
                new_spread_cost = trade_size * self.public_com_costs['bid_ask_spread']
                new_slippage_cost = trade_size * self.public_com_costs['slippage']
                new_total_costs = new_commission_cost + new_contract_cost + new_spread_cost + new_slippage_cost - new_rebate
                
                net_return = trade_return - (new_total_costs / trade_size)
                daily_new_costs += new_total_costs
                daily_rebates += new_rebate
                
                trade_pnl = net_return * trade_size
                
                # Create position
                position = {
                    'strategy': strategy_name,
                    'symbol': symbol,
                    'entry_price': trade_size,
                    'entry_day': day,
                    'current_pnl': trade_pnl,
                    'days_held': 0,
                    'max_profit': trade_pnl,
                    'trailing_stop_level': trade_pnl * (1 - strategy_config['trailing_stop']),
                    'profit_target': trade_pnl * strategy_config['profit_target'],
                    'max_loss': trade_pnl * (1 - strategy_config['max_loss']),
                    'wave_confidence': wave_confidence,
                    'market_regime': market_regime['regime'],
                    'news_sentiment': news_sentiment,
                    'news_quality': news_quality
                }
                
                # Check if we should take profit immediately
                if trade_pnl >= position['profit_target']:
                    daily_trade_pnl += trade_pnl
                    logger.info(f'Profit target hit for {strategy_name}: ${trade_pnl:.2f}')
                else:
                    active_positions.append(position)
                
                total_trades += 1
                daily_trades += 1
                total_new_costs += new_total_costs
            
            # Add conservative market noise
            market_noise = np.random.normal(0, 0.002) * portfolio_value
            daily_trade_pnl += market_noise
            
            # Update portfolio
            portfolio_value += daily_trade_pnl
            daily_pnl.append(daily_trade_pnl)
            current_month_pnl += daily_trade_pnl
            total_contracts += daily_contracts
            days_in_month += 1
            
            # End of month
            if days_in_month >= 21:
                monthly_returns.append(current_month_pnl / portfolio_value)
                current_month_pnl = 0
                days_in_month = 0
            
            # Apply financing cost
            portfolio_value *= (1 - self.public_com_costs['financing_cost'])
            
            # Track drawdown
            if portfolio_value > peak_value:
                peak_value = portfolio_value
            else:
                drawdown = (peak_value - portfolio_value) / peak_value
                if drawdown > 0.10:
                    logger.warning(f'Max drawdown reached on day {day}: {drawdown:.2%}')
                    break
        
        # Close remaining positions
        for position in active_positions:
            daily_trade_pnl += position['current_pnl']
        
        # Calculate final metrics
        total_return = (portfolio_value - self.initial_capital) / self.initial_capital
        annual_return = (1 + total_return) ** (365 / len(daily_pnl)) - 1
        
        # Calculate drawdown
        max_drawdown = 0
        running_max = self.initial_capital
        for pnl in daily_pnl:
            running_max += pnl
            if running_max > peak_value:
                peak_value = running_max
            drawdown = (peak_value - running_max) / peak_value
            max_drawdown = max(max_drawdown, drawdown)
        
        # Calculate Sharpe ratio
        if len(monthly_returns) > 1:
            monthly_volatility = np.std(monthly_returns)
            if monthly_volatility > 0:
                sharpe_ratio = np.mean(monthly_returns) / monthly_volatility * np.sqrt(12)
            else:
                sharpe_ratio = 0
        else:
            sharpe_ratio = 0
        
        return {
            'final_value': portfolio_value,
            'total_return': total_return,
            'annual_return': annual_return,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'total_trades': total_trades,
            'total_contracts': total_contracts,
            'total_rebates': total_rebates,
            'total_new_costs': total_new_costs,
            'net_rebate_benefit': total_rebates,
            'daily_pnl': daily_pnl,
            'monthly_returns': monthly_returns
        }
    
    def _calculate_conservative_position_pnl(self, position, market_regime):
        """Calculate position P&L conservatively"""
        cycle_multiplier = market_regime['volatility']
        
        # Base P&L calculation
        if market_regime['regime'] in ['bull', 'trending', 'impulse']:
            pnl_change = position['current_pnl'] * cycle_multiplier * (1 + np.random.normal(0.02, 0.04))
        elif market_regime['regime'] == 'bear':
            pnl_change = position['current_pnl'] * cycle_multiplier * (1 + np.random.normal(-0.02, 0.04))
        else:
            pnl_change = position['current_pnl'] * cycle_multiplier * (1 + np.random.normal(0, 0.02))
        
        # Time decay for options
        days_factor = min(1.0, position['days_held'] / 45)
        pnl_change *= (1 - days_factor * 0.1)
        
        return position['current_pnl'] + pnl_change
    
    def _check_conservative_trailing_stop(self, position, current_pnl, trailing_stop_multiplier):
        """Conservative trailing stop check"""
        # Update max profit
        if current_pnl > position['max_profit']:
            position['max_profit'] = current_pnl
            position['trailing_stop_level'] = current_pnl * (1 - 0.15)
        
        # Apply trailing stop multiplier
        trailing_stop = 0.15 * trailing_stop_multiplier
        
        # Check trailing stop
        if current_pnl <= position['max_profit'] * (1 - trailing_stop):
            return True
        
        # Check profit target
        if current_pnl >= position['profit_target']:
            return True
        
        # Check max loss
        if current_pnl <= position['max_loss']:
            return True
        
        # Time-based exit
        if position['days_held'] >= 45:
            return True
        
        return False
    
    def run_conservative_news_test(self, num_iterations=5):
        """Test conservative news-enhanced strategies"""
        logger.info(f'🚀 Testing conservative news-enhanced strategies with {num_iterations} iterations')
        
        results = []
        
        for i in range(num_iterations):
            logger.info(f'Running iteration {i+1}/{num_iterations}')
            
            result = self.run_conservative_news_backtest(years=2)
            results.append(result)
        
        returns = [r['annual_return'] for r in results]
        costs = [r['total_new_costs'] for r in results]
        rebates = [r['total_rebates'] for r in results]
        drawdowns = [r['max_drawdown'] for r in results]
        sharpes = [r['sharpe_ratio'] for r in results]
        
        report = f'''
================================================================================
🚀 CONSERVATIVE NEWS-ENHANCED STRATEGIES BACKTEST
================================================================================

📈 CONSERVATIVE ENHANCEMENTS IMPLEMENTED:
   • News quality scoring system (4 criteria)
   • Conservative news integration (risk management only)
   • High-quality news filtering (60%+ quality threshold)
   • News-based position reduction (not signal generation)
   • News-informed risk management
   • Conservative trailing stop adjustments

💰 COST OPTIMIZATION:
   • Mean Annual Costs: ${np.mean(costs):,.2f}
   • Mean Rebates: ${np.mean(rebates):,.2f}
   • Net Annual Benefit: ${np.mean(rebates) - np.mean(costs):,.2f}

📊 PERFORMANCE METRICS:
   • Mean Annual Return: {np.mean(returns):.2%}
   • Std Dev: {np.std(returns):.2%}
   • Mean Sharpe: {np.mean(sharpes):.3f}
   • Mean Max Drawdown: {np.mean(drawdowns):.2%}

🎯 NEWS QUALITY SCORING SYSTEM:
   • Source Reliability: Tier 1 (Fed, SEC) to Tier 3 (Social Media)
   • Impact Magnitude: High (Fed decisions) to Low (rumors)
   • Sentiment Confidence: Clear sentiment vs mixed signals
   • Market Correlation: Strong vs weak market correlation
   • Quality Threshold: 60% minimum for risk management

🔍 CONSERVATIVE NEWS INTEGRATION:
   • Risk Management Focus: News used for risk, not signals
   • High Quality Filter: Only 60%+ quality news considered
   • Position Reduction: Reduce size on negative news
   • Trailing Stop Adjustment: Tighter stops on bad news
   • Exit Triggers: Exit on very negative high-quality news
   • Minimal Regime Impact: News has minimal impact on regime detection

💡 KEY INSIGHTS:
'''
        
        if np.mean(returns) > 0:
            report += f'     ✅ POSITIVE RETURNS: {np.mean(returns):.2%} annual return\n'
        else:
            report += f'     ⚠️  RETURNS NEED IMPROVEMENT: {np.mean(returns):.2%} annual return\n'
        
        if np.mean(sharpes) > 0.5:
            report += f'     ✅ EXCELLENT RISK-ADJUSTED RETURNS: {np.mean(sharpes):.3f} Sharpe\n'
        elif np.mean(sharpes) > 0.3:
            report += f'     ✅ GOOD RISK-ADJUSTED RETURNS: {np.mean(sharpes):.3f} Sharpe\n'
        else:
            report += f'     ⚠️  RISK-ADJUSTED RETURNS NEED WORK: {np.mean(sharpes):.3f} Sharpe\n'
        
        report += f'     💰 Cost optimization provides ${np.mean(rebates) - np.mean(costs):,.2f} annual benefit\n'
        report += f'     📈 {"Higher" if np.mean(returns) > 0 else "Lower"} returns with {"excellent" if np.mean(sharpes) > 0.5 else "good" if np.mean(sharpes) > 0.3 else "moderate"} risk management\n\n'
        
        report += '================================================================================\n'
        
        print(report)
        
        logger.info('Conservative news-enhanced strategies backtest completed!')
        
        return report, results

def main():
    """Main execution function"""
    backtest = ConservativeNewsEnhancedBacktest()
    
    # Run conservative news-enhanced test
    report, results = backtest.run_conservative_news_test(num_iterations=5)
    
    logger.info("Conservative news-enhanced strategies backtest completed!")

if __name__ == "__main__":
    main()





















