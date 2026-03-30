import stripe
from config.settings import STRIPE_SECRET_KEY, STRIPE_PRICE_PRO_MONTHLY, BILLING_SUCCESS_URL, BILLING_CANCEL_URL
import logging
from typing import Optional

logger = logging.getLogger(__name__)


stripe.api_key = STRIPE_SECRET_KEY

def create_checkout_session(customer_id:str, user_id:int) -> Optional[str]:
    try:
        session = stripe.checkout.Session.create(
            mode="subscription",
            customer=customer_id,
            line_items = [{"price":STRIPE_PRICE_PRO_MONTHLY,"quantity":1}],
            success_url=BILLING_SUCCESS_URL,
            cancel_url=BILLING_CANCEL_URL,
            metadata={"user_id":str(user_id)},
        )

        return session.url
    except Exception as e:
        logger.error(f"Error creating checkout session: {e}")
        return None

def create_portal_session(customer_id:str) -> str:
    try:
        session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url="http://localhost:3000/dashboard/billing",
        )
        return session.url
    except Exception as e:
        logger.error(f"Error creating portal session: {e}")
        return None


