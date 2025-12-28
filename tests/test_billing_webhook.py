"""Stripe webhook idempotency (duplicate evt_* deliveries short-circuit)."""

import pytest

from api.models import StripeProcessedEvent, User


@pytest.fixture(autouse=True)
def stripe_webhook_secret(monkeypatch):
    monkeypatch.setattr("api.routes.billing.STRIPE_WEBHOOK_SECRET", "whsec_test")


def test_subscription_updated_once_then_duplicate_no_extra_side_effect(client, db_session, make_user, monkeypatch):
    user = make_user(stripe_customer_id="cus_test_webhook", plan_id="free")

    event = {
        "id": "evt_idempotent_test_1",
        "type": "customer.subscription.updated",
        "data": {
            "object": {
                "id": "sub_test_1",
                "customer": "cus_test_webhook",
                "status": "active",
            }
        },
    }

    monkeypatch.setattr(
        "api.routes.billing.stripe.Webhook.construct_event",
        lambda payload, sig, secret: event,
    )

    r1 = client.post("/billing/webhook", content=b"{}", headers={"stripe-signature": "sig"})
    assert r1.status_code == 200
    assert r1.json() == {"ok": True}

    db_session.expire_all()
    user = db_session.get(User, user.id)
    assert user.plan_id == "pro"
    assert user.stripe_subscription_id == "sub_test_1"
    assert user.billing_status == "active"

    rows = db_session.query(StripeProcessedEvent).all()
    assert len(rows) == 1
    assert rows[0].id == "evt_idempotent_test_1"

    r2 = client.post("/billing/webhook", content=b"{}", headers={"stripe-signature": "sig"})
    assert r2.status_code == 200
    assert r2.json() == {"ok": True, "duplicate": True}

    db_session.expire_all()
    user = db_session.get(User, user.id)
    assert user.plan_id == "pro"
    assert db_session.query(StripeProcessedEvent).count() == 1


def test_checkout_completed_persists_marker_when_user_present(client, db_session, make_user, monkeypatch):
    user = make_user(stripe_customer_id="cus_checkout", plan_id="free")

    event = {
        "id": "evt_checkout_1",
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "customer": "cus_checkout",
                "subscription": "sub_from_checkout",
            }
        },
    }

    monkeypatch.setattr(
        "api.routes.billing.stripe.Webhook.construct_event",
        lambda payload, sig, secret: event,
    )

    r = client.post("/billing/webhook", content=b"{}", headers={"stripe-signature": "sig"})
    assert r.status_code == 200

    db_session.expire_all()
    user = db_session.get(User, user.id)
    assert user.stripe_subscription_id == "sub_from_checkout"
    assert db_session.query(StripeProcessedEvent).filter_by(id="evt_checkout_1").one()


def test_subscription_deleted_applies_then_duplicate(client, db_session, make_user, monkeypatch):
    user = make_user(
        stripe_customer_id="cus_del",
        plan_id="pro",
        stripe_subscription_id="sub_del",
        billing_status="active",
    )

    event = {
        "id": "evt_deleted_1",
        "type": "customer.subscription.deleted",
        "data": {
            "object": {
                "id": "sub_del",
                "customer": "cus_del",
            }
        },
    }

    monkeypatch.setattr(
        "api.routes.billing.stripe.Webhook.construct_event",
        lambda payload, sig, secret: event,
    )

    assert client.post("/billing/webhook", content=b"{}", headers={"stripe-signature": "sig"}).status_code == 200

    db_session.expire_all()
    user = db_session.get(User, user.id)
    assert user.plan_id == "free"
    assert user.stripe_subscription_id is None
    assert user.billing_status == "canceled"

    dup = client.post("/billing/webhook", content=b"{}", headers={"stripe-signature": "sig"})
    assert dup.status_code == 200
    assert dup.json()["duplicate"] is True


def test_webhook_rejects_invalid_signature(client, monkeypatch):
    def _raise(*args, **kwargs):
        raise ValueError("Invalid signature")

    monkeypatch.setattr("api.routes.billing.stripe.Webhook.construct_event", _raise)

    response = client.post("/billing/webhook", content=b"{}", headers={"stripe-signature": "bad"})
    assert response.status_code == 400


def test_unknown_event_type_still_records_idempotency_row(client, db_session, monkeypatch):
    event = {
        "id": "evt_unknown_1",
        "type": "invoice.paid",
        "data": {"object": {}},
    }

    monkeypatch.setattr(
        "api.routes.billing.stripe.Webhook.construct_event",
        lambda payload, sig, secret: event,
    )

    assert client.post("/billing/webhook", content=b"{}", headers={"stripe-signature": "sig"}).status_code == 200
    assert db_session.query(StripeProcessedEvent).filter_by(id="evt_unknown_1").one()
