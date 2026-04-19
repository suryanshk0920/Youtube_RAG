-- Complete database schema setup with proper foreign keys and CASCADE DELETE
-- Run this in Supabase SQL Editor

-- Step 1: Ensure user_profiles table exists (don't recreate it)
-- The user_profiles table should already exist with structure like:
CREATE TABLE user_profiles (
    uid TEXT PRIMARY KEY,
    email TEXT,
    display_name TEXT,
    photo_url TEXT,
    plan TEXT DEFAULT 'free',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Step 2: Drop existing tables to recreate with proper foreign keys
DROP TABLE IF EXISTS daily_usage CASCADE;
DROP TABLE IF EXISTS user_subscriptions CASCADE;
DROP TABLE IF EXISTS plan_features CASCADE;
DROP TABLE IF EXISTS usage_logs CASCADE;
DROP TABLE IF EXISTS chat_sessions CASCADE;
DROP TABLE IF EXISTS sources CASCADE;
DROP TABLE IF EXISTS knowledge_bases CASCADE;

-- Step 3: Create knowledge_bases table with proper foreign key to user_profiles
CREATE TABLE knowledge_bases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL REFERENCES user_profiles(uid) ON DELETE CASCADE,
    name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, name)
);

-- Step 4: Create sources table with proper foreign keys
CREATE TABLE sources (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES user_profiles(uid) ON DELETE CASCADE,
    kb_id UUID NOT NULL REFERENCES knowledge_bases(id) ON DELETE CASCADE,
    kb_name TEXT NOT NULL, -- for ChromaDB lookups
    url TEXT NOT NULL,
    title TEXT,
    source_type TEXT DEFAULT 'youtube',
    status TEXT DEFAULT 'pending',
    video_count INTEGER DEFAULT 0,
    chunk_count INTEGER DEFAULT 0,
    error_message TEXT,
    intro_cache JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Step 5: Create chat_sessions table with proper foreign keys
CREATE TABLE chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL REFERENCES user_profiles(uid) ON DELETE CASCADE,
    source_id TEXT NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
    kb_name TEXT NOT NULL,
    source_title TEXT,
    messages JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Step 6: Create usage_logs table with proper foreign key
CREATE TABLE usage_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL REFERENCES user_profiles(uid) ON DELETE CASCADE,
    action TEXT NOT NULL,
    resource_id TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Step 7: Create user_subscriptions table with proper foreign key
CREATE TABLE user_subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL REFERENCES user_profiles(uid) ON DELETE CASCADE,
    plan_type TEXT NOT NULL DEFAULT 'free' CHECK (plan_type IN ('free', 'pro', 'enterprise')),
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'cancelled', 'expired', 'past_due')),
    stripe_customer_id TEXT,
    stripe_subscription_id TEXT,
    current_period_start TIMESTAMP,
    current_period_end TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id)
);

-- Step 8: Create daily_usage table with proper foreign key
CREATE TABLE daily_usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL REFERENCES user_profiles(uid) ON DELETE CASCADE,
    date DATE NOT NULL,
    videos_ingested INTEGER DEFAULT 0,
    questions_asked INTEGER DEFAULT 0,
    summaries_generated INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, date)
);

-- Step 9: Create plan_features table (no foreign key needed - it's reference data)
CREATE TABLE plan_features (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plan_type TEXT NOT NULL,
    feature_name TEXT NOT NULL,
    feature_value TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(plan_type, feature_name)
);

-- Step 10: Insert default plan features
INSERT INTO plan_features (plan_type, feature_name, feature_value) VALUES
-- Free plan
('free', 'videos_per_day', '3'),
('free', 'questions_per_day', '20'),
('free', 'history_retention_days', '7'),
('free', 'max_concurrent_videos', '5'),
('free', 'advanced_features', 'false'),
('free', 'priority_processing', 'false'),
('free', 'export_enabled', 'false'),

-- Pro plan  
('pro', 'videos_per_day', '50'),
('pro', 'questions_per_day', '500'),
('pro', 'history_retention_days', '365'),
('pro', 'max_concurrent_videos', '100'),
('pro', 'advanced_features', 'true'),
('pro', 'priority_processing', 'true'),
('pro', 'export_enabled', 'true'),

-- Enterprise plan
('enterprise', 'videos_per_day', '1000'),
('enterprise', 'questions_per_day', '10000'),
('enterprise', 'history_retention_days', '-1'),
('enterprise', 'max_concurrent_videos', '1000'),
('enterprise', 'advanced_features', 'true'),
('enterprise', 'priority_processing', 'true'),
('enterprise', 'export_enabled', 'true');

-- Step 11: Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_knowledge_bases_user_id ON knowledge_bases(user_id);
CREATE INDEX IF NOT EXISTS idx_sources_user_id ON sources(user_id);
CREATE INDEX IF NOT EXISTS idx_sources_kb_id ON sources(kb_id);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_id ON chat_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_source_id ON chat_sessions(source_id);
CREATE INDEX IF NOT EXISTS idx_usage_logs_user_id ON usage_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_usage_logs_action_date ON usage_logs(user_id, action, created_at);
CREATE INDEX IF NOT EXISTS idx_user_subscriptions_user_id ON user_subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_daily_usage_user_date ON daily_usage(user_id, date);

-- Step 12: Create function to update daily usage
CREATE OR REPLACE FUNCTION update_daily_usage(
    p_user_id TEXT,
    p_action TEXT
) RETURNS VOID AS $$
BEGIN
    INSERT INTO daily_usage (user_id, date, videos_ingested, questions_asked, summaries_generated)
    VALUES (
        p_user_id, 
        CURRENT_DATE,
        CASE WHEN p_action = 'ingest' THEN 1 ELSE 0 END,
        CASE WHEN p_action = 'chat' THEN 1 ELSE 0 END,
        CASE WHEN p_action = 'summary' THEN 1 ELSE 0 END
    )
    ON CONFLICT (user_id, date) 
    DO UPDATE SET
        videos_ingested = daily_usage.videos_ingested + CASE WHEN p_action = 'ingest' THEN 1 ELSE 0 END,
        questions_asked = daily_usage.questions_asked + CASE WHEN p_action = 'chat' THEN 1 ELSE 0 END,
        summaries_generated = daily_usage.summaries_generated + CASE WHEN p_action = 'summary' THEN 1 ELSE 0 END,
        updated_at = NOW();
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Step 13: Create function to ensure user exists in user_profiles and create default KB
CREATE OR REPLACE FUNCTION ensure_user_with_default_kb(
    p_user_id TEXT,
    p_email TEXT DEFAULT NULL,
    p_display_name TEXT DEFAULT NULL
) RETURNS UUID AS $$
DECLARE
    kb_id UUID;
BEGIN
    -- Insert or update user in user_profiles table
    INSERT INTO user_profiles (uid, email, display_name)
    VALUES (p_user_id, p_email, p_display_name)
    ON CONFLICT (uid) 
    DO UPDATE SET
        email = COALESCE(EXCLUDED.email, user_profiles.email),
        display_name = COALESCE(EXCLUDED.display_name, user_profiles.display_name),
        updated_at = NOW();
    
    -- Get or create default knowledge base
    SELECT id INTO kb_id
    FROM knowledge_bases 
    WHERE user_id = p_user_id AND name = 'default';
    
    IF kb_id IS NULL THEN
        INSERT INTO knowledge_bases (user_id, name)
        VALUES (p_user_id, 'default')
        RETURNING id INTO kb_id;
    END IF;
    
    RETURN kb_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;