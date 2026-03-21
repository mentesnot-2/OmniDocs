# OmniDocs

AI-powered, secure, multi-format document intelligence platform built with FastAPI + Next.js.

OmniDocs lets users upload documents, index them into a vector store, and ask grounded questions with traceable answers. It includes modern authentication, role-based admin APIs, usage analytics, email verification, and production-focused guardrails.

---

## Highlights

- Multi-format ingestion: PDF, DOCX, PPTX, XLSX, CSV, HTML, Markdown, TXT
- RAG Q&A with retrieved context (no blind generation)
- Session-based chat history
- HttpOnly cookie auth + refresh token flow
- Optional email verification and Google OAuth login
- Admin APIs for user management and support tickets
- Per-user usage analytics (queries/uploads per month + storage usage)
- Upload controls: extension allowlist, file-size limits, storage quota
- Rate limiting on sensitive and heavy endpoints

---

## Tech Stack

- Backend: FastAPI, SQLAlchemy, SlowAPI, ChromaDB
- Frontend: Next.js App Router, TypeScript, Tailwind CSS
- LLM/Embeddings: Gemini support + pluggable providers
- Auth: JWT access + refresh tokens in HttpOnly cookies
- Email: SMTP (Mailtrap-ready, generic SMTP fallback)

---

## Core Capabilities

### 1) Authentication and Security

- Signup/Login with strong password policy
- Optional email verification flow for production
- Google OAuth (`/auth/oauth/google/start`, callback flow)
- Refresh-token based silent session renewal
- Cookie-based auth (HttpOnly, SameSite)
- Route protection on frontend via `proxy.ts`

### 2) Document Intelligence

- Upload + parse + chunk + embed + index
- List and delete user-owned documents
- Query endpoint with optional message history context
- Guardrails for invalid file types, oversize files, and quota overflow

### 3) Admin and Support

- Admin-only user listing
- Activate/deactivate user accounts
- Admin support ticket listing and status updates

### 4) Analytics

- Per-user monthly metrics:
  - `queries_this_month`
  - `uploads_this_month`
- Per-user storage metrics:
  - `used_bytes`
  - `limit_bytes`
  - `used_percent`

---

## Project Structure

```text
OmniDocs/
  api/
    routes/        # auth, documents, chat, admin, usage
    models/        # user, chat, support, usage_event
    utils/         # email, logging
  frontend/
    app/           # login, signup, dashboard, chat, admin, verify-email
    lib/           # API client helpers
  config/
    settings.py
```

---

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+

### Backend

```bash
cd OmniDocs
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn api.main:app --reload --host 127.0.0.1 --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open:
- Frontend: http://localhost:3000
- Backend: http://127.0.0.1:8000

Note: using `127.0.0.1` avoids IPv6 localhost proxy issues on some systems.

---

## Docker (Recommended One-Command Run)

### Prerequisites

- Docker Desktop (or Docker Engine + Compose)

### Build and Run

```bash
docker compose up --build
```

Open:
- Frontend: http://localhost:3000
- Backend: http://localhost:8000

### Run in Detached Mode

```bash
docker compose up -d --build
```

### Stop Containers

```bash
docker compose down
```

### Persisted Data

Docker volumes are configured for:
- SQLite and uploads: `omnidocs_data`
- Vector DB storage: `omnidocs_chroma`

---

## Environment Configuration

Create `.env` at project root.

### Required

```env
JWT_SECRET_KEY=change-me-in-production
```

### Recommended Core

```env
LLM_PROVIDER=gemini
LLM_MODEL=gemini-flash-latest
GEMINI_API_KEY=

EMBEDDING_PROVIDER=sentence-transformers
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

TOP_K=5
CHUNK_SIZE=512
CHUNK_OVERLAP=50
```

### Upload and Storage Controls

```env
MAX_FILE_SIZE_MB=25
MAX_USER_STORAGE_MB=500
```

### Email Verification

```env
EMAIL_VERIFICATION_REQUIRED=true
EMAIL_SENDER=no-reply@your-domain.com
EMAIL_VERIFICATION_BASE_URL=http://localhost:3000
```

### Mailtrap SMTP (or generic SMTP fallback)

```env
MAILTRAP_TOKEN=
MAILTRAP_HOST=sandbox.smtp.mailtrap.io
MAILTRAP_PORT=2525
MAILTRAP_USERNAME=
MAILTRAP_PASSWORD=
SMTP_USE_TLS=true
```

### OAuth (Google)

```env
SSO_ENABLED=true
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
FRONTEND_BASE_URL=http://localhost:3000
```

Google OAuth redirect URI:
- `http://localhost:3000/api/auth/oauth/google/callback`

---

## API Snapshot

### Auth

- `POST /auth/signup`
- `POST /auth/login`
- `POST /auth/refresh`
- `GET /auth/me`
- `POST /auth/logout`
- `GET /auth/verify/{token}`
- `GET /auth/oauth/google/start`
- `GET /auth/oauth/google/callback`

### Documents and Chat

- `GET /documents` and `GET /documents/`
- `POST /documents/upload`
- `DELETE /documents/{filename}`
- `POST /documents/query`
- `GET /documents/storage`
- `POST /chat/sessions`
- `GET /chat/sessions`
- `GET /chat/sessions/{session_id}`
- `POST /chat/sessions/{session_id}/messages`

### Admin

- `GET /admin/users`
- `PATCH /admin/users/{user_id}/active`
- `GET /admin/support/tickets`
- `PATCH /admin/support/tickets/{ticket_id}`

### Usage

- `GET /usage/me`

---

## Production Notes

- Move `secure=False` cookie flags to `secure=True` behind HTTPS.
- Use migrations (Alembic) for schema evolution.
- Rotate SMTP/API credentials regularly.
- Keep `.env` out of version control.

---

## Why OmniDocs

OmniDocs is designed for real-world reliability: security-first auth, controllable data usage, explainable AI answers, and an architecture that scales from local development to production deployment.

