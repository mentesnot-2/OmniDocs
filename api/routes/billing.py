from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
import stripe


from api.database import get_db
from api.dependencies import get_current_user, require_csrf
from api.models import User
from api.services.billing import create_checkout_session, create_portal_session
from config.settings import STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET
from config.plans import PLANS, DEFAULT_PLAN_ID
from api.rate_limiter import limiter
from api.utils.logging_config import logger


router = APIRouter(prefix="/billing", tags=["billing"])
stripe.api_key = STRIPE_SECRET_KEY


def get_or_create_customer(user:User) -> str:
    if user.stripe_customer_id:
        return user.stripe_customer_id
    
    customer = stripe.Customer.create(
        email=user.email,
        metadata={"user_id":str(user.id)}
    )
    return customer.id


def get_user_by_customer_id(db: Session, customer_id: str | None) -> User | None:
    if not customer_id:
        return None
    return db.query(User).filter(User.stripe_customer_id == customer_id).first()

@router.post("/checkout")
@limiter.limit("10/minute")
def start_checkout(request: Request, _csrf: None = Depends(require_csrf), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> dict:
    try:
        customer_id = get_or_create_customer(current_user)
        if not current_user.stripe_customer_id:
            current_user.stripe_customer_id = customer_id
            db.commit()
            db.refresh(current_user)
        url = create_checkout_session(customer_id, current_user.id)
        if not url:
            raise HTTPException(status_code=500, detail="Failed to create checkout session")
        return {"url":url}
    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to start Stripe checkout for user %s", current_user.id)
        raise HTTPException(status_code=500, detail="Unable to start checkout right now.")

@router.post("/portal")
@limiter.limit("10/minute")
def open_portal(request: Request, _csrf: None = Depends(require_csrf), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> dict:
    try:
        if not current_user.stripe_customer_id:
            raise HTTPException(status_code=400, detail="No Stripe customer found")
        url = create_portal_session(current_user.stripe_customer_id)
        return {"url":url}
    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to open Stripe portal for user %s", current_user.id)
        raise HTTPException(status_code=500, detail="Unable to open billing portal right now.")

@router.post("/webhook")
@limiter.limit("120/minute")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)) -> dict:
    try:
        payload = await request.body()
        sig_header = request.headers.get("stripe-signature", "")

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, STRIPE_WEBHOOK_SECRET

            )
        except Exception:
            logger.exception("Invalid Stripe webhook signature")
            raise HTTPException(status_code=400, detail="Invalid webhook signature.")
        event_type = event["type"]
        obj = event["data"]["object"]

        if event_type == "checkout.session.completed":
            customer_id = obj.get("customer")
            subscription_id = obj.get("subscription")
            user = get_user_by_customer_id(db, customer_id)
            if user and subscription_id:
                user.stripe_subscription_id = subscription_id
                db.commit()

        elif event_type in ("customer.subscription.created", "customer.subscription.updated"):
            customer_id = obj.get("customer")
            subscription_id = obj.get("id")
            subscription_status = obj.get("status", "inactive")
            user = get_user_by_customer_id(db, customer_id)
            if user:
                user.stripe_subscription_id = subscription_id
                user.billing_status = subscription_status
                if subscription_status in ("active", "trialing", "past_due"):
                    user.plan_id = "pro"
                else:
                    user.plan_id = DEFAULT_PLAN_ID
                db.commit()

        elif event_type == "customer.subscription.deleted":
            customer_id = obj.get("customer")
            subscription_id = obj.get("id")
            user = get_user_by_customer_id(db, customer_id)
            if user:
                user.plan_id = DEFAULT_PLAN_ID
                user.billing_status = "canceled"
                if user.stripe_subscription_id == subscription_id:
                    user.stripe_subscription_id = None
                db.commit()
        return {"ok":True}
    except HTTPException:
        raise
    except Exception:
        logger.exception("Stripe webhook processing failed")
        raise HTTPException(status_code=500, detail="Webhook processing failed.")