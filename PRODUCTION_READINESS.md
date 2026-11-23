# Production Readiness Review

**Status: not approved for production use.** Configuration and container packaging are safer now, but authentication and operational controls still need work and external deployment checks remain outstanding.

## Implemented in this review

- Non-development settings reject development JWT secrets, debug mode, unsupported JWT algorithms, invalid token lifetimes, wildcard CORS, and non-HTTPS CORS origins.
- Production Compose template keeps PostgreSQL and Redis private, binds web services to loopback, enables health checks, restarts services, and persists database, Redis, and generated PDF data.
- Backend images use the repository's `uv.lock`, run as a non-root user, and no longer depend on Poetry or an absent Poetry lockfile.
- Frontend has a multi-stage production image. CI builds the backend, worker, and frontend and runs backend/frontend checks.
- Frontend production dependencies were updated via targeted compatible fixes for the registry advisories. The lockfile audit returned zero vulnerabilities; CI now enforces an audit gate.
- Fake MCP search/scrape data and the legacy fake PDF byte response now fail explicitly rather than looking successful.
- API responses include baseline security headers; auth logs no longer include email addresses or exception messages.
- Added regression tests for production configuration gates and the unsupported PDF helper.

## Release blockers

- **Remote crawling boundary:** target validation in this API cannot guarantee the external Firecrawl service will block private-IP redirects or DNS rebinding. Confirm and configure equivalent restrictions at the crawler provider boundary before allowing untrusted users to submit URLs.
- **Browser token storage:** the access token remains readable by page JavaScript in `localStorage` and a JavaScript-readable cookie. Move to a secure HttpOnly cookie/BFF design with CSRF protection before serving sensitive accounts.
- **Authentication abuse and recovery:** login/register have no rate limiting, email verification, password reset, or refresh/revocation flow. Implement and test account lifecycle controls.
- **Authorization and e2e:** live API verification covered two-account isolation and competitor CRUD; full browser navigation and provider-backed scan/report flows remain unverified.
- **Static analysis:** existing `mypy src` reports 55 errors across 19 files; `isort --check-only src tests` reports widespread legacy import-order failures. Black checking also found files requiring formatting. Resolve these technical debts and restore static checks as CI gates.
- **Deployment operations:** TLS proxy, provider credentials, email sender verification, backup/restore, alerting, and real-host health checks must be configured and verified in the deployment environment.

## Verification evidence

- Frontend ESLint and production Next.js build: passed in the Linux Docker build; `npm ci --omit=dev` reported zero vulnerabilities.
- Focused production/security regression tests: 11 passed.
- Full backend pytest suite in the Linux test image: **121 passed, 5 warnings**. Three warnings are unawaited coroutine warnings from monitoring test mocks; two are dependency deprecations.
- Backend, worker, and frontend production images built successfully. Production Compose configuration validated; isolated stack health checks passed for API, PostgreSQL, Redis, and frontend. Database migrations completed; Celery worker responded to `inspect ping`.
- Production API smoke: health/security headers, unauthenticated access rejection, registration/login, competitor create/list/detail/update/delete, and cross-account access denial passed. Configured CORS origin was accepted and an untrusted origin rejected; production `/docs` returned 404. Frontend returned the application HTML with HTTP 200.
- Third-party Firecrawl/Tavily scans, provider-backed AI reports, email/PDF delivery, full browser navigation, and responsive visual review were not exercised; real provider credentials and deployment services were not configured for the isolated smoke test.
- A prior local backend run had 113 passing tests. The fresh Linux run above is the current full-suite result.
