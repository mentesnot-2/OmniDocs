# Incident Runbook

## Ingestion jobs stuck in `queued` or `processing`

1. Check worker health: `docker compose ps worker`
2. Check Redis connectivity from worker container
3. Inspect failed jobs: `GET /documents/jobs/{id}`
4. Restart worker: `docker compose restart worker`
5. Re-upload document if job status is `failed`

## API healthy but uploads never index

- Confirm `CELERY_BROKER_URL` matches worker configuration
- Confirm worker logs show `ingestion.process_job` tasks
- Verify storage key exists for the document version in DB

## Readiness degraded

- `GET /health/ready` returns per-check status
- Database failure: verify Postgres connectivity and migrations
- Chroma failure: verify `chroma_db/` volume mount permissions
- Storage failure: verify local path or S3 credentials

## Rate limit false positives

- Confirm all API replicas use the same `RATE_LIMIT_STORAGE_URI`
- Redis outage causes limiter misbehavior; fail over to healthy Redis

## Stripe webhook duplicates

- Expected: second delivery returns `{"duplicate": true}`
- Check `stripe_processed_events` for the `evt_*` id
