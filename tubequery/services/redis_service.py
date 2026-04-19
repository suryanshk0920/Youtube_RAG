"""
Redis Service - Upstash Integration
===================================
High-performance Redis operations for usage tracking, rate limiting,
session management, and background job processing.
"""

from __future__ import annotations

import json
import logging
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from contextlib import asynccontextmanager

import redis.asyncio as redis
from upstash_redis import Redis as UpstashRedis

import config

logger = logging.getLogger(__name__)

@dataclass
class UsageStats:
    """User usage statistics for a specific date."""
    user_id: str
    date: str
    videos_ingested: int = 0
    questions_asked: int = 0
    summaries_generated: int = 0
    last_updated: Optional[datetime] = None

@dataclass
class RateLimitInfo:
    """Rate limiting information."""
    allowed: bool
    remaining: int
    reset_time: datetime
    window_size: int

class RedisService:
    """
    Redis service using Upstash for high-performance operations.
    Supports both direct Redis protocol and REST API for reliability.
    """
    
    def __init__(self):
        self._redis_client: Optional[redis.Redis] = None
        self._upstash_client: Optional[UpstashRedis] = None
        self._connection_pool: Optional[redis.ConnectionPool] = None
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize Redis connections with REST API as primary."""
        if self._initialized:
            return
            
        try:
            # Initialize Upstash REST client as primary
            self._upstash_client = UpstashRedis(
                url=config.UPSTASH_REDIS_REST_URL,
                token=config.UPSTASH_REDIS_TOKEN,
            )
            
            # Try to initialize direct Redis connection as secondary
            try:
                self._connection_pool = redis.ConnectionPool.from_url(
                    config.UPSTASH_REDIS_URL,
                    max_connections=config.REDIS_MAX_CONNECTIONS,
                    retry_on_timeout=config.REDIS_RETRY_ON_TIMEOUT,
                    socket_keepalive=True,
                    socket_keepalive_options={},
                    health_check_interval=30,
                )
                
                self._redis_client = redis.Redis(
                    connection_pool=self._connection_pool,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                )
                logger.info("Direct Redis connection initialized")
            except Exception as e:
                logger.warning(f"Direct Redis connection failed, using REST API only: {e}")
                self._redis_client = None
                self._connection_pool = None
            
            # Test connection
            await self._test_connection()
            self._initialized = True
            logger.info("Redis service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Redis service: {e}")
            raise
    
    async def _test_connection(self) -> None:
        """Test Redis connection with ping."""
        try:
            # Test Upstash REST connection first (primary)
            if self._upstash_client:
                rest_result = self._upstash_client.ping()
                if rest_result == "PONG":
                    logger.info("Upstash REST API connection successful")
                else:
                    raise ConnectionError("Upstash REST API ping failed")
            
            # Test direct Redis connection if available (secondary)
            if self._redis_client:
                try:
                    result = await self._redis_client.ping()
                    if result:
                        logger.info("Direct Redis connection successful")
                    else:
                        logger.warning("Direct Redis ping failed")
                except Exception as e:
                    logger.warning(f"Direct Redis connection failed: {e}")
                    # Don't fail initialization if REST API works
                    
        except Exception as e:
            logger.error(f"Redis connection test failed: {e}")
            raise
    
    async def close(self) -> None:
        """Close Redis connections and cleanup resources."""
        try:
            if self._redis_client:
                await self._redis_client.close()
            if self._connection_pool:
                await self._connection_pool.disconnect()
            self._initialized = False
            logger.info("Redis service closed successfully")
        except Exception as e:
            logger.error(f"Error closing Redis service: {e}")
    
    @asynccontextmanager
    async def _get_client(self):
        """Get Redis client with REST API as primary."""
        if not self._initialized:
            await self.initialize()
            
        # Always use REST API as primary since it's more reliable with Upstash
        if self._upstash_client:
            yield self._upstash_client
        elif self._redis_client:
            try:
                yield self._redis_client
            except Exception as e:
                logger.error(f"Both Redis connections failed: {e}")
                raise
        else:
            raise ConnectionError("No Redis connection available")
    
    # ── Usage Tracking Methods ─────────────────────────────────────────
    
    async def increment_usage(self, user_id: str, action: str, amount: int = 1) -> bool:
        """
        Increment usage count for a user action (atomic operation).
        
        Args:
            user_id: User identifier
            action: Action type ('ingest', 'chat', 'summary')
            amount: Amount to increment (default: 1)
            
        Returns:
            bool: Success status
        """
        today = datetime.now(timezone.utc).date().isoformat()
        usage_key = f"{config.REDIS_USAGE_KEY_PREFIX}{user_id}:{today}"
        
        try:
            async with self._get_client() as client:
                # Use Redis hash to store different usage types
                field_map = {
                    'ingest': 'videos_ingested',
                    'chat': 'questions_asked', 
                    'summary': 'summaries_generated'
                }
                
                field = field_map.get(action, action)
                
                # Check if this is the async Redis client or sync Upstash client
                if hasattr(client, 'connection_pool'):
                    # Direct Redis client (async)
                    pipe = client.pipeline()
                    pipe.hincrby(usage_key, field, amount)
                    pipe.hset(usage_key, 'last_updated', datetime.now(timezone.utc).isoformat())
                    pipe.expire(usage_key, config.USAGE_TTL_SECONDS)
                    await pipe.execute()
                else:
                    # Upstash REST client (sync)
                    client.hincrby(usage_key, field, amount)
                    client.hset(usage_key, 'last_updated', datetime.now(timezone.utc).isoformat())
                    client.expire(usage_key, config.USAGE_TTL_SECONDS)
                
                logger.info(f"Incremented {action} usage for user {user_id} by {amount}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to increment usage for user {user_id}: {e}")
            return False
    
    async def get_usage_stats(self, user_id: str, date: Optional[str] = None) -> UsageStats:
        """
        Get usage statistics for a user on a specific date.
        
        Args:
            user_id: User identifier
            date: Date in YYYY-MM-DD format (default: today)
            
        Returns:
            UsageStats: Usage statistics object
        """
        if date is None:
            date = datetime.now(timezone.utc).date().isoformat()
            
        usage_key = f"{config.REDIS_USAGE_KEY_PREFIX}{user_id}:{date}"
        
        try:
            async with self._get_client() as client:
                if hasattr(client, 'connection_pool'):
                    # Direct Redis client (async)
                    usage_data = await client.hgetall(usage_key)
                else:
                    # Upstash REST client (sync)
                    usage_data = client.hgetall(usage_key) or {}
                
                return UsageStats(
                    user_id=user_id,
                    date=date,
                    videos_ingested=int(usage_data.get('videos_ingested', 0)),
                    questions_asked=int(usage_data.get('questions_asked', 0)),
                    summaries_generated=int(usage_data.get('summaries_generated', 0)),
                    last_updated=datetime.fromisoformat(usage_data['last_updated']) if usage_data.get('last_updated') else None
                )
                
        except Exception as e:
            logger.error(f"Failed to get usage stats for user {user_id}: {e}")
            return UsageStats(user_id=user_id, date=date)
    
    async def get_usage_history(self, user_id: str, days: int = 7) -> List[UsageStats]:
        """
        Get usage history for a user over multiple days.
        
        Args:
            user_id: User identifier
            days: Number of days to retrieve (default: 7)
            
        Returns:
            List[UsageStats]: List of usage statistics
        """
        history = []
        today = datetime.now(timezone.utc).date()
        
        try:
            # Get usage for each day
            for i in range(days):
                date = (today - timedelta(days=i)).isoformat()
                stats = await self.get_usage_stats(user_id, date)
                history.append(stats)
                
            return history
            
        except Exception as e:
            logger.error(f"Failed to get usage history for user {user_id}: {e}")
            return []
    
    # ── Rate Limiting Methods ──────────────────────────────────────────
    
    async def check_rate_limit(self, user_id: str, action: str, limit: int, window_seconds: int) -> RateLimitInfo:
        """
        Check rate limit using sliding window algorithm.
        
        Args:
            user_id: User identifier
            action: Action being rate limited
            limit: Maximum requests allowed in window
            window_seconds: Time window in seconds
            
        Returns:
            RateLimitInfo: Rate limit status and details
        """
        now = datetime.now(timezone.utc)
        window_start = now - timedelta(seconds=window_seconds)
        rate_key = f"{config.REDIS_RATE_LIMIT_KEY_PREFIX}{user_id}:{action}"
        
        try:
            async with self._get_client() as client:
                if hasattr(client, 'connection_pool'):
                    # Direct Redis client (async)
                    pipe = client.pipeline()
                    pipe.zremrangebyscore(rate_key, 0, window_start.timestamp())
                    pipe.zcard(rate_key)
                    pipe.zadd(rate_key, {str(now.timestamp()): now.timestamp()})
                    pipe.expire(rate_key, window_seconds + 60)
                    results = await pipe.execute()
                    current_count = results[1]
                else:
                    # Upstash REST client (sync) - simplified approach
                    client.zremrangebyscore(rate_key, 0, window_start.timestamp())
                    current_count = client.zcard(rate_key)
                    client.zadd(rate_key, {str(now.timestamp()): now.timestamp()})
                    client.expire(rate_key, window_seconds + 60)
                
                allowed = current_count < limit
                remaining = max(0, limit - current_count - 1)
                reset_time = now + timedelta(seconds=window_seconds)
                
                return RateLimitInfo(
                    allowed=allowed,
                    remaining=remaining,
                    reset_time=reset_time,
                    window_size=window_seconds
                )
                
        except Exception as e:
            logger.error(f"Rate limit check failed for user {user_id}: {e}")
            # Fail open - allow request but log error
            return RateLimitInfo(
                allowed=True,
                remaining=limit,
                reset_time=now + timedelta(seconds=window_seconds),
                window_size=window_seconds
            )
    
    # ── Session Management Methods ─────────────────────────────────────
    
    async def store_session(self, session_id: str, session_data: Dict[str, Any], ttl_seconds: int = 86400 * 7) -> bool:
        """
        Store session data with TTL.
        
        Args:
            session_id: Session identifier
            session_data: Session data dictionary
            ttl_seconds: Time to live in seconds (default: 7 days)
            
        Returns:
            bool: Success status
        """
        session_key = f"{config.REDIS_SESSION_KEY_PREFIX}{session_id}"
        
        try:
            async with self._get_client() as client:
                session_json = json.dumps(session_data, default=str)
                
                if hasattr(client, 'connection_pool'):
                    # Direct Redis client (async)
                    await client.setex(session_key, ttl_seconds, session_json)
                else:
                    # Upstash REST client (sync)
                    client.setex(session_key, ttl_seconds, session_json)
                    
                logger.info(f"Stored session {session_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to store session {session_id}: {e}")
            return False
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve session data.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Optional[Dict]: Session data or None if not found
        """
        session_key = f"{config.REDIS_SESSION_KEY_PREFIX}{session_id}"
        
        try:
            async with self._get_client() as client:
                if hasattr(client, 'connection_pool'):
                    # Direct Redis client (async)
                    session_json = await client.get(session_key)
                else:
                    # Upstash REST client (sync)
                    session_json = client.get(session_key)
                    
                if session_json:
                    return json.loads(session_json)
                return None
                
        except Exception as e:
            logger.error(f"Failed to get session {session_id}: {e}")
            return None
    
    async def delete_session(self, session_id: str) -> bool:
        """
        Delete session data.
        
        Args:
            session_id: Session identifier
            
        Returns:
            bool: Success status
        """
        session_key = f"{config.REDIS_SESSION_KEY_PREFIX}{session_id}"
        
        try:
            async with self._get_client() as client:
                if hasattr(client, 'connection_pool'):
                    # Direct Redis client (async)
                    result = await client.delete(session_key)
                else:
                    # Upstash REST client (sync)
                    result = client.delete(session_key)
                    
                logger.info(f"Deleted session {session_id}")
                return bool(result)
                
        except Exception as e:
            logger.error(f"Failed to delete session {session_id}: {e}")
            return False
    
    # ── Background Job Queue Methods ───────────────────────────────────
    
    async def enqueue_job(self, job_data: Dict[str, Any]) -> bool:
        """
        Add job to background processing queue.
        
        Args:
            job_data: Job data dictionary
            
        Returns:
            bool: Success status
        """
        try:
            async with self._get_client() as client:
                job_json = json.dumps(job_data, default=str)
                
                if hasattr(client, 'connection_pool'):
                    # Direct Redis client (async)
                    await client.lpush(config.REDIS_JOB_QUEUE_KEY, job_json)
                else:
                    # Upstash REST client (sync)
                    client.lpush(config.REDIS_JOB_QUEUE_KEY, job_json)
                    
                logger.info(f"Enqueued job: {job_data.get('type', 'unknown')}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to enqueue job: {e}")
            return False
    
    async def dequeue_job(self, timeout: int = 10) -> Optional[Dict[str, Any]]:
        """
        Get job from background processing queue (blocking).
        
        Args:
            timeout: Timeout in seconds for blocking pop
            
        Returns:
            Optional[Dict]: Job data or None if timeout
        """
        try:
            async with self._get_client() as client:
                if hasattr(client, 'connection_pool'):
                    # Direct Redis client (async)
                    result = await client.brpop(config.REDIS_JOB_QUEUE_KEY, timeout=timeout)
                    if result:
                        _, job_json = result
                        return json.loads(job_json)
                else:
                    # Upstash REST client (sync) - use non-blocking pop
                    job_json = client.rpop(config.REDIS_JOB_QUEUE_KEY)
                    if job_json:
                        return json.loads(job_json)
                        
                return None
                
        except Exception as e:
            logger.error(f"Failed to dequeue job: {e}")
            return None
    
    # ── Health Check Methods ───────────────────────────────────────────
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform comprehensive health check.
        
        Returns:
            Dict: Health status information
        """
        health_info = {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "redis_connection": False,
            "upstash_rest": False,
            "response_time_ms": None
        }
        
        try:
            start_time = datetime.now(timezone.utc)
            
            # Test Upstash REST connection
            if self._upstash_client:
                result = self._upstash_client.ping()
                health_info["upstash_rest"] = (result == "PONG")
            
            # Test direct Redis connection if available
            if self._redis_client:
                try:
                    result = await self._redis_client.ping()
                    health_info["redis_connection"] = bool(result)
                except Exception as e:
                    logger.warning(f"Direct Redis health check failed: {e}")
                    health_info["redis_connection"] = False
            
            end_time = datetime.now(timezone.utc)
            health_info["response_time_ms"] = int((end_time - start_time).total_seconds() * 1000)
            
            # Overall status
            if not health_info["upstash_rest"] and not health_info["redis_connection"]:
                health_info["status"] = "unhealthy"
            
        except Exception as e:
            health_info["status"] = "unhealthy"
            health_info["error"] = str(e)
            logger.error(f"Redis health check failed: {e}")
        
        return health_info

# ── Global Redis Service Instance ──────────────────────────────────────

# Global instance - initialized on first use
_redis_service: Optional[RedisService] = None

async def get_redis_service() -> RedisService:
    """Get global Redis service instance (singleton pattern)."""
    global _redis_service
    if _redis_service is None:
        _redis_service = RedisService()
        await _redis_service.initialize()
    return _redis_service

async def close_redis_service() -> None:
    """Close global Redis service instance."""
    global _redis_service
    if _redis_service:
        await _redis_service.close()
        _redis_service = None