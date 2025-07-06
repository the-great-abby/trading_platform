"""
User Service - Internal microservice for user management operations
"""

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import os
import logging
from datetime import datetime
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="User Service", version="1.0.0")

class User(BaseModel):
    user_id: str
    username: str
    email: str
    role: str
    is_active: bool
    created_at: str
    last_login: Optional[str] = None

class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    role: str = "user"

class UserUpdate(BaseModel):
    email: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "user-service"}

@app.get("/status")
async def get_status():
    """Get user service status"""
    return {
        "service": "user-service",
        "version": "1.0.0",
        "status": "operational"
    }

@app.get("/users")
async def get_users(limit: int = 100, offset: int = 0):
    """Get all users"""
    try:
        # Mock users data
        users = [
            {
                "user_id": "user_1",
                "username": "admin",
                "email": "admin@example.com",
                "role": "admin",
                "is_active": True,
                "created_at": "2024-01-01T00:00:00Z",
                "last_login": "2024-01-01T10:00:00Z"
            },
            {
                "user_id": "user_2",
                "username": "trader1",
                "email": "trader1@example.com",
                "role": "trader",
                "is_active": True,
                "created_at": "2024-01-01T00:00:00Z",
                "last_login": "2024-01-01T09:00:00Z"
            }
        ]
        
        return {
            "users": users[offset:offset+limit],
            "count": len(users),
            "total_count": len(users)
        }
    except Exception as e:
        logger.error(f"Failed to get users: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get users: {str(e)}")

@app.get("/users/{user_id}")
async def get_user(user_id: str):
    """Get specific user"""
    try:
        # Mock user data
        user = {
            "user_id": user_id,
            "username": "trader1",
            "email": "trader1@example.com",
            "role": "trader",
            "is_active": True,
            "created_at": "2024-01-01T00:00:00Z",
            "last_login": "2024-01-01T09:00:00Z",
            "permissions": ["read_portfolio", "execute_trades", "view_analytics"]
        }
        
        return user
    except Exception as e:
        logger.error(f"Failed to get user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get user: {str(e)}")

@app.post("/users", response_model=Dict[str, Any])
async def create_user(user_data: UserCreate):
    """Create a new user"""
    try:
        user_id = str(uuid.uuid4())
        
        # Mock user creation
        logger.info(f"Creating user: {user_data.username}")
        
        return {
            "user_id": user_id,
            "username": user_data.username,
            "email": user_data.email,
            "role": user_data.role,
            "is_active": True,
            "created_at": datetime.now().isoformat(),
            "message": "User created successfully"
        }
    except Exception as e:
        logger.error(f"Failed to create user: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create user: {str(e)}")

@app.put("/users/{user_id}")
async def update_user(user_id: str, user_update: UserUpdate):
    """Update user"""
    try:
        logger.info(f"Updating user: {user_id}")
        
        return {
            "user_id": user_id,
            "message": "User updated successfully",
            "updated_fields": user_update.dict(exclude_unset=True),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to update user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update user: {str(e)}")

@app.delete("/users/{user_id}")
async def delete_user(user_id: str):
    """Delete user"""
    try:
        logger.info(f"Deleting user: {user_id}")
        
        return {
            "user_id": user_id,
            "message": "User deleted successfully",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to delete user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete user: {str(e)}")

@app.get("/users/{user_id}/permissions")
async def get_user_permissions(user_id: str):
    """Get user permissions"""
    try:
        # Mock permissions based on role
        permissions = {
            "admin": ["read_portfolio", "write_portfolio", "execute_trades", "view_analytics", "manage_users", "system_config"],
            "trader": ["read_portfolio", "execute_trades", "view_analytics"],
            "viewer": ["read_portfolio", "view_analytics"]
        }
        
        # Mock user role
        user_role = "trader"
        
        return {
            "user_id": user_id,
            "role": user_role,
            "permissions": permissions.get(user_role, []),
            "last_updated": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get permissions for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get permissions: {str(e)}")

@app.post("/auth/login")
async def login(username: str, password: str):
    """User login"""
    try:
        # Mock authentication
        if username == "admin" and password == "password":
            return {
                "access_token": "mock_jwt_token",
                "token_type": "bearer",
                "user_id": "user_1",
                "username": username,
                "role": "admin",
                "expires_in": 3600
            }
        else:
            raise HTTPException(status_code=401, detail="Invalid credentials")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login failed: {e}")
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")

@app.post("/auth/logout")
async def logout():
    """User logout"""
    try:
        return {
            "message": "Logged out successfully",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Logout failed: {e}")
        raise HTTPException(status_code=500, detail=f"Logout failed: {str(e)}")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8008))
    uvicorn.run(app, host="0.0.0.0", port=port)
