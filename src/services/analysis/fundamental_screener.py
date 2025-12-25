#!/usr/bin/env python3
"""
Fundamental Stock Screener
Uses Polygon Financials API to screen stocks based on fundamental criteria
"""

import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import pandas as pd

from src.services.market_data.polygon_financials import (
    PolygonFinancialsClient,
    FinancialRatios
)

logger = logging.getLogger(__name__)


class ScreenerCondition(Enum):
    """Screening condition types"""
    GREATER_THAN = ">"
    LESS_THAN = "<"
    GREATER_EQUAL = ">="
    LESS_EQUAL = "<="
    EQUAL = "=="
    BETWEEN = "between"


@dataclass
class ScreenerCriteria:
    """Criteria for fundamental screening"""
    field_name: str  # Name of the ratio field (e.g., "price_to_earnings")
    condition: ScreenerCondition
    value: float
    value_max: Optional[float] = None  # For BETWEEN condition
    
    def evaluate(self, ratios: FinancialRatios) -> bool:
        """Evaluate if ratios meet this criteria"""
        try:
            field_value = getattr(ratios, self.field_name, None)
            
            if field_value is None:
                return False
            
            if self.condition == ScreenerCondition.GREATER_THAN:
                return field_value > self.value
            elif self.condition == ScreenerCondition.LESS_THAN:
                return field_value < self.value
            elif self.condition == ScreenerCondition.GREATER_EQUAL:
                return field_value >= self.value
            elif self.condition == ScreenerCondition.LESS_EQUAL:
                return field_value <= self.value
            elif self.condition == ScreenerCondition.EQUAL:
                return abs(field_value - self.value) < 0.01
            elif self.condition == ScreenerCondition.BETWEEN:
                if self.value_max is None:
                    return False
                return self.value <= field_value <= self.value_max
            
            return False
        except Exception as e:
            logger.error(f"Error evaluating criteria: {str(e)}")
            return False


@dataclass
class ScreenerPreset:
    """Pre-defined screening presets"""
    name: str
    description: str
    criteria: List[ScreenerCriteria]


@dataclass
class ScreenerResult:
    """Result from fundamental screening"""
    ticker: str
    ratios: FinancialRatios
    score: float  # 0-100, based on how many criteria met
    passed_criteria: List[str]
    failed_criteria: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "ticker": self.ticker,
            "score": self.score,
            "passed_criteria": self.passed_criteria,
            "failed_criteria": self.failed_criteria,
            "ratios": {
                "price": self.ratios.price,
                "pe_ratio": self.ratios.price_to_earnings,
                "pb_ratio": self.ratios.price_to_book,
                "ps_ratio": self.ratios.price_to_sales,
                "roe": self.ratios.return_on_equity,
                "roa": self.ratios.return_on_assets,
                "debt_to_equity": self.ratios.debt_to_equity,
                "current_ratio": self.ratios.current,
                "quick_ratio": self.ratios.quick,
                "ev_to_ebitda": self.ratios.ev_to_ebitda,
                "dividend_yield": self.ratios.dividend_yield,
                "market_cap": self.ratios.market_cap
            }
        }


class FundamentalScreener:
    """Fundamental stock screener using Polygon Financials API"""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize fundamental screener"""
        self.client = PolygonFinancialsClient(api_key)
        self.presets = self._create_presets()
    
    def _create_presets(self) -> Dict[str, ScreenerPreset]:
        """Create pre-defined screening presets"""
        return {
            "value_stocks": ScreenerPreset(
                name="Value Stocks",
                description="Low P/E, P/B with strong profitability",
                criteria=[
                    ScreenerCriteria("price_to_earnings", ScreenerCondition.BETWEEN, 5, 15),
                    ScreenerCriteria("price_to_book", ScreenerCondition.LESS_THAN, 3),
                    ScreenerCriteria("return_on_equity", ScreenerCondition.GREATER_THAN, 0.15),
                    ScreenerCriteria("debt_to_equity", ScreenerCondition.LESS_THAN, 1.5)
                ]
            ),
            "growth_stocks": ScreenerPreset(
                name="Growth Stocks",
                description="High profitability, low debt",
                criteria=[
                    ScreenerCriteria("return_on_equity", ScreenerCondition.GREATER_THAN, 0.20),
                    ScreenerCriteria("return_on_assets", ScreenerCondition.GREATER_THAN, 0.10),
                    ScreenerCriteria("debt_to_equity", ScreenerCondition.LESS_THAN, 1.0),
                    ScreenerCriteria("current", ScreenerCondition.GREATER_THAN, 1.5)
                ]
            ),
            "dividend_stocks": ScreenerPreset(
                name="Dividend Stocks",
                description="High dividend yield with financial stability",
                criteria=[
                    ScreenerCriteria("dividend_yield", ScreenerCondition.GREATER_THAN, 0.03),
                    ScreenerCriteria("debt_to_equity", ScreenerCondition.LESS_THAN, 2.0),
                    ScreenerCriteria("current", ScreenerCondition.GREATER_THAN, 1.0),
                    ScreenerCriteria("return_on_equity", ScreenerCondition.GREATER_THAN, 0.10)
                ]
            ),
            "quality_stocks": ScreenerPreset(
                name="Quality Stocks",
                description="Strong balance sheet and profitability",
                criteria=[
                    ScreenerCriteria("return_on_equity", ScreenerCondition.GREATER_THAN, 0.15),
                    ScreenerCriteria("return_on_assets", ScreenerCondition.GREATER_THAN, 0.08),
                    ScreenerCriteria("debt_to_equity", ScreenerCondition.LESS_THAN, 1.0),
                    ScreenerCriteria("current", ScreenerCondition.GREATER_THAN, 1.5),
                    ScreenerCriteria("quick", ScreenerCondition.GREATER_THAN, 1.0)
                ]
            ),
            "undervalued_high_quality": ScreenerPreset(
                name="Undervalued High Quality",
                description="Low EV/EBITDA with strong ROE and liquidity",
                criteria=[
                    ScreenerCriteria("ev_to_ebitda", ScreenerCondition.LESS_THAN, 12),
                    ScreenerCriteria("return_on_equity", ScreenerCondition.GREATER_THAN, 0.15),
                    ScreenerCriteria("current", ScreenerCondition.GREATER_THAN, 1.5),
                    ScreenerCriteria("debt_to_equity", ScreenerCondition.LESS_THAN, 1.5)
                ]
            ),
            "buffett_style": ScreenerPreset(
                name="Buffett Style",
                description="Warren Buffett inspired criteria - high ROE, low debt, reasonable valuation",
                criteria=[
                    ScreenerCriteria("return_on_equity", ScreenerCondition.GREATER_THAN, 0.20),
                    ScreenerCriteria("debt_to_equity", ScreenerCondition.LESS_THAN, 0.5),
                    ScreenerCriteria("current", ScreenerCondition.GREATER_THAN, 1.5),
                    ScreenerCriteria("price_to_earnings", ScreenerCondition.BETWEEN, 10, 25)
                ]
            ),
            "deep_value": ScreenerPreset(
                name="Deep Value",
                description="Extremely low valuation multiples",
                criteria=[
                    ScreenerCriteria("price_to_earnings", ScreenerCondition.LESS_THAN, 10),
                    ScreenerCriteria("price_to_book", ScreenerCondition.LESS_THAN, 1.5),
                    ScreenerCriteria("price_to_sales", ScreenerCondition.LESS_THAN, 1.0),
                    ScreenerCriteria("return_on_equity", ScreenerCondition.GREATER_THAN, 0.10)
                ]
            ),
            "financially_strong": ScreenerPreset(
                name="Financially Strong",
                description="Focus on liquidity and low leverage",
                criteria=[
                    ScreenerCriteria("current", ScreenerCondition.GREATER_THAN, 2.0),
                    ScreenerCriteria("quick", ScreenerCondition.GREATER_THAN, 1.5),
                    ScreenerCriteria("debt_to_equity", ScreenerCondition.LESS_THAN, 0.5),
                    ScreenerCriteria("cash", ScreenerCondition.GREATER_THAN, 0.5)
                ]
            ),
            "fcf_focused": ScreenerPreset(
                name="Free Cash Flow Focused",
                description="Strong free cash flow generation",
                criteria=[
                    ScreenerCriteria("price_to_free_cash_flow", ScreenerCondition.LESS_THAN, 20),
                    ScreenerCriteria("return_on_assets", ScreenerCondition.GREATER_THAN, 0.08),
                    ScreenerCriteria("current", ScreenerCondition.GREATER_THAN, 1.2)
                ]
            )
        }
    
    def screen_stock(
        self,
        ticker: str,
        criteria: List[ScreenerCriteria]
    ) -> Optional[ScreenerResult]:
        """
        Screen a single stock against criteria
        
        Args:
            ticker: Stock ticker symbol
            criteria: List of screening criteria
        
        Returns:
            ScreenerResult if ratios available, None otherwise
        """
        try:
            ratios_list = self.client.get_ratios(ticker, limit=1)
            
            if not ratios_list:
                logger.warning(f"No ratios data for {ticker}")
                return None
            
            ratios = ratios_list[0]
            
            passed = []
            failed = []
            
            for criterion in criteria:
                if criterion.evaluate(ratios):
                    passed.append(criterion.field_name)
                else:
                    failed.append(criterion.field_name)
            
            score = (len(passed) / len(criteria)) * 100 if criteria else 0
            
            return ScreenerResult(
                ticker=ticker,
                ratios=ratios,
                score=score,
                passed_criteria=passed,
                failed_criteria=failed
            )
            
        except Exception as e:
            logger.error(f"Error screening {ticker}: {str(e)}")
            return None
    
    def screen_stocks(
        self,
        tickers: List[str],
        criteria: List[ScreenerCriteria],
        min_score: float = 80.0
    ) -> List[ScreenerResult]:
        """
        Screen multiple stocks and return those meeting criteria
        
        Args:
            tickers: List of ticker symbols
            criteria: List of screening criteria
            min_score: Minimum score (0-100) to include in results
        
        Returns:
            List of ScreenerResults sorted by score
        """
        results = []
        
        for ticker in tickers:
            result = self.screen_stock(ticker, criteria)
            if result and result.score >= min_score:
                results.append(result)
                logger.info(f"{ticker}: Score {result.score:.1f}% - {len(result.passed_criteria)}/{len(criteria)} criteria met")
        
        # Sort by score descending
        results.sort(key=lambda x: x.score, reverse=True)
        
        return results
    
    def screen_with_preset(
        self,
        tickers: List[str],
        preset_name: str,
        min_score: float = 80.0
    ) -> List[ScreenerResult]:
        """
        Screen stocks using a pre-defined preset
        
        Args:
            tickers: List of ticker symbols
            preset_name: Name of preset to use
            min_score: Minimum score to include in results
        
        Returns:
            List of ScreenerResults
        """
        if preset_name not in self.presets:
            logger.error(f"Unknown preset: {preset_name}")
            return []
        
        preset = self.presets[preset_name]
        logger.info(f"Screening with preset: {preset.name} - {preset.description}")
        
        return self.screen_stocks(tickers, preset.criteria, min_score)
    
    def get_available_presets(self) -> List[Dict[str, str]]:
        """Get list of available screening presets"""
        return [
            {
                "name": preset.name,
                "key": key,
                "description": preset.description,
                "criteria_count": len(preset.criteria)
            }
            for key, preset in self.presets.items()
        ]
    
    def create_custom_screen(
        self,
        tickers: List[str],
        **kwargs
    ) -> List[ScreenerResult]:
        """
        Create a custom screen with flexible criteria
        
        Args:
            tickers: List of ticker symbols
            **kwargs: Criteria as keyword arguments, e.g.:
                pe_ratio_max=15,
                roe_min=0.15,
                debt_to_equity_max=1.5
        
        Returns:
            List of ScreenerResults
        """
        criteria = []
        
        # Parse kwargs into criteria
        for key, value in kwargs.items():
            parts = key.rsplit('_', 1)
            if len(parts) != 2:
                continue
            
            field_name, condition_str = parts
            
            # Convert condition string to ScreenerCondition
            if condition_str == 'max':
                condition = ScreenerCondition.LESS_EQUAL
            elif condition_str == 'min':
                condition = ScreenerCondition.GREATER_EQUAL
            else:
                continue
            
            criteria.append(ScreenerCriteria(field_name, condition, value))
        
        return self.screen_stocks(tickers, criteria, min_score=80.0)
    
    def calculate_financial_health_score(self, ratios: FinancialRatios) -> Dict[str, Any]:
        """
        Calculate a comprehensive financial health score
        
        Args:
            ratios: Financial ratios for a stock
        
        Returns:
            Dictionary with overall score and component scores
        """
        scores = {
            "valuation": 0,
            "profitability": 0,
            "liquidity": 0,
            "leverage": 0,
            "efficiency": 0
        }
        
        # Valuation Score (0-20)
        if ratios.price_to_earnings:
            if ratios.price_to_earnings < 15:
                scores["valuation"] += 10
            elif ratios.price_to_earnings < 25:
                scores["valuation"] += 5
        
        if ratios.price_to_book:
            if ratios.price_to_book < 2:
                scores["valuation"] += 10
            elif ratios.price_to_book < 4:
                scores["valuation"] += 5
        
        # Profitability Score (0-20)
        if ratios.return_on_equity:
            if ratios.return_on_equity > 0.20:
                scores["profitability"] += 10
            elif ratios.return_on_equity > 0.15:
                scores["profitability"] += 7
            elif ratios.return_on_equity > 0.10:
                scores["profitability"] += 5
        
        if ratios.return_on_assets:
            if ratios.return_on_assets > 0.10:
                scores["profitability"] += 10
            elif ratios.return_on_assets > 0.05:
                scores["profitability"] += 5
        
        # Liquidity Score (0-20)
        if ratios.current:
            if ratios.current > 2.0:
                scores["liquidity"] += 10
            elif ratios.current > 1.5:
                scores["liquidity"] += 7
            elif ratios.current > 1.0:
                scores["liquidity"] += 5
        
        if ratios.quick:
            if ratios.quick > 1.5:
                scores["liquidity"] += 10
            elif ratios.quick > 1.0:
                scores["liquidity"] += 5
        
        # Leverage Score (0-20)
        if ratios.debt_to_equity is not None:
            if ratios.debt_to_equity < 0.5:
                scores["leverage"] += 20
            elif ratios.debt_to_equity < 1.0:
                scores["leverage"] += 15
            elif ratios.debt_to_equity < 1.5:
                scores["leverage"] += 10
            elif ratios.debt_to_equity < 2.0:
                scores["leverage"] += 5
        
        # Efficiency Score (0-20)
        if ratios.ev_to_ebitda:
            if ratios.ev_to_ebitda < 10:
                scores["efficiency"] += 10
            elif ratios.ev_to_ebitda < 15:
                scores["efficiency"] += 7
            elif ratios.ev_to_ebitda < 20:
                scores["efficiency"] += 5
        
        if ratios.price_to_free_cash_flow:
            if ratios.price_to_free_cash_flow < 15:
                scores["efficiency"] += 10
            elif ratios.price_to_free_cash_flow < 25:
                scores["efficiency"] += 5
        
        # Calculate overall score
        overall_score = sum(scores.values())
        
        return {
            "overall_score": overall_score,
            "max_score": 100,
            "percentage": (overall_score / 100) * 100,
            "rating": self._get_rating(overall_score),
            "component_scores": scores
        }
    
    def _get_rating(self, score: float) -> str:
        """Get rating based on score"""
        if score >= 80:
            return "Excellent"
        elif score >= 65:
            return "Good"
        elif score >= 50:
            return "Fair"
        elif score >= 35:
            return "Poor"
        else:
            return "Very Poor"


if __name__ == "__main__":
    # Demo usage
    logging.basicConfig(level=logging.INFO)
    
    screener = FundamentalScreener()
    
    # Show available presets
    print("\n=== Available Screening Presets ===")
    for preset in screener.get_available_presets():
        print(f"- {preset['key']}: {preset['name']} ({preset['criteria_count']} criteria)")
    
    # Screen some stocks with "quality_stocks" preset
    test_tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]
    print(f"\n=== Screening {test_tickers} for Quality Stocks ===")
    
    results = screener.screen_with_preset(test_tickers, "quality_stocks", min_score=50.0)
    
    for result in results:
        print(f"\n{result.ticker} - Score: {result.score:.1f}%")
        print(f"  Passed: {', '.join(result.passed_criteria)}")
        if result.failed_criteria:
            print(f"  Failed: {', '.join(result.failed_criteria)}")
        
        # Calculate health score
        health = screener.calculate_financial_health_score(result.ratios)
        print(f"  Health Score: {health['percentage']:.0f}% - {health['rating']}")

