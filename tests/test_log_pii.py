"""Tests for GDPR-friendly log redaction helpers."""

import pytest


@pytest.fixture()
def log_pii_off(monkeypatch):
    monkeypatch.setattr("api.utils.log_pii.LOG_PII", False, raising=False)


def test_redact_email_hmac_form(log_pii_off):
    from api.utils.log_pii import redact_email_for_log

    out = redact_email_for_log("User@Example.com")
    assert out.startswith("<email:")
    assert "@" not in out
    assert "User" not in out
    out2 = redact_email_for_log("User@Example.com")
    assert out == out2


def test_redact_email_passthrough_when_log_pii_true(monkeypatch):
    import api.utils.log_pii as lp

    monkeypatch.setattr(lp, "LOG_PII", True)
    assert lp.redact_email_for_log("a@b.co") == "a@b.co"


def test_redact_filename_preserves_extension_label(log_pii_off):
    from api.utils.log_pii import redact_filename_for_log

    out = redact_filename_for_log("My Secret Report.FINAL.pdf")
    assert "Secret" not in out
    assert "pdf" in out.lower() or ".pdf" in out


def test_maybe_redact_email_like(log_pii_off):
    from api.utils.log_pii import maybe_redact_email_like

    assert "@" not in maybe_redact_email_like("x@y.com")
    assert maybe_redact_email_like("not-an-email") == "not-an-email"
