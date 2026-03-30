# External Integrations

**Analysis Date:** 2026-03-30

## APIs & External Services

**Not detected** - No external API integrations found. Application is completely self-contained.

## Data Storage

**Databases:**
- SQLite (local file-based)
  - Connection: File path `.hashcards.db` in user's cards directory
  - Client: Built-in Python `sqlite3` module
  - Scope: Stores scheduling state and review history only
  - Location: `hashcards/storage.py`

**File Storage:**
- Local filesystem only
  - Card files: Plain Markdown files in user-specified directory
  - Database: `.hashcards.db` SQLite file
  - Templates: Bundled with package in `hashcards/web/templates/`
  - No cloud storage, no S3, no CDN

**Caching:**
- In-memory card cache only
  - Populated on app startup: `self.cards_cache = {}` in `HashcardsApp._load_all_cards()` (`hashcards/web/app.py:43-64`)
  - No Redis, Memcached, or distributed cache
  - Cache invalidated via `/api/reload` endpoint

## Authentication & Identity

**Auth Provider:**
- None - No user authentication system
- Single-user assumption
- Flask session secret key generated randomly (not persisted): `os.urandom(24)` in `hashcards/web/app.py:48`
- Design: Intended for single-user or local trusted network only

**Authorization:**
- Not implemented - No access control layers detected

## Monitoring & Observability

**Error Tracking:**
- Not detected - No Sentry, Rollbar, or equivalent

**Logging:**
- Console output only
  - Print statements in CLI: `hashcards/cli.py`
  - Flask debug logging (when debug mode enabled)
- No file-based logs
- No structured logging library

**Metrics/Analytics:**
- Not detected - No analytics, tracking, or telemetry

## CI/CD & Deployment

**Hosting:**
- Self-hosted only (intended for local machines)
- No cloud platform integrations (AWS, GCP, Azure, etc.)

**CI Pipeline:**
- Not detected - No GitHub Actions, GitLab CI, or equivalent

**Deployment:**
- Manual Python installation
- Entry point: `hashcards` CLI script (installed via `setup.py` entry_points)
- Run command: `hashcards drill ./CardDirectory`

## Environment Configuration

**Required env vars:**
- None detected - All configuration via CLI arguments

**Optional env vars:**
- None detected

**Secrets location:**
- No secrets management system
- Flask session key: Generated randomly at runtime (not persisted)
- Design principle: Local-first, no credentials needed

## Webhooks & Callbacks

**Incoming Webhooks:**
- Not detected - No webhook endpoints

**Outgoing Webhooks:**
- Not detected - No external service notifications

## External Dependencies Summary

**Zero external service dependencies:**
- ✓ No authentication provider (Auth0, Firebase, etc.)
- ✓ No database service (AWS RDS, Firebase, Supabase, etc.)
- ✓ No file storage (S3, GCS, Azure Storage, etc.)
- ✓ No API services (third-party APIs)
- ✓ No logging service (Datadog, CloudWatch, etc.)
- ✓ No monitoring/observability (New Relic, AppDynamics, etc.)
- ✓ No CI/CD platform
- ✓ No CDN or asset delivery

**Only external package:**
- Flask 2.3.0+ (HTTP framework)

## Data Sovereignty

**By Design:**
- All card content stored as Markdown files (user controls location)
- All scheduling state in local SQLite database (user controls location)
- No data leaves user's machine
- No network connectivity required after startup
- Data export: Cards are already in portable Markdown format

---

*Integration audit: 2026-03-30*
