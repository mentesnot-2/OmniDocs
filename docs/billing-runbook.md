# Billing Runbook

## Webhook setup

1. Create endpoint: `POST /billing/webhook`
2. Subscribe to:
   - `checkout.session.completed`
   - `customer.subscription.created`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
3. Set `STRIPE_WEBHOOK_SECRET` from the Stripe dashboard

## Idempotency

Each processed event is stored in `stripe_processed_events` by Stripe event id (`evt_*`). Replayed deliveries short-circuit with `{"duplicate": true}`.

## Local testing

Use Stripe CLI:

```bash
stripe listen --forward-to localhost:8000/billing/webhook
stripe trigger checkout.session.completed
```

## Failure handling

- Invalid signature returns HTTP 400
- Unknown event types are recorded but may not mutate user billing fields
- Subscription deleted moves user back to `free` plan
