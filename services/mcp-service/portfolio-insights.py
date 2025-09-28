"""
MCP Service Integration for Portfolio Insights
Advanced portfolio analysis and insights using Model Context Protocol
"""
import asyncio
import logging
import json
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, date, timedelta
from dataclasses import dataclass, asdict
import aiohttp

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logger = logging.getLogger(__name__)

@dataclass
class PortfolioInsight:
    """Portfolio insight data structure"""
    insight_id: str
    portfolio_id: str
    insight_type: str
    title: str
    description: str
    severity: str  # low, medium, high, critical
    confidence: float
    actionable: bool
    recommendation: Optional[str]
    data: Dict[str, Any]
    created_at: datetime
    expires_at: Optional[datetime]

@dataclass
class PortfolioAnalysis:
    """Comprehensive portfolio analysis"""
    portfolio_id: str
    analysis_date: datetime
    overall_health: str
    risk_score: float
    performance_score: float
    optimization_score: float
    insights: List[PortfolioInsight]
    recommendations: List[str]
    alerts: List[str]

class PortfolioInsightsMCP:
    """MCP service for portfolio insights and analysis"""
    
    def __init__(self, portfolio_api_url: str = "http://localhost:11180", 
                 risk_api_url: str = "http://localhost:11181"):
        self.portfolio_api_url = portfolio_api_url
        self.risk_api_url = risk_api_url
        self.session: Optional[aiohttp.ClientSession] = None
        self.mcp_client: Optional[ClientSession] = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
        if self.mcp_client:
            await self.mcp_client.close()
    
    async def initialize_mcp_client(self):
        """Initialize MCP client connection"""
        try:
            # Connect to MCP server
            server_params = StdioServerParameters(
                command="python",
                args=["-m", "mcp.server.portfolio_insights"]
            )
            
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    self.mcp_client = session
                    
                    # Initialize the session
                    await session.initialize()
                    
                    logger.info("MCP client initialized successfully")
                    
        except Exception as e:
            logger.error(f"Error initializing MCP client: {e}")
            raise
    
    async def analyze_portfolio(self, portfolio_id: str) -> PortfolioAnalysis:
        """Perform comprehensive portfolio analysis"""
        try:
            # Get portfolio data
            portfolio_data = await self._get_portfolio_data(portfolio_id)
            if not portfolio_data:
                raise ValueError(f"Portfolio {portfolio_id} not found")
            
            # Get risk metrics
            risk_metrics = await self._get_risk_metrics(portfolio_id)
            
            # Get optimization results
            optimization_results = await self._get_optimization_results(portfolio_id)
            
            # Perform analysis using MCP
            analysis = await self._perform_mcp_analysis(
                portfolio_data, risk_metrics, optimization_results
            )
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing portfolio {portfolio_id}: {e}")
            raise
    
    async def _get_portfolio_data(self, portfolio_id: str) -> Optional[Dict[str, Any]]:
        """Get portfolio data from API"""
        try:
            async with self.session.get(
                f"{self.portfolio_api_url}/api/v1/portfolios/{portfolio_id}"
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Error fetching portfolio data: HTTP {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Error fetching portfolio data: {e}")
            return None
    
    async def _get_risk_metrics(self, portfolio_id: str) -> Optional[Dict[str, Any]]:
        """Get risk metrics from API"""
        try:
            async with self.session.get(
                f"{self.risk_api_url}/api/v1/risk/metrics/{portfolio_id}"
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Error fetching risk metrics: HTTP {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Error fetching risk metrics: {e}")
            return None
    
    async def _get_optimization_results(self, portfolio_id: str) -> Optional[Dict[str, Any]]:
        """Get optimization results from API"""
        try:
            async with self.session.get(
                f"{self.portfolio_api_url}/api/v1/optimization/results/{portfolio_id}"
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Error fetching optimization results: HTTP {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Error fetching optimization results: {e}")
            return None
    
    async def _perform_mcp_analysis(self, portfolio_data: Dict[str, Any], 
                                  risk_metrics: Optional[Dict[str, Any]], 
                                  optimization_results: Optional[Dict[str, Any]]) -> PortfolioAnalysis:
        """Perform analysis using MCP"""
        try:
            # Prepare analysis context
            analysis_context = {
                "portfolio": portfolio_data,
                "risk_metrics": risk_metrics,
                "optimization_results": optimization_results,
                "analysis_date": datetime.now().isoformat()
            }
            
            # Use MCP to analyze the portfolio
            if self.mcp_client:
                # Call MCP analysis function
                result = await self.mcp_client.call_tool(
                    "analyze_portfolio",
                    arguments=analysis_context
                )
                
                # Parse MCP response
                analysis_data = json.loads(result.content[0].text)
                
                # Create PortfolioAnalysis object
                analysis = PortfolioAnalysis(
                    portfolio_id=portfolio_data.get("portfolio_id", ""),
                    analysis_date=datetime.now(),
                    overall_health=analysis_data.get("overall_health", "unknown"),
                    risk_score=analysis_data.get("risk_score", 0.0),
                    performance_score=analysis_data.get("performance_score", 0.0),
                    optimization_score=analysis_data.get("optimization_score", 0.0),
                    insights=self._parse_insights(analysis_data.get("insights", [])),
                    recommendations=analysis_data.get("recommendations", []),
                    alerts=analysis_data.get("alerts", [])
                )
                
                return analysis
            else:
                # Fallback to local analysis if MCP is not available
                return await self._perform_local_analysis(portfolio_data, risk_metrics, optimization_results)
                
        except Exception as e:
            logger.error(f"Error performing MCP analysis: {e}")
            # Fallback to local analysis
            return await self._perform_local_analysis(portfolio_data, risk_metrics, optimization_results)
    
    def _parse_insights(self, insights_data: List[Dict[str, Any]]) -> List[PortfolioInsight]:
        """Parse insights from MCP response"""
        insights = []
        
        for insight_data in insights_data:
            insight = PortfolioInsight(
                insight_id=insight_data.get("insight_id", ""),
                portfolio_id=insight_data.get("portfolio_id", ""),
                insight_type=insight_data.get("insight_type", ""),
                title=insight_data.get("title", ""),
                description=insight_data.get("description", ""),
                severity=insight_data.get("severity", "low"),
                confidence=insight_data.get("confidence", 0.0),
                actionable=insight_data.get("actionable", False),
                recommendation=insight_data.get("recommendation"),
                data=insight_data.get("data", {}),
                created_at=datetime.fromisoformat(insight_data.get("created_at", datetime.now().isoformat())),
                expires_at=datetime.fromisoformat(insight_data.get("expires_at")) if insight_data.get("expires_at") else None
            )
            insights.append(insight)
        
        return insights
    
    async def _perform_local_analysis(self, portfolio_data: Dict[str, Any], 
                                    risk_metrics: Optional[Dict[str, Any]], 
                                    optimization_results: Optional[Dict[str, Any]]) -> PortfolioAnalysis:
        """Perform local analysis without MCP"""
        try:
            # Basic analysis logic
            insights = []
            recommendations = []
            alerts = []
            
            # Analyze portfolio composition
            positions = portfolio_data.get("positions", [])
            if len(positions) < 5:
                insights.append(PortfolioInsight(
                    insight_id="diversification_low",
                    portfolio_id=portfolio_data.get("portfolio_id", ""),
                    insight_type="diversification",
                    title="Low Diversification",
                    description=f"Portfolio has only {len(positions)} positions, consider diversifying",
                    severity="medium",
                    confidence=0.8,
                    actionable=True,
                    recommendation="Add more positions to improve diversification",
                    data={"position_count": len(positions)},
                    created_at=datetime.now(),
                    expires_at=None
                ))
            
            # Analyze risk metrics
            if risk_metrics:
                var_95 = abs(risk_metrics.get("var_95", 0))
                if var_95 > 0.05:  # 5% VaR
                    insights.append(PortfolioInsight(
                        insight_id="high_var",
                        portfolio_id=portfolio_data.get("portfolio_id", ""),
                        insight_type="risk",
                        title="High Value at Risk",
                        description=f"VaR 95% is {var_95:.2%}, which is above recommended 5%",
                        severity="high",
                        confidence=0.9,
                        actionable=True,
                        recommendation="Consider reducing portfolio risk",
                        data={"var_95": var_95},
                        created_at=datetime.now(),
                        expires_at=None
                    ))
            
            # Analyze optimization results
            if optimization_results:
                sharpe_ratio = optimization_results.get("sharpe_ratio", 0)
                if sharpe_ratio < 1.0:
                    insights.append(PortfolioInsight(
                        insight_id="low_sharpe",
                        portfolio_id=portfolio_data.get("portfolio_id", ""),
                        insight_type="performance",
                        title="Low Sharpe Ratio",
                        description=f"Sharpe ratio is {sharpe_ratio:.2f}, consider optimization",
                        severity="medium",
                        confidence=0.7,
                        actionable=True,
                        recommendation="Run portfolio optimization to improve risk-adjusted returns",
                        data={"sharpe_ratio": sharpe_ratio},
                        created_at=datetime.now(),
                        expires_at=None
                    ))
            
            # Calculate overall scores
            risk_score = self._calculate_risk_score(risk_metrics)
            performance_score = self._calculate_performance_score(portfolio_data, optimization_results)
            optimization_score = self._calculate_optimization_score(optimization_results)
            
            # Determine overall health
            overall_health = self._determine_overall_health(risk_score, performance_score, optimization_score)
            
            return PortfolioAnalysis(
                portfolio_id=portfolio_data.get("portfolio_id", ""),
                analysis_date=datetime.now(),
                overall_health=overall_health,
                risk_score=risk_score,
                performance_score=performance_score,
                optimization_score=optimization_score,
                insights=insights,
                recommendations=recommendations,
                alerts=alerts
            )
            
        except Exception as e:
            logger.error(f"Error performing local analysis: {e}")
            raise
    
    def _calculate_risk_score(self, risk_metrics: Optional[Dict[str, Any]]) -> float:
        """Calculate risk score (0-1, lower is better)"""
        if not risk_metrics:
            return 0.5  # Default moderate risk
        
        try:
            var_95 = abs(risk_metrics.get("var_95", 0))
            volatility = risk_metrics.get("portfolio_volatility", 0)
            max_drawdown = risk_metrics.get("max_drawdown", 0)
            
            # Normalize risk metrics to 0-1 scale
            var_score = min(var_95 / 0.1, 1.0)  # 10% VaR = max score
            vol_score = min(volatility / 0.3, 1.0)  # 30% volatility = max score
            dd_score = min(max_drawdown / 0.2, 1.0)  # 20% drawdown = max score
            
            # Weighted average
            risk_score = (var_score * 0.4 + vol_score * 0.4 + dd_score * 0.2)
            return min(max(risk_score, 0.0), 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating risk score: {e}")
            return 0.5
    
    def _calculate_performance_score(self, portfolio_data: Dict[str, Any], 
                                   optimization_results: Optional[Dict[str, Any]]) -> float:
        """Calculate performance score (0-1, higher is better)"""
        try:
            if not optimization_results:
                return 0.5  # Default moderate performance
            
            sharpe_ratio = optimization_results.get("sharpe_ratio", 0)
            total_return = optimization_results.get("total_return", 0)
            
            # Normalize performance metrics
            sharpe_score = min(max(sharpe_ratio / 2.0, 0.0), 1.0)  # 2.0 Sharpe = max score
            return_score = min(max(total_return / 0.2, 0.0), 1.0)  # 20% return = max score
            
            # Weighted average
            performance_score = (sharpe_score * 0.6 + return_score * 0.4)
            return min(max(performance_score, 0.0), 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating performance score: {e}")
            return 0.5
    
    def _calculate_optimization_score(self, optimization_results: Optional[Dict[str, Any]]) -> float:
        """Calculate optimization score (0-1, higher is better)"""
        if not optimization_results:
            return 0.5  # Default moderate optimization
        
        try:
            convergence_achieved = optimization_results.get("convergence_achieved", False)
            iterations = optimization_results.get("iterations", 0)
            
            # Base score on convergence
            base_score = 1.0 if convergence_achieved else 0.3
            
            # Adjust for iteration efficiency
            if iterations > 0:
                efficiency = min(1000 / iterations, 1.0)  # Fewer iterations = better
                base_score *= efficiency
            
            return min(max(base_score, 0.0), 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating optimization score: {e}")
            return 0.5
    
    def _determine_overall_health(self, risk_score: float, performance_score: float, 
                                optimization_score: float) -> str:
        """Determine overall portfolio health"""
        try:
            # Weighted average of all scores
            overall_score = (risk_score * 0.4 + performance_score * 0.4 + optimization_score * 0.2)
            
            if overall_score >= 0.8:
                return "excellent"
            elif overall_score >= 0.6:
                return "good"
            elif overall_score >= 0.4:
                return "fair"
            else:
                return "poor"
                
        except Exception as e:
            logger.error(f"Error determining overall health: {e}")
            return "unknown"
    
    async def generate_insights_report(self, portfolio_id: str) -> Dict[str, Any]:
        """Generate comprehensive insights report"""
        try:
            # Perform analysis
            analysis = await self.analyze_portfolio(portfolio_id)
            
            # Generate report
            report = {
                "portfolio_id": portfolio_id,
                "analysis_date": analysis.analysis_date.isoformat(),
                "overall_health": analysis.overall_health,
                "scores": {
                    "risk_score": analysis.risk_score,
                    "performance_score": analysis.performance_score,
                    "optimization_score": analysis.optimization_score
                },
                "insights": [asdict(insight) for insight in analysis.insights],
                "recommendations": analysis.recommendations,
                "alerts": analysis.alerts,
                "summary": self._generate_summary(analysis)
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating insights report: {e}")
            raise
    
    def _generate_summary(self, analysis: PortfolioAnalysis) -> str:
        """Generate summary text for the analysis"""
        try:
            health = analysis.overall_health
            risk_score = analysis.risk_score
            performance_score = analysis.performance_score
            insight_count = len(analysis.insights)
            
            summary = f"Portfolio health: {health.title()}. "
            summary += f"Risk score: {risk_score:.2f}, Performance score: {performance_score:.2f}. "
            summary += f"Found {insight_count} insights and {len(analysis.recommendations)} recommendations."
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return "Analysis completed with some issues."

# Global MCP service instance
_portfolio_insights_mcp: Optional[PortfolioInsightsMCP] = None

def get_portfolio_insights_mcp() -> PortfolioInsightsMCP:
    """Get global portfolio insights MCP service"""
    global _portfolio_insights_mcp
    if _portfolio_insights_mcp is None:
        _portfolio_insights_mcp = PortfolioInsightsMCP()
    return _portfolio_insights_mcp

async def analyze_portfolio(portfolio_id: str) -> PortfolioAnalysis:
    """Analyze portfolio using MCP service"""
    async with PortfolioInsightsMCP() as mcp_service:
        return await mcp_service.analyze_portfolio(portfolio_id)

async def generate_insights_report(portfolio_id: str) -> Dict[str, Any]:
    """Generate insights report using MCP service"""
    async with PortfolioInsightsMCP() as mcp_service:
        return await mcp_service.generate_insights_report(portfolio_id)



