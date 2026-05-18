"""Configure the Stripe SDK once at application startup (avoid import-time api_key side effects)."""

import stripe

from api.utils.logging_config import logger
from config.settings import APP_ENV, STRIPE_SECRET_KEY


def init_stripe() -> None:
    """
    Set stripe.api_key from settings and validate.

    Production requires STRIPE_SECRET_KEY so billing failures fail fast instead of
    surfacing only on first Stripe HTTP call with an empty key.
    """
    key = (STRIPE_SECRET_KEY or "").strip()
    stripe.api_key = key or ""

    if not key:
        if APP_ENV == "production":
            raise RuntimeError(
                "STRIPE_SECRET_KEY is required when APP_ENV=production "
                "(Stripe Billing REST calls cannot run without it)."
            )
        logger.warning(
            "STRIPE_SECRET_KEY is empty; Stripe Billing REST calls will fail until configured."
        )
        return

    logger.info("Stripe SDK initialized (publishable REST secret present).")
