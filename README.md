# OmniDocs

OmniDocs is a multi-tenant, retrieval-augmented document intelligence platform built with FastAPI and Next.js. Users sign up, upload PDFs, Office documents, spreadsheets, Markdown, HTML, or plain text files, and then ask natural-language questions whose answers are generated only from chunks retrieved from their own documents.

---

## Project Overview

### What it does

- Lets authenticated users upload, list, and delete documents in 9 formats: `.pdf`, `.docx`, `.pptx`, `.xlsx`, `.csv`, `.html`, `.htm`, `.md`, `.txt` (see `config/settings.py` and `ingestion/document_ingestion.py`).
- Parses, chunks (token-based with overlap via `tiktoken` in `chunking/text_chunker.py`), embeds, and indexes each document into a **tenant-scoped** ChromaDB collection (`vectorstore/chroma_store.py`).
- Answers questions by retrieving top-k chunks only from the requesting user's collection, then generating a grounded answer with Gemini or OpenAI (`retrieval/retriever.py`, `generation/answer_generator.py`).
- Persists chat sessions and message history per user (`api/models/chat.py`, `api/routes/chat.py`).
- Tracks per-user monthly usage (queries, uploads, storage bytes) and enforces plan-based limits (`api/services/usage_limits.py`, `config/plans.py`).
- Provides admin APIs to list users, (de)activate accounts, and triage support tickets (`api/routes/admin.py`).
- Integrates Stripe Checkout and Customer Portal for paid plans, including webhook-driven plan state transitions (`api/routes/billing.py`).

### Problem it solves

Knowledge-heavy teams accumulate documents that are hard to search and harder to trust. OmniDocs gives every account a private, retrieval-grounded assistant with verifiable sources, plan-aware quotas, and the auth, billing, and operational primitives needed to run as a real product rather than a notebook demo.

### Intended audience

- SaaS teams that need a production-shaped RAG backend to extend rather than build from scratch.
- Internal platform teams shipping AI document search behind authenticated workspaces.
- Developers studying a hardened FastAPI + Next.js reference implementation (JWT with refresh sessions, CSRF, per-tenant vectors, streaming uploads, signature-based file validation).

### Key highlights

- **Strict tenant isolation** at the vector-store layer: each user gets a dedicated Chroma collection named `omnidocs__<user_id>` (`vectorstore/chroma_store.py`).
- **HttpOnly cookie auth** with short-lived 15-minute access tokens and 7-day rotating refresh sessions tracked in `refresh_sessions` with reuse detection (`api/core/security.py`, `api/routes/auth.py`).
- **CSRF defense** via double-submit cookie + `X-CSRF-Token` header and an Origin/Host check on every mutating route (`api/dependencies.py`).
- **Streaming uploads** with hard size caps, magic-byte / MIME validation, OOXML archive structure checks, and zip-bomb guardrails (`api/services/ingestion_file.py`, `api/services/file_validation.py`).
- **Prompt-injection hardening**: the LLM prompt isolates untrusted context inside explicit tags and sanitizes retrieved text plus prior chat history (`generation/answer_generator.py`).
- **Rate limiting** is user-aware when authenticated and IP-aware otherwise, with Redis as the supported shared backend (`api/rate_limiter.py`).
- **Pluggable storage** (local filesystem or S3-compatible) and pluggable embedding/LLM providers (sentence-transformers, OpenAI, Gemini).
- **Cached runtime services**: embedding generator, retriever, and answer generator are `lru_cache`-backed singletons to avoid recreating heavy models per request (`api/services/runtime_services.py`).

---

## Table of Contents

- [Project Overview](#project-overview)
- [Architecture Overview](#architecture-overview)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Data Flow & Key Workflows](#data-flow--key-workflows)
- [Security](#security)
- [Getting Started](#getting-started)
- [Configuration](#configuration)
- [API Reference](#api-reference)
- [Testing](#testing)
- [Deployment](#deployment)
- [Performance & Scalability](#performance--scalability)
- [Known Limitations & Future Work](#known-limitations--future-work)
- [Contributing](#contributing)
- [License](#license)

---

## Architecture Overview

OmniDocs is a **two-tier modular monolith**:

1. A **FastAPI backend** that owns authentication, document ingestion, retrieval, generation, billing, admin, and usage analytics. It is composed as a set of focused routers (`api/routes/*.py`) backed by services and a SQLAlchemy data layer.
2. A **Next.js 16 App Router frontend** (React 19, Tailwind v4) that serves the marketing site, auth screens, dashboard, chat, admin console, and billing pages.

The frontend never calls the backend directly from the browser. All API traffic is sent to `/api/*` and rewritten to the backend through `frontend/next.config.ts`, which keeps cookies on the same origin and avoids CORS surface where possible. CSRF is enforced on mutating endpoints via a double-submit token plus an `Origin` / `Host` check.

State and side effects are split across:

- **SQLAlchemy database** (PostgreSQL via `psycopg` v3 by default; SQLite supported for tests) — users, refresh sessions, chat sessions, chat messages, usage events, support tickets, and billing fields.
- **ChromaDB persistent client** — one collection per user under `chroma_db/`.
- **Object storage** — local filesystem under `data/uploads/<user_id>/...` or an S3-compatible bucket, abstracted by `api/services/storage_backend.py`.
- **Optional Redis** — shared rate-limit storage when `RATE_LIMIT_STORAGE_URI` points at a Redis instance.
- **External providers** — Google OAuth, Stripe, an SMTP relay (Mailtrap or generic), and either Gemini or OpenAI for embeddings and generation.

### Component diagram

```mermaid
flowchart LR
    subgraph Browser
        UI[Next.js App Router<br/>React 19 + Tailwind v4]
    end

    subgraph NextEdge[Next.js Server]
        Proxy[proxy.ts route guard]
        Rewrite[next.config.ts<br/>/api/* rewrite]
    end

    subgraph Backend[FastAPI Backend]
        Auth[auth router]
        Docs[documents router]
        Chat[chat router]
        Admin[admin router]
        Usage[usage router]
        Billing[billing router]
        Limiter[SlowAPI rate limiter]
        Deps[Dependencies<br/>get_current_user, require_csrf, require_admin]
        Runtime[runtime_services<br/>cached embedder/retriever/generator]
        Validation[file_validation<br/>signature + OOXML checks]
        Ingest[ingestion + parsers + chunking]
        Retriever[retrieval.Retriever]
        Generator[generation.AnswerGenerator]
    end

    subgraph Data
        DB[(PostgreSQL<br/>users, refresh_sessions,<br/>chat_sessions, chat_messages,<br/>usage_events, support_tickets)]
        Chroma[(ChromaDB<br/>omnidocs__user_id)]
        Storage[(Local FS or S3<br/>data/uploads/user_id/)]
        Redis[(Redis<br/>optional, rate limits)]
    end

    subgraph External
        SMTP[SMTP / Mailtrap]
        Stripe[Stripe API + Webhooks]
        Google[Google OAuth]
        LLM[Gemini or OpenAI]
    end

    UI --> Proxy --> Rewrite --> Auth
    Rewrite --> Docs
    Rewrite --> Chat
    Rewrite --> Admin
    Rewrite --> Usage
    Rewrite --> Billing

    Auth --> Deps
    Docs --> Deps
    Chat --> Deps
    Admin --> Deps
    Usage --> Deps
    Billing --> Deps

    Docs --> Validation
    Docs --> Ingest
    Docs --> Runtime
    Runtime --> Retriever
    Runtime --> Generator
    Retriever --> Chroma
    Ingest --> Chroma
    Ingest --> Storage

    Auth --> DB
    Docs --> DB
    Chat --> DB
    Admin --> DB
    Usage --> DB
    Billing --> DB

    Limiter --> Redis
    Auth --> SMTP
    Auth --> Google
    Billing --> Stripe
    Generator --> LLM
```

---

## Tech Stack

Versions below are pinned in `requirements.txt` (generated by `pip-tools` from `requirements.in`) and `frontend/package.json`.

| Layer | Technology | Version | Why it is used |
|-------|------------|---------|----------------|
| Backend framework | FastAPI | 0.x (pinned in `requirements.txt`) — see `requirements.in` | Async-friendly Python web framework with first-class Pydantic and dependency-injection support, used for all routers in `api/routes/*`. |
| ASGI server | Uvicorn (`[standard]`) | 0.x | Production ASGI runner; `ProxyHeadersMiddleware` is imported from `uvicorn.middleware.proxy_headers`. |
| Database ORM | SQLAlchemy | 2.x | Declarative models in `api/models/*`, sessions managed in `api/database.py`. |
| Database driver | psycopg | 3.x (`psycopg[binary]`) | PostgreSQL driver selected via `postgresql+psycopg://` URLs. SQLite is also supported through standard SQLAlchemy URLs (used by `tests/conftest.py`). |
| Auth crypto | `python-jose[cryptography]`, `bcrypt` | pinned | JWT signing/decoding in `api/core/security.py`; bcrypt password hashing with a 72-byte safety truncation. |
| Validation | Pydantic (via FastAPI), `email-validator` | pinned | Schemas in `api/schemas/*`, password policy enforcement in `api/schemas/user.py`. |
| Rate limiting | SlowAPI | pinned | Shared `Limiter` in `api/rate_limiter.py`, exception handler wired in `api/main.py`. |
| Shared rate-limit store | Redis (optional) | pinned (`redis`) | Used when `RATE_LIMIT_STORAGE_URI` is set to a `redis://` URL. |
| Vector store | ChromaDB | 1.5.9 | Per-tenant persistent collections under `chroma_db/`. |
| Embeddings | `sentence-transformers`, `google-genai`, `openai` | pinned | Provider selected by `EMBEDDING_PROVIDER` in `embeddings/embedding_generator.py`. |
| LLM | `google-genai` (default) or `openai` | pinned | Provider selected by `LLM_PROVIDER` in `generation/answer_generator.py`. |
| Tokenization | `tiktoken` | pinned | Used in `chunking/text_chunker.py` for token-bounded chunking with overlap. |
| Document parsing | `pypdf`, `python-docx`, `python-pptx`, `openpyxl`, `beautifulsoup4` | pinned | Format-specific parsers in `parsers/*.py`. |
| File content validation | `filetype` | pinned | Magic-byte detection in `api/services/file_validation.py`. |
| HTTP client | `httpx` | pinned | Google OAuth token + userinfo exchange in `api/routes/auth.py`. |
| Object storage SDK | `boto3` | pinned | S3 backend in `api/services/storage_backend.py`. |
| Payments | `stripe` | pinned | Checkout, portal, and webhook handling in `api/routes/billing.py`. |
| Multipart parsing | `python-multipart` | pinned | Required by FastAPI for upload handling. |
| Env loading | `python-dotenv` | pinned | `.env` loaded from project root in `config/settings.py` and `api/database.py`. |
| Frontend framework | Next.js | 16.1.6 | App Router-based SSR/SSG/edge framework; rewrites and route guard live in `frontend/next.config.ts` and `frontend/proxy.ts`. |
| UI runtime | React | 19.2.3 | Drives the App Router pages and client components. |
| Styling | Tailwind CSS | ^4 (via `@tailwindcss/postcss`) | Utility-first styling for landing, auth, and dashboard pages. |
| Language (frontend) | TypeScript | ^5 | Type-safe API helpers in `frontend/lib/api.ts`. |
| Linting (frontend) | ESLint + `eslint-config-next` | ^9 / 16.1.6 | `npm run lint` script. |
| Container runtime | Docker + Docker Compose | [TODO: add minimum supported Docker / Compose version] | `Dockerfile.backend`, `frontend/Dockerfile`, `docker-compose.yml`. |
| Testing | `pytest` | pinned | Test harness in `tests/conftest.py`; suites in `tests/test_auth.py` and `tests/test_file_validation.py`. |
| Dev tooling | `pip-tools`, `pip-audit` | pinned in `requirements-dev.in` | `pip-compile` lock workflow and dependency vulnerability auditing. |

---

## Project Structure

```text
OmniDocs/
├── api/                            # FastAPI backend
│   ├── main.py                     # App factory, middleware wiring, router registration
│   ├── database.py                 # SQLAlchemy engine + session, loads DATABASE_URL from .env
│   ├── dependencies.py             # get_current_user, ensure_user_is_active, require_csrf, require_admin
│   ├── rate_limiter.py             # SlowAPI limiter with user-aware key function
│   ├── storage.py                  # Legacy dir_size_bytes helper (kept for compatibility)
│   ├── core/
│   │   ├── config.py               # Legacy stub re-exporting JWT_SECRET_KEY
│   │   └── security.py             # bcrypt + JWT (access + refresh with jti)
│   ├── models/
│   │   ├── user.py                 # Users table (auth, plan, verification, OAuth, billing fields)
│   │   ├── chat.py                 # ChatSession, ChatMessage
│   │   ├── refresh_session.py      # Revocable refresh tokens with rotation chain
│   │   ├── support.py              # SupportTicket
│   │   └── usage_event.py          # Per-user upload/query events
│   ├── routes/
│   │   ├── auth.py                 # signup, login, refresh, logout, /me, verify, Google OAuth
│   │   ├── documents.py            # upload, list, delete, query, storage usage
│   │   ├── chat.py                 # Chat sessions and messages
│   │   ├── admin.py                # User and ticket admin APIs
│   │   ├── usage.py                # /usage/me analytics endpoint
│   │   └── billing.py              # Stripe checkout, portal, webhook
│   ├── schemas/                    # Pydantic request/response models
│   ├── services/
│   │   ├── billing.py              # Stripe Checkout + Portal helpers
│   │   ├── file_validation.py      # Magic-byte, MIME, and OOXML structural validation
│   │   ├── ingestion_file.py       # Streaming temp-file writer with size cap
│   │   ├── runtime_services.py     # lru_cache-backed embedder/retriever/generator singletons
│   │   ├── storage_backend.py      # Local + S3 storage backends behind a common interface
│   │   └── usage_limits.py         # Plan resolution + monthly quota enforcement
│   └── utils/
│       ├── email.py                # SMTP sender with EmailDeliveryError
│       └── logging_config.py       # Shared "omnidocs" logger
├── chunking/
│   └── text_chunker.py             # Token-based chunking with overlap (cl100k_base)
├── config/
│   ├── settings.py                 # Env-driven settings + ensure_dirs()
│   └── plans.py                    # Free / Pro plan definitions
├── embeddings/
│   └── embedding_generator.py      # sentence-transformers / OpenAI / Gemini
├── generation/
│   └── answer_generator.py         # Prompt-injection-hardened LLM call
├── ingestion/
│   └── document_ingestion.py       # Parser dispatch + ParsedDocument output
├── parsers/                        # One module per supported file format
│   ├── base.py                     # ParsedDocument dataclass + normalize_source_file
│   ├── pdf_parser.py
│   ├── docx_parser.py
│   ├── pptx_parser.py
│   ├── xlsx_parser.py
│   ├── csv_parser.py
│   ├── html_parser.py
│   └── txt_parser.py               # Also serves .md / .markdown
├── retrieval/
│   └── retriever.py                # Embedding -> tenant-scoped Chroma search -> context formatting
├── vectorstore/
│   └── chroma_store.py             # Per-tenant collection wrapper + deterministic chunk IDs
├── frontend/
│   ├── app/
│   │   ├── page.tsx                # Marketing landing page
│   │   ├── layout.tsx              # Root layout + Geist fonts
│   │   ├── login/page.tsx          # Login + OAuth error display
│   │   ├── signup/page.tsx         # Signup with password policy UI
│   │   ├── verify-email/page.tsx   # Email verification page
│   │   └── dashboard/              # Authenticated app (uploads, chat, admin, billing)
│   ├── lib/api.ts                  # Cookie-aware fetch helpers, CSRF header injection, 401 silent refresh
│   ├── proxy.ts                    # Route guard for /dashboard, /login, /signup
│   ├── next.config.ts              # Rewrites /api/* to backend
│   ├── Dockerfile                  # Multi-stage build using NEXT_PUBLIC_API_URL build arg
│   ├── tsconfig.json
│   ├── eslint.config.mjs
│   └── package.json                # Next 16.1.6, React 19.2.3, Tailwind 4
├── tests/
│   ├── conftest.py                 # Fixtures: app, client, db_session, make_user, force_current_user
│   ├── test_auth.py                # Cookies, refresh rotation, reuse detection, OAuth auto-link block
│   ├── test_file_validation.py     # Signature, MIME, and OOXML checks
│   ├── test_documents.py           # Empty (placeholder)
│   └── test_billing.py             # Empty (placeholder)
├── main.py                         # CLI: python main.py index <path> | query "question" (uses CLI_USER_ID = "cli")
├── Dockerfile.backend              # Python 3.11-slim image for the API
├── docker-compose.yml              # backend + frontend services with named volumes
├── requirements.in                 # Top-level Python dependencies
├── requirements-dev.in             # Dev tooling (pip-tools, pip-audit, pytest)
├── requirements.txt                # Locked dependency graph (pip-compile output)
├── .env.example                    # Empty placeholder for users to copy into .env
├── VISION_ASSESSMENT.md            # Historical design notes (predates the current product)
└── README.md                       # This file
```

---

## Data Flow & Key Workflows

### 1. Signup (with optional email verification)

`api/routes/auth.py::signup`

1. Pydantic validates the email and enforces the password policy in `api/schemas/user.py` (length, character classes, common-password block-list).
2. If the email already exists, a `400 Email already registered` is raised. (See *Known Limitations* — this signup endpoint currently reveals existence; user-enumeration hardening is on the roadmap.)
3. If `EMAIL_VERIFICATION_REQUIRED=true`, a verification token and 24-hour expiry are generated, the user is persisted, and an email is sent via `api/utils/email.py`. If SMTP delivery raises `EmailDeliveryError`, the user row is rolled back and a `503` is returned.
4. If verification is disabled, fresh access + refresh cookies are issued immediately via `_issue_auth_response`.

### 2. Password login

`api/routes/auth.py::login`

1. Rate-limited to 5/minute by SlowAPI.
2. Looks up the user, verifies the password with `bcrypt.checkpw`, returns `401` on mismatch.
3. Rejects deactivated accounts with `403` (`is_active = false`).
4. Rejects unverified accounts with `403` when `EMAIL_VERIFICATION_REQUIRED=true` and the user has not verified.
5. On success, calls `_issue_auth_response` which:
   - Generates an access token (15-minute lifetime, `type: access`).
   - Creates a `RefreshSession` row with a fresh `jti` and a 7-day `expires_at`.
   - Sets three cookies: `omnidocs_token` (HttpOnly), `omnidocs_refresh` (HttpOnly), `omnidocs_csrf` (readable, double-submit token).

### 3. Silent refresh with rotation and reuse detection

`api/routes/auth.py::refresh` — also called automatically by `frontend/app/dashboard/layout.tsx` every 9 minutes and by `frontend/lib/api.ts` after any `401`.

1. Requires the CSRF header check via `require_csrf` since this is a mutating cookie-authenticated endpoint.
2. Decodes the refresh JWT (`type: refresh` + `jti` required by `decode_refresh_token`).
3. Looks up the matching `RefreshSession`. If the JTI is missing, the token is rejected.
4. **Reuse detection**: if the matching session is already `revoked_at`, the entire descendant chain (followed via `replaced_by_jti`) is revoked and the request is rejected. This neutralizes stolen refresh tokens after the first replay.
5. If valid, the current session is revoked, a new JTI + `RefreshSession` is created, and new access + refresh cookies are returned. The old session's `replaced_by_jti` points at the new one to preserve the rotation chain.

### 4. Google OAuth (when `SSO_ENABLED=true`)

`api/routes/auth.py::oauth_google_start` and `::oauth_google_callback`

1. `/auth/oauth/google/start` issues a CSRF-style state, sets `omnidocs_oauth_state` as an HttpOnly cookie, and redirects to Google's consent screen.
2. The callback verifies that the returned `state` matches the cookie, exchanges the auth code at `oauth2.googleapis.com/token`, and fetches the OIDC userinfo.
3. The `email_verified` flag must be true; otherwise the request is rejected.
4. If a user with the same `oauth_sub` exists, that user is loaded (after `ensure_user_is_active`).
5. **Account-takeover hardening**: if the email already exists as a password user but `oauth_sub` does not match, auto-linking is refused with a redirect to `/login?error=An%20account%20with%20this%20email...`. This blocks an attacker from claiming an existing email account simply by signing in with Google.

### 5. Document upload pipeline

`api/routes/documents.py::upload` (rate-limited 10/minute)

```mermaid
sequenceDiagram
    autonumber
    participant FE as Next.js client
    participant API as FastAPI /documents/upload
    participant Tmp as Temp file
    participant Val as file_validation
    participant Storage as Storage backend
    participant Ingest as ingest_document + chunker
    participant Embed as EmbeddingGenerator (cached)
    participant Chroma as ChromaDB (tenant collection)
    participant DB as Postgres

    FE->>API: POST multipart with file + X-CSRF-Token
    API->>API: require_csrf + get_current_user
    API->>API: Validate filename (Path basename), extension allow-list
    API->>API: enforce_upload_limit (plan monthly quota)
    API->>Tmp: write_upload_to_temp_file (streaming, max_bytes cap)
    Tmp-->>API: total_bytes
    API->>Val: validate_uploaded_file_content (magic bytes, MIME, OOXML structure)
    API->>API: enforce_storage_limit (incoming + current usage)
    API->>Storage: save_fileobj(user_id, filename, stream)
    API->>Ingest: ingest_document -> parse, chunk
    Ingest-->>API: ParsedDocument + chunks
    API->>Embed: embed_batch(chunk texts)
    API->>Chroma: delete_by_source(filename); add_chunks(texts, embeddings, metadatas)
    API->>DB: UsageEvent(event_type="upload")
    API-->>FE: 200 {file_name, chunk_indexed}
    Note over API,Storage: On any failure after save_fileobj, the stored file is deleted (rollback). Temp file is always removed.
```

Key safeguards:

- The `Content-Length` header is pre-checked, and the body is also enforced byte-by-byte during the streaming write so that an oversized upload never lands in memory or on disk in full.
- Filename traversal is prevented by enforcing `Path(filename).name == original_filename`.
- `validate_uploaded_file_content` rejects content/extension mismatches and validates OOXML archives (`[Content_Types].xml`, `word/document.xml`, etc.) plus zip-bomb heuristics (max members and compression ratio).
- `ChromaVectorStore(user_id=...)` resolves to a tenant-only collection, so chunks cannot leak across users.
- `_track_usage_event` writes a `UsageEvent` row used by both `/usage/me` and the plan-limit enforcers.
- Indexing failures (parser, embed, or vector store error) trigger deletion of the just-saved file.

### 6. Query and grounded generation

`api/routes/documents.py::query` (rate-limited 30/minute)

1. CSRF-protected, requires an authenticated user.
2. Question must be non-empty and ≤ 2000 characters.
3. `enforce_query_limit` blocks once the plan's `monthly_queries` is reached.
4. The cached `Retriever` performs `embed_text -> ChromaVectorStore(user_id=...).search` and formats the top-k chunks with source markers.
5. If no chunks are returned, the API responds with a refusal message and an empty sources list — no LLM call is made.
6. Otherwise the cached `AnswerGenerator` builds a structured prompt (`<retrieved_documents>`, `<prior_conversation>`, `<current_question>` sections) with sanitization of untrusted text and calls Gemini or OpenAI.
7. `_track_usage_event` records a `query` event.

### 7. Stripe billing

`api/routes/billing.py`

- `POST /billing/checkout` (CSRF-protected) lazily creates a Stripe Customer if missing, then opens a Checkout Session for the configured `STRIPE_PRICE_PRO_MONTHLY` price.
- `POST /billing/portal` (CSRF-protected) returns a Stripe Billing Portal URL for the current customer.
- `POST /billing/webhook` verifies signatures with `stripe.Webhook.construct_event` and updates `stripe_subscription_id`, `billing_status`, and `plan_id` based on `checkout.session.completed`, `customer.subscription.created`/`updated`, and `customer.subscription.deleted` events. Errors return generic messages and log details via `logger.exception` to avoid leaking internals.

---

## Security

### Authentication

- **Password hashing**: bcrypt with a 72-byte input cap (handled in `api/core/security.py`).
- **Password policy** (`api/schemas/user.py`): 8–128 chars, must include upper, lower, digit, special; common passwords are blocked.
- **JWT**: HS256 by default, secret loaded from `JWT_SECRET_KEY`. Startup fails fast if the secret is missing or shorter than 32 characters (`config/settings.py`).
- **Access tokens** are 15 minutes long and carry `type: access`. Refresh tokens are 7 days, carry `type: refresh` + `jti`, and require a matching server-side `RefreshSession` row to be honored.
- **Refresh-token rotation and reuse detection**: on every successful refresh the prior session is revoked; replaying a revoked token revokes the whole descendant chain (`_revoke_refresh_session_chain`).
- **Deactivation enforcement**: `ensure_user_is_active` is called from `get_current_user`, login, refresh, and OAuth callback so disabled accounts cannot continue using existing tokens.
- **Google OAuth**: anti-CSRF `state` cookie, mandatory `email_verified`, and refusal to silently link a Google identity onto an existing password account.

### Authorization

- Cookie-first auth in `get_token` (`api/dependencies.py`), with a fallback `Authorization: Bearer` header for server-to-server clients.
- Admin routes are gated by `require_admin`, which inspects `User.is_admin` (`api/routes/admin.py`).
- Tenant ownership is enforced both at the database layer (queries always filter by `current_user.id`) and at the vector store layer (per-tenant Chroma collections).

### CSRF

- Implemented in `api/dependencies.py::require_csrf`:
  - The frontend reads the readable `omnidocs_csrf` cookie and echoes it back as `X-CSRF-Token` for all mutating requests (`frontend/lib/api.ts::getCsrfHeaders`).
  - The server requires both to be present and equal.
  - The `Origin` header (when present) must end with the `Host` header, providing a second-layer check against cross-site requests.
- Applied to `/auth/refresh`, `/auth/logout`, `/documents/upload`, `/documents/{filename}` DELETE, `/documents/query`, `/chat/sessions`, `/chat/sessions/{id}/messages`, `/admin/users/{id}/active`, `/admin/support/tickets/{id}`, `/billing/checkout`, and `/billing/portal`. The Stripe `/billing/webhook` is intentionally exempt because it is verified via Stripe's HMAC signature.

### Secrets and credentials

- All secrets are sourced from `.env` loaded by `python-dotenv` in `config/settings.py` and `api/database.py`. `.env` is git-ignored.
- `JWT_SECRET_KEY`, `DATABASE_URL`, and provider keys (`GEMINI_API_KEY`, `OPENAI_API_KEY`, Stripe keys, Google OAuth keys, SMTP credentials, S3 keys) are read from the environment. None are hard-coded.
- Cookies are flagged `HttpOnly` (except the CSRF readable cookie), `SameSite=Lax`, and use `secure=COOKIE_SECURE`, which defaults to true when `APP_ENV=production`.

### Input validation and sanitization

- File uploads run through three layers of validation in `api/services/file_validation.py`:
  1. Extension allow-list (`config.ALLOWED_EXTENSIONS`).
  2. Magic-byte / MIME check via `filetype` for binary formats; text-mode UTF-8 sanity check for text/HTML/CSV/Markdown.
  3. OOXML archive validation (presence of required parts, member count ≤ 500, compression ratio ≤ 100) for `.docx`, `.xlsx`, `.pptx`.
- Filenames go through `Path(...).name` to eliminate traversal sequences.
- Question length is capped at 2000 characters in `/documents/query`.
- Pydantic models validate all request bodies (email format, password policy, billing payloads, admin update fields).

### LLM-specific defenses

- The system prompt explicitly tells the model that retrieved documents and prior history are untrusted data and not instructions.
- `_sanitize_untrusted_text` neutralizes null bytes and rewrites the structural tags (`</retrieved_documents>`, `</prior_conversation>`, `</current_question>`) so injected text cannot escape its section.
- Chat history is bounded to the last 8 turns and 4000 characters to limit prompt-context manipulation.

### Threat mitigations summary

| Threat | Mitigation |
|--------|------------|
| SQL injection | SQLAlchemy ORM with parameterized queries everywhere; no raw string interpolation. |
| XSS in auth cookies | Access and refresh cookies are `HttpOnly`; the readable CSRF cookie carries only a random token. |
| CSRF | Double-submit token + `Origin`/`Host` check on every mutating cookie-auth route. |
| Path traversal on upload | `Path(filename).name` enforcement plus tenant-scoped storage directories. |
| Memory-exhaustion DoS via uploads | Streaming temp-file write with hard byte cap; oversized requests get `413`. |
| File-spoofing (e.g. EXE as PDF) | Magic-byte / MIME check + OOXML structural validation. |
| Zip-bomb in `.docx`/`.xlsx`/`.pptx` | Member count + compression ratio guards in `_validate_ooxml_archive`. |
| Stolen refresh token replay | Server-side `RefreshSession` table with rotation, JTI uniqueness, and full-chain revocation on reuse. |
| OAuth account takeover | Refusal to auto-link Google identities to existing email accounts without matching `oauth_sub`. |
| Stripe webhook spoofing | Webhook verified with `STRIPE_WEBHOOK_SECRET` via `stripe.Webhook.construct_event`. |
| Prompt injection through documents | Structured prompt sections, untrusted-text sanitization, history bounding. |
| Information disclosure via errors | Routes return generic messages; details go to `logger.exception`. |
| Brute-force login / signup | SlowAPI rate limits (5/min on signup and login). |
| Cross-tenant data leak in vectors | One Chroma collection per user (`omnidocs__<user_id>`); no shared collection is ever queried. |

### Security-related dependencies and tooling

- `bcrypt`, `python-jose[cryptography]`, `email-validator`, `filetype` for runtime security.
- `pip-audit` listed in `requirements-dev.in` for dependency vulnerability scanning.

---

## Getting Started

### Prerequisites

- Python 3.10 or newer (Dockerfile uses 3.11-slim, requirements lockfile is pinned for Python 3.12 — see `requirements.txt` header).
- Node.js 18 or newer (Dockerfile uses `node:20-alpine`).
- PostgreSQL 14+ recommended (the project uses `psycopg` v3; SQLite is supported only for tests).
- Optional: Docker Desktop (or Docker Engine + Compose) for the one-command path.
- Optional: a Redis instance for shared rate-limit storage in multi-process or multi-host deployments.

### Local setup (no Docker)

1. **Clone and enter the repo**

   ```bash
   git clone <your fork or origin url>
   cd OmniDocs
   ```

2. **Create and populate `.env`** at the project root. See [Configuration](#configuration) for the full table. At minimum:

   ```dotenv
   JWT_SECRET_KEY=replace-with-a-32-plus-char-random-string
   DATABASE_URL=postgresql+psycopg://USER:PASSWORD@localhost:5432/omnidocs
   GEMINI_API_KEY=your-gemini-key
   ```

   If your password contains special characters (`@`, `:`, `/`, etc.) they must be URL-encoded in `DATABASE_URL`.

3. **Create the Python environment and install dependencies**

   ```bash
   python -m venv venv
   .\venv\Scripts\activate            # Windows PowerShell
   # source venv/bin/activate         # macOS/Linux
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Initialize the database**. Tables are created on startup by `Base.metadata.create_all(bind=engine)` in `api/main.py`. There are currently no Alembic migrations.

5. **Run the backend** (binding to `127.0.0.1` avoids IPv6 issues observed during development):

   ```bash
   uvicorn api.main:app --reload --host 127.0.0.1 --port 8000
   ```

6. **Run the frontend** in a separate shell:

   ```bash
   cd frontend
   npm install
   npm run dev
   ```

7. Open `http://localhost:3000`. The Next.js dev server proxies `/api/*` to `http://127.0.0.1:8000` based on `frontend/.env.local`.

### Docker Compose (one command)

```bash
docker compose up --build
```

This builds two services defined in `docker-compose.yml`:

- `omnidocs-backend` from `Dockerfile.backend`, exposing port `8000`, mounting named volumes `omnidocs_data` (uploads) and `omnidocs_chroma` (vector store).
- `omnidocs-frontend` from `frontend/Dockerfile`, baking `NEXT_PUBLIC_API_URL=http://backend:8000` into the Next build.

Run detached with `docker compose up -d --build` and stop with `docker compose down`.

### CLI mode

The original CLI is still wired up and uses a fixed `CLI_USER_ID = "cli"`:

```bash
python main.py index <file_or_dir>
python main.py query "your question"
```

Indexed CLI content goes into the `omnidocs__cli` Chroma collection and is not visible to authenticated web users.

---

## Configuration

All configuration is environment-driven via `.env`. The table below documents every variable read by the backend (`config/settings.py`, `api/database.py`, `api/services/storage_backend.py`, `api/services/billing.py`) and frontend (`frontend/.env.local`, `frontend/next.config.ts`, `frontend/Dockerfile`).

### Backend variables

| Variable | Required | Default | Purpose |
|----------|----------|---------|---------|
| `JWT_SECRET_KEY` | Yes | _none — fails at startup if missing or < 32 chars_ | HS256 secret for access and refresh JWTs. |
| `JWT_ALGORITHM` | No | `HS256` | JWT signing algorithm. |
| `DATABASE_URL` | Yes | _none — fails at startup if missing_ | SQLAlchemy URL. Example: `postgresql+psycopg://user:pass@localhost:5432/omnidocs`. |
| `APP_ENV` | No | `development` | When `production`, `COOKIE_SECURE` defaults to `true`. |
| `COOKIE_SECURE` | No | `true` in prod, `false` otherwise | Sets the `Secure` flag on auth and CSRF cookies. |
| `CHUNK_SIZE` | No | `512` | Tokens per chunk in `chunking/text_chunker.py`. |
| `CHUNK_OVERLAP` | No | `50` | Token overlap between adjacent chunks. |
| `MAX_FILE_SIZE` | No | `100` (MB) | Legacy generic limit. |
| `MAX_FILE_SIZE_MB` | No | `25` | Per-upload hard cap enforced during streaming. |
| `MAX_USER_STORAGE_MB` | No | `500` | Legacy default user storage cap. Effective limit comes from plan in `config/plans.py`. |
| `TOP_K` | No | `5` | Default number of retrieved chunks per query. |
| `EMBEDDING_PROVIDER` | No | `sentence-transformers` | One of `sentence-transformers`, `openai`, `gemini` / `google`. |
| `EMBEDDING_MODEL` | No | `sentence-transformers/all-MiniLM-L6-v2` | Model name passed to the selected provider. |
| `LLM_PROVIDER` | No | `gemini` | `gemini` or `openai`. |
| `LLM_MODEL` | No | `gemini-flash-latest` | LLM identifier passed to the provider. |
| `GEMINI_API_KEY` | Required if `LLM_PROVIDER=gemini` or `EMBEDDING_PROVIDER` is Gemini | _empty_ | Google AI Studio API key. |
| `OPENAI_API_KEY` | Required if using OpenAI | _empty_ | OpenAI API key. |
| `VECTOR_STORE_PATH` | No | `./chroma_db` | Chroma persistence directory. |
| `COLLECTION_NAME` | No | `omnidocs` | Base name; per-tenant collections become `<base>__<user_id>`. |
| `EMAIL_VERIFICATION_REQUIRED` | No | `false` | Toggles the email-verification signup flow. |
| `EMAIL_SENDER` | No | `mentesnotsibatu63@gmail.com` (development placeholder — change for production) | `From:` address on outgoing email. |
| `EMAIL_VERIFICATION_BASE_URL` | No | `http://localhost:3000` | Base URL for the verification link sent to users. |
| `MAILTRAP_HOST` / `MAILTRAP_PORT` / `MAILTRAP_USERNAME` / `MAILTRAP_PASSWORD` / `MAILTRAP_TOKEN` | No | empty / `2525` / empty / empty / empty | When `MAILTRAP_HOST` is set, it overrides the generic SMTP settings. |
| `SMTP_HOST` / `SMTP_PORT` / `SMTP_USERNAME` / `SMTP_PASSWORD` | No | `localhost` / `25` / empty / empty | Fallback SMTP relay used when Mailtrap is not configured. |
| `SMTP_USE_TLS` | No | `true` | Whether to call `starttls()`. |
| `SMTP_USE_SSL` | No | `false` | Reserved; the current implementation always uses plain SMTP + optional STARTTLS. |
| `SSO_ENABLED` | No | `false` | Master switch for `/auth/oauth/google/*` routes. |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | Required when SSO is on | empty | Google OAuth client credentials. |
| `GITHUB_CLIENT_ID` / `GITHUB_CLIENT_SECRET` | No | empty | Declared in settings but no GitHub OAuth route exists yet. [TODO: add GitHub OAuth implementation or remove these settings.] |
| `BACKEND_BASE_URL` | No | `http://127.0.0.1:8000` | Reserved for backend self-references. |
| `FRONTEND_BASE_URL` | No | `http://localhost:3000` | Used for OAuth callback URL construction and redirects. |
| `STRIPE_SECRET_KEY` | Required for billing routes | empty | Stripe API key. |
| `STRIPE_WEBHOOK_SECRET` | Required for `/billing/webhook` | empty | Used to verify webhook signatures. |
| `STRIPE_PRICE_PRO_MONTHLY` | Required for `/billing/checkout` | empty | Stripe Price ID for the Pro plan. |
| `BILLING_SUCCESS_URL` / `BILLING_CANCEL_URL` | No | `http://localhost:3000/dashboard/billing?success=1` / `http://localhost:3000/dashboard/billing/canceled=1` | Stripe Checkout redirects. |
| `STORAGE_BACKEND` | No | `local` | `local` (default) or `s3`. |
| `S3_BUCKET_NAME` / `S3_REGION` / `S3_ACCESS_KEY_ID` / `S3_SECRET_ACCESS_KEY` / `S3_ENDPOINT_URL` / `S3_KEY_PREFIX` | Required if `STORAGE_BACKEND=s3` | empty / empty / empty / empty / empty / `uploads` | S3 (or S3-compatible) connection settings. |
| `RATE_LIMIT_STORAGE_URI` | No | `memory://` | SlowAPI storage URI. Use a `redis://...` URI in production to share counters across processes. |
| `TRUST_PROXY_HEADERS` | No | `false` | When `true`, registers `ProxyHeadersMiddleware`. |
| `PROXY_TRUSTED_HOSTS` | No | `127.0.0.1,localhost` | Comma-separated list of trusted upstream proxies. |
| `CORS_ALLOWED_ORIGINS` | No | value of `FRONTEND_BASE_URL` | Comma-separated allowed origins. |
| `CORS_ALLOWED_METHODS` | No | `GET,POST,PATCH,DELETE,OPTIONS` | Comma-separated allowed methods. |
| `CORS_ALLOWED_HEADERS` | No | `Content-Type,X-CSRF-Token,Authorization` | Comma-separated allowed headers. |

### Frontend variables

| Variable | Required | Default | Purpose |
|----------|----------|---------|---------|
| `NEXT_PUBLIC_API_URL` | Yes (for non-default backend hostnames) | `http://127.0.0.1:8000` (in `next.config.ts`) / `http://backend:8000` (Docker build arg) | Target for the `/api/*` rewrite in `frontend/next.config.ts`. Must be set as a build arg in Docker so it is baked into the build. |

### Plan limits (`config/plans.py`)

| Plan | Monthly queries | Monthly uploads | Storage |
|------|-----------------|-----------------|---------|
| `free` (default) | 100 | 20 | 100 MB |
| `pro` | 5,000 | 1,000 | 5,000 MB |

---

## API Reference

All routes are mounted under the FastAPI app exposed by `api.main:app`. Mutating cookie-authenticated routes require both the auth cookie and the `X-CSRF-Token` header (frontend helpers handle this automatically). Rate limits below are taken from each route's `@limiter.limit(...)` decorator.

### Health

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Liveness probe — `{ "status": "ok", "message": "OmniDocs API is running" }`. |
| GET | `/health` | Returns `{ "status": "healthy" }`. |

### Auth (`/auth`)

| Method | Path | Auth | CSRF | Rate limit | Description |
|--------|------|------|------|------------|-------------|
| POST | `/auth/signup` | Public | No | 5/min | Create an account. Body: `UserSignup { email, password }`. Returns either tokens (verification off) or a 201 detail message (verification on). |
| POST | `/auth/login` | Public | No | 5/min | Email + password login. Returns `UserResponse` body and sets cookies. |
| POST | `/auth/refresh` | Cookie | Yes | _none_ | Rotates refresh session, returns user JSON, sets fresh cookies. |
| GET | `/auth/me` | Cookie | No | _none_ | Returns `{ id, email, is_admin }` for the current user. |
| POST | `/auth/logout` | Cookie | Yes | _none_ | Revokes the current refresh session and clears cookies. |
| GET | `/auth/verify/{token}` | Public | No | _none_ | Marks the user as verified if the token is valid and not expired. |
| GET | `/auth/oauth/google/start` | Public | No | 20/min | Begins Google OAuth (only when `SSO_ENABLED=true`). |
| GET | `/auth/oauth/google/callback` | Public | No | 20/min | Completes Google OAuth, sets cookies, redirects to `${FRONTEND_BASE_URL}/dashboard`. |

Example login:

```bash
curl -i -c cookies.txt -H 'Content-Type: application/json' \
  -d '{"email":"alice@example.com","password":"CorrectHorse9!"}' \
  http://localhost:8000/auth/login
```

### Documents (`/documents`)

| Method | Path | Auth | CSRF | Rate limit | Description |
|--------|------|------|------|------------|-------------|
| GET | `/documents` (and `/documents/`) | Cookie | No | _none_ | Lists files for the current user with `filename` and `uploaded_at`. |
| POST | `/documents/upload` | Cookie | Yes | 10/min | Multipart `file` upload. Streams to disk, validates content, indexes into ChromaDB. |
| DELETE | `/documents/{filename}` | Cookie | Yes | _none_ | Removes a file and all its chunks from the user's Chroma collection. |
| POST | `/documents/query` | Cookie | Yes | 30/min | Body: `{ question, top_k?, message_history?, session_id? }`. Returns `{ answer, sources, refused }`. |
| GET | `/documents/storage` | Cookie | No | _none_ | `{ used_bytes, limit_bytes, used_percent, plan_id, plan_name }`. |

Example upload:

```bash
curl -i -b cookies.txt \
  -H "X-CSRF-Token: $(grep omnidocs_csrf cookies.txt | awk '{print $7}')" \
  -F 'file=@/path/to/whitepaper.pdf' \
  http://localhost:8000/documents/upload
```

### Chat (`/chat`)

| Method | Path | Auth | CSRF | Rate limit | Description |
|--------|------|------|------|------------|-------------|
| POST | `/chat/sessions` | Cookie | Yes | 30/min | Creates a chat session. |
| GET | `/chat/sessions` | Cookie | No | 60/min | Lists sessions newest-first with eagerly-loaded messages. |
| GET | `/chat/sessions/{id}` | Cookie | No | 60/min | Returns one session if owned by the caller. |
| POST | `/chat/sessions/{id}/messages` | Cookie | Yes | 60/min | Appends a user/assistant message pair from a `{ question, answer }` body. |

### Admin (`/admin`, requires `is_admin = true`)

| Method | Path | CSRF | Rate limit | Description |
|--------|------|------|------------|-------------|
| GET | `/admin/users` | No | 30/min | Lists all users with auth/billing flags. |
| PATCH | `/admin/users/{id}/active` | Yes | 20/min | Body `{ is_active: bool }`. Admins cannot deactivate themselves. |
| GET | `/admin/support/tickets` | No | 30/min | Lists support tickets. |
| PATCH | `/admin/support/tickets/{id}` | Yes | 20/min | Body `{ status }` ∈ `{open, in_progress, resolved}`. |

### Usage (`/usage`)

| Method | Path | Auth | CSRF | Rate limit | Description |
|--------|------|------|------|------------|-------------|
| GET | `/usage/me` | Cookie | No | 60/min | `{ month, plan, queries_this_month, uploads_this_month, storage: { used_bytes, limit_bytes, used_percent } }`. |

### Billing (`/billing`)

| Method | Path | Auth | CSRF | Rate limit | Description |
|--------|------|------|------|------------|-------------|
| POST | `/billing/checkout` | Cookie | Yes | 10/min | Returns `{ url }` for Stripe Checkout. |
| POST | `/billing/portal` | Cookie | Yes | 10/min | Returns `{ url }` for Stripe Customer Portal. Requires an existing customer. |
| POST | `/billing/webhook` | Stripe signature | _exempt_ | 120/min | Verifies the Stripe signature and updates the user's plan/subscription. |

OpenAPI is also auto-generated at `http://localhost:8000/docs` (Swagger UI) and `/redoc` once the server is running.

---

## Testing

### Tooling

- `pytest` is the test runner (declared in `requirements.in` and `requirements-dev.in`).
- `tests/conftest.py` builds an isolated SQLite database per test, swaps `runtime_services` with lightweight `DummyEmbeddingGenerator`, `DummyRetriever`, and `DummyAnswerGenerator` so tests do not load real ML models, and disables the SlowAPI limiter.

### Running the suite

```bash
pip install -r requirements.txt        # includes pytest
pytest
```

Environment defaults are set inside `tests/conftest.py` (`DATABASE_URL=sqlite:///./tests_bootstrap.db`, `JWT_SECRET_KEY="x" * 32`, `GEMINI_API_KEY=test-gemini-api-key`), so no production secrets are required.

### Current coverage

| Suite | What it covers |
|-------|----------------|
| `tests/test_auth.py` | Cookie issuance on login; blocking inactive users; refresh rotation; rejection of revoked/missing refresh sessions; logout-driven revocation; reuse detection across the rotation chain; Google OAuth callback refusal to auto-link an existing email. |
| `tests/test_file_validation.py` | Rejection of mismatched magic bytes; acceptance of plain text; rejection of binary content under a text extension; rejection of malformed `.docx` archives; acceptance of a minimal valid OOXML archive. |
| `tests/test_documents.py` | _Placeholder — file is empty._ |
| `tests/test_billing.py` | _Placeholder — file is empty._ |

[TODO: add coverage percentage once a `pytest --cov` configuration is introduced.]

### Manual smoke checks

- Backend health: `curl http://localhost:8000/health`.
- Frontend health: open `http://localhost:3000` and verify the marketing page renders.
- Upload + query: sign up, upload a PDF via the dashboard, ask a question via `/dashboard/chat`.

---

## Deployment

There is no committed CI/CD pipeline yet (the repo contains no `.github/workflows/` or other CI definitions). [TODO: add a CI workflow that runs `pytest`, `npm run lint`, `pip-audit`, and a Docker build on pull requests.]

### Container deployment

`Dockerfile.backend` builds a `python:3.11-slim` image, installs the locked `requirements.txt`, and runs `uvicorn api.main:app --host 0.0.0.0 --port 8000`. `frontend/Dockerfile` builds the Next.js app with `npm ci && npm run build` and starts `npm run start`. `docker-compose.yml` wires the two with named volumes for `data/` and `chroma_db/`.

For production:

1. Provision a managed PostgreSQL (or self-host) and set `DATABASE_URL` accordingly.
2. Provision Redis and set `RATE_LIMIT_STORAGE_URI=redis://host:6379/0` so rate limits are coherent across replicas.
3. Set `APP_ENV=production` so `COOKIE_SECURE` defaults to `true`; ensure HTTPS termination is in place (the cookies will not be sent over plain HTTP).
4. If running behind a reverse proxy, set `TRUST_PROXY_HEADERS=true` and configure `PROXY_TRUSTED_HOSTS` to the upstream addresses so `X-Forwarded-For` is honored for SlowAPI's IP keys.
5. Choose a storage backend: keep `STORAGE_BACKEND=local` plus a persistent volume, or switch to `STORAGE_BACKEND=s3` and supply S3 credentials.
6. Build the frontend image with `NEXT_PUBLIC_API_URL` pointing at your backend's public origin (it is baked at build time).
7. Configure Stripe and SMTP credentials before enabling billing or email verification respectively.

### Infrastructure overview

[TODO: add the chosen cloud provider, regions, managed services (DB, Redis, object storage, secrets manager), and traffic ingress diagram for your deployment.]

---

## Performance & Scalability

### Caching

- `api/services/runtime_services.py` wraps `EmbeddingGenerator`, `Retriever`, and `AnswerGenerator` in `lru_cache(maxsize=1)` so heavy models load once per process instead of per request.
- `api/main.py` warms these caches at import time so the first request does not pay the cold-start cost.
- ChromaDB's persistent client is created on demand per request inside `ChromaVectorStore(user_id=...)`, but each request still benefits from on-disk persistence and the embedded HNSW index using cosine distance (`metadata={"hnsw:space": "cosine"}`).

### Database indexing

Indexes declared in the SQLAlchemy models (`api/models/*.py`):

- `users.email` (unique), `users.verification_token` (unique), `users.oauth_sub`, `users.stripe_customer_id` (unique), `users.stripe_subscription_id` (unique), `users.id` (primary).
- `refresh_sessions.jti` (unique), `refresh_sessions.user_id`, `refresh_sessions.expires_at`, `refresh_sessions.replaced_by_jti`.
- `chat_sessions.user_id`, `chat_messages.session_id`.
- `usage_events.user_id`, `usage_events.event_type`.
- `support_tickets.user_id`.

These cover the dominant query patterns (per-user lookups, refresh validation, monthly usage aggregation).

### Horizontal scalability considerations

- The Python backend is stateless apart from in-memory caches; it can be replicated horizontally behind a load balancer.
- Redis-backed rate limiting (`RATE_LIMIT_STORAGE_URI=redis://...`) keeps limits consistent across replicas.
- Refresh sessions are stored in PostgreSQL, so rotation is durable across instances.
- The S3 storage backend allows file uploads to scale beyond a single host; ChromaDB persistence currently relies on shared disk and would need a different backend (Chroma server, or a different vector DB) to scale horizontally beyond one node. See *Known Limitations*.
- Token-based chunking and batch embedding (`embed_batch`) keep ingestion costs sub-linear in document size when using sentence-transformers locally.

### Operational guardrails

- Plan-aware quotas (`enforce_query_limit`, `enforce_upload_limit`, `enforce_storage_limit`) protect against runaway usage.
- Per-route rate limits in SlowAPI protect against bursts on heavy endpoints.
- Streaming upload + magic-byte validation keeps malicious or oversized files from reaching the parsers.

---

## Known Limitations & Future Work

- **No database migrations.** `Base.metadata.create_all` is fine for first-run but does not support iterative schema changes. [TODO: add Alembic.]
- **Empty test placeholders.** `tests/test_documents.py` and `tests/test_billing.py` exist but contain no tests yet.
- **No CI/CD.** There are no GitHub Actions or other pipelines committed.
- **User-enumeration on signup.** `/auth/signup` currently returns a distinct `"Email already registered"` error. Switching to a generic response is on the security backlog.
- **GitHub OAuth.** Environment slots (`GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET`) are read but no GitHub OAuth route is implemented yet.
- **ChromaDB single-node persistence.** The embedded persistent client uses local disk under `chroma_db/`. Multi-replica deployments require migrating to a Chroma server or another vector store.
- **AV scanning and parser sandboxing.** Phase-2 hardening — ClamAV (or similar) virus scanning of uploads and isolated parser workers — is on the roadmap but not implemented.
- **HTML sanitization.** Parsed HTML content is currently injected into chunks as-is; HTML sanitization for indexed text is not yet hardened.
- **CSRF Origin check is heuristic.** `origin.endswith(host)` is intentionally permissive for development. Production deployments behind a reverse proxy should consider an explicit allow-list of trusted origins.
- **Default `EMAIL_SENDER`.** `config/settings.py` ships with a developer placeholder address; production deployments must override `EMAIL_SENDER`.
- **`BILLING_CANCEL_URL` default has a typo.** The default contains `canceled=1` as a path segment instead of a query string (`?canceled=1`). Override this in production.
- **No structured request logging or tracing.** A simple stdout logger is configured. [TODO: add OpenTelemetry or structured JSON logs for production observability.]
- **No PII redaction in logs.** Exception logs include user IDs and emails — adjust `api/utils/logging_config.py` if your compliance posture requires otherwise.
- **Refresh sessions are not pruned.** Expired or revoked rows accumulate. [TODO: add a periodic cleanup task.]

---

## Contributing

### Issues and pull requests

[TODO: add the issue tracker URL, PR template path, and any required Contributor License Agreement once the project's contribution channels are finalized.]

General guidance until those are in place:

- Open an issue describing the bug or feature before sending a non-trivial PR.
- Keep PRs scoped to a single concern; large changes should be split.
- Include reproduction steps for bugs and a test for behavior changes whenever practical.

### Coding standards

- **Python**: follow PEP 8 and prefer type hints. Match the style of nearby modules (FastAPI routers favor explicit `Depends(...)` and Pydantic models). Add or update tests in `tests/` for any change in `api/`.
- **TypeScript/React**: keep client components marked with `"use client"`. Run `npm run lint` (ESLint + `eslint-config-next`) before pushing.
- **Dependencies**: update `requirements.in` (and `requirements-dev.in`) and regenerate `requirements.txt` via `pip-compile` rather than editing `requirements.txt` by hand. Run `pip-audit` after upgrades.
- **Secrets**: never commit `.env`, real API keys, or fixtures containing secrets.

### Commit messages

[TODO: pin a commit-message convention (e.g. Conventional Commits) and document it here.] Current history uses short, imperative-mood subjects ("harden auth, storage, and ingestion reliability"). Following the same style keeps logs scannable.

### Branch strategy

[TODO: document the long-lived branches (e.g. `main`, `develop`) and the expected PR base branch once finalized.]

---

## License

[TODO: add the chosen license (e.g. MIT, Apache-2.0) here and place the corresponding `LICENSE` file at the project root. No license file is currently committed.]
