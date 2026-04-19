"""
Database Models using SQLAlchemy
===============================
Defines all database models with proper relationships and constraints.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional

from sqlalchemy import (
    Boolean, Column, Date, DateTime, ForeignKey, Integer, JSON, String, Text,
    UniqueConstraint, CheckConstraint, create_engine, text
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.sql import func

Base = declarative_base()

# Enums
class PlanType(str, Enum):
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"

class SubscriptionStatus(str, Enum):
    ACTIVE = "active"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    PAST_DUE = "past_due"

class SourceType(str, Enum):
    YOUTUBE = "youtube"
    PLAYLIST = "playlist"
    CHANNEL = "channel"

class SourceStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

# Models
class UserProfile(Base):
    __tablename__ = "user_profiles"
    
    uid = Column(String, primary_key=True)
    email = Column(String)
    display_name = Column(String)
    photo_url = Column(String)
    plan = Column(String, default=PlanType.FREE.value)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    knowledge_bases = relationship("KnowledgeBase", back_populates="user", cascade="all, delete-orphan")
    sources = relationship("Source", back_populates="user", cascade="all, delete-orphan")
    chat_sessions = relationship("ChatSession", back_populates="user", cascade="all, delete-orphan")
    usage_logs = relationship("UsageLog", back_populates="user", cascade="all, delete-orphan")
    subscription = relationship("UserSubscription", back_populates="user", uselist=False, cascade="all, delete-orphan")
    daily_usage = relationship("DailyUsage", back_populates="user", cascade="all, delete-orphan")

class KnowledgeBase(Base):
    __tablename__ = "knowledge_bases"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String, ForeignKey("user_profiles.uid", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Constraints
    __table_args__ = (
        UniqueConstraint("user_id", "name", name="uq_user_kb_name"),
    )
    
    # Relationships
    user = relationship("UserProfile", back_populates="knowledge_bases")
    sources = relationship("Source", back_populates="knowledge_base", cascade="all, delete-orphan")

class Source(Base):
    __tablename__ = "sources"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("user_profiles.uid", ondelete="CASCADE"), nullable=False)
    kb_id = Column(UUID(as_uuid=True), ForeignKey("knowledge_bases.id", ondelete="CASCADE"), nullable=False)
    kb_name = Column(String, nullable=False)  # for ChromaDB lookups
    url = Column(String, nullable=False)
    title = Column(String)
    source_type = Column(String, default=SourceType.YOUTUBE.value)
    status = Column(String, default=SourceStatus.PENDING.value)
    video_count = Column(Integer, default=0)
    chunk_count = Column(Integer, default=0)
    error_message = Column(Text)
    intro_cache = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("UserProfile", back_populates="sources")
    knowledge_base = relationship("KnowledgeBase", back_populates="sources")
    chat_sessions = relationship("ChatSession", back_populates="source", cascade="all, delete-orphan")

class ChatSession(Base):
    __tablename__ = "chat_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String, ForeignKey("user_profiles.uid", ondelete="CASCADE"), nullable=False)
    source_id = Column(String, ForeignKey("sources.id", ondelete="CASCADE"), nullable=False)
    kb_name = Column(String, nullable=False)
    source_title = Column(String)
    messages = Column(JSON, default=list)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("UserProfile", back_populates="chat_sessions")
    source = relationship("Source", back_populates="chat_sessions")

class UsageLog(Base):
    __tablename__ = "usage_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String, ForeignKey("user_profiles.uid", ondelete="CASCADE"), nullable=False)
    action = Column(String, nullable=False)
    resource_id = Column(String)
    event_metadata = Column(JSON)  # Renamed from 'metadata' to avoid conflict
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("UserProfile", back_populates="usage_logs")

class UserSubscription(Base):
    __tablename__ = "user_subscriptions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String, ForeignKey("user_profiles.uid", ondelete="CASCADE"), nullable=False, unique=True)
    plan_type = Column(String, nullable=False, default=PlanType.FREE.value)
    status = Column(String, nullable=False, default=SubscriptionStatus.ACTIVE.value)
    stripe_customer_id = Column(String)
    stripe_subscription_id = Column(String)
    current_period_start = Column(DateTime(timezone=True))
    current_period_end = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Constraints
    __table_args__ = (
        CheckConstraint(
            plan_type.in_([PlanType.FREE.value, PlanType.PRO.value, PlanType.ENTERPRISE.value]),
            name="ck_plan_type"
        ),
        CheckConstraint(
            status.in_([
                SubscriptionStatus.ACTIVE.value,
                SubscriptionStatus.CANCELLED.value,
                SubscriptionStatus.EXPIRED.value,
                SubscriptionStatus.PAST_DUE.value
            ]),
            name="ck_subscription_status"
        ),
    )
    
    # Relationships
    user = relationship("UserProfile", back_populates="subscription")

class DailyUsage(Base):
    __tablename__ = "daily_usage"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String, ForeignKey("user_profiles.uid", ondelete="CASCADE"), nullable=False)
    date = Column(Date, nullable=False)
    videos_ingested = Column(Integer, default=0)
    questions_asked = Column(Integer, default=0)
    summaries_generated = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Constraints
    __table_args__ = (
        UniqueConstraint("user_id", "date", name="uq_user_date"),
    )
    
    # Relationships
    user = relationship("UserProfile", back_populates="daily_usage")

class PlanFeature(Base):
    __tablename__ = "plan_features"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plan_type = Column(String, nullable=False)
    feature_name = Column(String, nullable=False)
    feature_value = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Constraints
    __table_args__ = (
        UniqueConstraint("plan_type", "feature_name", name="uq_plan_feature"),
    )