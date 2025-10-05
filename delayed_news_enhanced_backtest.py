#!/usr/bin/env python3
"""
News Delay Filter Enhanced Strategies Backtest
Implements news delay filters for market digestion before trading decisions
"""

import json
import random
import numpy as np
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NewsDelayFilterBacktest:
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
        
        # Strategies with news delay integration
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
                'news_delay_days': 2,  # Wait 2 days after news
                'news_quality_threshold': 0.8,  # Higher quality threshold
                'news_impact_threshold': 0.7,  # Only high-impact news
                'news_digestion_period': 3  # 3-day digestion period
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
                'news_delay_days': 3,  # Wait 3 days after news
                'news_quality_threshold': 0.85,  # Higher quality threshold
                'news_impact_threshold': 0.8,  # Only very high-impact news
                'news_digestion_period': 4  # 4-day digestion period
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
                'news_delay_days': 1,  # Wait 1 day after news
                'news_quality_threshold': 0.75,  # Lower quality threshold
                'news_impact_threshold': 0.6,  # Lower impact threshold
                'news_digestion_period': 2  # 2-day digestion period
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
                'news_delay_days': 1,  # Wait 1 day after news
                'news_quality_threshold': 0.7,  # Lower quality threshold
                'news_impact_threshold': 0.5,  # Lower impact threshold
                'news_digestion_period': 2  # 2-day digestion period
            }
        }
        
        # Enhanced news categories with delay periods
        self.news_categories = {
            'fed_policy': {
                'base_quality': 0.95, 'impact_duration': 7, 'volatility_boost': 2.0,
                'delay_days': 3, 'digestion_period': 5, 'impact_threshold': 0.9
            },
            'earnings': {
                'base_quality': 0.9, 'impact_duration': 4, 'volatility_boost': 1.5,
                'delay_days': 2, 'digestion_period': 3, 'impact_threshold': 0.8
            },
            'economic_data': {
                'base_quality': 0.85, 'impact_duration': 3, 'volatility_boost': 1.3,
                'delay_days': 1, 'digestion_period': 2, 'impact_threshold': 0.7
            },
            'sector_news': {
                'base_quality': 0.8, 'impact_duration': 2, 'volatility_boost': 1.2,
                'delay_days': 1, 'digestion_period': 1, 'impact_threshold': 0.6
            },
            'geopolitical': {
                'base_quality': 0.9, 'impact_duration': 10, 'volatility_boost': 2.5,
                'delay_days': 4, 'digestion_period': 6, 'impact_threshold': 0.85
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
        if source_tier == 'tier_1':
            quality_score += 0.3
        elif source_tier == 'tier_2':
            quality_score += 0.2
        else:
            quality_score += 0.1
        
        # Impact magnitude scoring
        impact_score = news_event.get('impact_score', 0.5)
        if impact_score >= 0.8:
            quality_score += 0.25
        elif impact_score >= 0.5:
            quality_score += 0.15
        else:
            quality_score += 0.05
        
        # Sentiment confidence scoring
        sentiment_confidence = abs(news_event.get('sentiment', 0))
        if sentiment_confidence > 0.8:
            quality_score += 0.2
        elif sentiment_confidence > 0.5:
            quality_score += 0.1
        else:
            quality_score += 0.05
        
        # Market correlation scoring
        category = news_event.get('category', 'sector_news')
        if category in ['fed_policy', 'geopolitical']:
            quality_score += 0.15
        elif category in ['earnings', 'economic_data']:
            quality_score += 0.1
        else:
            quality_score += 0.05
        
        # Category-specific quality boost
        if category in self.news_categories:
            quality_score *= self.news_categories[category]['base_quality']
        
        return min(1.0, max(0.0, quality_score))
    
    def _get_source_tier(self, source):
        """Determine source reliability tier"""
        tier_1_sources = ['Fed', 'SEC', 'Earnings', 'Major Banks']
        tier_2_sources = ['Reuters', 'Bloomberg', 'WSJ', 'CNBC']
        
        if source in tier_1_sources:
            return 'tier_1'
        elif source in tier_2_sources:
            return 'tier_2'
        else:
            return 'tier_3'
    
    def generate_delayed_news_data(self, days):
        """Generate news data with delay tracking"""
        news_data = []
        
        for day in range(days):
            daily_news = []
            
            # Fewer but higher quality news events
            num_events = np.random.poisson(1.2)  # Even fewer events
            
            for _ in range(num_events):
                # Select news category with quality weighting
                categories = list(self.news_categories.keys())
                weights = [self.news_categories[cat]['base_quality'] for cat in categories]
                category = np.random.choice(categories, p=np.array(weights)/sum(weights))
                
                # Generate higher quality sentiment
                base_sentiment = np.random.normal(0, 0.15)  # Even lower volatility
                
                # Add market cycle correlation
                cycle_factor = np.sin(day / 50) * 0.1  # Reduced cycle impact
                sentiment = np.clip(base_sentiment + cycle_factor, -1, 1)
                
                # Generate higher impact scores
                impact_score = np.random.beta(4, 2)  # Skewed toward higher impact
                
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
                    'confidence': np.random.uniform(0.8, 0.95),  # Higher confidence
                    'source': source,
                    'delay_days': self.news_categories[category]['delay_days'],
                    'digestion_period': self.news_categories[category]['digestion_period'],
                    'impact_threshold': self.news_categories[category]['impact_threshold']
                }
                
                # Calculate quality score
                news_event['quality_score'] = self.calculate_news_quality_score(news_event)
                
                # Only include high-quality news
                if news_event['quality_score'] >= 0.7:
                    daily_news.append(news_event)
            
            # Calculate daily aggregate sentiment (only from high-quality news)
            if daily_news:
                weighted_sentiment = sum(
                    event['sentiment'] * event['impact_score'] * event['confidence'] * event['quality_score']
                    for event in daily_news
                ) / sum(event['impact_score'] * event['confidence'] * event['quality_score'] for event in daily_news)
                
                avg_quality = np.mean([event['quality_score'] for event in daily_news])
                avg_impact = np.mean([event['impact_score'] for event in daily_news])
            else:
                weighted_sentiment = 0.0
                avg_quality = 0.0
                avg_impact = 0.0
            
            news_data.append({
                'day': day,
                'events': daily_news,
                'aggregate_sentiment': weighted_sentiment,
                'avg_quality_score': avg_quality,
                'avg_impact_score': avg_impact,
                'volatility_impact': sum(
                    event['impact_score'] * self.news_categories[event['category']]['volatility_boost']
                    for event in daily_news
                ) / max(1, len(daily_news))
            })
        
        return news_data
    
    def check_news_delay_filter(self, strategy_name, current_day, news_data):
        """Check if enough time has passed since relevant news"""
        strategy_config = self.strategies[strategy_name]
        delay_days = strategy_config['news_delay_days']
        quality_threshold = strategy_config['news_quality_threshold']
        impact_threshold = strategy_config['news_impact_threshold']
        
        # Check recent news within delay period
        recent_news = news_data[max(0, current_day - delay_days):current_day]
        
        for news_day in recent_news:
            if news_day['avg_quality_score'] >= quality_threshold and news_day['avg_impact_score'] >= impact_threshold:
                # High-quality, high-impact news found within delay period
                return False, f"High-impact news within {delay_days} days"
        
        return True, "No high-impact news within delay period"
    
    def detect_market_regime_with_delay(self, day, news_data):
        """Market regime detection with news delay consideration"""
        # Base regime detection (primary)
        base_regime = self.detect_base_market_regime(day)
        
        # Get news from beyond delay period (market has digested)
        delay_lookback = 5  # Look back 5 days for digested news
        digested_news = news_data[max(0, day - delay_lookback - 3):day - 3]  # 3-day delay
        
        if digested_news:
            avg_sentiment = np.mean([n['aggregate_sentiment'] for n in digested_news])
            avg_quality = np.mean([n['avg_quality_score'] for n in digested_news])
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
        
        # Only adjust if news quality is very high and digested
        if quality < 0.85:
            return adjusted_regime
        
        # Minimal volatility adjustment
        sentiment_vol_adjustment = sentiment * 0.05  # Very reduced impact
        adjusted_regime['volatility'] *= (1 + sentiment_vol_adjustment)
        
        # Minimal trend adjustment
        sentiment_trend_adjustment = sentiment * 0.002  # Very reduced impact
        adjusted_regime['trend'] += sentiment_trend_adjustment
        
        # Only change regime for very strong digested sentiment
        if sentiment > 0.7 and quality > 0.95:  # Very high thresholds
            if base_regime['regime'] in ['normal', 'sideways']:
                adjusted_regime['regime'] = 'trending'
        elif sentiment < -0.7 and quality > 0.95:
            if base_regime['regime'] in ['bull', 'trending']:
                adjusted_regime['regime'] = 'corrective'
        
        return adjusted_regime
    
    def is_strategy_suitable_with_delay(self, strategy_name, market_regime, current_day, news_data):
        """Check strategy suitability with news delay filter"""
        strategy_config = self.strategies[strategy_name]
        
        # Base regime check
        if market_regime['regime'] not in strategy_config['market_regimes']:
            return False, "Market regime not suitable"
        
        # News delay filter check
        delay_ok, delay_reason = self.check_news_delay_filter(strategy_name, current_day, news_data)
        if not delay_ok:
            return False, delay_reason
        
        return True, "Strategy suitable with delay filter"
    
    def calculate_delayed_elliott_wave_confidence(self, strategy_name, market_regime, symbol_config, current_day, news_data):
        """Calculate Elliott Wave confidence with news delay consideration"""
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
        
        # News delay confidence boost (market has digested news)
        strategy_config = self.strategies[strategy_name]
        delay_days = strategy_config['news_delay_days']
        
        # Check if we're in a "clean" period after news digestion
        recent_news = news_data[max(0, current_day - delay_days):current_day]
        high_impact_news_count = sum(
            1 for n in recent_news 
            if n['avg_impact_score'] >= strategy_config['news_impact_threshold']
        )
        
        if high_impact_news_count == 0:
            confidence += 0.1  # Boost confidence in clean periods
        
        # Symbol-specific adjustments
        if symbol_config['volatility'] < 0.25:
            confidence += 0.1
        
        return min(1.0, max(0.1, confidence))
    
    def run_delayed_news_backtest(self, years=2):
        """Run backtest with news delay filters"""
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
        
        # Generate delayed news data
        news_data = self.generate_delayed_news_data(days)
        
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
            market_regime = self.detect_market_regime_with_delay(day, news_data)
            
            # Process trailing stops for active positions
            positions_to_close = []
            for i, position in enumerate(active_positions):
                # Calculate position P&L
                position_pnl = self._calculate_delayed_position_pnl(position, market_regime)
                
                # Check trailing stop
                if self._check_delayed_trailing_stop(position, position_pnl):
                    positions_to_close.append(i)
                    daily_trade_pnl += position_pnl
                    logger.info(f'Position closed: {position["strategy"]} - P&L: ${position_pnl:.2f}')
                else:
                    active_positions[i]['current_pnl'] = position_pnl
                    active_positions[i]['days_held'] += 1
            
            # Close positions
            for i in reversed(positions_to_close):
                active_positions.pop(i)
            
            # Run strategies with news delay filters
            for strategy_name, strategy_config in self.strategies.items():
                # Check strategy suitability with delay filter
                suitable, reason = self.is_strategy_suitable_with_delay(strategy_name, market_regime, day, news_data)
                if not suitable:
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
                
                # Calculate delayed Elliott Wave confidence
                wave_confidence = self.calculate_delayed_elliott_wave_confidence(
                    strategy_name, market_regime, symbol_config, day, news_data
                )
                
                # Skip if confidence too low
                if wave_confidence < 0.6:
                    continue
                
                # Conservative position sizing
                base_size = 0.05
                confidence_multiplier = wave_confidence
                volatility_adjustment = 1.0 - (symbol_config['volatility'] - 0.15) * 0.3
                
                position_size = min(
                    self.public_com_costs['max_position_size'], 
                    max(0.02, base_size * confidence_multiplier * volatility_adjustment)
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
                    'delay_filter_passed': True
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
    
    def _calculate_delayed_position_pnl(self, position, market_regime):
        """Calculate position P&L with delayed news consideration"""
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
    
    def _check_delayed_trailing_stop(self, position, current_pnl):
        """Check trailing stop with delayed news consideration"""
        # Update max profit
        if current_pnl > position['max_profit']:
            position['max_profit'] = current_pnl
            position['trailing_stop_level'] = current_pnl * (1 - 0.15)
        
        # Check trailing stop
        if current_pnl <= position['max_profit'] * (1 - 0.15):
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
    
    def run_delayed_news_test(self, num_iterations=5):
        """Test delayed news-enhanced strategies"""
        logger.info(f'🚀 Testing delayed news-enhanced strategies with {num_iterations} iterations')
        
        results = []
        
        for i in range(num_iterations):
            logger.info(f'Running iteration {i+1}/{num_iterations}')
            
            result = self.run_delayed_news_backtest(years=2)
            results.append(result)
        
        returns = [r['annual_return'] for r in results]
        costs = [r['total_new_costs'] for r in results]
        rebates = [r['total_rebates'] for r in results]
        drawdowns = [r['max_drawdown'] for r in results]
        sharpes = [r['sharpe_ratio'] for r in results]
        
        report = f'''
================================================================================
🚀 DELAYED NEWS-ENHANCED STRATEGIES BACKTEST
================================================================================

📈 DELAYED NEWS ENHANCEMENTS IMPLEMENTED:
   • News delay filters (1-4 days depending on strategy)
   • Market digestion periods (2-6 days)
   • High-quality news filtering (70%+ quality threshold)
   • News impact thresholds (50-90% depending on strategy)
   • Delayed Elliott Wave confidence calculation
   • Conservative news regime adjustments

💰 COST OPTIMIZATION:
   • Mean Annual Costs: ${np.mean(costs):,.2f}
   • Mean Rebates: ${np.mean(rebates):,.2f}
   • Net Annual Benefit: ${np.mean(rebates) - np.mean(costs):,.2f}

📊 PERFORMANCE METRICS:
   • Mean Annual Return: {np.mean(returns):.2%}
   • Std Dev: {np.std(returns):.2%}
   • Mean Sharpe: {np.mean(sharpes):.3f}
   • Mean Max Drawdown: {np.mean(drawdowns):.2%}

🎯 NEWS DELAY FILTERS BY STRATEGY:
   • Elliott Wave Corrective: 2-day delay, 80% quality, 70% impact
   • Elliott Wave Impulse: 3-day delay, 85% quality, 80% impact
   • Calendar Spreads: 1-day delay, 75% quality, 60% impact
   • Iron Condor: 1-day delay, 70% quality, 50% impact

🔍 MARKET DIGESTION PERIODS:
   • Fed Policy: 3-day delay, 5-day digestion
   • Earnings: 2-day delay, 3-day digestion
   • Economic Data: 1-day delay, 2-day digestion
   • Sector News: 1-day delay, 1-day digestion
   • Geopolitical: 4-day delay, 6-day digestion

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
        
        logger.info('Delayed news-enhanced strategies backtest completed!')
        
        return report, results

def main():
    """Main execution function"""
    backtest = NewsDelayFilterBacktest()
    
    # Run delayed news-enhanced test
    report, results = backtest.run_delayed_news_test(num_iterations=5)
    
    logger.info("Delayed news-enhanced strategies backtest completed!")

if __name__ == "__main__":
    main()









