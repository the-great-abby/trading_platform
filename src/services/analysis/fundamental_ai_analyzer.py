#!/usr/bin/env python3
"""
Fundamental AI Analyzer
Combines Polygon Financials data with LLM analysis for comprehensive stock evaluation
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

import pandas as pd

from src.services.market_data.polygon_financials import (
    PolygonFinancialsClient,
    FinancialRatios,
    IncomeStatement,
    CashFlowStatement,
    BalanceSheet
)
from src.services.analysis.fundamental_screener import FundamentalScreener
from src.utils.trading_config import FUNDAMENTAL_ANALYSIS_CONFIG

logger = logging.getLogger(__name__)


@dataclass
class FundamentalAnalysis:
    """Comprehensive fundamental analysis result"""
    ticker: str
    timestamp: datetime
    
    # Ratios
    ratios: Optional[FinancialRatios]
    
    # Financial Health
    health_score: Dict[str, Any]
    health_rating: str
    
    # LLM Analysis
    llm_recommendation: str  # BUY, SELL, HOLD
    llm_confidence: float  # 0-100
    llm_reasoning: str
    
    # Key Insights
    strengths: List[str]
    weaknesses: List[str]
    opportunities: List[str]
    risks: List[str]
    
    # Valuation
    is_undervalued: bool
    is_overvalued: bool
    fair_value_estimate: Optional[float]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "ticker": self.ticker,
            "timestamp": self.timestamp.isoformat(),
            "ratios": {
                "price": self.ratios.price if self.ratios else None,
                "pe_ratio": self.ratios.price_to_earnings if self.ratios else None,
                "pb_ratio": self.ratios.price_to_book if self.ratios else None,
                "roe": self.ratios.return_on_equity if self.ratios else None,
                "debt_to_equity": self.ratios.debt_to_equity if self.ratios else None,
                "current_ratio": self.ratios.current if self.ratios else None,
            },
            "health_score": self.health_score,
            "health_rating": self.health_rating,
            "llm_analysis": {
                "recommendation": self.llm_recommendation,
                "confidence": self.llm_confidence,
                "reasoning": self.llm_reasoning
            },
            "insights": {
                "strengths": self.strengths,
                "weaknesses": self.weaknesses,
                "opportunities": self.opportunities,
                "risks": self.risks
            },
            "valuation": {
                "is_undervalued": self.is_undervalued,
                "is_overvalued": self.is_overvalued,
                "fair_value_estimate": self.fair_value_estimate
            }
        }


class FundamentalAIAnalyzer:
    """
    Combines fundamental data from Polygon Financials with AI analysis
    for comprehensive stock evaluation
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize analyzer"""
        self.financials_client = PolygonFinancialsClient(api_key)
        self.screener = FundamentalScreener(api_key)
        self.config = FUNDAMENTAL_ANALYSIS_CONFIG
    
    def get_fundamental_context(self, ticker: str) -> Dict[str, Any]:
        """
        Get comprehensive fundamental context for a stock
        This can be used to enhance LLM prompts
        
        Args:
            ticker: Stock ticker symbol
        
        Returns:
            Dictionary with fundamental data formatted for LLM context
        """
        context = {
            "ticker": ticker,
            "has_data": False
        }
        
        try:
            # Get ratios
            ratios_list = self.financials_client.get_ratios(ticker, limit=1)
            if not ratios_list:
                logger.warning(f"No ratios data for {ticker}")
                return context
            
            ratios = ratios_list[0]
            context["has_data"] = True
            
            # Calculate health score
            health_score = self.screener.calculate_financial_health_score(ratios)
            
            # Build context
            context.update({
                "valuation": {
                    "pe_ratio": ratios.price_to_earnings,
                    "pb_ratio": ratios.price_to_book,
                    "ps_ratio": ratios.price_to_sales,
                    "ev_to_ebitda": ratios.ev_to_ebitda,
                    "price_to_fcf": ratios.price_to_free_cash_flow,
                    "market_cap": ratios.market_cap,
                    "enterprise_value": ratios.enterprise_value
                },
                "profitability": {
                    "roe": ratios.return_on_equity,
                    "roa": ratios.return_on_assets,
                    "eps": ratios.earnings_per_share
                },
                "financial_health": {
                    "debt_to_equity": ratios.debt_to_equity,
                    "current_ratio": ratios.current,
                    "quick_ratio": ratios.quick,
                    "cash_ratio": ratios.cash
                },
                "income": {
                    "dividend_yield": ratios.dividend_yield,
                    "free_cash_flow": ratios.free_cash_flow
                },
                "health_score": health_score,
                "date": ratios.date
            })
            
            # Add income statement data if requested
            if self.config['ai_integration'].get('include_statements', False):
                income_stmts = self.financials_client.get_income_statements(
                    ticker, 
                    timeframe="trailing_twelve_months", 
                    limit=1
                )
                if income_stmts:
                    inc = income_stmts[0]
                    context["income_statement_ttm"] = {
                        "revenue": inc.revenue,
                        "gross_profit": inc.gross_profit,
                        "operating_income": inc.operating_income,
                        "net_income": inc.net_income_loss_attributable_common_shareholders,
                        "ebitda": inc.ebitda,
                        "period_end": inc.period_end
                    }
            
            return context
            
        except Exception as e:
            logger.error(f"Error getting fundamental context for {ticker}: {str(e)}")
            return context
    
    def build_llm_prompt_with_fundamentals(
        self,
        ticker: str,
        current_price: float,
        technical_data: Optional[Dict] = None,
        sentiment_data: Optional[Dict] = None
    ) -> str:
        """
        Build an enhanced LLM prompt that includes fundamental data
        
        Args:
            ticker: Stock ticker symbol
            current_price: Current stock price
            technical_data: Technical analysis data (optional)
            sentiment_data: Sentiment analysis data (optional)
        
        Returns:
            Enhanced prompt string for LLM
        """
        context = self.get_fundamental_context(ticker)
        
        if not context.get("has_data"):
            return self._build_basic_prompt(ticker, current_price, technical_data, sentiment_data)
        
        # Build comprehensive prompt with fundamental data
        prompt = f"""
You are an expert stock analyst. Provide a comprehensive analysis of {ticker} considering fundamental, technical, and sentiment factors.

CURRENT MARKET DATA:
- Ticker: {ticker}
- Price: ${current_price:.2f}
- Market Cap: ${context['valuation'].get('market_cap', 0):,.0f}

FUNDAMENTAL ANALYSIS:

Valuation Metrics:
- P/E Ratio: {context['valuation'].get('pe_ratio') if context['valuation'].get('pe_ratio') else 'N/A'}
- P/B Ratio: {f"{context['valuation'].get('pb_ratio'):.2f}" if context['valuation'].get('pb_ratio') else 'N/A'}
- P/S Ratio: {f"{context['valuation'].get('ps_ratio'):.2f}" if context['valuation'].get('ps_ratio') else 'N/A'}
- EV/EBITDA: {f"{context['valuation'].get('ev_to_ebitda'):.2f}" if context['valuation'].get('ev_to_ebitda') else 'N/A'}
- P/FCF: {f"{context['valuation'].get('price_to_fcf'):.2f}" if context['valuation'].get('price_to_fcf') else 'N/A'}

Profitability Metrics:
- ROE: {context['profitability'].get('roe', 0)*100:.2f}%
- ROA: {context['profitability'].get('roa', 0)*100:.2f}%
- EPS: ${context['profitability'].get('eps', 0):.2f}

Financial Health:
- Debt/Equity: {f"{context['financial_health'].get('debt_to_equity'):.2f}" if context['financial_health'].get('debt_to_equity') is not None else 'N/A'}
- Current Ratio: {f"{context['financial_health'].get('current_ratio'):.2f}" if context['financial_health'].get('current_ratio') else 'N/A'}
- Quick Ratio: {f"{context['financial_health'].get('quick_ratio'):.2f}" if context['financial_health'].get('quick_ratio') else 'N/A'}

Overall Financial Health Score: {context['health_score']['percentage']:.0f}/100 ({context['health_score']['rating']})
"""

        # Add income statement if available
        if 'income_statement_ttm' in context:
            inc_stmt = context['income_statement_ttm']
            prompt += f"""
Recent Financial Performance (TTM):
- Revenue: ${inc_stmt.get('revenue', 0):,.0f}
- Gross Profit: ${inc_stmt.get('gross_profit', 0):,.0f}
- Operating Income: ${inc_stmt.get('operating_income', 0):,.0f}
- Net Income: ${inc_stmt.get('net_income', 0):,.0f}
- EBITDA: ${inc_stmt.get('ebitda', 0):,.0f}
"""

        # Add technical data if provided
        if technical_data:
            prompt += f"""
TECHNICAL ANALYSIS:
- RSI: {technical_data.get('rsi', 'N/A')}
- MACD: {technical_data.get('macd', {}).get('value', 'N/A')}
- 20-day SMA: ${technical_data.get('sma_20', 0):.2f}
- 50-day SMA: ${technical_data.get('sma_50', 0):.2f}
- 200-day SMA: ${technical_data.get('sma_200', 0):.2f}
"""

        # Add sentiment data if provided
        if sentiment_data:
            prompt += f"""
SENTIMENT ANALYSIS:
- Sentiment Score: {sentiment_data.get('sentiment_score', 0):.2f}
- News Count: {sentiment_data.get('news_count', 0)}
- Recent Headlines: {sentiment_data.get('headlines', [])}
"""

        # Add analysis instructions
        prompt += """
Based on this comprehensive data, provide your analysis in JSON format:
{
    "recommendation": "BUY|SELL|HOLD",
    "confidence": 0-100,
    "reasoning": "Detailed explanation combining fundamental, technical, and sentiment factors",
    "target_price": estimated fair value,
    "stop_loss": recommended stop loss level,
    "position_size": "SMALL|MEDIUM|LARGE",
    "risk_level": "LOW|MEDIUM|HIGH",
    "strengths": ["key strength 1", "key strength 2", "key strength 3"],
    "weaknesses": ["key weakness 1", "key weakness 2"],
    "opportunities": ["opportunity 1", "opportunity 2"],
    "risks": ["risk 1", "risk 2"],
    "is_undervalued": true/false,
    "is_overvalued": true/false,
    "time_horizon": "SHORT_TERM|MEDIUM_TERM|LONG_TERM"
}

Focus on:
1. Valuation - Is the stock fairly valued based on fundamentals?
2. Financial Health - Does the company have a strong balance sheet?
3. Profitability - Is the company generating good returns?
4. Growth Potential - What are the growth prospects?
5. Risk Assessment - What are the key risks to consider?
6. Technical Signals - Do technicals support the fundamental view?
7. Market Sentiment - How does sentiment align with fundamentals?

Provide a balanced, data-driven analysis that considers all factors.
"""

        return prompt
    
    def _build_basic_prompt(
        self,
        ticker: str,
        current_price: float,
        technical_data: Optional[Dict],
        sentiment_data: Optional[Dict]
    ) -> str:
        """Build basic prompt without fundamental data"""
        prompt = f"""
You are an expert stock analyst. Analyze {ticker} at ${current_price:.2f}.

Note: Fundamental data not available for detailed analysis.
"""

        if technical_data:
            prompt += f"""
TECHNICAL ANALYSIS:
- RSI: {technical_data.get('rsi', 'N/A')}
- MACD: {technical_data.get('macd', {}).get('value', 'N/A')}
"""

        if sentiment_data:
            prompt += f"""
SENTIMENT ANALYSIS:
- Sentiment Score: {sentiment_data.get('sentiment_score', 0):.2f}
"""

        prompt += """
Provide basic analysis in JSON format with recommendation, confidence, and reasoning.
"""
        
        return prompt
    
    def analyze_with_fundamentals(
        self,
        ticker: str,
        include_technical: bool = True,
        include_sentiment: bool = True
    ) -> Dict[str, Any]:
        """
        Perform comprehensive analysis including fundamentals
        
        Args:
            ticker: Stock ticker symbol
            include_technical: Include technical analysis
            include_sentiment: Include sentiment analysis
        
        Returns:
            Comprehensive analysis dictionary
        """
        try:
            # Get fundamental context
            context = self.get_fundamental_context(ticker)
            
            if not context.get("has_data"):
                return {
                    "ticker": ticker,
                    "error": "No fundamental data available",
                    "has_fundamental_data": False
                }
            
            # Build analysis result
            analysis = {
                "ticker": ticker,
                "timestamp": datetime.utcnow().isoformat(),
                "has_fundamental_data": True,
                "fundamental_context": context,
                "prompt_ready": True
            }
            
            # The prompt can be used by LLM services
            analysis["llm_prompt"] = self.build_llm_prompt_with_fundamentals(
                ticker,
                context['valuation'].get('market_cap', 0) / 1e9,  # Approximate price
                None,  # Technical data would come from separate service
                None   # Sentiment data would come from separate service
            )
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing {ticker}: {str(e)}")
            return {
                "ticker": ticker,
                "error": str(e),
                "has_fundamental_data": False
            }
    
    def compare_stocks(self, tickers: List[str]) -> pd.DataFrame:
        """
        Compare multiple stocks based on fundamental metrics
        
        Args:
            tickers: List of ticker symbols to compare
        
        Returns:
            DataFrame with comparison data
        """
        import pandas as pd
        
        comparison_data = []
        
        for ticker in tickers:
            try:
                ratios_list = self.financials_client.get_ratios(ticker, limit=1)
                if not ratios_list:
                    continue
                
                ratios = ratios_list[0]
                health_score = self.screener.calculate_financial_health_score(ratios)
                
                comparison_data.append({
                    "Ticker": ticker,
                    "Price": ratios.price,
                    "Market Cap (B)": ratios.market_cap / 1e9 if ratios.market_cap else None,
                    "P/E": ratios.price_to_earnings,
                    "P/B": ratios.price_to_book,
                    "ROE %": ratios.return_on_equity * 100 if ratios.return_on_equity else None,
                    "ROA %": ratios.return_on_assets * 100 if ratios.return_on_assets else None,
                    "D/E": ratios.debt_to_equity,
                    "Current Ratio": ratios.current,
                    "EV/EBITDA": ratios.ev_to_ebitda,
                    "Div Yield %": ratios.dividend_yield * 100 if ratios.dividend_yield else None,
                    "Health Score": health_score['percentage'],
                    "Rating": health_score['rating']
                })
                
            except Exception as e:
                logger.error(f"Error comparing {ticker}: {str(e)}")
        
        df = pd.DataFrame(comparison_data)
        
        if not df.empty:
            # Sort by health score
            df = df.sort_values("Health Score", ascending=False)
        
        return df


if __name__ == "__main__":
    # Demo usage
    import pandas as pd
    logging.basicConfig(level=logging.INFO)
    
    analyzer = FundamentalAIAnalyzer()
    
    # Get fundamental context for a stock
    print("\n=== Fundamental Context for AAPL ===")
    context = analyzer.get_fundamental_context("AAPL")
    print(f"Has Data: {context.get('has_data')}")
    if context.get('has_data'):
        print(f"P/E Ratio: {context['valuation'].get('pe_ratio')}")
        print(f"ROE: {context['profitability'].get('roe', 0)*100:.2f}%")
        print(f"Health Score: {context['health_score']['percentage']:.0f}%")
    
    # Compare stocks
    print("\n=== Comparing Tech Stocks ===")
    comparison = analyzer.compare_stocks(["AAPL", "MSFT", "GOOGL", "AMZN"])
    if not comparison.empty:
        print(comparison.to_string(index=False))
    
    # Generate LLM prompt
    print("\n=== Sample LLM Prompt (first 500 chars) ===")
    prompt = analyzer.build_llm_prompt_with_fundamentals("AAPL", 175.0)
    print(prompt[:500] + "...")

