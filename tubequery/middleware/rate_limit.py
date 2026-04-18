"""
Rate Limiting Middleware
========================
Simple in-memory rate limiting for API endpoints.
"""

import time
from collections import defaultdict, deque
from typing import Dict, Deque
from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Simple sliding window rate limiter.
    
    Limits requests per user per endpoint.
    """
    
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.window_size = 60  # seconds
        
        # Store request timestamps per user
        self.request_history: Dict[str, Deque[float]] = defaultdict(deque)
    
    async def dispatch(self, request: Request, call_next):
        # Only rate limit chat endpoints
        if not request.url.path.startswith("/chat"):
            return await call_next(request)
        
        # Get user ID from request (assumes auth middleware runs first)
        user_id = getattr(request.state, 'user_id', None)
        if not user_id:
            return await call_next(request)
        
        current_time = time.time()
        user_requests = self.request_history[user_id]
        
        # Remove old requests outside the window
        while user_requests and user_requests[0] < current_time - self.window_size:
            user_requests.popleft()
        
        # Check if user has exceeded rate limit
        if len(user_requests) >= self.requests_per_minute:
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded. Max {self.requests_per_minute} requests per minute."
            )
        
        # Add current request
        user_requests.append(current_time)
        
        # Clean up old users periodically
        if len(self.request_history) > 10000:
            cutoff = current_time - self.window_size * 2
            users_to_remove = [
                uid for uid, requests in self.request_history.items()
                if not requests or requests[-1] < cutoff
            ]
            for uid in users_to_remove:
                del self.request_history[uid]
        
        response = await call_next(request)
        return response