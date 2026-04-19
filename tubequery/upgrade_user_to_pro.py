"""
Upgrade a user to Pro plan for testing
Usage: python upgrade_user_to_pro.py <user_id>
"""
import sys
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    print("❌ Error: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in .env")
    sys.exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

def get_current_user_id():
    """Get the most recent user from user_profiles"""
    try:
        result = supabase.table("user_profiles").select("uid, email").order("created_at", desc=True).limit(1).execute()
        if result.data:
            return result.data[0]["uid"], result.data[0].get("email", "unknown")
        return None, None
    except Exception as e:
        print(f"❌ Error getting user: {e}")
        return None, None

def upgrade_to_pro(user_id: str):
    """Upgrade user to Pro plan"""
    try:
        # Check if user exists
        user_result = supabase.table("user_profiles").select("*").eq("uid", user_id).execute()
        if not user_result.data:
            print(f"❌ User {user_id} not found in user_profiles")
            return False
        
        user = user_result.data[0]
        print(f"\n📋 Current user info:")
        print(f"   Email: {user.get('email', 'N/A')}")
        print(f"   Current plan: {user.get('plan', 'free')}")
        
        # Check if subscription exists
        sub_result = supabase.table("user_subscriptions").select("*").eq("user_id", user_id).execute()
        
        # Calculate dates
        now = datetime.utcnow()
        next_month = now + timedelta(days=30)
        
        subscription_data = {
            "user_id": user_id,
            "plan_type": "pro",
            "status": "active",
            "current_period_start": now.isoformat(),
            "current_period_end": next_month.isoformat(),
            "cancel_at_period_end": False,
        }
        
        if sub_result.data:
            # Update existing subscription
            print(f"\n🔄 Updating existing subscription...")
            result = supabase.table("user_subscriptions").update(subscription_data).eq("user_id", user_id).execute()
        else:
            # Create new subscription
            print(f"\n✨ Creating new Pro subscription...")
            result = supabase.table("user_subscriptions").insert(subscription_data).execute()
        
        if result.data:
            print(f"\n✅ Successfully upgraded user to Pro!")
            print(f"\n📊 Pro Plan Benefits:")
            print(f"   • 50 videos per day (vs 3 for free)")
            print(f"   • 500 questions per day (vs 20 for free)")
            print(f"   • Playlist ingestion ✓")
            print(f"   • Channel ingestion ✓")
            print(f"   • Priority processing ✓")
            print(f"   • Valid until: {next_month.strftime('%Y-%m-%d')}")
            return True
        else:
            print(f"❌ Failed to upgrade user")
            return False
            
    except Exception as e:
        print(f"❌ Error upgrading user: {e}")
        import traceback
        traceback.print_exc()
        return False

def downgrade_to_free(user_id: str):
    """Downgrade user back to free plan"""
    try:
        # Delete subscription
        result = supabase.table("user_subscriptions").delete().eq("user_id", user_id).execute()
        print(f"✅ User downgraded to free plan")
        return True
    except Exception as e:
        print(f"❌ Error downgrading user: {e}")
        return False

if __name__ == "__main__":
    print("=" * 70)
    print("USER PLAN MANAGER")
    print("=" * 70)
    
    if len(sys.argv) > 1:
        user_id = sys.argv[1]
        
        if user_id == "--downgrade":
            if len(sys.argv) > 2:
                user_id = sys.argv[2]
                downgrade_to_free(user_id)
            else:
                print("Usage: python upgrade_user_to_pro.py --downgrade <user_id>")
        else:
            upgrade_to_pro(user_id)
    else:
        # Auto-detect most recent user
        print("\n🔍 No user ID provided, finding most recent user...")
        user_id, email = get_current_user_id()
        
        if user_id:
            print(f"\n👤 Found user: {email}")
            print(f"   User ID: {user_id}")
            
            response = input("\n❓ Upgrade this user to Pro? (y/n): ")
            if response.lower() == 'y':
                upgrade_to_pro(user_id)
            else:
                print("❌ Cancelled")
        else:
            print("\n❌ No users found. Please provide a user ID:")
            print("   Usage: python upgrade_user_to_pro.py <user_id>")
            print("\n💡 You can find your user ID by:")
            print("   1. Log in to the app")
            print("   2. Open browser DevTools (F12)")
            print("   3. Go to Console tab")
            print("   4. Type: localStorage")
            print("   5. Look for your Firebase user ID")
