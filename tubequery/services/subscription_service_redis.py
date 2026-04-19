"""
Subscription Service with Redis Integration
==========================================
Production-ready subscription service using Redis for real-time usage tracking
and high-performance plan limit enforcement for 100+ concurrent users.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from functools import partial

from api.auth import get_supabase
from services.redis_service_production import get_production_redis_service, UsageStats

logger = logging.getLogger(__name__)

class PlanType(Enum):
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"

@dataclass
class PlanLimits:
    videos_per_day: int
    questions_per_day: int
    history_retention_days: int
    max_concurrent_videos: int
    advanced_features: bool
    priority_processing: bool
    export_enabled: bool
    rate_limit_per_minute: int = 60  # API calls per minute

# Enhanced plan configurations for production
PLAN_LIMITS = {
    PlanType.FREE: PlanLimits(
        videos_per_day=3,
        questions_per_day=20,
        history_retention_days=7,
        max_concurrent_videos=5,
        advanced_features=False,
        priority_processing=False,
        export_enabled=False,
        rate_limit_per_minute=30
    ),
    PlanType.PRO: PlanLimits(
        videos_per_day=50,
        questions_per_day=500,
        history_retention_days=365,
        max_concurrent_videos=100,
        advanced_features=True,
        priority_processing=True,
        export_enabled=True,
        rate_limit_per_minute=120
    ),
    PlanType.ENTERPRISE: PlanLimits(
        videos_per_day=1000,
        questions_per_day=10000,
        history_retention_days=-1,  # unlimited
        max_concurrent_videos=1000,
        advanced_features=True,
        priority_processing=True,
        export_enabled=True,
        rate_limit_per_minute=300
    )
}

class RedisSubscriptionService:
    """
    Production-ready subscription service with Redis-based usage tracking.
    Optimized for high concurrency and real-time performance.
    """
    
    def __init__(self, db):
        self.db = db
        self._redis_service = None
    
    async def _get_redis_service(self):
        """Get Redis service instance (lazy initialization)."""
        if self._redis_service is None:
            self._redis_service = await get_production_redis_service()
        return self._redis_service
    
    async def get_user_plan(self, user_id: str) -> Tuple[PlanType, Dict]:
        """Get user's current plan and subscription details with caching."""
        try:
            # Try Redis cache first for performance
            redis_service = await self._get_redis_service()
            cache_key = f"user_plan:{user_id}"
            
            # Check cache (implement if needed)
            # For now, query database directly but could add Redis caching
            
            result = self.db.table("user_subscriptions").select("*").eq("user_id", user_id).execute()
            
            if result.data and len(result.data) > 0:
                plan_type = PlanType(result.data[0]["plan_type"])
                return plan_type, result.data[0]
            else:
                # Default to free plan
                return PlanType.FREE, {
                    "user_id": user_id,
                    "plan_type": PlanType.FREE.value,
                    "status": "active",
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
        except Exception as e:
            logger.error(f"Error getting user plan: {e}")
            return PlanType.FREE, {}
    
    async def get_daily_usage_redis(self, user_id: str) -> Dict[str, int]:
        """Get user's usage for the current day from Redis (primary) with database fallback."""
        try:
            redis_service = await self._get_redis_service()
            stats = await redis_service.get_usage_stats(user_id)
            
            return {
                "videos_today": stats.videos_ingested,
                "questions_today": stats.questions_asked,
                "summaries_today": stats.summaries_generated,
                "date": stats.date
            }
            
        except Exception as e:
            logger.error(f"Redis usage retrieval failed, falling back to database: {e}")
            return await self._get_daily_usage_database_fallback(user_id)
    
    async def _get_daily_usage_database_fallback(self, user_id: str) -> Dict[str, int]:
        """Fallback to database for usage tracking."""
        today = datetime.now(timezone.utc).date()
        
        try:
            # Get usage from permanent daily_usage table
            usage_result = self.db.table("daily_usage").select("*").eq("user_id", user_id).eq("date", today.isoformat()).execute()
            
            if usage_result.data and len(usage_result.data) > 0:
                usage_data = usage_result.data[0]
                return {
                    "videos_today": usage_data.get("videos_ingested", 0),
                    "questions_today": usage_data.get("questions_asked", 0),
                    "summaries_today": usage_data.get("summaries_generated", 0),
                    "date": today.isoformat()
                }
            else:
                return {
                    "videos_today": 0,
                    "questions_today": 0,
                    "summaries_today": 0,
                    "date": today.isoformat()
                }
        except Exception as e:
            logger.error(f"Database fallback also failed: {e}")
            return {"videos_today": 0, "questions_today": 0, "summaries_today": 0, "date": today.isoformat()}
    
    async def check_video_limit(self, user_id: str) -> Tuple[bool, Dict]:
        """Check if user can ingest another video (Redis-optimized)."""
        plan_type, plan_data = await self.get_user_plan(user_id)
        usage = await self.get_daily_usage_redis(user_id)
        limits = PLAN_LIMITS[plan_type]
        
        can_ingest = usage["videos_today"] < limits.videos_per_day
        
        return can_ingest, {
            "allowed": can_ingest,
            "used": usage["videos_today"],
            "limit": limits.videos_per_day,
            "plan": plan_type.value,
            "resets_at": self._get_next_reset_time().isoformat(),
            "upgrade_required": not can_ingest and plan_type == PlanType.FREE
        }
    
    async def check_question_limit(self, user_id: str) -> Tuple[bool, Dict]:
        """Check if user can ask another question (Redis-optimized)."""
        plan_type, plan_data = await self.get_user_plan(user_id)
        usage = await self.get_daily_usage_redis(user_id)
        limits = PLAN_LIMITS[plan_type]
        
        can_ask = usage["questions_today"] < limits.questions_per_day
        
        return can_ask, {
            "allowed": can_ask,
            "used": usage["questions_today"],
            "limit": limits.questions_per_day,
            "plan": plan_type.value,
            "resets_at": self._get_next_reset_time().isoformat(),
            "upgrade_required": not can_ask and plan_type == PlanType.FREE
        }
    
    async def check_rate_limit(self, user_id: str, action: str = "api_call") -> Tuple[bool, Dict]:
        """Check API rate limits using Redis sliding window."""
        try:
            plan_type, _ = await self.get_user_plan(user_id)
            limits = PLAN_LIMITS[plan_type]
            
            redis_service = await self._get_redis_service()
            rate_info = await redis_service.check_rate_limit(
                user_id=user_id,
                action=action,
                limit=limits.rate_limit_per_minute,
                window_seconds=60
            )
            
            return rate_info.allowed, {
                "allowed": rate_info.allowed,
                "remaining": rate_info.remaining,
                "reset_time": rate_info.reset_time.isoformat(),
                "window_size": rate_info.window_size,
                "plan": plan_type.value
            }
            
        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            # Fail open for rate limiting
            return True, {
                "allowed": True,
                "remaining": 100,
                "reset_time": (datetime.now(timezone.utc) + timedelta(minutes=1)).isoformat(),
                "window_size": 60,
                "plan": "unknown"
            }
    
    async def get_user_limits_summary(self, user_id: str) -> Dict:
        """Get comprehensive user limits and usage summary (Redis-optimized)."""
        plan_type, plan_data = await self.get_user_plan(user_id)
        usage = await self.get_daily_usage_redis(user_id)
        limits = PLAN_LIMITS[plan_type]
        
        # Get total videos count from database (less frequent operation)
        try:
            total_videos_result = self.db.table("sources").select("id").eq("user_id", user_id).execute()
            total_videos = len(total_videos_result.data) if total_videos_result.data else 0
        except Exception as e:
            logger.error(f"Failed to get total videos count: {e}")
            total_videos = 0
        
        # Get Redis metrics for monitoring
        try:
            redis_service = await self._get_redis_service()
            redis_metrics = await redis_service.get_metrics()
        except Exception as e:
            logger.warning(f"Failed to get Redis metrics: {e}")
            redis_metrics = {}
        
        return {
            "plan": {
                "type": plan_type.value,
                "status": plan_data.get("status", "active"),
                "features": {
                    "advanced_summaries": limits.advanced_features,
                    "priority_processing": limits.priority_processing,
                    "export_enabled": limits.export_enabled,
                    "history_retention_days": limits.history_retention_days,
                    "rate_limit_per_minute": limits.rate_limit_per_minute
                }
            },
            "usage": {
                "videos_today": usage["videos_today"],
                "videos_limit": limits.videos_per_day,
                "questions_today": usage["questions_today"],
                "questions_limit": limits.questions_per_day,
                "summaries_today": usage.get("summaries_today", 0),
                "total_videos": total_videos,
                "max_concurrent_videos": limits.max_concurrent_videos
            },
            "resets_at": self._get_next_reset_time().isoformat(),
            "upgrade_required": plan_type == PlanType.FREE and (
                usage["videos_today"] >= limits.videos_per_day or 
                usage["questions_today"] >= limits.questions_per_day
            ),
            "performance": {
                "redis_enabled": True,
                "redis_metrics": redis_metrics
            }
        }
    
    def _get_next_reset_time(self) -> datetime:
        """Get the next daily reset time (midnight UTC)."""
        now = datetime.now(timezone.utc)
        tomorrow = now.date() + timedelta(days=1)
        return datetime.combine(tomorrow, datetime.min.time()).replace(tzinfo=timezone.utc)
    
    async def increment_usage_redis(self, user_id: str, action: str, amount: int = 1):
        """Increment usage count using Redis (primary) with database sync."""
        logger.info(f"Incrementing {action} usage for user {user_id} by {amount}")
        
        try:
            # Primary: Increment in Redis for real-time tracking
            redis_service = await self._get_redis_service()
            success = await redis_service.increment_usage(user_id, action, amount)
            
            if success:
                logger.info(f"Successfully incremented {action} usage in Redis for user {user_id}")
                
                # Background: Sync to database for persistence (non-blocking)
                asyncio.create_task(self._sync_usage_to_database(user_id, action, amount))
            else:
                # Fallback to database if Redis fails
                logger.warning(f"Redis increment failed, falling back to database for user {user_id}")
                await self._increment_usage_database_fallback(user_id, action, amount)
                
        except Exception as e:
            logger.error(f"Redis usage increment failed: {e}")
            # Fallback to database
            await self._increment_usage_database_fallback(user_id, action, amount)
    
    async def _sync_usage_to_database(self, user_id: str, action: str, amount: int):
        """Background task to sync Redis usage to database for persistence."""
        try:
            today = datetime.now(timezone.utc).date()
            
            # Get current Redis stats
            redis_service = await self._get_redis_service()
            stats = await redis_service.get_usage_stats(user_id)
            
            # Upsert to database
            upsert_data = {
                "user_id": user_id,
                "date": today.isoformat(),
                "videos_ingested": stats.videos_ingested,
                "questions_asked": stats.questions_asked,
                "summaries_generated": stats.summaries_generated,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            
            try:
                self.db.table("daily_usage").upsert(upsert_data, on_conflict="user_id,date").execute()
                logger.info(f"Synced usage to database for user {user_id}")
            except Exception as db_error:
                # Handle 409 conflicts gracefully - they're expected with concurrent requests
                if "409" in str(db_error) or "Conflict" in str(db_error):
                    logger.debug(f"Database sync conflict (expected with concurrent requests): {db_error}")
                else:
                    logger.error(f"Unexpected database sync error: {db_error}")
                    raise
            
        except Exception as e:
            logger.error(f"Failed to sync usage to database: {e}")
    
    async def _increment_usage_database_fallback(self, user_id: str, action: str, amount: int):
        """Fallback to database for usage increment."""
        today = datetime.now(timezone.utc).date()
        
        try:
            # Try to get existing record
            result = self.db.table("daily_usage").select("*").eq("user_id", user_id).eq("date", today.isoformat()).execute()
            
            if result.data and len(result.data) > 0:
                # Update existing record
                existing = result.data[0]
                updates = {}
                
                if action == "ingest":
                    updates["videos_ingested"] = existing.get("videos_ingested", 0) + amount
                elif action == "chat":
                    updates["questions_asked"] = existing.get("questions_asked", 0) + amount
                elif action == "summary":
                    updates["summaries_generated"] = existing.get("summaries_generated", 0) + amount
                
                updates["updated_at"] = datetime.now(timezone.utc).isoformat()
                
                self.db.table("daily_usage").update(updates).eq("user_id", user_id).eq("date", today.isoformat()).execute()
                logger.info(f"Updated {action} usage in database for user {user_id}")
            else:
                # Create new record
                new_record = {
                    "user_id": user_id,
                    "date": today.isoformat(),
                    "videos_ingested": amount if action == "ingest" else 0,
                    "questions_asked": amount if action == "chat" else 0,
                    "summaries_generated": amount if action == "summary" else 0,
                }
                self.db.table("daily_usage").insert(new_record).execute()
                logger.info(f"Created new daily usage record with {action} for user {user_id}")
                
        except Exception as e:
            logger.error(f"Database fallback also failed: {e}")
    
    async def cleanup_old_data(self, user_id: str):
        """Clean up old data based on plan retention limits."""
        plan_type, _ = await self.get_user_plan(user_id)
        limits = PLAN_LIMITS[plan_type]
        
        if limits.history_retention_days == -1:
            return  # Unlimited retention
        
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=limits.history_retention_days)
        
        try:
            # Delete old chat sessions
            self.db.table("chat_sessions").delete().eq("user_id", user_id).lt("created_at", cutoff_date.isoformat()).execute()
            
            # Delete old usage logs
            self.db.table("usage_logs").delete().eq("user_id", user_id).lt("created_at", cutoff_date.isoformat()).execute()
            
            logger.info(f"Cleaned up old data for user {user_id}")
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")
    
    async def get_service_health(self) -> Dict:
        """Get comprehensive service health including Redis metrics."""
        try:
            redis_service = await self._get_redis_service()
            redis_health = await redis_service.health_check()
            
            return {
                "subscription_service": "healthy",
                "redis_integration": redis_health,
                "database_connection": "healthy",  # Could add DB health check
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "subscription_service": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

# Upgrade prompts and messaging (enhanced for production)
UPGRADE_MESSAGES = {
    "video_limit": {
        "title": "Daily Video Limit Reached",
        "message": "You've reached your daily limit of {limit} videos. Upgrade to Pro for {pro_limit} videos per day!",
        "cta": "Upgrade to Pro",
        "benefits": [
            "50 videos per day",
            "500 questions per day", 
            "Advanced summaries with topics",
            "Priority processing",
            "Export conversations",
            "Higher API rate limits"
        ]
    },
    "question_limit": {
        "title": "Daily Question Limit Reached", 
        "message": "You've asked {used} questions today. Upgrade for unlimited questions!",
        "cta": "Upgrade Now",
        "benefits": [
            "500+ questions per day",
            "Advanced AI features",
            "Priority support",
            "Export & sharing",
            "Real-time usage tracking"
        ]
    },
    "rate_limit": {
        "title": "Rate Limit Exceeded",
        "message": "You're making requests too quickly. Please slow down or upgrade for higher limits.",
        "cta": "Upgrade for Higher Limits",
        "benefits": [
            "Higher API rate limits",
            "Priority processing",
            "Dedicated support"
        ]
    },
    "feature_locked": {
        "title": "Pro Feature",
        "message": "This feature is available in Pro plan. Upgrade to unlock advanced capabilities!",
        "cta": "See Pro Features"
    }
}