"""
Database Service Layer
======================
High-level database operations using SQLAlchemy ORM.
Replaces the raw SQL operations in api/db.py.
"""

from __future__ import annotations

import logging
from datetime import datetime, date, timezone, timedelta
from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy import and_, func, desc
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from models.database import (
    UserProfile, KnowledgeBase, Source, ChatSession, UsageLog,
    UserSubscription, DailyUsage, PlanFeature,
    PlanType, SubscriptionStatus, SourceStatus
)

logger = logging.getLogger(__name__)

class DatabaseService:
    """High-level database operations using SQLAlchemy ORM."""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ── User Management ──────────────────────────────────────────────────
    
    def upsert_user(self, user_id: str, email: Optional[str] = None, display_name: Optional[str] = None) -> UserProfile:
        """Create or update a user profile."""
        user = self.db.query(UserProfile).filter_by(uid=user_id).first()
        
        if user:
            # Update existing user
            if email:
                user.email = email
            if display_name:
                user.display_name = display_name
            user.updated_at = datetime.now(timezone.utc)
        else:
            # Create new user
            user = UserProfile(
                uid=user_id,
                email=email,
                display_name=display_name
            )
            self.db.add(user)
        
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def get_user(self, user_id: str) -> Optional[UserProfile]:
        """Get user by ID."""
        return self.db.query(UserProfile).filter_by(uid=user_id).first()
    
    def ensure_user_with_default_kb(self, user_id: str, email: Optional[str] = None, display_name: Optional[str] = None) -> tuple[UserProfile, KnowledgeBase]:
        """Ensure user exists and has a default knowledge base."""
        user = self.upsert_user(user_id, email, display_name)
        
        # Get or create default KB
        kb = self.db.query(KnowledgeBase).filter_by(user_id=user_id, name="default").first()
        if not kb:
            kb = KnowledgeBase(user_id=user_id, name="default")
            self.db.add(kb)
            self.db.commit()
            self.db.refresh(kb)
        
        return user, kb
    
    # ── Knowledge Base Management ────────────────────────────────────────
    
    def get_or_create_kb(self, user_id: str, name: str) -> KnowledgeBase:
        """Get a KB by name, creating it if it doesn't exist."""
        kb = self.db.query(KnowledgeBase).filter_by(user_id=user_id, name=name).first()
        if not kb:
            kb = KnowledgeBase(user_id=user_id, name=name)
            self.db.add(kb)
            self.db.commit()
            self.db.refresh(kb)
        return kb
    
    def list_kbs(self, user_id: str) -> List[KnowledgeBase]:
        """List all knowledge bases for a user."""
        return self.db.query(KnowledgeBase).filter_by(user_id=user_id).order_by(KnowledgeBase.created_at).all()
    
    def delete_kb(self, kb_id: UUID, user_id: str) -> bool:
        """Delete a knowledge base."""
        kb = self.db.query(KnowledgeBase).filter_by(id=kb_id, user_id=user_id).first()
        if kb:
            self.db.delete(kb)
            self.db.commit()
            return True
        return False
    
    # ── Source Management ────────────────────────────────────────────────
    
    def save_source(self, user_id: str, kb_id: UUID, source_data: Dict[str, Any]) -> Source:
        """Insert or update a source record."""
        source = self.db.query(Source).filter_by(id=source_data["id"]).first()
        
        if source:
            # Update existing source
            for key, value in source_data.items():
                if hasattr(source, key):
                    setattr(source, key, value)
            source.updated_at = datetime.now(timezone.utc)
        else:
            # Create new source
            source = Source(
                user_id=user_id,
                kb_id=kb_id,
                **source_data
            )
            self.db.add(source)
        
        self.db.commit()
        self.db.refresh(source)
        return source
    
    def list_sources(self, user_id: str, kb_id: Optional[UUID] = None) -> List[Source]:
        """List sources for a user, optionally filtered by KB."""
        query = self.db.query(Source).filter_by(user_id=user_id)
        if kb_id:
            query = query.filter_by(kb_id=kb_id)
        return query.order_by(desc(Source.created_at)).all()
    
    def get_source(self, source_id: str, user_id: str) -> Optional[Source]:
        """Get a specific source."""
        return self.db.query(Source).filter_by(id=source_id, user_id=user_id).first()
    
    def delete_source(self, source_id: str, user_id: str) -> bool:
        """Delete a source."""
        source = self.db.query(Source).filter_by(id=source_id, user_id=user_id).first()
        if source:
            self.db.delete(source)
            self.db.commit()
            return True
        return False
    
    # ── Chat Session Management ──────────────────────────────────────────
    
    def list_sessions(self, user_id: str) -> List[ChatSession]:
        """List all chat sessions for a user."""
        return (
            self.db.query(ChatSession)
            .filter_by(user_id=user_id)
            .order_by(desc(ChatSession.updated_at))
            .all()
        )
    
    def get_session(self, session_id: UUID, user_id: str) -> Optional[ChatSession]:
        """Get a specific chat session."""
        return self.db.query(ChatSession).filter_by(id=session_id, user_id=user_id).first()
    
    def create_session(self, user_id: str, source_id: str, source_title: str, kb_name: str) -> ChatSession:
        """Create a new chat session."""
        session = ChatSession(
            user_id=user_id,
            source_id=source_id,
            source_title=source_title,
            kb_name=kb_name,
            messages=[]
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session
    
    def update_session_messages(self, session_id: UUID, user_id: str, messages: List[Dict]) -> Optional[ChatSession]:
        """Update chat session messages."""
        session = self.db.query(ChatSession).filter_by(id=session_id, user_id=user_id).first()
        if session:
            session.messages = messages
            session.updated_at = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(session)
        return session
    
    def delete_session(self, session_id: UUID, user_id: str) -> bool:
        """Delete a chat session."""
        session = self.db.query(ChatSession).filter_by(id=session_id, user_id=user_id).first()
        if session:
            self.db.delete(session)
            self.db.commit()
            return True
        return False
    
    # ── Usage Tracking ───────────────────────────────────────────────────
    
    def log_usage(self, user_id: str, action: str, resource_id: Optional[str] = None, event_metadata: Optional[Dict] = None) -> None:
        """Log a usage event."""
        try:
            usage_log = UsageLog(
                user_id=user_id,
                action=action,
                resource_id=resource_id,
                event_metadata=event_metadata or {}
            )
            self.db.add(usage_log)
            self.db.commit()
        except Exception as e:
            logger.warning(f"Failed to log usage event: {e}")
            self.db.rollback()
    
    def get_daily_usage(self, user_id: str, target_date: Optional[date] = None) -> DailyUsage:
        """Get or create daily usage record for a specific date."""
        if target_date is None:
            target_date = datetime.now(timezone.utc).date()
        
        usage = self.db.query(DailyUsage).filter_by(user_id=user_id, date=target_date).first()
        if not usage:
            usage = DailyUsage(
                user_id=user_id,
                date=target_date,
                videos_ingested=0,
                questions_asked=0,
                summaries_generated=0
            )
            self.db.add(usage)
            self.db.commit()
            self.db.refresh(usage)
        
        return usage
    
    def increment_daily_usage(self, user_id: str, action: str) -> DailyUsage:
        """Increment daily usage for a specific action."""
        usage = self.get_daily_usage(user_id)
        
        if action == "ingest":
            usage.videos_ingested += 1
        elif action == "chat":
            usage.questions_asked += 1
        elif action == "summary":
            usage.summaries_generated += 1
        
        usage.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(usage)
        return usage
    
    # ── Subscription Management ──────────────────────────────────────────
    
    def get_user_subscription(self, user_id: str) -> UserSubscription:
        """Get user subscription, creating default free plan if none exists."""
        subscription = self.db.query(UserSubscription).filter_by(user_id=user_id).first()
        if not subscription:
            subscription = UserSubscription(
                user_id=user_id,
                plan_type=PlanType.FREE.value,
                status=SubscriptionStatus.ACTIVE.value
            )
            self.db.add(subscription)
            self.db.commit()
            self.db.refresh(subscription)
        return subscription
    
    def update_subscription(self, user_id: str, plan_type: str, status: str, **kwargs) -> UserSubscription:
        """Update user subscription."""
        subscription = self.get_user_subscription(user_id)
        subscription.plan_type = plan_type
        subscription.status = status
        
        for key, value in kwargs.items():
            if hasattr(subscription, key):
                setattr(subscription, key, value)
        
        subscription.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(subscription)
        return subscription
    
    # ── Plan Features ────────────────────────────────────────────────────
    
    def get_plan_features(self, plan_type: str) -> Dict[str, str]:
        """Get all features for a plan type."""
        features = self.db.query(PlanFeature).filter_by(plan_type=plan_type).all()
        return {f.feature_name: f.feature_value for f in features}
    
    def seed_plan_features(self) -> None:
        """Seed default plan features."""
        features_data = [
            # Free plan
            ("free", "videos_per_day", "3"),
            ("free", "questions_per_day", "20"),
            ("free", "history_retention_days", "7"),
            ("free", "max_concurrent_videos", "5"),
            ("free", "advanced_features", "false"),
            ("free", "priority_processing", "false"),
            ("free", "export_enabled", "false"),
            
            # Pro plan
            ("pro", "videos_per_day", "50"),
            ("pro", "questions_per_day", "500"),
            ("pro", "history_retention_days", "365"),
            ("pro", "max_concurrent_videos", "100"),
            ("pro", "advanced_features", "true"),
            ("pro", "priority_processing", "true"),
            ("pro", "export_enabled", "true"),
            
            # Enterprise plan
            ("enterprise", "videos_per_day", "1000"),
            ("enterprise", "questions_per_day", "10000"),
            ("enterprise", "history_retention_days", "-1"),
            ("enterprise", "max_concurrent_videos", "1000"),
            ("enterprise", "advanced_features", "true"),
            ("enterprise", "priority_processing", "true"),
            ("enterprise", "export_enabled", "true"),
        ]
        
        for plan_type, feature_name, feature_value in features_data:
            existing = self.db.query(PlanFeature).filter_by(
                plan_type=plan_type, 
                feature_name=feature_name
            ).first()
            
            if not existing:
                feature = PlanFeature(
                    plan_type=plan_type,
                    feature_name=feature_name,
                    feature_value=feature_value
                )
                self.db.add(feature)
        
        self.db.commit()
    
    # ── Data Cleanup ─────────────────────────────────────────────────────
    
    def cleanup_old_data(self, user_id: str, retention_days: int) -> None:
        """Clean up old data based on retention policy."""
        if retention_days == -1:
            return  # Unlimited retention
        
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=retention_days)
        
        try:
            # Delete old chat sessions
            self.db.query(ChatSession).filter(
                and_(
                    ChatSession.user_id == user_id,
                    ChatSession.created_at < cutoff_date
                )
            ).delete()
            
            # Delete old usage logs
            self.db.query(UsageLog).filter(
                and_(
                    UsageLog.user_id == user_id,
                    UsageLog.created_at < cutoff_date
                )
            ).delete()
            
            self.db.commit()
            logger.info(f"Cleaned up old data for user {user_id}")
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")
            self.db.rollback()