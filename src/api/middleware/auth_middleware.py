"""
Authentication middleware
"""

import jwt
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import Request, HTTPException, status, WebSocket
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from src.api.config.security_config import JWTConfig


class JWTManager:
    """JWT token management"""
    
    def __init__(self, config: JWTConfig):
        self.config = config
        self.secret_key = config.secret_key
        self.algorithm = config.algorithm
        self.access_token_expire_minutes = config.access_token_expire_minutes
        self.refresh_token_expire_days = config.refresh_token_expire_days
    
    def create_access_token(self, user_data: Dict[str, Any]) -> str:
        """Create access token"""
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        payload = {
            **user_data,
            "exp": expire,
            "type": "access"
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def create_refresh_token(self, user_data: Dict[str, Any]) -> str:
        """Create refresh token"""
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        payload = {
            **user_data,
            "exp": expire,
            "type": "refresh"
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def decode_token(self, token: str) -> Dict[str, Any]:
        """Decode JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify and decode token"""
        payload = self.decode_token(token)
        if payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        return payload
    
    def verify_refresh_token(self, token: str) -> Dict[str, Any]:
        """Verify and decode refresh token"""
        payload = self.decode_token(token)
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        return payload


class AuthMiddleware(BaseHTTPMiddleware):
    """Authentication middleware"""
    
    def __init__(self, app, jwt_manager: Optional[JWTManager] = None):
        super().__init__(app)
        self.jwt_manager = jwt_manager or JWTManager(JWTConfig(secret_key="default-secret"))
        self.security = HTTPBearer()
    
    async def dispatch(self, request: Request, call_next):
        """Process request with authentication"""
        
        # Skip authentication for public endpoints
        if self._is_public_endpoint(request.url.path):
            response = await call_next(request)
            return response
        
        # Extract token from Authorization header
        try:
            credentials: HTTPAuthorizationCredentials = await self.security(request)
            token = credentials.credentials
        except Exception:
            return Response(
                content=f'{{"error": "unauthorized", "message": "Missing or invalid authorization header", "timestamp": {time.time()}}}',
                status_code=status.HTTP_401_UNAUTHORIZED,
                media_type="application/json"
            )
        
        # Verify token
        try:
            payload = self.jwt_manager.verify_token(token)
            request.state.user = payload
        except HTTPException as e:
            return Response(
                content=f'{{"error": "unauthorized", "message": "{e.detail}", "timestamp": {time.time()}}}',
                status_code=status.HTTP_401_UNAUTHORIZED,
                media_type="application/json"
            )
        
        # Check permissions for admin endpoints
        if self._is_admin_endpoint(request.url.path):
            if payload.get("role") != "admin":
                return Response(
                    content='{"error": "forbidden", "message": "Insufficient permissions"}',
                    status_code=status.HTTP_403_FORBIDDEN,
                    media_type="application/json"
                )
        
        response = await call_next(request)
        return response
    
    def _is_public_endpoint(self, path: str) -> bool:
        """Check if endpoint is public"""
        public_paths = [
            "/",
            "/health",
            "/api/health",
            "/docs",
            "/openapi.json",
            "/redoc",
            "/public",  # For testing
            "/test",    # For testing
            "/metrics"  # For testing
        ]
        # Also allow test endpoints
        if path.startswith("/api/trading/test/"):
            return True
        return path in public_paths
    
    def _is_admin_endpoint(self, path: str) -> bool:
        """Check if endpoint requires admin permissions"""
        admin_paths = [
            "/api/admin",
            "/api/users",
            "/api/system",
            "/admin"  # For testing
        ]
        return any(path.startswith(admin_path) for admin_path in admin_paths)


# Dependency function for FastAPI
def get_current_user(request: Request) -> Dict[str, Any]:
    """
    FastAPI dependency to get current user from request
    
    Args:
        request: FastAPI request object
        
    Returns:
        User information dictionary
        
    Raises:
        HTTPException: If user is not authenticated
    """
    # Get user from request state (set by auth middleware)
    user = getattr(request.state, 'user', None)
    
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Authentication required"
        )
    
    return user


# WebSocket dependency function for FastAPI
def get_current_user_websocket(websocket: WebSocket) -> Dict[str, Any]:
    """
    FastAPI WebSocket dependency to get current user from websocket
    
    Args:
        websocket: FastAPI websocket object
        
    Returns:
        User information dictionary
        
    Raises:
        HTTPException: If user is not authenticated
    """
    # Get user from websocket state (set by auth middleware)
    user = getattr(websocket.state, 'user', None)
    
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Authentication required"
        )
    
    return user
