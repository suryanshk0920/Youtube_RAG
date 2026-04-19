"""
Simple script to upgrade user to Pro using direct HTTP requests
Usage: python upgrade_user_simple.py
"""
import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    print("❌ Error: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in .env")
    exit(1)

headers = {
    "apikey": SUPABASE_SERVICE_ROLE_KEY,
    "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

def get_recent_user():
    """Get the most recent user"""
    url = f"{SUPABASE_URL}/rest/v1/user_profiles?select=uid,email&order=created_at.desc&limit=1"
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200 and response.json():
        return response.json()[0]
    return None

def upgrade_to_pro(user_id: str):
    """Upgrade user to Pro"""
    now = datetime.utcnow()
    next_month = now + timedelta(days=30)
    
    data = {
        "user_id": user_id,
        "plan_type": "pro",
        "status": "active",
        "current_period_start": now.isoformat(),
        "current_period_end": next_month.isoformat()
    }
    
    # Try to insert, if conflict then update
    url = f"{SUPABASE_URL}/rest/v1/user_subscriptions"
    headers_with_upsert = {**headers, "Prefer": "resolution=merge-duplicates"}
    
    response = requests.post(url, json=data, headers=headers_with_upsert)
    
    if response.status_code in [200, 201]:
        print(f"\n✅ Successfully upgraded user to Pro!")
        print(f"\n📊 Pro Plan Benefits:")
        print(f"   • 50 videos per day (vs 3 for free)")
        print(f"   • 500 questions per day (vs 20 for free)")
        print(f"   • Playlist ingestion ✓")
        print(f"   • Channel ingestion ✓")
        print(f"   • Valid until: {next_month.strftime('%Y-%m-%d')}")
        print(f"\n🔄 Changes are effective immediately!")
        print(f"   (No server restart needed - plan data is read from database)")
        return True
    else:
        print(f"❌ Failed to upgrade: {response.status_code}")
        print(f"   Response: {response.text}")
        return False

if __name__ == "__main__":
    print("=" * 70)
    print("USER PLAN MANAGER (Simple)")
    print("=" * 70)
    
    print("\n🔍 Finding most recent user...")
    user = get_recent_user()
    
    if user:
        print(f"\n👤 Found user:")
        print(f"   Email: {user.get('email', 'N/A')}")
        print(f"   User ID: {user['uid']}")
        
        response = input("\n❓ Upgrade this user to Pro? (y/n): ")
        if response.lower() == 'y':
            upgrade_to_pro(user['uid'])
        else:
            print("❌ Cancelled")
    else:
        print("\n❌ No users found")
        print("\n💡 To manually upgrade a user:")
        print("   1. Go to Supabase Dashboard")
        print("   2. Open SQL Editor")
        print("   3. Run the queries in upgrade_to_pro.sql")
