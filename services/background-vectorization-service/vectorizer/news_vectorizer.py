"""
News Vectorizer Module

Handles vectorization of news articles including:
- Content analysis and summarization
- Sentiment analysis
- Key topic extraction
- Source credibility assessment
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import re
import asyncpg
import aiohttp

from database.models import VectorizationJob, VectorizationStatus
from database.manager import DatabaseManager

logger = logging.getLogger(__name__)

class NewsVectorizer:
    """Vectorizes news articles for RAG search and analysis."""
    
    def __init__(self, db_manager: DatabaseManager, vector_storage_url: str):
        self.db_manager = db_manager
        self.vector_storage_url = vector_storage_url
        
    async def vectorize_news_data(self, job: VectorizationJob) -> bool:
        """Vectorize news article data."""
        try:
            news_id = job.data.get('id')
            if not news_id:
                logger.error(f"No news ID provided in job {job.job_id}")
                return False
                
            # Fetch news article details
            news_data = await self._fetch_news_article(news_id)
            if not news_data:
                logger.warning(f"No news article found with ID {news_id}")
                return False
                
            logger.info(f"Vectorizing news article: {news_data['title']}")
            
            # Generate enhanced text content
            text_content = self._generate_news_text(news_data)
            
            # Send to vector storage
            success = await self._send_to_vector_storage(
                content=text_content,
                metadata={
                    "type": "news",
                    "news_id": news_id,
                    "title": news_data['title'],
                    "source": news_data['source'],
                    "published_at": news_data['published_at'].isoformat(),
                    "sentiment": self._analyze_sentiment(news_data['content']),
                    "topics": self._extract_topics(news_data['content']),
                    "source_service": "background_vectorization_service",
                    "job_id": job.job_id
                }
            )
            
            if success:
                # Mark as vectorized in database
                await self._mark_news_vectorized(news_id)
                logger.info(f"Successfully vectorized news article: {news_data['title']}")
                return True
            else:
                logger.error(f"Failed to send news article to vector storage: {news_data['title']}")
                return False
                
        except Exception as e:
            logger.error(f"Error vectorizing news article {job.data.get('id', 'unknown')}: {e}")
            return False
            
    async def _fetch_news_article(self, news_id: int) -> Optional[Dict[str, Any]]:
        """Fetch news article from the database."""
        try:
            conn = await self.db_manager.get_connection()
            
            query = """
            SELECT id, title, content, published_at, source, url, summary
            FROM news_articles
            WHERE id = $1
            """
            
            row = await conn.fetchrow(query, news_id)
            await conn.close()
            
            if row:
                return dict(row)
            return None
            
        except Exception as e:
            logger.error(f"Error fetching news article {news_id}: {e}")
            return None
            
    def _generate_news_text(self, news_data: Dict[str, Any]) -> str:
        """Generate comprehensive text content for news article."""
        title = news_data['title']
        content = news_data['content']
        source = news_data['source']
        published_at = news_data['published_at']
        summary = news_data.get('summary', '')
        url = news_data.get('url', '')
        
        # Clean and process content
        cleaned_content = self._clean_content(content)
        
        # Extract key information
        sentiment = self._analyze_sentiment(cleaned_content)
        topics = self._extract_topics(cleaned_content)
        key_entities = self._extract_entities(cleaned_content)
        
        # Generate comprehensive text
        text_content = f"""
        News Article: {title}
        
        Source: {source}
        Published: {published_at.strftime('%Y-%m-%d %H:%M:%S UTC')}
        URL: {url if url else 'Not available'}
        
        Summary:
        {summary if summary else 'No summary available'}
        
        Content Analysis:
        - Sentiment: {sentiment}
        - Primary Topics: {', '.join(topics[:5]) if topics else 'General news'}
        - Key Entities: {', '.join(key_entities[:5]) if key_entities else 'None identified'}
        
        Full Content:
        {cleaned_content[:3000]}{'...' if len(cleaned_content) > 3000 else ''}
        
        Content Statistics:
        - Word Count: {len(cleaned_content.split())}
        - Character Count: {len(cleaned_content)}
        - Reading Time: {len(cleaned_content.split()) // 200 + 1} minutes (estimated)
        
        Source Credibility:
        {self._assess_source_credibility(source)}
        """
        
        return text_content.strip()
        
    def _clean_content(self, content: str) -> str:
        """Clean and normalize news content."""
        if not content:
            return ""
            
        # Remove extra whitespace
        cleaned = re.sub(r'\s+', ' ', content.strip())
        
        # Remove HTML tags if present
        cleaned = re.sub(r'<[^>]+>', '', cleaned)
        
        # Remove special characters that might interfere with processing
        cleaned = re.sub(r'[^\w\s\.\,\!\?\:\;\-\(\)]', '', cleaned)
        
        # Normalize quotes and apostrophes
        cleaned = cleaned.replace('"', '"').replace('"', '"')
        cleaned = cleaned.replace(''', "'").replace(''', "'")
        
        return cleaned
        
    def _analyze_sentiment(self, content: str) -> str:
        """Analyze the sentiment of news content."""
        if not content:
            return "Neutral"
            
        content_lower = content.lower()
        
        # Positive indicators
        positive_words = [
            'positive', 'growth', 'increase', 'rise', 'gain', 'profit', 'success',
            'strong', 'improve', 'better', 'excellent', 'outperform', 'beat',
            'surge', 'jump', 'climb', 'advance', 'rally', 'boom', 'thrive'
        ]
        
        # Negative indicators
        negative_words = [
            'negative', 'decline', 'decrease', 'fall', 'loss', 'drop', 'weak',
            'worse', 'poor', 'fail', 'miss', 'underperform', 'crash', 'plunge',
            'tumble', 'slump', 'recession', 'crisis', 'risk', 'concern', 'worry'
        ]
        
        # Count occurrences
        positive_count = sum(1 for word in positive_words if word in content_lower)
        negative_count = sum(1 for word in negative_words if word in content_lower)
        
        # Determine sentiment
        if positive_count > negative_count * 1.5:
            return "Positive"
        elif negative_count > positive_count * 1.5:
            return "Negative"
        elif abs(positive_count - negative_count) <= 2:
            return "Neutral"
        elif positive_count > negative_count:
            return "Slightly Positive"
        else:
            return "Slightly Negative"
            
    def _extract_topics(self, content: str) -> List[str]:
        """Extract main topics from news content."""
        if not content:
            return []
            
        content_lower = content.lower()
        
        # Define topic keywords
        topics = {
            'Technology': ['tech', 'technology', 'software', 'ai', 'artificial intelligence', 'machine learning', 'digital', 'cyber'],
            'Finance': ['finance', 'financial', 'banking', 'investment', 'trading', 'market', 'stock', 'economy'],
            'Healthcare': ['health', 'healthcare', 'medical', 'pharmaceutical', 'biotech', 'medicine', 'treatment'],
            'Energy': ['energy', 'oil', 'gas', 'renewable', 'solar', 'wind', 'fossil fuel', 'electric'],
            'Transportation': ['transport', 'automotive', 'car', 'vehicle', 'airline', 'shipping', 'logistics'],
            'Retail': ['retail', 'consumer', 'shopping', 'e-commerce', 'commerce', 'sales', 'store'],
            'Real Estate': ['real estate', 'property', 'housing', 'construction', 'mortgage', 'rental'],
            'Politics': ['political', 'government', 'policy', 'election', 'congress', 'senate', 'president'],
            'Environment': ['environment', 'climate', 'sustainability', 'green', 'carbon', 'pollution'],
            'Education': ['education', 'school', 'university', 'learning', 'student', 'academic']
        }
        
        # Find matching topics
        found_topics = []
        for topic, keywords in topics.items():
            if any(keyword in content_lower for keyword in keywords):
                found_topics.append(topic)
                
        # Add general topics if no specific ones found
        if not found_topics:
            found_topics.append('General News')
            
        return found_topics[:5]  # Limit to top 5 topics
        
    def _extract_entities(self, content: str) -> List[str]:
        """Extract key entities (companies, people, places) from content."""
        if not content:
            return []
            
        # Simple entity extraction using capitalization patterns
        entities = []
        
        # Find capitalized words that might be entities
        words = content.split()
        for i, word in enumerate(words):
            # Skip common words and short words
            if len(word) < 3 or word.lower() in ['the', 'and', 'for', 'with', 'this', 'that']:
                continue
                
            # Check if word starts with capital letter and previous word doesn't end with period
            if (word[0].isupper() and 
                (i == 0 or not words[i-1].endswith('.')) and
                not word.endswith('.') and
                not word.endswith(',') and
                not word.endswith('!')):
                entities.append(word)
                
        # Remove duplicates and limit results
        unique_entities = list(set(entities))
        return unique_entities[:10]  # Limit to top 10 entities
        
    def _assess_source_credibility(self, source: str) -> str:
        """Assess the credibility of the news source."""
        if not source:
            return "Source not specified"
            
        source_lower = source.lower()
        
        # High credibility sources
        high_credibility = [
            'reuters', 'bloomberg', 'cnbc', 'wall street journal', 'wsj',
            'financial times', 'ft', 'forbes', 'fortune', 'cnn', 'bbc',
            'associated press', 'ap', 'marketwatch', 'yahoo finance'
        ]
        
        # Medium credibility sources
        medium_credibility = [
            'seeking alpha', 'motley fool', 'investing.com', 'tradingview',
            'benzinga', 'street insider', 'zacks', 'morningstar'
        ]
        
        # Check credibility level
        if any(credible in source_lower for credible in high_credibility):
            return "High credibility - Established financial news source"
        elif any(credible in source_lower for credible in medium_credibility):
            return "Medium credibility - Financial analysis platform"
        else:
            return "Unknown credibility - Source not in recognized list"
            
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
            
    async def _mark_news_vectorized(self, news_id: int):
        """Mark news article as vectorized in the database."""
        try:
            conn = await self.db_manager.get_connection()
            query = """
            UPDATE news_articles
            SET vectorized = true, vectorized_at = NOW()
            WHERE id = $1
            """
            await conn.execute(query, news_id)
            await conn.close()
        except Exception as e:
            logger.error(f"Error marking news as vectorized: {e}")
            
    async def batch_vectorize_news(self, news_ids: List[int]) -> Dict[int, bool]:
        """Vectorize multiple news articles in parallel."""
        logger.info(f"Starting batch vectorization for {len(news_ids)} news articles")
        
        # Create jobs for each news ID
        jobs = []
        for news_id in news_ids:
            job = VectorizationJob(
                job_id=f"news_{news_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                data_type="news",
                data={"id": news_id},
                priority=2
            )
            jobs.append(job)
            
        # Process jobs in parallel with limited concurrency
        semaphore = asyncio.Semaphore(3)  # Limit to 3 concurrent vectorizations
        
        async def process_job(job):
            async with semaphore:
                return await self.vectorize_news_data(job)
                
        # Execute all jobs
        tasks = [process_job(job) for job in jobs]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        success_count = 0
        failure_count = 0
        results_dict = {}
        
        for i, result in enumerate(results):
            news_id = news_ids[i]
            if isinstance(result, Exception):
                logger.error(f"Exception vectorizing news {news_id}: {result}")
                results_dict[news_id] = False
                failure_count += 1
            else:
                results_dict[news_id] = result
                if result:
                    success_count += 1
                else:
                    failure_count += 1
                    
        logger.info(f"Batch news vectorization completed: {success_count} success, {failure_count} failure")
        return results_dict
        
    async def get_unvectorized_news(self, limit: int = 100) -> List[int]:
        """Get list of news article IDs that haven't been vectorized."""
        try:
            conn = await self.db_manager.get_connection()
            
            query = """
            SELECT id
            FROM news_articles
            WHERE vectorized = false OR vectorized IS NULL
            AND published_at >= NOW() - INTERVAL '30 days'
            ORDER BY published_at DESC
            LIMIT $1
            """
            
            rows = await conn.fetch(query, limit)
            await conn.close()
            
            return [row['id'] for row in rows]
            
        except Exception as e:
            logger.error(f"Error fetching unvectorized news: {e}")
            return []
