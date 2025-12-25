#!/usr/bin/env python3
"""
Fundamental Analysis Service
Provides REST API for Polygon Financials data, screening, and AI-enhanced analysis
"""

import os
import sys
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Add src to path
sys.path.insert(0, '/app/src')

from src.services.market_data.polygon_financials import PolygonFinancialsClient
from src.services.analysis.fundamental_screener import FundamentalScreener, ScreenerCriteria, ScreenerCondition
from src.services.analysis.fundamental_ai_analyzer import FundamentalAIAnalyzer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="Fundamental Analysis Service",
    description="Comprehensive fundamental analysis using Polygon Financials API",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize clients
financials_client = None
screener = None
ai_analyzer = None

def get_clients():
    """Lazy initialization of clients"""
    global financials_client, screener, ai_analyzer
    
    if financials_client is None:
        api_key = os.getenv('POLYGON_API_KEY')
        financials_client = PolygonFinancialsClient(api_key)
        screener = FundamentalScreener(api_key)
        ai_analyzer = FundamentalAIAnalyzer(api_key)
    
    return financials_client, screener, ai_analyzer


# Request/Response Models
class ScreenRequest(BaseModel):
    tickers: List[str]
    preset: Optional[str] = "quality_stocks"
    min_score: float = 80.0


class ComparisonRequest(BaseModel):
    tickers: List[str]


# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "fundamental-analysis-service",
        "timestamp": datetime.utcnow().isoformat()
    }


# Ratios Endpoints
@app.get("/api/v1/ratios/{ticker}")
async def get_ratios(ticker: str):
    """
    Get latest financial ratios for a ticker
    
    Returns daily snapshot with valuation, profitability, liquidity, and leverage ratios
    """
    try:
        client, _, _ = get_clients()
        ratios_list = client.get_ratios(ticker, limit=1)
        
        if not ratios_list:
            raise HTTPException(status_code=404, detail=f"No ratios data found for {ticker}")
        
        ratios = ratios_list[0]
        
        return {
            "ticker": ratios.ticker,
            "date": ratios.date,
            "valuation": {
                "price": ratios.price,
                "market_cap": ratios.market_cap,
                "pe_ratio": ratios.price_to_earnings,
                "pb_ratio": ratios.price_to_book,
                "ps_ratio": ratios.price_to_sales,
                "pcf_ratio": ratios.price_to_cash_flow,
                "pfcf_ratio": ratios.price_to_free_cash_flow,
                "ev_to_sales": ratios.ev_to_sales,
                "ev_to_ebitda": ratios.ev_to_ebitda,
                "enterprise_value": ratios.enterprise_value
            },
            "profitability": {
                "eps": ratios.earnings_per_share,
                "roe": ratios.return_on_equity,
                "roa": ratios.return_on_assets
            },
            "liquidity": {
                "current_ratio": ratios.current,
                "quick_ratio": ratios.quick,
                "cash_ratio": ratios.cash
            },
            "leverage": {
                "debt_to_equity": ratios.debt_to_equity
            },
            "income": {
                "dividend_yield": ratios.dividend_yield,
                "free_cash_flow": ratios.free_cash_flow
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching ratios for {ticker}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/income-statement/{ticker}")
async def get_income_statement(
    ticker: str,
    timeframe: str = Query("trailing_twelve_months", regex="^(quarterly|annual|trailing_twelve_months)$"),
    limit: int = Query(4, ge=1, le=20)
):
    """Get income statement data for a ticker"""
    try:
        client, _, _ = get_clients()
        income_statements = client.get_income_statements(ticker, timeframe=timeframe, limit=limit)
        
        if not income_statements:
            raise HTTPException(status_code=404, detail=f"No income statement data found for {ticker}")
        
        results = []
        for inc in income_statements:
            results.append({
                "ticker": inc.ticker,
                "period_end": inc.period_end,
                "fiscal_year": inc.fiscal_year,
                "fiscal_quarter": inc.fiscal_quarter,
                "timeframe": inc.timeframe,
                "revenue": inc.revenue,
                "cost_of_revenue": inc.cost_of_revenue,
                "gross_profit": inc.gross_profit,
                "operating_expenses": inc.total_operating_expenses,
                "operating_income": inc.operating_income,
                "net_income": inc.net_income_loss_attributable_common_shareholders,
                "ebitda": inc.ebitda,
                "eps_basic": inc.basic_earnings_per_share,
                "eps_diluted": inc.diluted_earnings_per_share,
                "shares_outstanding": inc.diluted_shares_outstanding
            })
        
        return {"ticker": ticker, "timeframe": timeframe, "results": results}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching income statement for {ticker}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/cash-flow/{ticker}")
async def get_cash_flow(
    ticker: str,
    timeframe: str = Query("trailing_twelve_months", regex="^(quarterly|annual|trailing_twelve_months)$"),
    limit: int = Query(4, ge=1, le=20)
):
    """Get cash flow statement data for a ticker"""
    try:
        client, _, _ = get_clients()
        cash_flows = client.get_cash_flow_statements(ticker, timeframe=timeframe, limit=limit)
        
        if not cash_flows:
            raise HTTPException(status_code=404, detail=f"No cash flow data found for {ticker}")
        
        results = []
        for cf in cash_flows:
            results.append({
                "ticker": cf.ticker,
                "period_end": cf.period_end,
                "fiscal_year": cf.fiscal_year,
                "fiscal_quarter": cf.fiscal_quarter,
                "timeframe": cf.timeframe,
                "operating_cash_flow": cf.net_cash_from_operating_activities,
                "investing_cash_flow": cf.net_cash_from_investing_activities,
                "financing_cash_flow": cf.net_cash_from_financing_activities,
                "net_cash_change": cf.change_in_cash_and_equivalents,
                "capex": cf.purchase_of_property_plant_and_equipment,
                "dividends": cf.dividends,
                "net_income": cf.net_income
            })
        
        return {"ticker": ticker, "timeframe": timeframe, "results": results}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching cash flow for {ticker}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/balance-sheet/{ticker}")
async def get_balance_sheet(
    ticker: str,
    timeframe: str = Query("quarterly", regex="^(quarterly|annual)$"),
    limit: int = Query(4, ge=1, le=20)
):
    """Get balance sheet data for a ticker"""
    try:
        client, _, _ = get_clients()
        balance_sheets = client.get_balance_sheets(ticker, timeframe=timeframe, limit=limit)
        
        if not balance_sheets:
            raise HTTPException(status_code=404, detail=f"No balance sheet data found for {ticker}")
        
        results = []
        for bs in balance_sheets:
            results.append({
                "ticker": bs.ticker,
                "period_end": bs.period_end,
                "fiscal_year": bs.fiscal_year,
                "fiscal_quarter": bs.fiscal_quarter,
                "timeframe": bs.timeframe,
                "total_assets": bs.total_assets,
                "current_assets": bs.total_current_assets,
                "cash": bs.cash_and_equivalents,
                "total_liabilities": bs.total_liabilities,
                "current_liabilities": bs.total_current_liabilities,
                "long_term_debt": bs.long_term_debt_and_capital_lease_obligations,
                "total_equity": bs.total_equity,
                "retained_earnings": bs.retained_earnings_deficit
            })
        
        return {"ticker": ticker, "timeframe": timeframe, "results": results}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching balance sheet for {ticker}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/comprehensive/{ticker}")
async def get_comprehensive_financials(ticker: str):
    """Get all financial data for a ticker in one call"""
    try:
        client, _, _ = get_clients()
        data = client.get_comprehensive_financials(ticker)
        
        return {
            "ticker": ticker,
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "ratios": [r.__dict__ for r in data.get("ratios", [])],
                "income_statement_ttm": [i.__dict__ for i in data.get("income_statement_ttm", [])],
                "cash_flow_ttm": [c.__dict__ for c in data.get("cash_flow_ttm", [])],
                "balance_sheet_latest": [b.__dict__ for b in data.get("balance_sheet_quarterly", [])][:1]
            }
        }
        
    except Exception as e:
        logger.error(f"Error fetching comprehensive financials for {ticker}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Screening Endpoints
@app.get("/api/v1/screening/presets")
async def get_screening_presets():
    """Get available screening presets"""
    try:
        _, screener_client, _ = get_clients()
        return {"presets": screener_client.get_available_presets()}
        
    except Exception as e:
        logger.error(f"Error fetching presets: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/screening/screen")
async def screen_stocks(request: ScreenRequest):
    """Screen stocks using a preset"""
    try:
        _, screener_client, _ = get_clients()
        
        results = screener_client.screen_with_preset(
            request.tickers,
            request.preset,
            request.min_score
        )
        
        return {
            "preset": request.preset,
            "min_score": request.min_score,
            "total_screened": len(request.tickers),
            "passed": len(results),
            "results": [r.to_dict() for r in results]
        }
        
    except Exception as e:
        logger.error(f"Error screening stocks: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/screening/health-score/{ticker}")
async def get_health_score(ticker: str):
    """Get financial health score for a ticker"""
    try:
        client, screener_client, _ = get_clients()
        
        ratios_list = client.get_ratios(ticker, limit=1)
        if not ratios_list:
            raise HTTPException(status_code=404, detail=f"No data found for {ticker}")
        
        health_score = screener_client.calculate_financial_health_score(ratios_list[0])
        
        return {
            "ticker": ticker,
            "health_score": health_score
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating health score for {ticker}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# AI Analysis Endpoints
@app.get("/api/v1/ai/context/{ticker}")
async def get_fundamental_context(ticker: str):
    """Get fundamental context suitable for LLM analysis"""
    try:
        _, _, analyzer = get_clients()
        context = analyzer.get_fundamental_context(ticker)
        
        if not context.get("has_data"):
            raise HTTPException(status_code=404, detail=f"No fundamental data found for {ticker}")
        
        return context
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting context for {ticker}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/ai/prompt/{ticker}")
async def get_llm_prompt(ticker: str, current_price: float = Query(..., gt=0)):
    """Get enhanced LLM prompt with fundamental data"""
    try:
        _, _, analyzer = get_clients()
        prompt = analyzer.build_llm_prompt_with_fundamentals(ticker, current_price)
        
        return {
            "ticker": ticker,
            "prompt": prompt,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error building prompt for {ticker}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/ai/compare")
async def compare_stocks(request: ComparisonRequest):
    """Compare multiple stocks based on fundamentals"""
    try:
        _, _, analyzer = get_clients()
        comparison_df = analyzer.compare_stocks(request.tickers)
        
        if comparison_df.empty:
            return {
                "tickers": request.tickers,
                "results": [],
                "message": "No data available for comparison"
            }
        
        # Convert DataFrame to dict
        results = comparison_df.to_dict('records')
        
        return {
            "tickers": request.tickers,
            "results": results,
            "count": len(results)
        }
        
    except Exception as e:
        logger.error(f"Error comparing stocks: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    port = int(os.getenv("PORT", "11090"))
    uvicorn.run(app, host="0.0.0.0", port=port)

