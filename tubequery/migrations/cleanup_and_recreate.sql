-- Step 1: Drop existing tables and function (if they exist)
DROP TABLE IF EXISTS daily_usage CASCADE;
DROP TABLE IF EXISTS user_subscriptions CASCADE;
DROP TABLE IF EXISTS plan_features CASCADE;
DROP FUNCTION IF EXISTS update_daily_usage(TEXT, TEXT);
DROP FUNCTION IF EXISTS update_daily_usage(UUID, TEXT);

-- Step 2: Create user subscriptions table (user_id is TEXT to match Firebase UID)
CREATE TABLE user_subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
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

-- Step 3: Create usage tracking table (user_id is TEXT to match Firebase UID)
CREATE TABLE daily_usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    date DATE NOT NULL,
    videos_ingested INTEGER DEFAULT 0,
    questions_asked INTEGER DEFAULT 0,
    summaries_generated INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, date)
);

-- Step 4: Create plan features table
CREATE TABLE plan_features (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plan_type TEXT NOT NULL,
    feature_name TEXT NOT NULL,
    feature_value TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(plan_type, feature_name)
);

-- Step 5: Insert default plan features
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

-- Step 6: Add user_id to sources table if not exists (TEXT to match Firebase UID)
ALTER TABLE sources ADD COLUMN IF NOT EXISTS user_id TEXT;

-- Step 7: Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_user_subscriptions_user_id ON user_subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_daily_usage_user_date ON daily_usage(user_id, date);
CREATE INDEX IF NOT EXISTS idx_sources_user_created ON sources(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_usage_logs_user_action_date ON usage_logs(user_id, action, created_at);

-- Step 8: Create function to update daily usage (user_id is TEXT)
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
