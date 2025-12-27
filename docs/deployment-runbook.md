# Deployment Runbook

## Pre-deploy checklist

- `DATABASE_URL` points to production PostgreSQL
- `RATE_LIMIT_STORAGE_URI` points to shared Redis
- `CELERY_BROKER_URL` and `CELERY_RESULT_BACKEND` point to Redis
- `JWT_SECRET_KEY` is at least 32 characters
- Stripe, SMTP, and LLM API keys are set
- Persistent volumes exist for `data/`, `chroma_db/`, and object storage

## Deploy order

1. Build images: `docker compose build`
2. Run migrations: `alembic upgrade head`
3. Start infrastructure: Postgres and Redis
4. Start API: `docker compose up -d backend`
5. Start worker: `docker compose up -d worker`
6. Start frontend: `docker compose up -d frontend`
7. Smoke test:
   - `GET /health`
   - `GET /health/ready`
   - Login and upload a small `.txt` file
   - Poll `GET /documents/jobs/{id}` until `completed`

## Rollback

1. Stop `frontend`, `worker`, and `backend`
2. Restore database backup if schema/data rollback is required
3. Deploy previous image tag
4. Run `alembic downgrade -1` only when the release notes require it
5. Restart API and worker

## Backups

- **PostgreSQL:** nightly logical backup (`pg_dump`)
- **Chroma:** snapshot the `chroma_db/` volume
- **Uploads / S3:** bucket versioning or periodic object sync

## Local production-like stack

```bash
docker compose up -d postgres redis backend worker frontend
alembic upgrade head
```

Optional S3-compatible storage:

```bash
docker compose --profile s3 up -d minio
```
