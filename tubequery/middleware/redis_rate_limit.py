"""
Redis-Based Rate Limiting Middleware
====================================
Production-grade rate limiting using Redis sliding window algorithm.
Supports plan-based limits and graceful degradation.
"""

import logging
import time
from typing import Callable, Optional
from datetime import datetime, timezone

from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from services.redis_service_production import get_production_redis_service
from services.subscription_service_redis import RedisSubscriptionService, PlanType, PLAN_LIMITS
from api.auth import get_supabase

logger = logging.getLogger(__name__)

class RedisRateLimitMiddleware(BaseHTTPMiddleware):
    """
    Production-grade rate limiting middleware using Redis (optimized for minimal calls).
    Features:
    - Plan-based rate limits (Free: 30/min, Pro: 120/min, Enterprise: 300/min)
    - Sliding window algorithm for accurate rate limiting
    - Graceful degradation when Redis is unavailable
    - Request caching to minimize Redis calls
    - Detailed rate limit headers in responses
    """
    
    def __init__(self, app, default_requests_per_minute: int = 60):
        super().__init__(app)
        self.default_requests_per_minute = default_requests_per_minute
        self._redis_service = None
        
        # Request caching to reduce Redis calls
        self._rate_cache: Dict[str, Dict] = {}
        self._cache_ttl = 10  # 10 seconds cache for rate limit checks
        
        # Paths to exclude from rate limiting
        self.excluded_paths = {
            "/health",
            "/health/redis", 
            "/metrics",
            "/docs",
            "/redoc",
            "/openapi.json"
        }
    
    def _get_cached_rate_info(self, client_id: str) -> Optional[Dict]:
        """Get cached rate limit info if still valid."""
        cached = self._rate_cache.get(client_id)
        if cached and time.time() - cached['timestamp'] < self._cache_ttl:
            # Update remaining count based on time elapsed
            elapsed = time.time() - cached['timestamp']
            if elapsed < 60:  # Within the same minute
                return cached['data']
        return None
    
    def _set_cached_rate_info(self, client_id: str, rate_info: Dict):
        """Cache rate limit info."""
        self._rate_cache[client_id] = {
            'data': rate_info,
            'timestamp': time.time()
        }
        
        # Clean old cache entries
        now = time.time()
        expired_keys = [
            key for key, value in self._rate_cache.items()
            if now - value['timestamp'] > self._cache_ttl * 2
        ]
        for key in expired_keys:
            del self._rate_cache[key]
    
    async def _get_redis_service(self):
        """Get Redis service instance (lazy initialization)."""
        if self._redis_service is None:
            try:
                self._redis_service = await get_production_redis_service()
            except Exception as e:
                logger.error(f"Failed to initialize Redis service for rate limiting: {e}")
                self._redis_service = None
        return self._redis_service
    
    async def _get_user_rate_limit(self, user_id: str) -> int:
        """Get rate limit for user based on their plan."""
        try:
            db = get_supabase()
            subscription_service = RedisSubscriptionService(db)
            plan_type, _ = await subscription_service.get_user_plan(user_id)
            limits = PLAN_LIMITS[plan_type]
            return limits.rate_limit_per_minute
        except Exception as e:
            logger.warning(f"Failed to get user plan for rate limiting: {e}")
            return self.default_requests_per_minute
    
    async def _check_rate_limit_redis(self, user_id: str, rate_limit: int) -> tuple[bool, dict]:
        """Check rate limit using Redis (with caching optimization)."""
        try:
            # Check cache first
            cached_info = self._get_cached_rate_info(user_id)
            if cached_info:
                logger.debug(f"Using cached rate limit for {user_id}")
                return cached_info["allowed"], cached_info
            
            redis_service = await self._get_redis_service()
            if not redis_service:
                # Fallback: allow request if Redis is unavailable
                return True, {
                    "allowed": True,
                    "remaining": rate_limit,
                    "reset_time": datetime.now(timezone.utc).isoformat(),
                    "fallback": True
                }
            
            rate_info = await redis_service.check_rate_limit(
                user_id=user_id,
                action="api_call",
                limit=rate_limit,
                window_seconds=60
            )
            
            result = {
                "allowed": rate_info.allowed,
                "remaining": rate_info.remaining,
                "reset_time": rate_info.reset_time.isoformat(),
                "current_usage": rate_info.current_usage,
                "window_size": rate_info.window_size,
                "fallback": False
            }
            
            # Cache the result
            self._set_cached_rate_info(user_id, result)
            
            return rate_info.allowed, result
            
        except Exception as e:
            logger.error(f"Redis rate limit check failed: {e}")
            # Fail open - allow request
            return True, {
                "allowed": True,
                "remaining": rate_limit,
                "reset_time": datetime.now(timezone.utc).isoformat(),
                "error": str(e),
                "fallback": True
            }
    
    def _get_client_identifier(self, request: Request) -> str:
        """Get client identifier for rate limiting."""
        # Try to get user ID from auth
        user = getattr(request.state, 'user', None)
        if user and isinstance(user, dict) and 'uid' in user:
            return f"user:{user['uid']}"
        
        # Fallback to IP address
        client_ip = request.client.host if request.client else "unknown"
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        
        return f"ip:{client_ip}"
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with rate limiting."""
        start_time = time.time()
        
        # Skip rate limiting for excluded paths
        if request.url.path in self.excluded_paths:
            return await call_next(request)
        
        # Get client identifier
        client_id = self._get_client_identifier(request)
        
        # Determine rate limit
        if client_id.startswith("user:"):
            user_id = client_id.split(":", 1)[1]
            rate_limit = await self._get_user_rate_limit(user_id)
        else:
            rate_limit = self.default_requests_per_minute
        
        # Check rate limit
        allowed, rate_info = await self._check_rate_limit_redis(client_id, rate_limit)
        
        if not allowed:
            # Rate limit exceeded
            logger.warning(f"Rate limit exceeded for {client_id}: {rate_info['current_usage']}/{rate_limit}")
            
            response = JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "message": f"Too many requests. Limit: {rate_limit} requests per minute.",
                    "retry_after": 60,
                    "upgrade_available": client_id.startswith("user:") and rate_limit <= 30
                }
            )
            
            # Add rate limit headers
            response.headers["X-RateLimit-Limit"] = str(rate_limit)
            response.headers["X-RateLimit-Remaining"] = str(rate_info["remaining"])
            response.headers["X-RateLimit-Reset"] = rate_info["reset_time"]
            response.headers["Retry-After"] = "60"
            
            return response
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers to successful responses
        response.headers["X-RateLimit-Limit"] = str(rate_limit)
        response.headers["X-RateLimit-Remaining"] = str(rate_info["remaining"])
        response.headers["X-RateLimit-Reset"] = rate_info["reset_time"]
        
        if rate_info.get("fallback"):
            response.headers["X-RateLimit-Fallback"] = "true"
        
        # Log performance metrics
        duration = time.time() - start_time
        logger.info(f"Rate limit check for {client_id}: {duration*1000:.2f}ms, allowed={allowed}")
        
        return response

# Legacy middleware for backward compatibility
class RateLimitMiddleware(RedisRateLimitMiddleware):
    """Legacy rate limiting middleware - redirects to Redis-based implementation."""
    pass