"""
Subscription Service
===================
Handles user plan limits, usage tracking, and upgrade enforcement.
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

# Plan configurations
PLAN_LIMITS = {
    PlanType.FREE: PlanLimits(
        videos_per_day=3,
        questions_per_day=20,
        history_retention_days=7,
        max_concurrent_videos=5,
        advanced_features=False,
        priority_processing=False,
        export_enabled=False
    ),
    PlanType.PRO: PlanLimits(
        videos_per_day=50,
        questions_per_day=500,
        history_retention_days=365,
        max_concurrent_videos=100,
        advanced_features=True,
        priority_processing=True,
        export_enabled=True
    ),
    PlanType.ENTERPRISE: PlanLimits(
        videos_per_day=1000,
        questions_per_day=10000,
        history_retention_days=-1,  # unlimited
        max_concurrent_videos=1000,
        advanced_features=True,
        priority_processing=True,
        export_enabled=True
    )
}

class SubscriptionService:
    def __init__(self, db):
        self.db = db
    
    async def get_user_plan(self, user_id: str) -> Tuple[PlanType, Dict]:
        """Get user's current plan and subscription details."""
        try:
            # Don't use .single() which causes 406 error, just get the first result
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
    
    async def get_daily_usage(self, user_id: str) -> Dict[str, int]:
        """Get user's usage for the current day from permanent daily_usage table."""
        today = datetime.now(timezone.utc).date()
        
        try:
            # Get usage from permanent daily_usage table
            usage_result = self.db.table("daily_usage").select("*").eq("user_id", user_id).eq("date", today.isoformat()).execute()
            
            if usage_result.data and len(usage_result.data) > 0:
                usage_data = usage_result.data[0]
                return {
                    "videos_today": usage_data.get("videos_ingested", 0),
                    "questions_today": usage_data.get("questions_asked", 0),
                    "date": today.isoformat()
                }
            else:
                # No usage record for today yet
                return {
                    "videos_today": 0,
                    "questions_today": 0,
                    "date": today.isoformat()
                }
        except Exception as e:
            logger.error(f"Error getting daily usage from daily_usage table: {e}")
            # Fallback: count from usage_events table
            try:
                start_of_day = datetime.combine(today, datetime.min.time()).replace(tzinfo=timezone.utc)
                end_of_day = start_of_day + timedelta(days=1)
                
                # Count questions from usage_events
                questions_result = self.db.table("usage_events").select("id").eq("user_id", user_id).eq("event_type", "chat").gte("created_at", start_of_day.isoformat()).lt("created_at", end_of_day.isoformat()).execute()
                questions_today = len(questions_result.data) if questions_result.data else 0
                
                # Count videos from usage_events (ingest events)
                videos_result = self.db.table("usage_events").select("id").eq("user_id", user_id).eq("event_type", "ingest").gte("created_at", start_of_day.isoformat()).lt("created_at", end_of_day.isoformat()).execute()
                videos_today = len(videos_result.data) if videos_result.data else 0
                
                logger.info(f"Using fallback usage counting from usage_events for user {user_id}: {videos_today} videos, {questions_today} questions")
                
                return {
                    "videos_today": videos_today,
                    "questions_today": questions_today,
                    "date": today.isoformat()
                }
            except Exception as fallback_error:
                logger.error(f"Fallback usage counting also failed: {fallback_error}")
                return {"videos_today": 0, "questions_today": 0, "date": today.isoformat()}
    
    async def check_video_limit(self, user_id: str) -> Tuple[bool, Dict]:
        """Check if user can ingest another video."""
        plan_type, plan_data = await self.get_user_plan(user_id)
        usage = await self.get_daily_usage(user_id)
        limits = PLAN_LIMITS[plan_type]
        
        can_ingest = usage["videos_today"] < limits.videos_per_day
        
        return can_ingest, {
            "allowed": can_ingest,
            "used": usage["videos_today"],
            "limit": limits.videos_per_day,
            "plan": plan_type.value,
            "resets_at": self._get_next_reset_time().isoformat()
        }
    
    async def check_question_limit(self, user_id: str) -> Tuple[bool, Dict]:
        """Check if user can ask another question."""
        plan_type, plan_data = await self.get_user_plan(user_id)
        usage = await self.get_daily_usage(user_id)
        limits = PLAN_LIMITS[plan_type]
        
        can_ask = usage["questions_today"] < limits.questions_per_day
        
        return can_ask, {
            "allowed": can_ask,
            "used": usage["questions_today"],
            "limit": limits.questions_per_day,
            "plan": plan_type.value,
            "resets_at": self._get_next_reset_time().isoformat()
        }
    
    async def get_user_limits_summary(self, user_id: str) -> Dict:
        """Get comprehensive user limits and usage summary."""
        plan_type, plan_data = await self.get_user_plan(user_id)
        usage = await self.get_daily_usage(user_id)
        limits = PLAN_LIMITS[plan_type]
        
        # Get total videos count
        total_videos_result = self.db.table("sources").select("id").eq("user_id", user_id).execute()
        total_videos = len(total_videos_result.data) if total_videos_result.data else 0
        
        return {
            "plan": {
                "type": plan_type.value,
                "status": plan_data.get("status", "active"),
                "features": {
                    "advanced_summaries": limits.advanced_features,
                    "priority_processing": limits.priority_processing,
                    "export_enabled": limits.export_enabled,
                    "history_retention_days": limits.history_retention_days
                }
            },
            "usage": {
                "videos_today": usage["videos_today"],
                "videos_limit": limits.videos_per_day,
                "questions_today": usage["questions_today"],
                "questions_limit": limits.questions_per_day,
                "total_videos": total_videos,
                "max_concurrent_videos": limits.max_concurrent_videos
            },
            "resets_at": self._get_next_reset_time().isoformat(),
            "upgrade_required": plan_type == PlanType.FREE and (
                usage["videos_today"] >= limits.videos_per_day or 
                usage["questions_today"] >= limits.questions_per_day
            )
        }
    
    def _get_next_reset_time(self) -> datetime:
        """Get the next daily reset time (midnight UTC)."""
        now = datetime.now(timezone.utc)
        tomorrow = now.date() + timedelta(days=1)
        return datetime.combine(tomorrow, datetime.min.time()).replace(tzinfo=timezone.utc)
    
    async def increment_usage(self, user_id: str, action: str):
        """Increment usage count for a specific action (ingest, chat, summary). Async-safe."""
        logger.info(f"Attempting to increment {action} usage for user {user_id}")
        # Run the sync database operation in a thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, partial(self._increment_usage_sync, user_id, action))
    
    def _increment_usage_sync(self, user_id: str, action: str):
        """Internal synchronous implementation of increment_usage."""
        today = datetime.now(timezone.utc).date()
        
        try:
            # Try to get existing record from daily_usage table
            result = self.db.table("daily_usage").select("*").eq("user_id", user_id).eq("date", today.isoformat()).execute()
            
            if result.data and len(result.data) > 0:
                # Update existing record
                existing = result.data[0]
                updates = {}
                
                if action == "ingest":
                    updates["videos_ingested"] = existing.get("videos_ingested", 0) + 1
                elif action == "chat":
                    updates["questions_asked"] = existing.get("questions_asked", 0) + 1
                elif action == "summary":
                    updates["summaries_generated"] = existing.get("summaries_generated", 0) + 1
                
                updates["updated_at"] = datetime.now(timezone.utc).isoformat()
                
                self.db.table("daily_usage").update(updates).eq("user_id", user_id).eq("date", today.isoformat()).execute()
                logger.info(f"Updated {action} usage for user {user_id}")
            else:
                # Create new record
                new_record = {
                    "user_id": user_id,
                    "date": today.isoformat(),
                    "videos_ingested": 1 if action == "ingest" else 0,
                    "questions_asked": 1 if action == "chat" else 0,
                    "summaries_generated": 1 if action == "summary" else 0,
                }
                self.db.table("daily_usage").insert(new_record).execute()
                logger.info(f"Created new daily usage record with {action} for user {user_id}")
                
        except Exception as e:
            logger.error(f"Error incrementing usage in daily_usage table: {e}")
            # Fallback: log to usage_events table
            try:
                self.db.table("usage_events").insert({
                    "user_id": user_id,
                    "event_type": action,
                    "source_id": None,
                    "metadata": {"fallback_usage_tracking": True, "date": today.isoformat()},
                }).execute()
                logger.info(f"Logged {action} usage event as fallback for user {user_id}")
            except Exception as fallback_error:
                logger.error(f"Fallback usage logging also failed: {fallback_error}")
    
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

# Upgrade prompts and messaging
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
            "Export conversations"
        ]
    },
    "question_limit": {
        "title": "Daily Question Limit Reached", 
        "message": "You've asked {used} questions today. Upgrade for unlimited questions!",
        "cta": "Upgrade Now",
        "benefits": [
            "Unlimited questions",
            "Advanced AI features",
            "Priority support",
            "Export & sharing"
        ]
    },
    "feature_locked": {
        "title": "Pro Feature",
        "message": "This feature is available in Pro plan. Upgrade to unlock advanced capabilities!",
        "cta": "See Pro Features"
    }
}