# Competitor Intelligence

A competitor monitoring prototype with a FastAPI API, PostgreSQL persistence, Celery/Redis jobs, AI-assisted change analysis, PDF reports, and a Next.js dashboard.

## Current capabilities

- JWT registration and login
- User-owned competitor CRUD
- Manual and scheduled monitoring jobs for competitor homepages and `/pricing`
- Snapshot history and Gemini-assisted change classification
- Asynchronous reports and PDF download
- Dashboard, monitoring, reports, analytics, and theme preference screens

Monitoring is currently a global daily schedule. Per-competitor monitored URL lists and frequency controls are not implemented. Password recovery, email verification, login rate limiting, profile editing, and notification preferences are also not implemented. The unused MCP adapter modules intentionally fail instead of returning fabricated results; production scraping and research use the direct Firecrawl and Tavily clients.

## Local development

1. Copy `.env.example` to `.env`, then set a unique `JWT_SECRET_KEY` and the AI provider keys needed for scans and reports.
2. Start PostgreSQL and Redis with `docker compose -f docker/docker-compose.yml up -d db redis`. If `competitor_intel_db` or `competitor_intel_redis` already exists, inspect it with `docker ps -a`; reuse it if it is running or start it if stopped. Do not remove a container or volume that holds data.
3. Install dependencies and apply migrations:

   ```powershell
   uv sync
   uv run alembic upgrade head
   ```

4. Start the API in one terminal:

   ```powershell
   uv run uvicorn src.main:app --reload --host 127.0.0.1 --port 8000
   ```

5. Start a Celery worker in another terminal. On Windows, use the solo pool:

   ```powershell
   uv run celery -A src.jobs.celery_app worker --loglevel=info --pool=solo
   ```

6. Start Celery Beat in a third terminal if you want scheduled jobs:

   ```powershell
   uv run celery -A src.jobs.celery_app beat --loglevel=info
   ```

7. Start the frontend in a fourth terminal:

   ```powershell
   Set-Location frontend
   npm.cmd ci
   npm.cmd run dev -- --hostname 127.0.0.1 --port 3000
   ```

The frontend API base is configured in `frontend/.env.local` and should point to the API origin, normally `http://127.0.0.1:8000`. Development API documentation is at `/docs` on the API origin.

## Production deployment template

Production configuration is fail-closed: set `ENV=production`, `DEBUG=false`, use a unique random JWT secret, and provide explicit HTTPS CORS origins. Create `.env.production` from `.env.production.example`, replacing every placeholder. The PostgreSQL password must match `POSTGRES_PASSWORD` and the password in `DATABASE_URL`; the example uses URL-safe random hex to avoid URL-encoding ambiguity.

Build and start the production Compose stack:

```powershell
docker compose --env-file .env.production -f docker/docker-compose.production.yml config --quiet
docker compose --env-file .env.production -f docker/docker-compose.production.yml build
docker compose --env-file .env.production -f docker/docker-compose.production.yml run --rm web alembic upgrade head
docker compose --env-file .env.production -f docker/docker-compose.production.yml up -d
```

The production template keeps PostgreSQL and Redis private and binds the frontend and API to loopback. Put a TLS-terminating reverse proxy in front of them, route the frontend host to port 3000 and the API host to port 8000, and set `PUBLIC_API_BASE_URL` and `CORS_ALLOWED_ORIGINS` to those HTTPS origins. Report PDFs use a shared persistent volume between the API and worker. Back up PostgreSQL and that report volume before upgrades.

**This repository is not yet cleared for real users or sensitive production data.** The browser stores its bearer token in JavaScript-readable storage, and the application lacks login rate limiting, email verification, and password recovery. These are release blockers that require implementation and security review; stricter deployment settings alone do not solve them. A production deployment also needs a verified TLS proxy, provider credentials, backups, and monitoring configured for its host.

## Checks

```powershell
uv run pytest tests/ -q
Set-Location frontend
npm.cmd ci
npm.cmd run lint
npm.cmd run build
```

CI runs these backend and frontend checks on pushes and pull requests. Release tags build backend, worker, and frontend container images.

The repository currently has outstanding Black/isort formatting and mypy errors in legacy Python modules. Those checks are not CI gates until the existing codebase is brought into compliance; see [PRODUCTION_READINESS.md](PRODUCTION_READINESS.md) for the current release assessment.
