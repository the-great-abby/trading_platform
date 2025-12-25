"""
0-DTE Covered Call Screener Strategy
=====================================
Specialized strategy for screening and trading 0-DTE (Zero Days to Expiration) covered calls.
Based on Polygon.io snapshot API for real-time options chain data.

Key Features:
- Same-day expiration screening (0-DTE)
- OTM call filtering with delta bands
- Liquidity and spread quality checks
- Premium yield ranking
- Probability of profit estimation
- Mark-to-market P&L tracking
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta, time as dt_time
from zoneinfo import ZoneInfo
import logging
import math
from dataclasses import dataclass, asdict

from src.strategies.base import BaseStrategy
from src.core.types import TradeSignal
from src.utils.enhanced_logging import get_trading_logger
from src.services.market_data.options_data_service import OptionsDataService

logger = get_trading_logger()

ET = ZoneInfo("America/New_York")


@dataclass
class ZeroDTECandidate:
    """Represents a 0-DTE covered call candidate"""
    ticker: str
    expiration: str
    strike: float
    delta: Optional[float]
    bid: float
    ask: float
    mid: float
    open_interest: int
    iv: Optional[float]
    spot: float
    premium_yield: float
    breakeven: float
    max_profit: float
    pop_est: Optional[float]  # Probability of profit estimate
    score: float
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CreditSpreadCandidate:
    """Represents a 0-DTE credit spread candidate"""
    ticker: str
    expiration: str
    short_strike: float
    long_strike: float
    spread_width: float
    short_delta: Optional[float]
    long_delta: Optional[float]
    short_bid: float
    short_ask: float
    short_mid: float
    long_bid: float
    long_ask: float
    long_mid: float
    net_credit: float
    max_loss: float
    max_profit: float
    risk_reward_ratio: float
    return_on_capital: float
    short_oi: int
    long_oi: int
    spot: float
    pop_est: Optional[float]
    score: float
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ZeroDTECoveredCallStrategy(BaseStrategy):
    """
    0-DTE Covered Call Screener Strategy
    
    Screens for same-day expiration covered call opportunities with:
    - Tight OTM bands (typically 0-3% above spot)
    - Delta targeting (15-35 delta range)
    - Spread quality checks (max 75% of mid)
    - Minimum bid requirements
    - Liquidity filtering
    - Probability of profit estimation
    
    Perfect for daily income generation with minimal time risk.
    """
    
    def __init__(self,
                 name: str = "ZeroDTE_CoveredCall",
                 expiration_days: int = 0,  # 0 for same-day
                 min_otm_pct: float = 0.00,  # Minimum OTM percentage
                 max_otm_pct: float = 0.03,  # Maximum OTM percentage (3%)
                 delta_lo: float = 0.15,     # Minimum delta
                 delta_hi: float = 0.35,     # Maximum delta (~30 delta sweet spot)
                 min_bid: float = 0.05,      # Minimum bid price ($0.05)
                 min_open_interest: int = 1,  # Minimum open interest
                 max_spread_to_mid: float = 0.75,  # Max spread as % of mid
                 rank_metric: str = "premium_yield",  # Ranking metric
                 target_tickers: Optional[List[str]] = None):
        super().__init__(name)
        
        # Strategy parameters
        self.expiration_days = expiration_days
        self.min_otm_pct = min_otm_pct
        self.max_otm_pct = max_otm_pct
        self.delta_lo = delta_lo
        self.delta_hi = delta_hi
        self.min_bid = min_bid
        self.min_open_interest = min_open_interest
        self.max_spread_to_mid = max_spread_to_mid
        self.rank_metric = rank_metric
        self.target_tickers = target_tickers or ["SPY"]
        
        # Initialize options service
        self.options_service = OptionsDataService()
        
        # State tracking
        self.candidates: List[ZeroDTECandidate] = []
        self.spread_candidates: List[CreditSpreadCandidate] = []
        self.active_positions: Dict[str, Any] = {}
        
    def today_et(self) -> datetime:
        """Get current time in ET"""
        return datetime.now(ET)
    
    def target_expiration_date(self, days_ahead: int = None) -> str:
        """Calculate target expiration date"""
        if days_ahead is None:
            days_ahead = self.expiration_days
        d = self.today_et().date() + timedelta(days=days_ahead)
        return d.strftime("%Y-%m-%d")
    
    def minutes_to_close_on(self, date_str: str) -> float:
        """Calculate minutes until market close on a specific date"""
        d = datetime.strptime(date_str, "%Y-%m-%d").date()
        close_dt = datetime.combine(d, dt_time(16, 0), tzinfo=ET)
        now = self.today_et()
        return max(0.0, (close_dt - now).total_seconds() / 60.0)
    
    def time_to_expiry_years(self, date_str: str) -> float:
        """Convert expiration date to years (for Greeks calculations)"""
        mins = self.minutes_to_close_on(date_str)
        return max(mins / (60 * 24 * 365), 1e-6)  # Keep small, never zero
    
    @staticmethod
    def norm_cdf(x: float) -> float:
        """Normal cumulative distribution function"""
        return 0.5 * (1.0 + math.erf(x / math.sqrt(2)))
    
    @staticmethod
    def midpoint(bid: Optional[float], ask: Optional[float]) -> Optional[float]:
        """Calculate midpoint of bid-ask"""
        if bid is None or ask is None or bid <= 0 or ask <= 0 or ask < bid:
            return None
        return 0.5 * (bid + ask)
    
    def pop_estimate(self, S0: float, breakeven: float, 
                    iv: Optional[float], t_years: float) -> Optional[float]:
        """
        Estimate probability of profit using Black-Scholes framework
        
        For a covered call, we profit if the stock stays below breakeven.
        This calculates P(S_T >= breakeven) as a rough POP estimate.
        """
        if iv is None or iv <= 0 or breakeven <= 0 or t_years <= 0:
            return None
        
        try:
            # Log-normal stock price at expiry (risk-neutral, r≈0)
            d2 = (math.log(S0 / breakeven) - 0.5 * (iv ** 2) * t_years) / (iv * math.sqrt(t_years))
            return self.norm_cdf(d2)
        except (ValueError, ZeroDivisionError):
            return None
    
    def fetch_chain_snapshot_calls(self, symbol: str, expiration_date: str) -> List[Dict[str, Any]]:
        """
        Fetch options chain snapshot for calls expiring on target date
        Uses Polygon API snapshot endpoint
        """
        try:
            import requests
            import os
            
            api_key = os.getenv('POLYGON_API_KEY')
            if not api_key:
                logger.error("POLYGON_API_KEY not found in environment")
                return []
            
            # Use Polygon's snapshot options chain endpoint
            url = f"https://api.polygon.io/v3/snapshot/options/{symbol}"
            params = {
                "apiKey": api_key,
                "contract_type": "call",
                "expiration_date.gte": expiration_date,
                "expiration_date.lte": expiration_date,
                "limit": 250  # Polygon's max
            }
            
            logger.info(f"📡 Fetching 0-DTE options chain for {symbol} expiring {expiration_date}")
            
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 429:
                logger.warning("⚠️ Rate limited by Polygon API")
                return []
            
            if response.status_code != 200:
                logger.error(f"❌ Polygon API error {response.status_code}: {response.text}")
                return []
            
            data = response.json()
            results = data.get("results", [])
            
            logger.info(f"✅ Retrieved {len(results)} call options for {symbol}")
            return results
            
        except Exception as e:
            logger.error(f"❌ Error fetching options chain: {e}")
            return []
    
    def resolve_spot(self, chain: List[Dict[str, Any]], symbol: str) -> Optional[float]:
        """Resolve underlying spot price from chain or fallback API"""
        # Try to get from chain first
        for option in chain:
            ua = option.get("underlying_asset", {})
            price = ua.get("price")
            if price:
                return float(price)
        
        # Fallback: fetch last trade
        try:
            import requests
            import os
            
            api_key = os.getenv('POLYGON_API_KEY')
            url = f"https://api.polygon.io/v2/last/trade/{symbol}"
            params = {"apiKey": api_key}
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                results = data.get("results", {})
                price = results.get("p")
                if price:
                    return float(price)
        except Exception as e:
            logger.error(f"❌ Error fetching spot price: {e}")
        
        return None
    
    def screen_candidates(self, 
                         chain: List[Dict[str, Any]],
                         spot: float,
                         expiration_date: str) -> List[ZeroDTECandidate]:
        """
        Screen and rank 0-DTE covered call candidates
        
        Returns list of candidates sorted by ranking metric
        """
        if not chain or not spot:
            return []
        
        # Calculate OTM bounds
        lo = spot * (1.0 + self.min_otm_pct)
        hi = spot * (1.0 + self.max_otm_pct)
        
        # Time to expiry for POP calculation
        t_years = self.time_to_expiry_years(expiration_date)
        
        candidates = []
        
        for option in chain:
            try:
                # Extract option details
                details = option.get("details", {})
                strike = details.get("strike_price")
                ticker = details.get("ticker")
                exp = details.get("expiration_date")
                
                if not strike or not ticker:
                    continue
                
                # Check strike is in OTM range
                if not (lo <= strike <= hi):
                    continue
                
                # Extract quote data
                quote = option.get("last_quote", {})
                bid = quote.get("bid")
                ask = quote.get("ask")
                
                if bid is None or ask is None or bid < self.min_bid:
                    continue
                
                # Calculate midpoint
                mid = self.midpoint(bid, ask)
                if mid is None or mid <= 0:
                    continue
                
                # Check spread quality
                spread = ask - bid
                if mid > 0 and (spread / mid) > self.max_spread_to_mid:
                    continue
                
                # Extract Greeks and volume data
                greeks = option.get("greeks", {})
                delta_val = greeks.get("delta")
                iv = greeks.get("implied_volatility")
                
                oi = option.get("open_interest", 0) or 0
                
                # Check delta band (if available)
                delta_ok = True
                if delta_val is not None:
                    abs_delta = abs(delta_val)
                    delta_ok = (self.delta_lo <= abs_delta <= self.delta_hi)
                
                if not delta_ok:
                    continue
                
                # Check open interest
                if oi < self.min_open_interest:
                    continue
                
                # Calculate metrics
                premium_yield = mid / spot
                breakeven = spot - mid  # For covered call
                max_profit = (strike - spot) + mid
                pop = self.pop_estimate(spot, breakeven, iv, t_years)
                
                # Calculate composite score
                score = self._calculate_score(
                    premium_yield, max_profit, pop, delta_val, oi, spread, mid
                )
                
                candidate = ZeroDTECandidate(
                    ticker=ticker,
                    expiration=exp,
                    strike=strike,
                    delta=delta_val,
                    bid=bid,
                    ask=ask,
                    mid=mid,
                    open_interest=oi,
                    iv=iv,
                    spot=spot,
                    premium_yield=premium_yield,
                    breakeven=breakeven,
                    max_profit=max_profit,
                    pop_est=pop,
                    score=score
                )
                
                candidates.append(candidate)
                
            except Exception as e:
                logger.warning(f"⚠️ Error processing option: {e}")
                continue
        
        # Sort by ranking metric
        if self.rank_metric == "premium_yield":
            candidates.sort(key=lambda c: c.premium_yield, reverse=True)
        elif self.rank_metric == "max_profit":
            candidates.sort(key=lambda c: c.max_profit, reverse=True)
        elif self.rank_metric == "pop_est":
            candidates.sort(key=lambda c: (c.pop_est or 0), reverse=True)
        elif self.rank_metric == "score":
            candidates.sort(key=lambda c: c.score, reverse=True)
        else:
            candidates.sort(key=lambda c: c.score, reverse=True)
        
        logger.info(f"✅ Found {len(candidates)} 0-DTE covered call candidates")
        
        return candidates
    
    def screen_credit_spreads(self,
                             chain: List[Dict[str, Any]],
                             spot: float,
                             expiration_date: str,
                             spread_width: float = 2.0,
                             min_credit: float = 0.10) -> List[CreditSpreadCandidate]:
        """
        Screen for credit spread opportunities
        
        A credit spread sells a lower strike call and buys a higher strike call
        to cap risk while collecting premium.
        
        Args:
            chain: Options chain data
            spot: Current stock price
            expiration_date: Target expiration
            spread_width: Width between strikes (default 2.0 points)
            min_credit: Minimum net credit to collect
        
        Returns:
            List of credit spread candidates
        """
        if not chain or not spot:
            return []
        
        # First, get potential short strikes (using same logic as covered calls)
        short_candidates = self.screen_candidates(chain, spot, expiration_date)
        
        if not short_candidates:
            return []
        
        # Create a map of strikes to option data for quick lookup
        strike_map = {}
        for option in chain:
            try:
                details = option.get("details", {})
                strike = details.get("strike_price")
                if strike:
                    strike_map[strike] = option
            except:
                continue
        
        spread_candidates = []
        
        for short_candidate in short_candidates:
            short_strike = short_candidate.strike
            
            # Look for long strike (spread_width points higher)
            long_strike = short_strike + spread_width
            
            # Find the long option in the chain
            long_option = strike_map.get(long_strike)
            if not long_option:
                # Try to find closest strike
                available_strikes = sorted([s for s in strike_map.keys() if s > short_strike])
                if not available_strikes:
                    continue
                # Find closest to desired width
                long_strike = min(available_strikes, key=lambda s: abs(s - (short_strike + spread_width)))
                long_option = strike_map.get(long_strike)
                if not long_option:
                    continue
            
            # Extract long option data
            try:
                long_quote = long_option.get("last_quote", {})
                long_bid = long_quote.get("bid")
                long_ask = long_quote.get("ask")
                
                if long_bid is None or long_ask is None:
                    continue
                
                long_mid = self.midpoint(long_bid, long_ask)
                if long_mid is None:
                    continue
                
                long_greeks = long_option.get("greeks", {})
                long_delta = long_greeks.get("delta")
                long_oi = long_option.get("open_interest", 0) or 0
                
                # Calculate spread metrics
                actual_width = long_strike - short_strike
                net_credit = short_candidate.mid - long_mid
                
                # Check minimum credit
                if net_credit < min_credit:
                    continue
                
                max_loss = (actual_width - net_credit) * 100
                max_profit = net_credit * 100
                
                if max_loss <= 0:
                    continue
                
                risk_reward_ratio = max_loss / max_profit if max_profit > 0 else 999
                return_on_capital = (max_profit / max_loss) if max_loss > 0 else 0
                
                # Estimate POP for the spread (conservative - use short strike)
                t_years = self.time_to_expiry_years(expiration_date)
                pop = self.pop_estimate(spot, short_strike, short_candidate.iv, t_years)
                
                # Calculate score for spread
                score = self._calculate_spread_score(
                    return_on_capital, net_credit, pop, 
                    short_candidate.delta, long_delta,
                    short_candidate.open_interest, long_oi
                )
                
                spread_candidate = CreditSpreadCandidate(
                    ticker=short_candidate.ticker,
                    expiration=short_candidate.expiration,
                    short_strike=short_strike,
                    long_strike=long_strike,
                    spread_width=actual_width,
                    short_delta=short_candidate.delta,
                    long_delta=long_delta,
                    short_bid=short_candidate.bid,
                    short_ask=short_candidate.ask,
                    short_mid=short_candidate.mid,
                    long_bid=long_bid,
                    long_ask=long_ask,
                    long_mid=long_mid,
                    net_credit=net_credit,
                    max_loss=max_loss / 100,  # Per share
                    max_profit=max_profit / 100,  # Per share
                    risk_reward_ratio=risk_reward_ratio,
                    return_on_capital=return_on_capital,
                    short_oi=short_candidate.open_interest,
                    long_oi=long_oi,
                    spot=spot,
                    pop_est=pop,
                    score=score
                )
                
                spread_candidates.append(spread_candidate)
                
            except Exception as e:
                logger.warning(f"⚠️ Error processing spread: {e}")
                continue
        
        # Sort by return on capital
        spread_candidates.sort(key=lambda c: c.return_on_capital, reverse=True)
        
        logger.info(f"✅ Found {len(spread_candidates)} 0-DTE credit spread candidates")
        
        return spread_candidates
    
    def _calculate_spread_score(self, return_on_capital: float, net_credit: float,
                               pop: Optional[float], short_delta: Optional[float],
                               long_delta: Optional[float], short_oi: int, long_oi: int) -> float:
        """Calculate composite score for credit spread"""
        score = 0.0
        
        # Return on capital (40% weight) - most important for spreads
        score += min(return_on_capital, 1.0) * 0.4
        
        # Net credit size (20% weight)
        score += min(net_credit / 0.50, 1.0) * 0.2
        
        # Probability of profit (25% weight)
        if pop:
            score += pop * 0.25
        
        # Delta spread (10% weight) - prefer reasonable delta difference
        if short_delta and long_delta:
            delta_diff = abs(short_delta) - abs(long_delta)
            # Want delta diff of 0.1-0.2
            if 0.05 <= delta_diff <= 0.25:
                score += 0.10
        
        # Liquidity (5% weight) - both legs should be liquid
        min_oi = min(short_oi, long_oi)
        liquidity_score = min(min_oi / 50, 1.0)
        score += liquidity_score * 0.05
        
        return score
    
    def scan_credit_spreads_multiple_tickers(self,
                                            tickers: Optional[List[str]] = None,
                                            spread_width: float = 2.0,
                                            min_credit: float = 0.10) -> pd.DataFrame:
        """
        Scan multiple tickers for credit spread opportunities
        
        Returns DataFrame with all credit spread candidates
        """
        if tickers is None:
            tickers = self.target_tickers
        
        all_spreads = []
        exp_date = self.target_expiration_date()
        
        for ticker in tickers:
            logger.info(f"🔍 Scanning {ticker} for 0-DTE credit spreads...")
            
            # Fetch chain
            chain = self.fetch_chain_snapshot_calls(ticker, exp_date)
            if not chain:
                continue
            
            # Resolve spot
            spot = self.resolve_spot(chain, ticker)
            if not spot:
                continue
            
            # Screen for credit spreads
            spreads = self.screen_credit_spreads(chain, spot, exp_date, spread_width, min_credit)
            all_spreads.extend([s.to_dict() for s in spreads])
        
        # Convert to DataFrame
        if all_spreads:
            df = pd.DataFrame(all_spreads)
            logger.info(f"✅ Found {len(df)} total credit spread candidates across {len(tickers)} tickers")
            return df
        else:
            logger.warning("No credit spread candidates found")
            return pd.DataFrame()
    
    def _calculate_score(self, premium_yield: float, max_profit: float,
                        pop: Optional[float], delta: Optional[float],
                        oi: int, spread: float, mid: float) -> float:
        """Calculate composite score for ranking"""
        score = 0.0
        
        # Premium yield (30% weight)
        score += premium_yield * 0.3
        
        # Max profit in dollars (20% weight)
        score += min(max_profit / 100, 1.0) * 0.2
        
        # Probability of profit (25% weight)
        if pop:
            score += pop * 0.25
        
        # Delta score - prefer ~30 delta (15% weight)
        if delta:
            delta_score = 1.0 - abs(abs(delta) - 0.30)
            score += max(delta_score, 0) * 0.15
        
        # Liquidity score (10% weight)
        liquidity_score = min(oi / 100, 1.0)
        score += liquidity_score * 0.10
        
        return score
    
    async def generate_signal(self, symbol: str, data: pd.DataFrame,
                            options_data: Optional[Dict[str, Any]] = None) -> Optional[TradeSignal]:
        """
        Generate 0-DTE covered call signal
        
        This method integrates with the existing strategy framework
        """
        # Get expiration date
        exp_date = self.target_expiration_date()
        
        # Fetch options chain
        chain = self.fetch_chain_snapshot_calls(symbol, exp_date)
        if not chain:
            logger.warning(f"No options chain data for {symbol}")
            return None
        
        # Resolve spot price
        spot = self.resolve_spot(chain, symbol)
        if not spot:
            logger.warning(f"Could not resolve spot price for {symbol}")
            return None
        
        # Screen candidates
        candidates = self.screen_candidates(chain, spot, exp_date)
        if not candidates:
            logger.warning(f"No 0-DTE candidates found for {symbol}")
            return None
        
        # Store candidates for later reference
        self.candidates = candidates
        
        # Get top candidate
        top_candidate = candidates[0]
        
        # Generate signal
        signal = TradeSignal(
            symbol=symbol,
            action="SELL_COVERED_CALL",
            quantity=1,
            price=top_candidate.mid,
            timestamp=datetime.now(),
            strategy=self.name,
            confidence=top_candidate.score,
            metadata={
                'strategy_type': '0-DTE',
                'expiration': top_candidate.expiration,
                'strike': top_candidate.strike,
                'delta': top_candidate.delta,
                'premium_yield': top_candidate.premium_yield,
                'max_profit': top_candidate.max_profit,
                'breakeven': top_candidate.breakeven,
                'pop_est': top_candidate.pop_est,
                'bid': top_candidate.bid,
                'ask': top_candidate.ask,
                'mid': top_candidate.mid,
                'open_interest': top_candidate.open_interest,
                'iv': top_candidate.iv,
                'spot': top_candidate.spot,
                'rank_metric': self.rank_metric,
                'candidates_found': len(candidates)
            }
        )
        
        logger.info(
            f"🎯 0-DTE signal: {symbol} ${top_candidate.strike:.2f} strike | "
            f"Premium: ${top_candidate.mid:.2f} ({top_candidate.premium_yield:.2%}) | "
            f"Score: {top_candidate.score:.3f}"
        )
        
        return signal
    
    def scan_multiple_tickers(self, tickers: Optional[List[str]] = None) -> pd.DataFrame:
        """
        Scan multiple tickers for 0-DTE opportunities
        
        Returns DataFrame with all candidates across tickers
        """
        if tickers is None:
            tickers = self.target_tickers
        
        all_candidates = []
        exp_date = self.target_expiration_date()
        
        for ticker in tickers:
            logger.info(f"🔍 Scanning {ticker} for 0-DTE opportunities...")
            
            # Fetch chain
            chain = self.fetch_chain_snapshot_calls(ticker, exp_date)
            if not chain:
                continue
            
            # Resolve spot
            spot = self.resolve_spot(chain, ticker)
            if not spot:
                continue
            
            # Screen
            candidates = self.screen_candidates(chain, spot, exp_date)
            all_candidates.extend([c.to_dict() for c in candidates])
        
        # Convert to DataFrame
        if all_candidates:
            df = pd.DataFrame(all_candidates)
            logger.info(f"✅ Found {len(df)} total 0-DTE candidates across {len(tickers)} tickers")
            return df
        else:
            logger.warning("No 0-DTE candidates found")
            return pd.DataFrame()
    
    def save_scan_results(self, df: pd.DataFrame, output_dir: str = "./data") -> str:
        """Save scan results to CSV"""
        import os
        from pathlib import Path
        
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        date_str = self.today_et().strftime("%Y-%m-%d")
        filename = f"0dte_covered_calls_{date_str}.csv"
        filepath = os.path.join(output_dir, filename)
        
        df.to_csv(filepath, index=False)
        logger.info(f"💾 Saved scan results to {filepath}")
        
        return filepath
    
    def mark_realized_pnl(self, csv_path: str, underlying_close: float) -> str:
        """
        Mark realized P&L for a previous scan after market close
        
        Args:
            csv_path: Path to previously saved scan CSV
            underlying_close: Closing price of underlying
        
        Returns:
            Path to marked CSV with P&L
        """
        df = pd.read_csv(csv_path)
        S_close = float(underlying_close)
        
        per_share_pnl = []
        assigned = []
        
        for _, row in df.iterrows():
            K = float(row["strike"])
            S0 = float(row["spot"])
            c = float(row["mid"])
            
            if S_close <= K:
                # Not assigned: keep premium
                pnl = c
                assigned.append(False)
            else:
                # Assigned: premium + (strike - original spot)
                pnl = c + (K - S0)
                assigned.append(True)
            
            per_share_pnl.append(pnl)
        
        df["assigned"] = assigned
        df["pnl_per_share"] = per_share_pnl
        df["pnl_per_contract"] = df["pnl_per_share"] * 100.0
        
        # Calculate return on capital (assuming we owned 100 shares)
        df["return_on_capital"] = df["pnl_per_share"] / df["spot"]
        
        # Save marked file
        out_path = csv_path.replace(".csv", "_marked.csv")
        df.to_csv(out_path, index=False)
        
        logger.info(f"✅ Marked P&L saved to {out_path}")
        logger.info(f"📊 Average P&L per contract: ${df['pnl_per_contract'].mean():.2f}")
        logger.info(f"📊 Win rate: {(df['pnl_per_contract'] > 0).mean():.1%}")
        
        return out_path
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """Get strategy information"""
        return {
            "name": self.name,
            "type": "0-DTE_options_income",
            "description": "0-DTE Covered Call screener for same-day income generation",
            "parameters": {
                "expiration_days": self.expiration_days,
                "min_otm_pct": self.min_otm_pct,
                "max_otm_pct": self.max_otm_pct,
                "delta_lo": self.delta_lo,
                "delta_hi": self.delta_hi,
                "min_bid": self.min_bid,
                "min_open_interest": self.min_open_interest,
                "max_spread_to_mid": self.max_spread_to_mid,
                "rank_metric": self.rank_metric
            },
            "target_tickers": self.target_tickers,
            "candidates_count": len(self.candidates),
            "active_positions": len(self.active_positions)
        }

