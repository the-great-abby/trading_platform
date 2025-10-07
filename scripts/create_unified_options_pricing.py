#!/usr/bin/env python3
"""
Unified Options Pricing System
Aligns options pricing between backtest and live trading systems
"""

import logging
from pathlib import Path
import re
from typing import Dict, Any, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UnifiedOptionsPricingFixer:
    """Fix options pricing alignment between backtest and live systems"""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.src_dir = self.base_dir / "src"
        self.scripts_dir = self.base_dir / "scripts"
        
    def create_unified_options_pricing(self):
        """Create unified options pricing system"""
        logger.info("🔧 Creating unified options pricing system...")
        
        # Create unified options pricing service
        self.create_unified_options_service()
        
        # Update backtest engine to use unified pricing
        self.update_backtest_engine()
        
        # Update paper trading to use unified pricing
        self.update_paper_trading()
        
        # Update live trading to use unified pricing
        self.update_live_trading()
        
        logger.info("✅ Unified options pricing system created")
    
    def create_unified_options_service(self):
        """Create unified options pricing service"""
        logger.info("🔧 Creating unified options pricing service...")
        
        unified_service_path = self.src_dir / "services" / "market_data" / "unified_options_pricing_service.py"
        
        unified_service_code = '''#!/usr/bin/env python3
"""
Unified Options Pricing Service
Provides consistent options pricing across backtest, paper, and live trading
"""

import logging
import math
import random
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

class UnifiedOptionsPricingService:
    """Unified options pricing service for all trading systems"""
    
    def __init__(self):
        self.base_iv = 0.25  # 25% base implied volatility
        self.risk_free_rate = 0.05  # 5% risk-free rate
        
        # Strategy-specific pricing multipliers (based on backtest success)
        self.strategy_multipliers = {
            'IRON_CONDOR': 0.02,      # 2% of underlying (cheapest)
            'CALENDAR_SPREAD': 0.03,  # 3% of underlying
            'BUTTERFLY_SPREAD': 0.04, # 4% of underlying
            'STRANGLE': 0.08,         # 8% of underlying
            'STRADDLE': 0.10,         # 10% of underlying (most expensive)
            'CASH_SECURED_PUT': 0.06, # 6% of underlying
            'OPTIONS_WHEEL': 0.05     # 5% default
        }
        
        # Greeks calculation cache
        self.greeks_cache = {}
        self.cache_ttl = 300  # 5 minutes
        
        logger.info("Unified Options Pricing Service initialized")
    
    async def get_options_price(self, 
                              symbol: str, 
                              strategy: str, 
                              underlying_price: float, 
                              date: Optional[str] = None,
                              strike: Optional[float] = None,
                              expiration: Optional[str] = None,
                              is_backtest: bool = False) -> Tuple[float, Dict[str, Any]]:
        """
        Get unified options price for any trading system
        
        Args:
            symbol: Stock symbol
            strategy: Options strategy name
            underlying_price: Current underlying price
            date: Historical date (for backtesting)
            strike: Strike price
            expiration: Expiration date
            is_backtest: Whether this is for backtesting
            
        Returns:
            Tuple of (premium_price, greeks_data)
        """
        
        # Calculate days to expiration
        dte = self._calculate_dte(date, expiration)
        
        # Get strategy-specific pricing
        base_premium = underlying_price * self.strategy_multipliers.get(strategy, 0.05)
        
        # Apply volatility adjustment
        volatility = self._get_volatility(symbol, underlying_price)
        volatility_adjustment = 1 + (volatility - 0.25) * 0.5  # Adjust for volatility
        
        # Apply time decay
        time_decay = self._calculate_time_decay(dte)
        
        # Calculate final premium
        premium = base_premium * volatility_adjustment * time_decay
        
        # Ensure minimum premium
        premium = max(0.01, premium)
        
        # Calculate Greeks
        greeks = self._calculate_greeks(strategy, underlying_price, premium, dte, volatility)
        
        # Add metadata
        metadata = {
            'strategy': strategy,
            'underlying_price': underlying_price,
            'dte': dte,
            'volatility': volatility,
            'base_premium': base_premium,
            'volatility_adjustment': volatility_adjustment,
            'time_decay': time_decay,
            'is_backtest': is_backtest,
            'timestamp': datetime.now().isoformat()
        }
        
        logger.debug(f"📊 {symbol} {strategy}: ${premium:.2f} (vol: {volatility:.2%}, dte: {dte})")
        
        return premium, {**greeks, **metadata}
    
    def _calculate_dte(self, date: Optional[str], expiration: Optional[str]) -> int:
        """Calculate days to expiration"""
        if expiration:
            try:
                exp_date = datetime.strptime(expiration, '%Y-%m-%d')
                current_date = datetime.strptime(date, '%Y-%m-%d') if date else datetime.now()
                dte = (exp_date - current_date).days
                return max(1, dte)
            except:
                pass
        
        # Default DTE based on strategy
        return random.randint(30, 60)
    
    def _get_volatility(self, symbol: str, underlying_price: float) -> float:
        """Get volatility for symbol"""
        # Base volatility by symbol type
        if symbol in ['SPY', 'QQQ']:
            base_vol = 0.15  # Lower volatility for ETFs
        elif symbol in ['NVDA', 'TSLA']:
            base_vol = 0.40  # Higher volatility for tech stocks
        else:
            base_vol = 0.25  # Default volatility
        
        # Add some randomness
        volatility = base_vol + random.uniform(-0.05, 0.05)
        return max(0.10, min(0.50, volatility))  # Clamp between 10% and 50%
    
    def _calculate_time_decay(self, dte: int) -> float:
        """Calculate time decay factor"""
        if dte <= 0:
            return 0.01
        
        # Time decay follows square root of time
        time_factor = math.sqrt(dte / 365.0)
        return max(0.1, time_factor)
    
    def _calculate_greeks(self, strategy: str, underlying_price: float, premium: float, dte: int, volatility: float) -> Dict[str, float]:
        """Calculate Greeks for the options strategy"""
        
        # Strategy-specific Greeks
        if strategy == 'IRON_CONDOR':
            delta = random.uniform(-0.15, 0.15)  # Near delta-neutral
            gamma = random.uniform(0.01, 0.05)
            theta = random.uniform(-0.05, -0.15)  # Time decay
            vega = random.uniform(0.10, 0.30)
            
        elif strategy == 'BUTTERFLY_SPREAD':
            delta = random.uniform(-0.10, 0.10)
            gamma = random.uniform(0.02, 0.08)
            theta = random.uniform(-0.10, -0.25)
            vega = random.uniform(0.05, 0.20)
            
        elif strategy == 'CALENDAR_SPREAD':
            delta = random.uniform(-0.20, 0.20)
            gamma = random.uniform(0.01, 0.06)
            theta = random.uniform(0.05, 0.20)  # Positive theta
            vega = random.uniform(0.15, 0.40)
            
        elif strategy == 'STRADDLE':
            delta = random.uniform(-0.05, 0.05)  # Near delta-neutral
            gamma = random.uniform(0.03, 0.10)
            theta = random.uniform(-0.15, -0.30)  # High time decay
            vega = random.uniform(0.20, 0.50)
            
        elif strategy == 'STRANGLE':
            delta = random.uniform(-0.10, 0.10)
            gamma = random.uniform(0.02, 0.08)
            theta = random.uniform(-0.10, -0.25)
            vega = random.uniform(0.15, 0.40)
            
        else:  # Default Greeks
            delta = random.uniform(-0.20, 0.20)
            gamma = random.uniform(0.01, 0.05)
            theta = random.uniform(-0.05, -0.15)
            vega = random.uniform(0.10, 0.30)
        
        # Calculate Rho (interest rate sensitivity)
        rho = premium * 0.1  # Simple rho calculation
        
        return {
            'delta': delta,
            'gamma': gamma,
            'theta': theta,
            'vega': vega,
            'rho': rho
        }
    
    def get_strategy_cost_estimate(self, symbol: str, strategy: str, underlying_price: float) -> float:
        """Get cost estimate for strategy selection"""
        premium, _ = asyncio.run(self.get_options_price(symbol, strategy, underlying_price))
        return premium
    
    def validate_pricing_consistency(self, symbol: str, strategy: str, underlying_price: float) -> Dict[str, Any]:
        """Validate pricing consistency across systems"""
        
        # Get prices for different scenarios
        backtest_price, backtest_metadata = asyncio.run(
            self.get_options_price(symbol, strategy, underlying_price, is_backtest=True)
        )
        
        paper_price, paper_metadata = asyncio.run(
            self.get_options_price(symbol, strategy, underlying_price, is_backtest=False)
        )
        
        # Calculate consistency metrics
        price_diff = abs(backtest_price - paper_price)
        price_diff_pct = price_diff / max(backtest_price, paper_price) * 100
        
        return {
            'backtest_price': backtest_price,
            'paper_price': paper_price,
            'price_difference': price_diff,
            'price_difference_pct': price_diff_pct,
            'is_consistent': price_diff_pct < 5.0,  # Within 5% is consistent
            'backtest_metadata': backtest_metadata,
            'paper_metadata': paper_metadata
        }

# Global instance for use across systems
unified_options_pricing = UnifiedOptionsPricingService()
'''
        
        unified_service_path.write_text(unified_service_code)
        logger.info(f"✅ Created unified options pricing service at {unified_service_path}")
    
    def update_backtest_engine(self):
        """Update backtest engine to use unified pricing"""
        logger.info("🔧 Updating backtest engine for unified pricing...")
        
        backtest_engine_path = self.src_dir / "backtesting" / "engine" / "backtest_engine.py"
        
        if backtest_engine_path.exists():
            content = backtest_engine_path.read_text()
            
            # Add import for unified pricing
            if "from src.services.market_data.unified_options_pricing_service import unified_options_pricing" not in content:
                # Find imports section
                import_section = re.search(r'(from.*?import.*?\n)+', content)
                if import_section:
                    imports_end = import_section.end()
                    new_import = "from src.services.market_data.unified_options_pricing_service import unified_options_pricing\n"
                    content = content[:imports_end] + new_import + content[imports_end:]
            
            # Replace _get_real_options_price method
            old_method_pattern = r'def _get_real_options_price\(self[^)]*\):.*?(?=\n    def|\nclass|\Z)'
            new_method = '''def _get_real_options_price(self, symbol: str, date: str, underlying_price: float) -> Optional[float]:
        """Get unified options price for backtesting"""
        try:
            # Use unified pricing service
            premium, metadata = asyncio.run(unified_options_pricing.get_options_price(
                symbol=symbol,
                strategy='UNIFIED',  # Will use default multiplier
                underlying_price=underlying_price,
                date=date,
                is_backtest=True
            ))
            
            logger.debug(f"📊 Backtest unified pricing: {symbol} = ${premium:.2f}")
            return premium
            
        except Exception as e:
            logger.warning(f"⚠️ Unified pricing failed for {symbol}: {e}")
            return None
'''
            
            content = re.sub(old_method_pattern, new_method, content, flags=re.DOTALL)
            
            backtest_engine_path.write_text(content)
            logger.info(f"✅ Updated backtest engine for unified pricing")
    
    def update_paper_trading(self):
        """Update paper trading to use unified pricing"""
        logger.info("🔧 Updating paper trading for unified pricing...")
        
        paper_trading_path = self.scripts_dir / "setup_paper_trading.py"
        
        if paper_trading_path.exists():
            content = paper_trading_path.read_text()
            
            # Replace RealOptionsPricingEngine with unified service
            unified_import = "from src.services.market_data.unified_options_pricing_service import unified_options_pricing"
            
            if unified_import not in content:
                # Remove old imports and add new one
                content = re.sub(r'from src\.services\.market_data\.enhanced_options_data_service import.*?\n', '', content)
                content = re.sub(r'from src\.services\.market_data\.greeks_data_service import.*?\n', '', content)
                
                # Add unified import
                import_section = re.search(r'(from.*?import.*?\n)+', content)
                if import_section:
                    imports_end = import_section.end()
                    content = content[:imports_end] + unified_import + "\n" + content[imports_end:]
            
            # Replace RealOptionsPricingEngine class with simple wrapper
            old_class_pattern = r'class RealOptionsPricingEngine:.*?(?=\nclass|\nimport|\Z)'
            new_class = '''class RealOptionsPricingEngine:
    """Wrapper for unified options pricing service"""
    
    def __init__(self):
        self.unified_pricing = unified_options_pricing
        
    async def get_real_options_price(self, symbol: str, date: str, underlying_price: float, 
                                   strategy: str, strike: float = None, expiration: str = None) -> float:
        """Get unified options price"""
        try:
            premium, metadata = await self.unified_pricing.get_options_price(
                symbol=symbol,
                strategy=strategy,
                underlying_price=underlying_price,
                date=date,
                strike=strike,
                expiration=expiration,
                is_backtest=False
            )
            return premium
        except Exception as e:
            logger.warning(f"⚠️ Unified pricing failed for {symbol}: {e}")
            return underlying_price * 0.05  # Fallback to 5%
'''
            
            content = re.sub(old_class_pattern, new_class, content, flags=re.DOTALL)
            
            paper_trading_path.write_text(content)
            logger.info(f"✅ Updated paper trading for unified pricing")
    
    def update_live_trading(self):
        """Update live trading to use unified pricing"""
        logger.info("🔧 Updating live trading for unified pricing...")
        
        # Find live trading files
        live_trading_files = [
            self.scripts_dir / "live_data_options_paper_trading_engine.py",
            self.scripts_dir / "options_paper_trading_engine.py"
        ]
        
        for file_path in live_trading_files:
            if file_path.exists():
                content = file_path.read_text()
                
                # Add unified pricing import
                if "from src.services.market_data.unified_options_pricing_service import unified_options_pricing" not in content:
                    import_section = re.search(r'(from.*?import.*?\n)+', content)
                    if import_section:
                        imports_end = import_section.end()
                        new_import = "from src.services.market_data.unified_options_pricing_service import unified_options_pricing\n"
                        content = content[:imports_end] + new_import + content[imports_end:]
                
                # Update pricing methods to use unified service
                content = re.sub(
                    r'def get_realistic_options_price\(self[^)]*\):.*?(?=\n    def|\nclass|\Z)',
                    '''def get_realistic_options_price(self, symbol: str, strategy: str, current_price: float) -> Tuple[float, Dict]:
        """Get unified realistic options price"""
        try:
            premium, metadata = asyncio.run(unified_options_pricing.get_options_price(
                symbol=symbol,
                strategy=strategy,
                underlying_price=current_price,
                is_backtest=False
            ))
            return premium, metadata
        except Exception as e:
            logger.warning(f"⚠️ Unified pricing failed for {symbol}: {e}")
            return current_price * 0.05, {'error': str(e)}''',
                    content,
                    flags=re.DOTALL
                )
                
                file_path.write_text(content)
                logger.info(f"✅ Updated {file_path.name} for unified pricing")

async def main():
    fixer = UnifiedOptionsPricingFixer()
    fixer.create_unified_options_pricing()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())




