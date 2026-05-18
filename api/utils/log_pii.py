"""
Pseudonymize personal data in application logs.

When ``LOG_PII`` is false (default), emails and filenames are replaced with
HMAC-based short fingerprints so operators can correlate repeated events
without storing full PII in log aggregators. Set ``LOG_PII=true`` only for
local debugging.
"""

from __future__ import annotations

import hashlib
import hmac
import re
from functools import lru_cache

from config.settings import JWT_SECRET_KEY, LOG_PII

_EMAIL_LIKE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@lru_cache(maxsize=1)
def _signing_key() -> bytes:
    return JWT_SECRET_KEY.encode("utf-8")


def redact_email_for_log(email: str | None) -> str:
    """
    Return a log-safe representation of an email address.
    With LOG_PII=true, returns the original (use only in development).
    """
    if not email:
        return ""
    raw = email.strip()
    if LOG_PII:
        return raw
    fp = hmac.new(_signing_key(), raw.lower().encode("utf-8"), hashlib.sha256).hexdigest()[:12]
    return f"<email:{fp}>"


def redact_filename_for_log(filename: str | None) -> str:
    """
    Return a log-safe representation of a file name (basename is assumed).
    Preserves a lowercased extension for support triage; the base name is never logged raw
    unless LOG_PII=true.
    """
    if not filename:
        return ""
    raw = filename.strip()
    if LOG_PII:
        return raw
    fp = hmac.new(_signing_key(), raw.encode("utf-8"), hashlib.sha256).hexdigest()[:12]
    ext = ""
    if "." in raw:
        tail = raw.rsplit(".", 1)[-1]
        if tail.isalnum() and len(tail) <= 10:
            ext = tail.lower()
    label = f"*.{ext}" if ext else "*"
    return f"<file {label} id={fp}>"


def maybe_redact_email_like(text: str | None) -> str:
    """
    If the whole string looks like an email, redact it; otherwise return as-is.
    Used for parameters that are sometimes an email (e.g. login identifier in future logs).
    """
    if not text:
        return ""
    s = text.strip()
    if LOG_PII:
        return s
    if _EMAIL_LIKE.match(s):
        return redact_email_for_log(s)
    return s
