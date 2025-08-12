"""
Earnings Vectorizer Module

Handles vectorization of earnings reports including:
- Financial performance analysis
- Earnings vs expectations
- Revenue growth analysis
- Forward-looking insights
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import asyncpg
import aiohttp

from database.models import VectorizationJob, VectorizationStatus
from database.manager import DatabaseManager

logger = logging.getLogger(__name__)

class EarningsVectorizer:
    """Vectorizes earnings reports for RAG search and analysis."""
    
    def __init__(self, db_manager: DatabaseManager, vector_storage_url: str):
        self.db_manager = db_manager
        self.vector_storage_url = vector_storage_url
        
    async def vectorize_earnings_data(self, job: VectorizationJob) -> bool:
        """Vectorize earnings report data."""
        try:
            earnings_id = job.data.get('id')
            if not earnings_id:
                logger.error(f"No earnings ID provided in job {job.job_id}")
                return False
                
            # Fetch earnings report details
            earnings_data = await self._fetch_earnings_report(earnings_id)
            if not earnings_data:
                logger.warning(f"No earnings report found with ID {earnings_id}")
                return False
                
            symbol = earnings_data['symbol']
            quarter = earnings_data['quarter']
            year = earnings_data['year']
            
            logger.info(f"Vectorizing earnings data for {symbol} Q{quarter} {year}")
            
            # Generate comprehensive text content
            text_content = self._generate_earnings_text(earnings_data)
            
            # Send to vector storage
            success = await self._send_to_vector_storage(
                content=text_content,
                metadata={
                    "type": "earnings",
                    "earnings_id": earnings_id,
                    "symbol": symbol,
                    "quarter": quarter,
                    "year": year,
                    "report_date": earnings_data['report_date'].isoformat(),
                    "eps": float(earnings_data['eps']) if earnings_data['eps'] else None,
                    "revenue": float(earnings_data['revenue']) if earnings_data['revenue'] else None,
                    "source_service": "background_vectorization_service",
                    "job_id": job.job_id
                }
            )
            
            if success:
                # Mark as vectorized in database
                await self._mark_earnings_vectorized(earnings_id)
                logger.info(f"Successfully vectorized earnings data for {symbol} Q{quarter} {year}")
                return True
            else:
                logger.error(f"Failed to send earnings data to vector storage for {symbol}")
                return False
                
        except Exception as e:
            logger.error(f"Error vectorizing earnings data for {job.data.get('symbol', 'unknown')}: {e}")
            return False
            
    async def _fetch_earnings_report(self, earnings_id: int) -> Optional[Dict[str, Any]]:
        """Fetch earnings report from the database."""
        try:
            conn = await self.db_manager.get_connection()
            
            query = """
            SELECT 
                id, symbol, quarter, year, eps, revenue, report_date,
                eps_estimate, revenue_estimate, eps_surprise, revenue_surprise,
                guidance, conference_call_date, notes
            FROM earnings_reports
            WHERE id = $1
            """
            
            row = await conn.fetchrow(query, earnings_id)
            await conn.close()
            
            if row:
                return dict(row)
            return None
            
        except Exception as e:
            logger.error(f"Error fetching earnings report {earnings_id}: {e}")
            return None
            
    def _generate_earnings_text(self, earnings_data: Dict[str, Any]) -> str:
        """Generate comprehensive text content for earnings report."""
        symbol = earnings_data['symbol']
        quarter = earnings_data['quarter']
        year = earnings_data['year']
        eps = earnings_data['eps']
        revenue = earnings_data['revenue']
        report_date = earnings_data['report_date']
        
        # Get estimates and surprises
        eps_estimate = earnings_data.get('eps_estimate')
        revenue_estimate = earnings_data.get('revenue_estimate')
        eps_surprise = earnings_data.get('eps_surprise')
        revenue_surprise = earnings_data.get('revenue_surprise')
        
        # Additional data
        guidance = earnings_data.get('guidance', '')
        conference_call_date = earnings_data.get('conference_call_date')
        notes = earnings_data.get('notes', '')
        
        # Convert Decimal values to float for safe formatting
        eps_float = float(eps) if eps is not None else 0.0
        revenue_float = float(revenue) if revenue is not None else 0.0
        eps_estimate_float = float(eps_estimate) if eps_estimate is not None else None
        revenue_estimate_float = float(revenue_estimate) if revenue_estimate is not None else None
        eps_surprise_float = float(eps_surprise) if eps_surprise is not None else None
        revenue_surprise_float = float(revenue_surprise) if revenue_surprise is not None else None
        
        # Generate analysis
        eps_analysis = self._analyze_eps_performance(eps_float, eps_estimate_float, eps_surprise_float)
        revenue_analysis = self._analyze_revenue_performance(revenue_float, revenue_estimate_float, revenue_surprise_float)
        overall_performance = self._assess_overall_performance(eps_float, revenue_float, eps_estimate_float, revenue_estimate_float)
        
        text_content = f"""
        Earnings Report: {symbol} Q{quarter} {year}
        
        Report Date: {report_date.strftime('%Y-%m-%d')}
        Conference Call: {conference_call_date.strftime('%Y-%m-%d') if conference_call_date else 'Not scheduled'}
        
        Financial Results:
        - EPS: ${eps_float:.2f}
        - Revenue: ${revenue_float:,.0f}
        
        Performance Analysis:
        {eps_analysis}
        
        {revenue_analysis}
        
        Overall Assessment:
        {overall_performance}
        
        Forward Guidance:
        {guidance if guidance else 'No specific guidance provided'}
        
        Additional Notes:
        {notes if notes else 'No additional notes'}
        
        Key Insights:
        {self._generate_key_insights(eps_float, revenue_float, quarter, year)}
        
        Historical Context:
        {self._generate_historical_context(earnings_data)}
        
        Market Impact:
        {self._assess_market_impact(eps_float, eps_estimate_float)}
        """
        
        return text_content.strip()
        
    def _analyze_eps_performance(self, eps: float, eps_estimate: Optional[float], eps_surprise: Optional[float]) -> str:
        """Analyze EPS performance vs estimates."""
        if eps_estimate is None:
            return f"EPS: ${eps:.2f} (No estimate available for comparison)"
            
        if eps_surprise is not None:
            surprise_pct = (eps_surprise / eps_estimate) * 100
            if surprise_pct > 0:
                return f"EPS: ${eps:.2f} vs ${eps_estimate:.2f} estimate (+${eps_surprise:.2f}, +{surprise_pct:.1f}% beat)"
            else:
                return f"EPS: ${eps:.2f} vs ${eps_estimate:.2f} estimate ({eps_surprise:.2f}, {surprise_pct:.1f}% miss)"
        else:
            difference = eps - eps_estimate
            difference_pct = (difference / eps_estimate) * 100
            if difference > 0:
                return f"EPS: ${eps:.2f} vs ${eps_estimate:.2f} estimate (+${difference:.2f}, +{difference_pct:.1f}% beat)"
            else:
                return f"EPS: ${eps:.2f} vs ${eps_estimate:.2f} estimate ({difference:.2f}, {difference_pct:.1f}% miss)"
                
    def _analyze_revenue_performance(self, revenue: float, revenue_estimate: Optional[float], revenue_surprise: Optional[float]) -> str:
        """Analyze revenue performance vs estimates."""
        if revenue_estimate is None:
            return f"Revenue: ${revenue:,.0f} (No estimate available for comparison)"
            
        if revenue_surprise is not None:
            surprise_pct = (revenue_surprise / revenue_estimate) * 100
            if surprise_pct > 0:
                return f"Revenue: ${revenue:,.0f} vs ${revenue_estimate:,.0f} estimate (+${revenue_surprise:,.0f}, +{surprise_pct:.1f}% beat)"
            else:
                return f"Revenue: ${revenue:,.0f} vs ${revenue_estimate:,.0f} estimate ({revenue_surprise:,.0f}, {surprise_pct:.1f}% miss)"
        else:
            difference = revenue - revenue_estimate
            difference_pct = (difference / revenue_estimate) * 100
            if difference > 0:
                return f"Revenue: ${revenue:,.0f} vs ${revenue_estimate:,.0f} estimate (+${difference:,.0f}, +{difference_pct:.1f}% beat)"
            else:
                return f"Revenue: ${revenue:,.0f} vs ${revenue_estimate:,.0f} estimate ({difference:,.0f}, {difference_pct:.1f}% miss)"
                
    def _assess_overall_performance(self, eps: float, revenue: float, eps_estimate: Optional[float], revenue_estimate: Optional[float]) -> str:
        """Assess overall earnings performance."""
        if eps_estimate is None or revenue_estimate is None:
            return "Performance assessment limited due to missing estimates"
            
        eps_beat = eps > eps_estimate
        revenue_beat = revenue > revenue_estimate
        
        if eps_beat and revenue_beat:
            return "Strong performance - Beat both EPS and revenue estimates"
        elif eps_beat and not revenue_beat:
            return "Mixed performance - Beat EPS estimates but missed revenue"
        elif not eps_beat and revenue_beat:
            return "Mixed performance - Beat revenue estimates but missed EPS"
        else:
            return "Weak performance - Missed both EPS and revenue estimates"
            
    def _generate_key_insights(self, eps: float, revenue: float, quarter: int, year: int) -> str:
        """Generate key insights from earnings data."""
        insights = []
        
        # EPS insights
        if eps > 0:
            insights.append(f"Company reported positive earnings of ${eps:.2f} per share")
        else:
            insights.append(f"Company reported a loss of ${abs(eps):.2f} per share")
            
        # Revenue insights
        insights.append(f"Total revenue reached ${revenue:,.0f}")
        
        # Seasonal insights
        if quarter == 4:
            insights.append("Q4 results typically include holiday season performance")
        elif quarter == 1:
            insights.append("Q1 results may reflect post-holiday season trends")
            
        # Year-over-year context
        insights.append(f"Results for {year} Q{quarter} period")
        
        return "\n".join(f"- {insight}" for insight in insights)
        
    def _generate_historical_context(self, earnings_data: Dict[str, Any]) -> str:
        """Generate historical context for earnings."""
        # This would ideally fetch historical data, but for now provide general context
        return """
        Historical Context:
        - Previous quarter performance provides baseline for comparison
        - Year-over-year trends show long-term growth trajectory
        - Seasonal patterns may influence quarterly results
        - Management execution vs. previous guidance
        """.strip()
        
    def _assess_market_impact(self, eps: float, eps_estimate: Optional[float]) -> str:
        """Assess potential market impact of earnings."""
        if eps_estimate is None:
            return "Market impact assessment limited due to missing estimates"
            
        eps_beat = eps > eps_estimate
        beat_magnitude = abs(eps - eps_estimate) / eps_estimate if eps_estimate != 0 else 0
        
        if eps_beat and beat_magnitude > 0.1:
            return "Significant positive market impact expected - Substantial EPS beat"
        elif eps_beat and beat_magnitude > 0.05:
            return "Positive market impact expected - Solid EPS beat"
        elif eps_beat:
            return "Moderate positive market impact - Small EPS beat"
        elif beat_magnitude > 0.1:
            return "Significant negative market impact expected - Substantial EPS miss"
        elif beat_magnitude > 0.05:
            return "Negative market impact expected - Notable EPS miss"
        else:
            return "Limited market impact expected - Close to estimates"
            
    async def _send_to_vector_storage(self, content: str, metadata: Dict[str, Any]) -> bool:
        """Send vectorized content to the vector storage service."""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "content": content,
                    "metadata": metadata,
                    "embedding_type": "text"
                }
                
                async with session.post(
                    f"{self.vector_storage_url}/api/vectorize/text",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"Successfully sent to vector storage: {result.get('id', 'unknown')}")
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(f"Vector storage error: {response.status} - {error_text}")
                        return False
                        
        except Exception as e:
            logger.error(f"Error sending to vector storage: {e}")
            return False
            
    async def _mark_earnings_vectorized(self, earnings_id: int):
        """Mark earnings report as vectorized in the database."""
        try:
            conn = await self.db_manager.get_connection()
            query = """
            UPDATE earnings_reports
            SET vectorized = true, vectorized_at = NOW()
            WHERE id = $1
            """
            await conn.execute(query, earnings_id)
            await conn.close()
        except Exception as e:
            logger.error(f"Error marking earnings as vectorized: {e}")
            
    async def batch_vectorize_earnings(self, earnings_ids: List[int]) -> Dict[int, bool]:
        """Vectorize multiple earnings reports in parallel."""
        logger.info(f"Starting batch vectorization for {len(earnings_ids)} earnings reports")
        
        # Create jobs for each earnings ID
        jobs = []
        for earnings_id in earnings_ids:
            job = VectorizationJob(
                job_id=f"earnings_{earnings_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                data_type="earnings",
                data={"id": earnings_id},
                priority=3
            )
            jobs.append(job)
            
        # Process jobs in parallel with limited concurrency
        semaphore = asyncio.Semaphore(3)  # Limit to 3 concurrent vectorizations
        
        async def process_job(job):
            async with semaphore:
                return await self.vectorize_earnings_data(job)
                
        # Execute all jobs
        tasks = [process_job(job) for job in jobs]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        success_count = 0
        failure_count = 0
        results_dict = {}
        
        for i, result in enumerate(results):
            earnings_id = earnings_ids[i]
            if isinstance(result, Exception):
                logger.error(f"Exception vectorizing earnings {earnings_id}: {result}")
                results_dict[earnings_id] = False
                failure_count += 1
            else:
                results_dict[earnings_id] = result
                if result:
                    success_count += 1
                else:
                    failure_count += 1
                    
        logger.info(f"Batch earnings vectorization completed: {success_count} success, {failure_count} failure")
        return results_dict
        
    async def get_unvectorized_earnings(self, limit: int = 50) -> List[int]:
        """Get list of earnings report IDs that haven't been vectorized."""
        try:
            conn = await self.db_manager.get_connection()
            
            query = """
            SELECT id
            FROM earnings_reports
            WHERE vectorized = false OR vectorized IS NULL
            AND report_date >= NOW() - INTERVAL '90 days'
            ORDER BY report_date DESC
            LIMIT $1
            """
            
            rows = await conn.fetch(query, limit)
            await conn.close()
            
            return [row['id'] for row in rows]
            
        except Exception as e:
            logger.error(f"Error fetching unvectorized earnings: {e}")
            return []
            
    async def get_earnings_by_symbol(self, symbol: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get earnings reports for a specific symbol."""
        try:
            conn = await self.db_manager.get_connection()
            
            query = """
            SELECT id, quarter, year, eps, revenue, report_date, vectorized
            FROM earnings_reports
            WHERE symbol = $1
            ORDER BY report_date DESC
            LIMIT $2
            """
            
            rows = await conn.fetch(query, symbol, limit)
            await conn.close()
            
            return [dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Error fetching earnings for {symbol}: {e}")
            return []
