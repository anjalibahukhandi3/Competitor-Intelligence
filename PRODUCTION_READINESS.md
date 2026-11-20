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

- **Browser token storage:** the access token remains readable by page JavaScript in `localStorage` and a JavaScript-readable cookie. Move to a secure HttpOnly cookie/BFF design with CSRF protection before serving sensitive accounts.
- **Authentication abuse and recovery:** login/register have no rate limiting, email verification, password reset, or refresh/revocation flow. Implement and test account lifecycle controls.
- **Remote crawling boundary:** target validation in this API cannot guarantee the external Firecrawl service will block private-IP redirects or DNS rebinding. Confirm and configure equivalent restrictions at the crawler provider boundary before allowing untrusted users to submit URLs.
- **Authorization and e2e:** tenant-isolation unit coverage exists, but a live two-account API/browser test has not been completed in this environment.
- **Static analysis:** existing `mypy src` reports 55 errors across 19 files; `isort --check-only src tests` reports widespread legacy import-order failures. Black checking also found files requiring formatting. Resolve these technical debts and restore static checks as CI gates.
- **Deployment operations:** TLS proxy, provider credentials, email sender verification, backup/restore, alerting, and real-host health checks must be configured and verified in the deployment environment.

## Verification evidence

- Frontend ESLint: passed.
- Frontend ESLint: passed after the production-image changes.
- Frontend Next.js build after enabling Next standalone output failed on this Windows/OneDrive workspace with `EPERM` while copying traced files. The standalone mode was removed in favor of a conventional multi-stage `next start` image; the final frontend build still needs a clean rerun.
- Focused production/security regression tests: 11 passed.
- Full backend suite: 113 tests passed in an earlier local run; a fresh full-suite run was not completed in this review because async API tests stalled in this Windows execution environment.
- Container image builds, production Compose launch, real database migrations, Celery execution, third-party scans/reports, and browser flows remain unverified here.
