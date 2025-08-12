"""
Market Data Vectorizer Module

Handles vectorization of stock market data including:
- Price movements and trends
- Volume analysis
- Technical indicators
- Market sentiment analysis
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

class MarketDataVectorizer:
    """Vectorizes market data for RAG search and analysis."""
    
    def __init__(self, db_manager: DatabaseManager, vector_storage_url: str):
        self.db_manager = db_manager
        self.vector_storage_url = vector_storage_url
        
    async def vectorize_market_data(self, job: VectorizationJob) -> bool:
        """Vectorize market data for a specific symbol."""
        try:
            symbol = job.data.get('symbol')
            if not symbol:
                logger.error(f"No symbol provided in job {job.job_id}")
                return False
                
            logger.info(f"Vectorizing market data for {symbol}")
            
            # Get detailed market data
            market_data = await self._fetch_market_data(symbol)
            if not market_data:
                logger.warning(f"No market data found for {symbol}")
                return False
                
            # Generate comprehensive text content
            text_content = self._generate_market_data_text(symbol, market_data)
            
            # Send to vector storage
            success = await self._send_to_vector_storage(
                content=text_content,
                metadata={
                    "type": "market_data",
                    "symbol": symbol,
                    "data_period": "30_days",
                    "latest_date": market_data[0]['date'].isoformat(),
                    "data_points": len(market_data),
                    "source_service": "background_vectorization_service",
                    "job_id": job.job_id
                }
            )
            
            if success:
                # Mark as vectorized in database
                await self._mark_market_data_vectorized(symbol)
                logger.info(f"Successfully vectorized market data for {symbol}")
                return True
            else:
                logger.error(f"Failed to send market data to vector storage for {symbol}")
                return False
                
        except Exception as e:
            logger.error(f"Error vectorizing market data for {job.data.get('symbol', 'unknown')}: {e}")
            return False
            
    async def _fetch_market_data(self, symbol: str) -> List[Dict[str, Any]]:
        """Fetch market data from the database."""
        try:
            conn = await self.db_manager.get_connection()
            
            # Get recent market data with technical indicators
            # Use correct table name 'historical_prices' and column names
            query = """
            SELECT 
                date, open_price, high_price, low_price, close_price, volume,
                (close_price - open_price) as daily_change,
                ((close_price - open_price) / open_price * 100) as daily_change_pct
            FROM historical_prices
            WHERE symbol = $1
            AND date >= NOW() - INTERVAL '30 days'
            ORDER BY date DESC
            """
            
            rows = await conn.fetch(query, symbol)
            await conn.close()
            
            # Convert Decimal values to float to avoid arithmetic errors
            converted_rows = []
            for row in rows:
                row_dict = dict(row)
                # Convert Decimal fields to float
                for key in ['open_price', 'high_price', 'low_price', 'close_price', 'daily_change', 'daily_change_pct']:
                    if key in row_dict and row_dict[key] is not None:
                        row_dict[key] = float(row_dict[key])
                converted_rows.append(row_dict)
            
            return converted_rows
            
        except Exception as e:
            logger.error(f"Error fetching market data for {symbol}: {e}")
            return []
            
    def _generate_market_data_text(self, symbol: str, market_data: List[Dict[str, Any]]) -> str:
        """Generate comprehensive text content from market data."""
        if not market_data:
            return f"No market data available for {symbol}"
        
        latest = market_data[0]
        oldest = market_data[-1]
        
        # Basic price information
        text_content = f"""
{symbol} Stock Market Data Analysis (Last 30 Days)

Price Summary:
- Latest Close: ${latest['close_price']:.2f}
- Latest Date: {latest['date'].strftime('%Y-%m-%d')}
- Daily Range: ${latest['low_price']:.2f} - ${latest['high_price']:.2f}
- Volume: {latest['volume']:,}

Trend Analysis:
- Starting Price: ${oldest['close_price']:.2f}
- Ending Price: ${latest['close_price']:.2f}
- Overall Change: ${latest['close_price'] - oldest['close_price']:+.2f}
- Change Percentage: {((latest['close_price'] - oldest['close_price']) / oldest['close_price'] * 100):+.1f}%

Technical Analysis:
{self._analyze_trend(market_data)}

Volume Analysis:
{self._generate_volume_analysis(market_data)}

Recent Price Movements:
{self._generate_recent_movements(market_data[:5])}

Support and Resistance:
{self._find_support_resistance(market_data)}

Market Sentiment:
{self._generate_sentiment_analysis(market_data)}
"""
        
        return text_content
        
    def _analyze_trend(self, market_data: List[Dict[str, Any]]) -> str:
        """Analyze price trend from market data."""
        if len(market_data) < 5:
            return "Insufficient data for trend analysis"
        
        # Get recent vs older prices
        recent_prices = [row['close_price'] for row in market_data[:5]]
        older_prices = [row['close_price'] for row in market_data[-5:]]
        
        recent_avg = sum(recent_prices) / len(recent_prices)
        older_avg = sum(older_prices) / len(older_prices)
        
        if recent_avg > older_avg * 1.02:
            return "Strong upward momentum in recent sessions"
        elif recent_avg > older_avg * 1.005:
            return "Moderate upward trend developing"
        elif recent_avg < older_avg * 0.98:
            return "Downward pressure building"
        elif recent_avg < older_avg * 0.995:
            return "Slight downward drift"
        else:
            return "Sideways consolidation pattern"
            
    def _find_support_resistance(self, market_data: List[Dict[str, Any]]) -> Dict[str, float]:
        """Find support and resistance levels."""
        if len(market_data) < 10:
            return {"support": 0, "resistance": 0}
        
        prices = [row['close_price'] for row in market_data]
        
        # Simple support/resistance calculation
        support = min(prices) * 0.98  # 2% below lowest
        resistance = max(prices) * 1.02  # 2% above highest
        
        return {"support": support, "resistance": resistance}
        
    def _generate_recent_movements(self, recent_data: List[Dict[str, Any]]) -> str:
        """Generate description of recent price movements."""
        if len(recent_data) < 3:
            return "Insufficient data for recent movement analysis"
        
        movements = []
        for row in recent_data:
            date_str = row['date'].strftime('%m/%d')
            close_price = row['close_price']
            daily_change = row.get('daily_change', 0)
            daily_change_pct = row.get('daily_change_pct', 0)
            
            if daily_change > 0:
                direction = "↗️"
            elif daily_change < 0:
                direction = "↘️"
            else:
                direction = "→"
                
            movements.append(f"- {date_str}: ${close_price:.2f} {direction} {daily_change:+.2f} ({daily_change_pct:+.1f}%)")
        
        return "\n".join(movements)
        
    def _generate_volume_analysis(self, market_data: List[Dict[str, Any]]) -> str:
        """Generate volume analysis text."""
        if len(market_data) < 5:
            return "Insufficient data for volume analysis"
            
        volumes = [row['volume'] for row in market_data]
        avg_volume = sum(volumes) / len(volumes)
        max_volume = max(volumes)
        min_volume = min(volumes)
        
        # Find high volume days
        high_volume_days = [row for row in market_data if row['volume'] > avg_volume * 1.5]
        
        analysis = f"""
        - Average Volume: {avg_volume:,.0f} shares
        - Highest Volume: {max_volume:,.0f} shares
        - Lowest Volume: {min_volume:,.0f} shares
        - High Volume Days: {len(high_volume_days)} out of {len(market_data)} days
        """
        
        if high_volume_days:
            analysis += "\nHigh Volume Days:"
            for day in high_volume_days[:3]:  # Show top 3
                analysis += f"\n  - {day['date'].strftime('%m/%d')}: {day['volume']:,} shares"
                
        return analysis.strip()
        
    def _generate_sentiment_analysis(self, market_data: List[Dict[str, Any]]) -> str:
        """Generate market sentiment analysis."""
        if len(market_data) < 5:
            return "Insufficient data for sentiment analysis"
            
        # Count up vs down days
        up_days = sum(1 for row in market_data if row['daily_change'] > 0)
        down_days = sum(1 for row in market_data if row['daily_change'] < 0)
        flat_days = len(market_data) - up_days - down_days
        
        # Calculate average daily change
        daily_changes = [row['daily_change_pct'] for row in market_data]
        avg_daily_change = sum(daily_changes) / len(daily_changes)
        
        # Determine sentiment
        if up_days > down_days * 1.5 and avg_daily_change > 0.5:
            sentiment = "Bullish - Strong buying pressure"
        elif up_days > down_days and avg_daily_change > 0:
            sentiment = "Moderately bullish"
        elif down_days > up_days * 1.5 and avg_daily_change < -0.5:
            sentiment = "Bearish - Strong selling pressure"
        elif down_days > up_days and avg_daily_change < 0:
            sentiment = "Moderately bearish"
        else:
            sentiment = "Neutral - Mixed signals"
            
        return f"""
        - Up Days: {up_days} ({up_days/len(market_data)*100:.1f}%)
        - Down Days: {down_days} ({down_days/len(market_data)*100:.1f}%)
        - Flat Days: {flat_days} ({flat_days/len(market_data)*100:.1f}%)
        - Average Daily Change: {avg_daily_change:+.2f}%
        - Overall Sentiment: {sentiment}
        """.strip()
        
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
            
    async def _mark_market_data_vectorized(self, symbol: str):
        """Mark market data as vectorized in the database."""
        try:
            conn = await self.db_manager.get_connection()
            query = """
            UPDATE market_data
            SET vectorized = true, vectorized_at = NOW()
            WHERE symbol = $1 AND date >= NOW() - INTERVAL '30 days'
            """
            await conn.execute(query, symbol)
            await conn.close()
        except Exception as e:
            logger.error(f"Error marking market data as vectorized: {e}")
            
    async def batch_vectorize_market_data(self, symbols: List[str]) -> Dict[str, bool]:
        """Vectorize market data for multiple symbols in parallel."""
        logger.info(f"Starting batch vectorization for {len(symbols)} symbols")
        
        # Create jobs for each symbol
        jobs = []
        for symbol in symbols:
            job = VectorizationJob(
                job_id=f"market_data_{symbol}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                data_type="market_data",
                symbol=symbol,
                data={"symbol": symbol},
                priority=1
            )
            jobs.append(job)
            
        # Process jobs in parallel with limited concurrency
        semaphore = asyncio.Semaphore(5)  # Limit to 5 concurrent vectorizations
        
        async def process_job(job):
            async with semaphore:
                return await self.vectorize_market_data(job)
                
        # Execute all jobs
        tasks = [process_job(job) for job in jobs]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        success_count = 0
        failure_count = 0
        results_dict = {}
        
        for i, result in enumerate(results):
            symbol = symbols[i]
            if isinstance(result, Exception):
                logger.error(f"Exception vectorizing {symbol}: {result}")
                results_dict[symbol] = False
                failure_count += 1
            else:
                results_dict[symbol] = result
                if result:
                    success_count += 1
                else:
                    failure_count += 1
                    
        logger.info(f"Batch vectorization completed: {success_count} success, {failure_count} failure")
        return results_dict
