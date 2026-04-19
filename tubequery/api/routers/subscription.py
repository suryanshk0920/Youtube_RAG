"""
Subscription Router
==================
Handles user plan management, usage tracking, and upgrade flows.
"""

from __future__ import annotations

import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from api.auth import get_current_user, get_supabase
from services.subscription_service_redis import RedisSubscriptionService, UPGRADE_MESSAGES

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/subscription", tags=["subscription"])

class UpgradeRequest(BaseModel):
    plan_type: str
    billing_cycle: str = "monthly"

@router.get("/limits")
async def get_user_limits(
    user: dict = Depends(get_current_user),
    db = Depends(get_supabase)
):
    """Get user's current plan limits and usage."""
    try:
        subscription_service = RedisSubscriptionService(db)
        limits = await subscription_service.get_user_limits_summary(user["uid"])
        return limits
    except Exception as e:
        logger.exception("Failed to get user limits")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/check/video")
async def check_video_limit(
    user: dict = Depends(get_current_user),
    db = Depends(get_supabase)
):
    """Check if user can ingest another video."""
    try:
        subscription_service = RedisSubscriptionService(db)
        can_ingest, details = await subscription_service.check_video_limit(user["uid"])
        
        if not can_ingest:
            # Return upgrade message
            message = UPGRADE_MESSAGES["video_limit"]
            details["upgrade_message"] = {
                "title": message["title"],
                "message": message["message"].format(
                    limit=details["limit"],
                    pro_limit=50
                ),
                "cta": message["cta"],
                "benefits": message["benefits"]
            }
        
        return details
    except Exception as e:
        logger.exception("Failed to check video limit")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/check/question")
async def check_question_limit(
    user: dict = Depends(get_current_user),
    db = Depends(get_supabase)
):
    """Check if user can ask another question."""
    try:
        subscription_service = RedisSubscriptionService(db)
        can_ask, details = await subscription_service.check_question_limit(user["uid"])
        
        if not can_ask:
            # Return upgrade message
            message = UPGRADE_MESSAGES["question_limit"]
            details["upgrade_message"] = {
                "title": message["title"],
                "message": message["message"].format(
                    used=details["used"]
                ),
                "cta": message["cta"],
                "benefits": message["benefits"]
            }
        
        return details
    except Exception as e:
        logger.exception("Failed to check question limit")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upgrade")
async def initiate_upgrade(
    request: UpgradeRequest,
    user: dict = Depends(get_current_user),
    db = Depends(get_supabase)
):
    """Initiate upgrade process (will integrate with Stripe)."""
    try:
        # TODO: Integrate with Stripe
        # For now, return checkout URL placeholder
        
        pricing = {
            "pro": {
                "monthly": {"price": 9, "stripe_price_id": "price_pro_monthly"},
                "yearly": {"price": 89, "stripe_price_id": "price_pro_yearly"}
            }
        }
        
        if request.plan_type not in pricing:
            raise HTTPException(status_code=400, detail="Invalid plan type")
        
        if request.billing_cycle not in pricing[request.plan_type]:
            raise HTTPException(status_code=400, detail="Invalid billing cycle")
        
        plan_info = pricing[request.plan_type][request.billing_cycle]
        
        return {
            "checkout_url": f"https://checkout.stripe.com/placeholder",
            "plan_type": request.plan_type,
            "billing_cycle": request.billing_cycle,
            "price": plan_info["price"],
            "stripe_price_id": plan_info["stripe_price_id"]
        }
        
    except Exception as e:
        logger.exception("Failed to initiate upgrade")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/webhook/stripe")
async def stripe_webhook(
    # TODO: Add Stripe webhook signature verification
    db = Depends(get_supabase)
):
    """Handle Stripe webhook events."""
    try:
        # TODO: Implement Stripe webhook handling
        # - subscription.created
        # - subscription.updated  
        # - subscription.deleted
        # - invoice.payment_succeeded
        # - invoice.payment_failed
        
        return {"status": "success"}
        
    except Exception as e:
        logger.exception("Failed to process Stripe webhook")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/cancel")
async def cancel_subscription(
    user: dict = Depends(get_current_user),
    db = Depends(get_supabase)
):
    """Cancel user's subscription."""
    try:
        # TODO: Cancel subscription in Stripe
        # Update user_subscriptions table
        
        result = db.table("user_subscriptions").update({
            "status": "cancelled"
        }).eq("user_id", user["uid"]).execute()
        
        return {"status": "cancelled"}
        
    except Exception as e:
        logger.exception("Failed to cancel subscription")
        raise HTTPException(status_code=500, detail=str(e))