#!/usr/bin/env python3
"""
Polygon Financials API Client
Provides access to Balance Sheets, Cash Flow, Income Statements, and Financial Ratios
"""

import os
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class BalanceSheet:
    """Balance Sheet data"""
    ticker: str
    cik: str
    period_end: str
    filing_date: str
    fiscal_quarter: int
    fiscal_year: int
    timeframe: str
    
    # Assets
    cash_and_equivalents: Optional[float] = None
    short_term_investments: Optional[float] = None
    receivables: Optional[float] = None
    inventories: Optional[float] = None
    other_current_assets: Optional[float] = None
    total_current_assets: Optional[float] = None
    property_plant_equipment_net: Optional[float] = None
    other_assets: Optional[float] = None
    total_assets: Optional[float] = None
    
    # Liabilities
    accounts_payable: Optional[float] = None
    deferred_revenue_current: Optional[float] = None
    debt_current: Optional[float] = None
    accrued_and_other_current_liabilities: Optional[float] = None
    total_current_liabilities: Optional[float] = None
    long_term_debt_and_capital_lease_obligations: Optional[float] = None
    other_noncurrent_liabilities: Optional[float] = None
    total_liabilities: Optional[float] = None
    
    # Equity
    common_stock: Optional[float] = None
    accumulated_other_comprehensive_income: Optional[float] = None
    retained_earnings_deficit: Optional[float] = None
    other_equity: Optional[float] = None
    total_equity_attributable_to_parent: Optional[float] = None
    total_equity: Optional[float] = None
    total_liabilities_and_equity: Optional[float] = None


@dataclass
class CashFlowStatement:
    """Cash Flow Statement data"""
    ticker: str
    cik: str
    period_end: str
    filing_date: str
    fiscal_quarter: int
    fiscal_year: int
    timeframe: str
    
    # Operating Activities
    net_income: Optional[float] = None
    depreciation_depletion_and_amortization: Optional[float] = None
    other_operating_activities: Optional[float] = None
    change_in_other_operating_assets_and_liabilities_net: Optional[float] = None
    cash_from_operating_activities_continuing_operations: Optional[float] = None
    net_cash_from_operating_activities: Optional[float] = None
    
    # Investing Activities
    purchase_of_property_plant_and_equipment: Optional[float] = None
    other_investing_activities: Optional[float] = None
    net_cash_from_investing_activities_continuing_operations: Optional[float] = None
    net_cash_from_investing_activities: Optional[float] = None
    
    # Financing Activities
    short_term_debt_issuances_repayments: Optional[float] = None
    long_term_debt_issuances_repayments: Optional[float] = None
    dividends: Optional[float] = None
    other_financing_activities: Optional[float] = None
    net_cash_from_financing_activities_continuing_operations: Optional[float] = None
    net_cash_from_financing_activities: Optional[float] = None
    
    change_in_cash_and_equivalents: Optional[float] = None


@dataclass
class IncomeStatement:
    """Income Statement data"""
    ticker: str
    cik: str
    period_end: str
    filing_date: str
    fiscal_quarter: int
    fiscal_year: int
    timeframe: str
    
    # Revenue and Costs
    revenue: Optional[float] = None
    cost_of_revenue: Optional[float] = None
    gross_profit: Optional[float] = None
    
    # Operating Expenses
    selling_general_administrative: Optional[float] = None
    research_development: Optional[float] = None
    other_operating_expenses: Optional[float] = None
    total_operating_expenses: Optional[float] = None
    
    # Income
    operating_income: Optional[float] = None
    other_income_expense: Optional[float] = None
    total_other_income_expense: Optional[float] = None
    income_before_income_taxes: Optional[float] = None
    income_taxes: Optional[float] = None
    consolidated_net_income_loss: Optional[float] = None
    net_income_loss_attributable_common_shareholders: Optional[float] = None
    
    # Per Share Data
    basic_earnings_per_share: Optional[float] = None
    diluted_earnings_per_share: Optional[float] = None
    basic_shares_outstanding: Optional[float] = None
    diluted_shares_outstanding: Optional[float] = None
    ebitda: Optional[float] = None


@dataclass
class FinancialRatios:
    """Financial Ratios - daily snapshot combining filings and market data"""
    ticker: str
    cik: str
    date: str  # Date for which ratios are calculated
    
    # Price and Market Data
    price: Optional[float] = None
    average_volume: Optional[float] = None
    market_cap: Optional[float] = None
    
    # Valuation Ratios
    earnings_per_share: Optional[float] = None
    price_to_earnings: Optional[float] = None  # P/E
    price_to_book: Optional[float] = None  # P/B
    price_to_sales: Optional[float] = None  # P/S
    price_to_cash_flow: Optional[float] = None  # P/CF
    price_to_free_cash_flow: Optional[float] = None  # P/FCF
    dividend_yield: Optional[float] = None
    
    # Profitability Ratios
    return_on_assets: Optional[float] = None  # ROA
    return_on_equity: Optional[float] = None  # ROE
    
    # Leverage Ratios
    debt_to_equity: Optional[float] = None  # D/E
    
    # Liquidity Ratios
    current: Optional[float] = None  # Current Ratio
    quick: Optional[float] = None  # Quick Ratio
    cash: Optional[float] = None  # Cash Ratio
    
    # EV Multiples
    ev_to_sales: Optional[float] = None  # EV/Sales
    ev_to_ebitda: Optional[float] = None  # EV/EBITDA
    enterprise_value: Optional[float] = None  # EV
    
    # Cash Flow Metrics
    free_cash_flow: Optional[float] = None


class PolygonFinancialsClient:
    """Client for Polygon.io Financials API"""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize Polygon Financials client"""
        self.api_key = api_key or os.getenv('POLYGON_API_KEY')
        if not self.api_key:
            logger.warning("Polygon API key not provided")
        
        self.base_url = "https://api.polygon.io"
        self.session = self._create_session()
        
        # Rate limiting state
        self.last_request_time = 0
        self.request_count = 0
        self.rate_limit_hits = 0
        self.min_delay_between_requests = 1.0
        self.max_requests_per_minute = 60
    
    def _create_session(self) -> requests.Session:
        """Create requests session with retry logic"""
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=3,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session
    
    def _enforce_rate_limit(self):
        """Enforce rate limiting with adaptive delays"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        required_delay = self.min_delay_between_requests
        
        if self.rate_limit_hits > 0:
            extra_delay = self.rate_limit_hits * 60
            required_delay += extra_delay
        
        if time_since_last_request < required_delay:
            sleep_time = required_delay - time_since_last_request
            logger.info(f"[Polygon Financials] Rate limiting: waiting {sleep_time:.2f}s")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
        self.request_count += 1
    
    def _make_request(self, endpoint: str, params: Dict[str, Any] = None) -> Optional[Dict]:
        """Make API request with error handling"""
        if not self.api_key:
            logger.error("Polygon API key required")
            return None
        
        try:
            self._enforce_rate_limit()
            
            params = params or {}
            
            # Send API key in Authorization header (more secure than URL params)
            # Polygon supports Bearer token authentication
            headers = {
                "Authorization": f"Bearer {self.api_key}"
            }
            
            url = f"{self.base_url}{endpoint}"
            logger.info(f"[Polygon Financials] Request: {endpoint}")
            
            # Try with Authorization header first
            response = self.session.get(url, params=params, headers=headers, timeout=30)
            
            # If we get 401/403, try with query param as fallback
            if response.status_code in [401, 403]:
                logger.info("[Polygon Financials] Retrying with query param authentication")
                params["apiKey"] = self.api_key
                response = self.session.get(url, params=params, timeout=30)
            
            if response.status_code == 429:
                self.rate_limit_hits += 1
                wait_time = 120 + (self.rate_limit_hits * 60)
                logger.warning(f"Rate limit hit. Waiting {wait_time}s")
                time.sleep(wait_time)
                return self._make_request(endpoint, params)
            
            # Handle 403 Forbidden - likely plan limitation
            if response.status_code == 403:
                logger.error(
                    f"[Polygon Financials] 403 Forbidden - Your Polygon plan does not include "
                    f"access to Financials API endpoints. Requires Stocks Advanced plan or "
                    f"Financials API add-on. Endpoint: {endpoint}"
                )
                return None
            
            response.raise_for_status()
            data = response.json()
            
            if data.get("status") == "OK":
                self.rate_limit_hits = max(0, self.rate_limit_hits - 1)
                return data
            else:
                logger.error(f"API error: {data.get('status')}")
                return None
            
        except Exception as e:
            logger.error(f"Request error: {str(e)}")
            return None
    
    def get_balance_sheets(
        self,
        ticker: str,
        fiscal_year: Optional[int] = None,
        fiscal_quarter: Optional[int] = None,
        timeframe: str = "quarterly",
        limit: int = 10
    ) -> List[BalanceSheet]:
        """
        Get balance sheet data for a ticker
        
        Args:
            ticker: Stock ticker symbol
            fiscal_year: Filter by fiscal year
            fiscal_quarter: Filter by quarter (1-4)
            timeframe: "quarterly" or "annual"
            limit: Number of results to return
        
        Returns:
            List of BalanceSheet objects
        """
        params = {
            "tickers": ticker,
            "timeframe": timeframe,
            "limit": limit
        }
        
        if fiscal_year:
            params["fiscal_year"] = fiscal_year
        if fiscal_quarter:
            params["fiscal_quarter"] = fiscal_quarter
        
        endpoint = "/stocks/financials/v1/balance-sheets"
        data = self._make_request(endpoint, params)
        
        if not data or "results" not in data:
            return []
        
        balance_sheets = []
        for result in data["results"]:
            try:
                bs = BalanceSheet(
                    ticker=result.get("tickers", [ticker])[0],
                    cik=result.get("cik", ""),
                    period_end=result.get("period_end", ""),
                    filing_date=result.get("filing_date", ""),
                    fiscal_quarter=result.get("fiscal_quarter", 0),
                    fiscal_year=result.get("fiscal_year", 0),
                    timeframe=result.get("timeframe", timeframe),
                    cash_and_equivalents=result.get("cash_and_equivalents"),
                    short_term_investments=result.get("short_term_investments"),
                    receivables=result.get("receivables"),
                    inventories=result.get("inventories"),
                    other_current_assets=result.get("other_current_assets"),
                    total_current_assets=result.get("total_current_assets"),
                    property_plant_equipment_net=result.get("property_plant_equipment_net"),
                    other_assets=result.get("other_assets"),
                    total_assets=result.get("total_assets"),
                    accounts_payable=result.get("accounts_payable"),
                    deferred_revenue_current=result.get("deferred_revenue_current"),
                    debt_current=result.get("debt_current"),
                    accrued_and_other_current_liabilities=result.get("accrued_and_other_current_liabilities"),
                    total_current_liabilities=result.get("total_current_liabilities"),
                    long_term_debt_and_capital_lease_obligations=result.get("long_term_debt_and_capital_lease_obligations"),
                    other_noncurrent_liabilities=result.get("other_noncurrent_liabilities"),
                    total_liabilities=result.get("total_liabilities"),
                    common_stock=result.get("common_stock"),
                    accumulated_other_comprehensive_income=result.get("accumulated_other_comprehensive_income"),
                    retained_earnings_deficit=result.get("retained_earnings_deficit"),
                    other_equity=result.get("other_equity"),
                    total_equity_attributable_to_parent=result.get("total_equity_attributable_to_parent"),
                    total_equity=result.get("total_equity"),
                    total_liabilities_and_equity=result.get("total_liabilities_and_equity")
                )
                balance_sheets.append(bs)
            except Exception as e:
                logger.error(f"Error parsing balance sheet data: {str(e)}")
        
        return balance_sheets
    
    def get_cash_flow_statements(
        self,
        ticker: str,
        fiscal_year: Optional[int] = None,
        fiscal_quarter: Optional[int] = None,
        timeframe: str = "quarterly",
        limit: int = 10
    ) -> List[CashFlowStatement]:
        """
        Get cash flow statement data for a ticker
        
        Args:
            ticker: Stock ticker symbol
            fiscal_year: Filter by fiscal year
            fiscal_quarter: Filter by quarter (1-4)
            timeframe: "quarterly", "annual", or "trailing_twelve_months"
            limit: Number of results to return
        
        Returns:
            List of CashFlowStatement objects
        """
        params = {
            "tickers": ticker,
            "timeframe": timeframe,
            "limit": limit
        }
        
        if fiscal_year:
            params["fiscal_year"] = fiscal_year
        if fiscal_quarter:
            params["fiscal_quarter"] = fiscal_quarter
        
        endpoint = "/stocks/financials/v1/cash-flow-statements"
        data = self._make_request(endpoint, params)
        
        if not data or "results" not in data:
            return []
        
        cash_flows = []
        for result in data["results"]:
            try:
                cf = CashFlowStatement(
                    ticker=result.get("tickers", [ticker])[0],
                    cik=result.get("cik", ""),
                    period_end=result.get("period_end", ""),
                    filing_date=result.get("filing_date", ""),
                    fiscal_quarter=result.get("fiscal_quarter", 0),
                    fiscal_year=result.get("fiscal_year", 0),
                    timeframe=result.get("timeframe", timeframe),
                    net_income=result.get("net_income"),
                    depreciation_depletion_and_amortization=result.get("depreciation_depletion_and_amortization"),
                    other_operating_activities=result.get("other_operating_activities"),
                    change_in_other_operating_assets_and_liabilities_net=result.get("change_in_other_operating_assets_and_liabilities_net"),
                    cash_from_operating_activities_continuing_operations=result.get("cash_from_operating_activities_continuing_operations"),
                    net_cash_from_operating_activities=result.get("net_cash_from_operating_activities"),
                    purchase_of_property_plant_and_equipment=result.get("purchase_of_property_plant_and_equipment"),
                    other_investing_activities=result.get("other_investing_activities"),
                    net_cash_from_investing_activities_continuing_operations=result.get("net_cash_from_investing_activities_continuing_operations"),
                    net_cash_from_investing_activities=result.get("net_cash_from_investing_activities"),
                    short_term_debt_issuances_repayments=result.get("short_term_debt_issuances_repayments"),
                    long_term_debt_issuances_repayments=result.get("long_term_debt_issuances_repayments"),
                    dividends=result.get("dividends"),
                    other_financing_activities=result.get("other_financing_activities"),
                    net_cash_from_financing_activities_continuing_operations=result.get("net_cash_from_financing_activities_continuing_operations"),
                    net_cash_from_financing_activities=result.get("net_cash_from_financing_activities"),
                    change_in_cash_and_equivalents=result.get("change_in_cash_and_equivalents")
                )
                cash_flows.append(cf)
            except Exception as e:
                logger.error(f"Error parsing cash flow data: {str(e)}")
        
        return cash_flows
    
    def get_income_statements(
        self,
        ticker: str,
        fiscal_year: Optional[int] = None,
        fiscal_quarter: Optional[int] = None,
        timeframe: str = "quarterly",
        limit: int = 10
    ) -> List[IncomeStatement]:
        """
        Get income statement data for a ticker
        
        Args:
            ticker: Stock ticker symbol
            fiscal_year: Filter by fiscal year
            fiscal_quarter: Filter by quarter (1-4)
            timeframe: "quarterly", "annual", or "trailing_twelve_months"
            limit: Number of results to return
        
        Returns:
            List of IncomeStatement objects
        """
        params = {
            "tickers": ticker,
            "timeframe": timeframe,
            "limit": limit
        }
        
        if fiscal_year:
            params["fiscal_year"] = fiscal_year
        if fiscal_quarter:
            params["fiscal_quarter"] = fiscal_quarter
        
        endpoint = "/stocks/financials/v1/income-statements"
        data = self._make_request(endpoint, params)
        
        if not data or "results" not in data:
            return []
        
        income_statements = []
        for result in data["results"]:
            try:
                inc = IncomeStatement(
                    ticker=result.get("tickers", [ticker])[0],
                    cik=result.get("cik", ""),
                    period_end=result.get("period_end", ""),
                    filing_date=result.get("filing_date", ""),
                    fiscal_quarter=result.get("fiscal_quarter", 0),
                    fiscal_year=result.get("fiscal_year", 0),
                    timeframe=result.get("timeframe", timeframe),
                    revenue=result.get("revenue"),
                    cost_of_revenue=result.get("cost_of_revenue"),
                    gross_profit=result.get("gross_profit"),
                    selling_general_administrative=result.get("selling_general_administrative"),
                    research_development=result.get("research_development"),
                    other_operating_expenses=result.get("other_operating_expenses"),
                    total_operating_expenses=result.get("total_operating_expenses"),
                    operating_income=result.get("operating_income"),
                    other_income_expense=result.get("other_income_expense"),
                    total_other_income_expense=result.get("total_other_income_expense"),
                    income_before_income_taxes=result.get("income_before_income_taxes"),
                    income_taxes=result.get("income_taxes"),
                    consolidated_net_income_loss=result.get("consolidated_net_income_loss"),
                    net_income_loss_attributable_common_shareholders=result.get("net_income_loss_attributable_common_shareholders"),
                    basic_earnings_per_share=result.get("basic_earnings_per_share"),
                    diluted_earnings_per_share=result.get("diluted_earnings_per_share"),
                    basic_shares_outstanding=result.get("basic_shares_outstanding"),
                    diluted_shares_outstanding=result.get("diluted_shares_outstanding"),
                    ebitda=result.get("ebitda")
                )
                income_statements.append(inc)
            except Exception as e:
                logger.error(f"Error parsing income statement data: {str(e)}")
        
        return income_statements
    
    def get_ratios(
        self,
        ticker: str,
        limit: int = 1
    ) -> List[FinancialRatios]:
        """
        Get daily financial ratios for a ticker
        These are computed from TTM income/cash flow, latest quarter balance sheet,
        and latest daily price/shares
        
        Args:
            ticker: Stock ticker symbol
            limit: Number of results to return (default 1 for latest)
        
        Returns:
            List of FinancialRatios objects
        """
        params = {
            "ticker": ticker,
            "limit": limit
        }
        
        endpoint = "/stocks/financials/v1/ratios"
        data = self._make_request(endpoint, params)
        
        if not data or "results" not in data:
            return []
        
        ratios_list = []
        for result in data["results"]:
            try:
                ratios = FinancialRatios(
                    ticker=result.get("ticker", ticker),
                    cik=result.get("cik", ""),
                    date=result.get("date", ""),
                    price=result.get("price"),
                    average_volume=result.get("average_volume"),
                    market_cap=result.get("market_cap"),
                    earnings_per_share=result.get("earnings_per_share"),
                    price_to_earnings=result.get("price_to_earnings"),
                    price_to_book=result.get("price_to_book"),
                    price_to_sales=result.get("price_to_sales"),
                    price_to_cash_flow=result.get("price_to_cash_flow"),
                    price_to_free_cash_flow=result.get("price_to_free_cash_flow"),
                    dividend_yield=result.get("dividend_yield"),
                    return_on_assets=result.get("return_on_assets"),
                    return_on_equity=result.get("return_on_equity"),
                    debt_to_equity=result.get("debt_to_equity"),
                    current=result.get("current"),
                    quick=result.get("quick"),
                    cash=result.get("cash"),
                    ev_to_sales=result.get("ev_to_sales"),
                    ev_to_ebitda=result.get("ev_to_ebitda"),
                    enterprise_value=result.get("enterprise_value"),
                    free_cash_flow=result.get("free_cash_flow")
                )
                ratios_list.append(ratios)
            except Exception as e:
                logger.error(f"Error parsing ratios data: {str(e)}")
        
        return ratios_list
    
    def get_comprehensive_financials(self, ticker: str) -> Dict[str, Any]:
        """
        Get comprehensive financial data for a ticker including all statements and ratios
        
        Args:
            ticker: Stock ticker symbol
        
        Returns:
            Dictionary with all financial data
        """
        return {
            "ticker": ticker,
            "ratios": self.get_ratios(ticker, limit=1),
            "income_statement_ttm": self.get_income_statements(ticker, timeframe="trailing_twelve_months", limit=1),
            "income_statement_quarterly": self.get_income_statements(ticker, timeframe="quarterly", limit=4),
            "cash_flow_ttm": self.get_cash_flow_statements(ticker, timeframe="trailing_twelve_months", limit=1),
            "cash_flow_quarterly": self.get_cash_flow_statements(ticker, timeframe="quarterly", limit=4),
            "balance_sheet_quarterly": self.get_balance_sheets(ticker, timeframe="quarterly", limit=4),
            "balance_sheet_annual": self.get_balance_sheets(ticker, timeframe="annual", limit=3)
        }


if __name__ == "__main__":
    # Demo usage
    logging.basicConfig(level=logging.INFO)
    
    client = PolygonFinancialsClient()
    
    # Example: Get AAPL ratios
    print("\n=== AAPL Financial Ratios ===")
    ratios = client.get_ratios("AAPL")
    if ratios:
        r = ratios[0]
        print(f"Ticker: {r.ticker}")
        print(f"Date: {r.date}")
        print(f"Price: ${r.price:.2f}")
        print(f"P/E Ratio: {r.price_to_earnings:.2f}")
        print(f"P/B Ratio: {r.price_to_book:.2f}")
        print(f"ROE: {r.return_on_equity*100:.2f}%")
        print(f"Debt/Equity: {r.debt_to_equity:.2f}")
        print(f"Current Ratio: {r.current:.2f}")
    
    # Example: Get income statement
    print("\n=== AAPL Income Statement (TTM) ===")
    income_statements = client.get_income_statements("AAPL", timeframe="trailing_twelve_months", limit=1)
    if income_statements:
        inc = income_statements[0]
        print(f"Period End: {inc.period_end}")
        print(f"Revenue: ${inc.revenue:,.0f}")
        print(f"Gross Profit: ${inc.gross_profit:,.0f}")
        print(f"Operating Income: ${inc.operating_income:,.0f}")
        print(f"Net Income: ${inc.net_income_loss_attributable_common_shareholders:,.0f}")
        print(f"EPS: ${inc.diluted_earnings_per_share:.2f}")

