"""
Rejection Tracking Service
==========================

Tracks and logs trade attempts that were rejected before submission to the broker.
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
import pytz

from .models import RejectedTradeAttempt

logger = logging.getLogger(__name__)

# Mountain Time (Denver) timezone
MOUNTAIN_TZ = pytz.timezone('America/Denver')


class RejectionTrackingService:
    """Service for tracking rejected trade attempts."""
    
    def __init__(self, db_session: AsyncSession):
        """Initialize the rejection tracking service."""
        self.db_session = db_session
    
    async def log_rejection(
        self,
        account_id: str,
        symbol: str,
        strategy: str,
        action: str,
        rejection_reason: str,
        rejection_category: str,
        quantity: Optional[int] = None,
        estimated_premium: Optional[float] = None,
        confidence_score: Optional[float] = None,
        current_price: Optional[float] = None,
        option_type: Optional[str] = None,
        strike_price: Optional[float] = None,
        expiration_date: Optional[datetime] = None,
        rejection_details: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Log a rejected trade attempt.
        
        Args:
            account_id: Trading account ID
            symbol: Symbol being traded
            strategy: Strategy name
            action: BUY or SELL
            rejection_reason: Human-readable reason for rejection
            rejection_category: Category of rejection (RISK, BUYING_POWER, CONFIDENCE, POSITION_EXISTS, VALIDATION)
            quantity: Quantity of shares/contracts
            estimated_premium: Estimated cost
            confidence_score: Signal confidence if applicable
            current_price: Current market price
            option_type: CALL, PUT, or None
            strike_price: Strike price for options
            expiration_date: Expiration date for options
            rejection_details: Additional context as dict
            
        Returns:
            The attempt_id of the logged rejection
        """
        try:
            # Create rejection record
            rejection = RejectedTradeAttempt(
                account_id=account_id,
                symbol=symbol,
                strategy=strategy,
                action=action,
                quantity=quantity,
                estimated_premium=estimated_premium,
                rejection_reason=rejection_reason,
                rejection_category=rejection_category,
                confidence_score=confidence_score,
                current_price=current_price,
                option_type=option_type,
                strike_price=strike_price,
                expiration_date=expiration_date,
                rejection_details=json.dumps(rejection_details) if rejection_details else None,
                created_at=datetime.now(MOUNTAIN_TZ)
            )
            
            self.db_session.add(rejection)
            await self.db_session.commit()
            
            logger.info(f"📝 Logged rejected trade attempt: {symbol} {action} - {rejection_reason}")
            
            return str(rejection.attempt_id)
            
        except Exception as e:
            logger.error(f"❌ Error logging rejected trade attempt: {e}")
            await self.db_session.rollback()
            return None
    
    async def get_recent_rejections(
        self,
        account_id: str,
        limit: int = 100
    ) -> list:
        """
        Get recent rejected trade attempts.
        
        Args:
            account_id: Trading account ID
            limit: Maximum number of records to return
            
        Returns:
            List of rejected trade attempts
        """
        try:
            from sqlalchemy import select, desc
            
            result = await self.db_session.execute(
                select(RejectedTradeAttempt)
                .where(RejectedTradeAttempt.account_id == account_id)
                .order_by(desc(RejectedTradeAttempt.created_at))
                .limit(limit)
            )
            
            rejections = result.scalars().all()
            
            # Convert to dict
            rejection_list = []
            for rejection in rejections:
                # Ensure timestamp is in Mountain Time
                created_at = rejection.created_at
                if created_at:
                    # If naive (no timezone), assume UTC and convert to Mountain
                    if created_at.tzinfo is None:
                        created_at = pytz.UTC.localize(created_at).astimezone(MOUNTAIN_TZ)
                    else:
                        created_at = created_at.astimezone(MOUNTAIN_TZ)
                
                rejection_dict = {
                    'attempt_id': str(rejection.attempt_id),
                    'symbol': rejection.symbol,
                    'strategy': rejection.strategy,
                    'action': rejection.action,
                    'quantity': rejection.quantity,
                    'estimated_premium': float(rejection.estimated_premium) if rejection.estimated_premium else None,
                    'rejection_reason': rejection.rejection_reason,
                    'rejection_category': rejection.rejection_category,
                    'confidence_score': float(rejection.confidence_score) if rejection.confidence_score else None,
                    'current_price': float(rejection.current_price) if rejection.current_price else None,
                    'option_type': rejection.option_type,
                    'strike_price': float(rejection.strike_price) if rejection.strike_price else None,
                    'expiration_date': rejection.expiration_date.isoformat() if rejection.expiration_date else None,
                    'rejection_details': json.loads(rejection.rejection_details) if rejection.rejection_details else {},
                    'created_at': created_at.isoformat() if created_at else None
                }
                rejection_list.append(rejection_dict)
            
            return rejection_list
            
        except Exception as e:
            logger.error(f"❌ Error fetching rejected trade attempts: {e}")
            return []

