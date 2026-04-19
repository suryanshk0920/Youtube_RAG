"""
Usage Tracking Middleware
========================
Automatically logs user actions for subscription limit tracking.
"""

import logging
from datetime import datetime, timezone
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from api.auth import get_supabase

logger = logging.getLogger(__name__)

class UsageTrackingMiddleware(BaseHTTPMiddleware):
    """Middleware to automatically track user actions for subscription limits."""
    
    def __init__(self, app):
        super().__init__(app)
        self.tracked_endpoints = {
            "/ingest/stream": "ingest",
            "/chat/stream": "chat",
            "/chat": "chat"
        }
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Only track successful requests
        if response.status_code < 400:
            await self._track_usage(request, response)
        
        return response
    
    async def _track_usage(self, request: Request, response: Response):
        """Track usage for subscription limits."""
        try:
            # Check if this endpoint should be tracked
            path = request.url.path
            action = self.tracked_endpoints.get(path)
            
            if not action:
                return
            
            # Get user from request (if authenticated)
            user_id = getattr(request.state, 'user_id', None)
            if not user_id:
                # Try to extract from Authorization header
                auth_header = request.headers.get('Authorization')
                if auth_header and auth_header.startswith('Bearer '):
                    # This would need to be implemented to decode the JWT
                    # For now, skip tracking for unauthenticated requests
                    return
            
            # Log the usage
            db = get_supabase()
            db.table("usage_logs").insert({
                "user_id": user_id,
                "action": action,
                "endpoint": path,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "metadata": {
                    "method": request.method,
                    "user_agent": request.headers.get("user-agent", ""),
                    "ip": request.client.host if request.client else None
                }
            }).execute()
            
        except Exception as e:
            # Don't fail the request if usage tracking fails
            logger.warning(f"Failed to track usage: {e}")