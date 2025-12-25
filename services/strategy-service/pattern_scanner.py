#!/usr/bin/env python3
"""
Pattern Scanner - Find symbols with recent valid Elliott Wave patterns
"""

import aiohttp
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class PatternScanner:
    """Scans multiple symbols to find those with recent valid Elliott Wave patterns"""
    
    def __init__(self, elliott_wave_url: str = "http://elliott-wave-service.trading-system.svc.cluster.local:8000"):
        self.elliott_wave_url = elliott_wave_url
        self.min_confidence = 0.5
        self.max_pattern_age_days = 60  # Only consider patterns from last 60 days
    
    async def scan_symbols_for_patterns(
        self, 
        symbols: List[str], 
        timeframe: str = "1d",
        min_confidence: Optional[float] = None
    ) -> List[Dict]:
        """
        Scan multiple symbols and return those with recent valid Elliott Wave patterns
        
        Args:
            symbols: List of symbols to scan
            timeframe: Analysis timeframe (1d, 1h, 15m, etc.)
            min_confidence: Minimum pattern confidence (defaults to 0.5)
            
        Returns:
            List of symbols with valid recent patterns, sorted by confidence
        """
        min_conf = min_confidence or self.min_confidence
        valid_patterns = []
        
        logger.info(f"🔍 Scanning {len(symbols)} symbols for recent Elliott Wave patterns...")
        
        async with aiohttp.ClientSession() as session:
            # Analyze all symbols concurrently
            tasks = []
            for symbol in symbols:
                tasks.append(self._analyze_symbol(session, symbol, timeframe))
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter and process results
            for symbol, result in zip(symbols, results):
                if isinstance(result, Exception):
                    logger.warning(f"Error analyzing {symbol}: {result}")
                    continue
                
                if result is None:
                    continue
                
                # Check if pattern is recent and meets confidence threshold
                if (result.get('pattern_found', False) and 
                    result.get('confidence', 0) >= min_conf and
                    self._is_pattern_recent(result)):
                    
                    valid_patterns.append({
                        'symbol': symbol,
                        'confidence': result['confidence'],
                        'pattern_type': result['pattern_type'],
                        'signal': result.get('signal', 'HOLD'),
                        'target_price': result.get('target_price'),
                        'current_price': result.get('waves', [])[-1]['price'] if result.get('waves') else None,
                        'pattern_end_date': result.get('waves', [])[-1]['timestamp'] if result.get('waves') else None,
                        'pattern_age_days': self._calculate_pattern_age(result),
                        'full_analysis': result
                    })
        
        # Sort by confidence (highest first)
        valid_patterns.sort(key=lambda x: x['confidence'], reverse=True)
        
        logger.info(f"✅ Found {len(valid_patterns)} symbols with recent valid patterns (out of {len(symbols)} scanned)")
        
        return valid_patterns
    
    async def _analyze_symbol(
        self, 
        session: aiohttp.ClientSession, 
        symbol: str, 
        timeframe: str
    ) -> Optional[Dict]:
        """Analyze a single symbol for Elliott Wave patterns"""
        try:
            url = f"{self.elliott_wave_url}/elliott-wave/analyze/{symbol}"
            params = {"timeframe": timeframe}
            
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.warning(f"Elliott Wave analysis failed for {symbol}: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error analyzing {symbol}: {e}")
            return None
    
    def _is_pattern_recent(self, analysis: Dict) -> bool:
        """Check if the pattern is recent (not too old)"""
        if not analysis.get('waves'):
            return False
        
        try:
            # Get the last wave timestamp
            last_wave = analysis['waves'][-1]
            last_wave_date = datetime.fromisoformat(last_wave['timestamp'].replace('Z', '+00:00'))
            
            # Calculate pattern age
            age_days = (datetime.now() - last_wave_date).days
            
            # Pattern should be from last 60 days
            return age_days <= self.max_pattern_age_days
            
        except Exception as e:
            logger.warning(f"Error checking pattern age: {e}")
            return False
    
    def _calculate_pattern_age(self, analysis: Dict) -> int:
        """Calculate how old the pattern is in days"""
        try:
            last_wave = analysis['waves'][-1]
            last_wave_date = datetime.fromisoformat(last_wave['timestamp'].replace('Z', '+00:00'))
            return (datetime.now() - last_wave_date).days
        except:
            return 999
    
    async def get_best_opportunities(
        self, 
        symbols: List[str],
        limit: int = 10,
        timeframe: str = "1d"
    ) -> List[Dict]:
        """
        Get the best trading opportunities based on recent Elliott Wave patterns
        
        Returns symbols with:
        - Recent patterns (last 60 days)
        - High confidence (>= 0.5)
        - Clear BUY or SELL signals
        - Sorted by confidence
        """
        patterns = await self.scan_symbols_for_patterns(symbols, timeframe)
        
        # Filter for actionable signals (BUY or SELL, not HOLD)
        actionable = [p for p in patterns if p['signal'] in ['BUY', 'SELL']]
        
        # Return top N
        return actionable[:limit]


async def scan_all_symbols(min_confidence: float = 0.5, max_age_days: int = 60) -> List[Dict]:
    """
    Convenience function to scan all available symbols for recent patterns
    """
    # Get all available symbols from a centralized source
    # This would ideally come from the database or market-data-service
    all_symbols = [
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'NFLX',
        'SPY', 'QQQ', 'VOO', 'VTI', 'ADBE', 'CRM', 'ORCL', 'CSCO',
        'QCOM', 'TXN', 'AVGO', 'SMCI', 'DIS', 'AMD', 'INTC'
    ]
    
    scanner = PatternScanner()
    scanner.min_confidence = min_confidence
    scanner.max_pattern_age_days = max_age_days
    
    return await scanner.scan_symbols_for_patterns(all_symbols)


if __name__ == "__main__":
    # Test the scanner
    async def test():
        patterns = await scan_all_symbols(min_confidence=0.5, max_age_days=60)
        
        print(f"\n🎯 Found {len(patterns)} symbols with recent valid Elliott Wave patterns:\n")
        
        for p in patterns:
            print(f"✅ {p['symbol']}: {p['signal']} signal")
            print(f"   Confidence: {p['confidence']:.2%}")
            print(f"   Pattern: {p['pattern_type']} (age: {p['pattern_age_days']} days)")
            print(f"   Target: ${p['target_price']:.2f}")
            print()
    
    asyncio.run(test())



















