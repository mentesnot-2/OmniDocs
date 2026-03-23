import smtplib
from email.message import EmailMessage
from api.utils.logging_config import logger
from config.settings import (
    EMAIL_SENDER,
    SMTP_HOST,
    SMTP_PORT,
    SMTP_USERNAME,
    SMTP_PASSWORD,
    SMTP_USE_TLS,
    # SMTP_USE_SSL,
)


class EmailDeliveryError(Exception):
    """Raised when an email could not be delivered."""


def send_email(to:str,subject:str,body:str):
    """
    SMTP sender for production.
    """
    msg = EmailMessage()
    msg['From'] = EMAIL_SENDER
    msg['To'] = to
    msg['Subject'] = subject
    msg.set_content(body)
    try:
        with smtplib.SMTP(SMTP_HOST,SMTP_PORT) as server:
            if SMTP_USE_TLS:
                server.starttls()
            if SMTP_USERNAME and SMTP_PASSWORD:
                server.login(SMTP_USERNAME,SMTP_PASSWORD)
            server.send_message(msg)
    except Exception as e:
        logger.exception("Failed to send email to %s", to)
        raise EmailDeliveryError("Failed to send verification email.") from e

