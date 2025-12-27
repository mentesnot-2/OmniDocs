# Secrets Runbook

## JWT secret rotation

1. Generate a new `JWT_SECRET_KEY` (32+ characters)
2. Deploy API with the new secret
3. Existing access tokens expire within 15 minutes
4. Refresh sessions remain valid until users log out or tokens rotate

## Stripe keys

- `STRIPE_SECRET_KEY`: billing API calls
- `STRIPE_WEBHOOK_SECRET`: webhook signature verification
- Rotate in Stripe Dashboard, update environment, redeploy API
- Replay protection uses the `stripe_processed_events` table

## SMTP / Mailtrap

- Update `MAILTRAP_*` or generic `SMTP_*` variables
- Redeploy API; no migration required

## LLM and embedding keys

- `GEMINI_API_KEY` / `OPENAI_API_KEY`
- Update environment and restart API + worker (workers load models at runtime)

## Storage credentials

- Local: ensure volume permissions on `data/uploads`
- S3: rotate `S3_ACCESS_KEY_ID` / `S3_SECRET_ACCESS_KEY` in your cloud provider
