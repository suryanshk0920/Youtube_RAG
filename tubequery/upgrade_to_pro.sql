-- Upgrade User to Pro Plan
-- Replace 'YOUR_USER_ID' with your actual Firebase user ID

-- Step 1: Check current user status
SELECT 
    uid,
    email,
    plan,
    created_at
FROM user_profiles
WHERE uid = 'YOUR_USER_ID';

-- Step 2: Check if subscription exists
SELECT * FROM user_subscriptions WHERE user_id = 'YOUR_USER_ID';

-- Step 3: Create or update Pro subscription
INSERT INTO user_subscriptions (
    user_id,
    plan_type,
    status,
    current_period_start,
    current_period_end,
    cancel_at_period_end
)
VALUES (
    'YOUR_USER_ID',
    'pro',
    'active',
    NOW(),
    NOW() + INTERVAL '30 days',
    false
)
ON CONFLICT (user_id) 
DO UPDATE SET
    plan_type = 'pro',
    status = 'active',
    current_period_start = NOW(),
    current_period_end = NOW() + INTERVAL '30 days',
    cancel_at_period_end = false,
    updated_at = NOW();

-- Step 4: Verify upgrade
SELECT 
    us.user_id,
    us.plan_type,
    us.status,
    us.current_period_end,
    up.email
FROM user_subscriptions us
JOIN user_profiles up ON us.user_id = up.uid
WHERE us.user_id = 'YOUR_USER_ID';

-- ============================================================================
-- QUICK UPGRADE: Get most recent user and upgrade them
-- ============================================================================

-- Find your user ID (most recent user)
SELECT uid, email, created_at 
FROM user_profiles 
ORDER BY created_at DESC 
LIMIT 1;

-- Copy the uid from above and use it in this query:
INSERT INTO user_subscriptions (
    user_id,
    plan_type,
    status,
    current_period_start,
    current_period_end,
    cancel_at_period_end
)
SELECT 
    uid,
    'pro',
    'active',
    NOW(),
    NOW() + INTERVAL '30 days',
    false
FROM user_profiles
ORDER BY created_at DESC
LIMIT 1
ON CONFLICT (user_id) 
DO UPDATE SET
    plan_type = 'pro',
    status = 'active',
    current_period_start = NOW(),
    current_period_end = NOW() + INTERVAL '30 days',
    cancel_at_period_end = false,
    updated_at = NOW();

-- ============================================================================
-- DOWNGRADE BACK TO FREE
-- ============================================================================

-- To downgrade back to free, just delete the subscription:
DELETE FROM user_subscriptions WHERE user_id = 'YOUR_USER_ID';
