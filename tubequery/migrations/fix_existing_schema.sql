-- Safe migration for existing database with user_profiles table
-- Run this in Supabase SQL Editor

-- Step 1: Drop existing tables that need to be recreated with foreign keys
-- (Keep user_profiles as it already exists)
DROP TABLE IF EXISTS daily_usage CASCADE;
DROP TABLE IF EXISTS user_subscriptions CASCADE;
DROP TABLE IF EXISTS plan_features CASCADE;
DROP TABLE IF EXISTS usage_logs CASCADE;
DROP TABLE IF EXISTS chat_sessions CASCADE;
DROP TABLE IF EXISTS sources CASCADE;
DROP TABLE IF EXISTS knowledge_bases CASCADE;

-- Step 2: Create knowledge_bases table with proper foreign key to existing user_profiles
CREATE TABLE knowledge_bases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL REFERENCES user_profiles(uid) ON DELETE CASCADE,
    name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, name)
);

-- Step 3: Create sources table with proper foreign keys
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

-- Step 4: Create chat_sessions table with proper foreign keys
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

-- Step 5: Create usage_logs table with proper foreign key
CREATE TABLE usage_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL REFERENCES user_profiles(uid) ON DELETE CASCADE,
    action TEXT NOT NULL,
    resource_id TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Step 6: Create user_subscriptions table with proper foreign key
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

-- Step 7: Create daily_usage table with proper foreign key
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

-- Step 8: Create plan_features table (no foreign key needed - it's reference data)
CREATE TABLE plan_features (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plan_type TEXT NOT NULL,
    feature_name TEXT NOT NULL,
    feature_value TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(plan_type, feature_name)
);

-- Step 9: Insert default plan features
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

-- Step 10: Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_knowledge_bases_user_id ON knowledge_bases(user_id);
CREATE INDEX IF NOT EXISTS idx_sources_user_id ON sources(user_id);
CREATE INDEX IF NOT EXISTS idx_sources_kb_id ON sources(kb_id);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_id ON chat_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_source_id ON chat_sessions(source_id);
CREATE INDEX IF NOT EXISTS idx_usage_logs_user_id ON usage_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_usage_logs_action_date ON usage_logs(user_id, action, created_at);
CREATE INDEX IF NOT EXISTS idx_user_subscriptions_user_id ON user_subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_daily_usage_user_date ON daily_usage(user_id, date);

-- Step 11: Create function to update daily usage
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

-- Step 12: Create function to ensure user exists in user_profiles and create default KB
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

-- Step 13: Enable RLS on all user data tables
ALTER TABLE knowledge_bases ENABLE ROW LEVEL SECURITY;
ALTER TABLE sources ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE usage_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE daily_usage ENABLE ROW LEVEL SECURITY;

-- Step 14: Create RLS policies for Firebase Auth
-- Note: These policies assume you're passing the Firebase UID in the JWT token

-- Knowledge bases: users can only see/modify their own KBs
CREATE POLICY "Users can manage own knowledge bases" ON knowledge_bases
    FOR ALL USING (user_id = current_setting('request.jwt.claims', true)::json->>'sub');

-- Sources: users can only see/modify their own sources
CREATE POLICY "Users can manage own sources" ON sources
    FOR ALL USING (user_id = current_setting('request.jwt.claims', true)::json->>'sub');

-- Chat sessions: users can only see/modify their own sessions
CREATE POLICY "Users can manage own chat sessions" ON chat_sessions
    FOR ALL USING (user_id = current_setting('request.jwt.claims', true)::json->>'sub');

-- Usage logs: users can only see their own usage logs
CREATE POLICY "Users can view own usage logs" ON usage_logs
    FOR SELECT USING (user_id = current_setting('request.jwt.claims', true)::json->>'sub');

-- User subscriptions: users can only see their own subscription
CREATE POLICY "Users can view own subscription" ON user_subscriptions
    FOR SELECT USING (user_id = current_setting('request.jwt.claims', true)::json->>'sub');

-- Daily usage: users can only see their own usage
CREATE POLICY "Users can view own daily usage" ON daily_usage
    FOR SELECT USING (user_id = current_setting('request.jwt.claims', true)::json->>'sub');

-- Step 15: Create service role policies for backend operations
-- These allow your backend (using service role key) to bypass RLS

-- Allow service role to manage all data (for your FastAPI backend)
CREATE POLICY "Service role can manage all data" ON knowledge_bases
    FOR ALL USING (current_setting('role') = 'service_role');

CREATE POLICY "Service role can manage all sources" ON sources
    FOR ALL USING (current_setting('role') = 'service_role');

CREATE POLICY "Service role can manage all sessions" ON chat_sessions
    FOR ALL USING (current_setting('role') = 'service_role');

CREATE POLICY "Service role can manage all usage logs" ON usage_logs
    FOR ALL USING (current_setting('role') = 'service_role');

CREATE POLICY "Service role can manage all subscriptions" ON user_subscriptions
    FOR ALL USING (current_setting('role') = 'service_role');

CREATE POLICY "Service role can manage all daily usage" ON daily_usage
    FOR ALL USING (current_setting('role') = 'service_role');