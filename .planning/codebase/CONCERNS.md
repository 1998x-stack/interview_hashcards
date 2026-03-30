# Codebase Concerns

**Analysis Date:** 2026-03-30

## Tech Debt

**Incomplete Error Handling in Web Routes:**
- Issue: Flask routes in `hashcards/web/app.py` lack comprehensive error handling. The `/review` endpoint assumes `rating` can be converted to int without validation, and `deck_name` from `request.form` could be None or malformed.
- Files: `hashcards/web/app.py` (lines 102-120)
- Impact: Invalid form submissions could crash the server or cause unhandled exceptions. No user-facing error messages provided.
- Fix approach: Add try-except blocks around form parsing, validate `rating` is within [1-4], sanitize `deck_name` input. Return 400 errors with helpful messages.

**Brittle Card Caching:**
- Issue: `HashcardsApp._load_all_cards()` loads all card files into memory at startup. Manual reload required via `/api/reload` after editing files. No automatic detection of file changes.
- Files: `hashcards/web/app.py` (lines 42-64)
- Impact: Users editing card files won't see changes until server restart or manual reload. Risk of reviewing stale cards.
- Fix approach: Implement file watching (e.g., `watchdog` library) to auto-reload on changes. Cache versioning via file hash.

**String Interpolation in SQL (Potential Injection):**
- Issue: `storage.py` line 209 uses f-string to build SQL LIMIT clause: `query += f" LIMIT {limit}"`. Though `limit` comes from application code, this is not parametric.
- Files: `hashcards/storage.py` (line 209)
- Impact: Low risk (internal use) but violates SQL safety best practices. Could be exploited if `limit` becomes user-controllable.
- Fix approach: Use proper parameterized query: `query += " LIMIT ?"` with `params.append(limit)`.

**Hardcoded Database Path in CLI:**
- Issue: Database path always defaults to `.hashcards.db` in the cards directory. No option to use custom database location.
- Files: `hashcards/web/app.py` (lines 36-37), `hashcards/cli.py` (line 39)
- Impact: Users cannot separate study data from card files. Limited flexibility for multi-directory setups.
- Fix approach: Add `--db-path` argument to CLI commands. Load from environment variable fallback.

**Secret Key Generation on Every Start:**
- Issue: Flask app generates a new random secret key on each restart: `self.app.secret_key = os.urandom(24)` (line 48 in app.py).
- Files: `hashcards/web/app.py` (line 48)
- Impact: Sessions would invalidate on server restart (though minimal impact for local-first app). Could complicate debugging.
- Fix approach: Generate key once on first run, store in `.hashcards/secret.key`, load on startup.

## Known Bugs

**Race Condition on Card Reload:**
- Symptoms: If user edits and reloads cards while a study session is active, references to old card objects could become stale.
- Files: `hashcards/web/app.py` (lines 42-64, 129-133)
- Trigger: Start review session, hit `/api/reload` in separate tab while mid-review
- Workaround: Restart server to reload cards

**Cloze Text Replacement Logic Bug:**
- Symptoms: Multiple identical cloze deletions in same card don't display correctly. Using `.replace()` without replacement count limits causes incorrect substitution.
- Files: `hashcards/parser.py` (lines 133-140), `hashcards/web/templates/study.html` (lines 39-44)
- Trigger: Create card like "C: The [blue] sky and [blue] ocean" - displays incorrectly
- Workaround: Use unique deletion text

**Missing Deck Validation on Form Submission:**
- Symptoms: If user submits review with non-existent `deck_name`, stored schedule uses wrong deck name.
- Files: `hashcards/web/app.py` (line 116)
- Trigger: Edit HTML form before submitting, change `deck_name` value
- Impact: Stats queries become inconsistent for modified decks

## Security Considerations

**XSS via Unsafe Template Rendering:**
- Risk: Card content (question, answer, cloze text) is rendered with `| safe` filter in templates without HTML escaping. User-provided content in .md files could contain script tags.
- Files: `hashcards/web/templates/study.html` (lines 34, 43), potentially other templates
- Current mitigation: Cards are in user-owned local files, not user-submitted data
- Recommendations: Replace `| safe` with proper escaping. Sanitize HTML content using `bleach` or similar. Or document that .md files should be treated as code (don't load untrusted card files).

**Unvalidated File Paths:**
- Risk: If card directory path is user-controlled (e.g., web parameter), path traversal attacks possible.
- Files: `hashcards/web/app.py` (line 34), `hashcards/cli.py` (lines 17, 65)
- Current mitigation: Path only comes from CLI arguments/environment, not web requests
- Recommendations: Resolve paths absolutely and validate they're within allowed directory. Use `pathlib.Path.resolve()` and check startswith() against expected directory.

**Hardcoded Default Parameters in Scheduler:**
- Risk: FSRS parameter weights are hardcoded. If discovered to be suboptimal, all cards use wrong parameters.
- Files: `hashcards/scheduler.py` (lines 70-76)
- Current mitigation: Parameters based on research (FSRS4Anki)
- Recommendations: Add ability to customize parameters via config file. Document parameter meaning and where they come from.

## Performance Bottlenecks

**Linear Card Loading:**
- Problem: `_load_all_cards()` iterates through all .md files and parses them on every server start.
- Files: `hashcards/web/app.py` (lines 51-64)
- Cause: No caching of parsed cards; regex parsing happens every startup
- Current capacity: <10,000 cards acceptable (probably <5s startup time)
- Improvement path: Cache parsed cards as pickle/json files keyed by file hash. Only re-parse if file changed.

**Full Database Scan for Stats:**
- Problem: `get_stats()` executes multiple COUNT queries without WHERE clause filtering.
- Files: `hashcards/storage.py` (lines 214-257)
- Cause: Queries aggregate over entire table even for single deck
- Improvement path: Pre-compute stats in scheduled job. Add materialized view for common aggregations.

**No Pagination in Browse:**
- Problem: `/browse` loads all cards into memory for template rendering.
- Files: `hashcards/web/app.py` (lines 135-153)
- Cause: No LIMIT/OFFSET on card retrieval
- Improvement path: Paginate browse view (50 cards/page). Add filtering by deck/search.

## Fragile Areas

**Parser Regex Patterns:**
- Files: `hashcards/parser.py` (lines 44-46)
- Why fragile: Regex patterns assume strict format (Q: on separate line, A: on separate line). Minor whitespace variations break parsing.
- Safe modification: Add `\s*` for flexible whitespace. Test with malformed input. Consider switch to proper Markdown parser.
- Test coverage: `cmd_validate` catches parsing errors but no unit tests

**Card Hash Collision Handling:**
- Files: `hashcards/hasher.py` (lines 31-38), `hashcards/storage.py` (lines 45-60)
- Why fragile: 16-char SHA-256 hash (64 bits) reduces collision risk but doesn't eliminate it. Two different cards could theoretically get same hash.
- Safe modification: Use full 64-char SHA-256 hash or add secondary uniqueness check. Add collision detection on card load.
- Test coverage: No unit tests for hasher

**DateTime Handling Across Timezones:**
- Files: `hashcards/scheduler.py` (uses `datetime.now()`), `hashcards/storage.py` (datetime serialization)
- Why fragile: Uses naive datetime (no timezone). If user travels or system timezone changes, scheduling calculations break.
- Safe modification: Use UTC everywhere. Store as ISO 8601 with timezone. Document timezone assumptions.
- Test coverage: No timezone-aware tests

## Scaling Limits

**In-Memory Card Cache:**
- Current capacity: 10,000 cards ≈ 1-2MB memory (rough estimate)
- Limit: ~100,000 cards becomes unwieldy (10-20MB). Flask memory consumption dominates.
- Scaling path: Move to lazy loading. Load cards on demand by deck. Implement LRU cache.

**SQLite Query Performance:**
- Current capacity: Tested up to ~10,000 reviews. Indexes should handle this.
- Limit: 1,000,000+ reviews → queries slow. SQLite not optimal for large analytic queries.
- Scaling path: Migrate to PostgreSQL or use background task to archive old reviews.

**Database File Size:**
- Current: 10,000 cards + 100,000 reviews ≈ 10-20MB SQLite file
- Limit: Single-file database becomes unwieldy beyond 1GB
- Scaling path: Partition by year. Archive old reviews to separate tables.

## Dependencies at Risk

**Flask Security Vulnerabilities:**
- Risk: Flask is actively maintained but local-first apps less critical. No auto-update mechanism.
- Files: `requirements.txt` specifies `flask>=2.3.0` (broad version range)
- Mitigation: Pin to specific patch version (e.g., `flask==2.3.4`)
- Migration plan: Review Flask changelog quarterly. Test before upgrading. Consider moving to Starlette/FastAPI if security becomes concern.

**Outdated Python Version:**
- Risk: Project doesn't specify Python version. Assumes 3.8+. Targeting newer Python enables modern features/security.
- Files: No `.python-version` or `pyproject.toml` with python_requires
- Mitigation: Document minimum Python 3.9. Add to setup.py: `python_requires=">=3.9"`
- Migration plan: Verify on Python 3.9, 3.10, 3.11

**No Lock File:**
- Risk: `requirements.txt` uses version ranges. Dependencies pull latest compatible versions - non-deterministic installs.
- Files: `requirements.txt` only lists `flask>=2.3.0`
- Mitigation: Use pip-tools or Poetry to generate lock file (requirements.lock)
- Migration plan: `pip-compile requirements.in > requirements.txt`

## Missing Critical Features

**No Export Functionality:**
- Problem: Users cannot export study data, only cards (which are plaintext anyway)
- Blocks: Can't analyze learning patterns, create statistics reports
- Gaps: Anki export, CSV export, statistics summary export

**No Import/Merge:**
- Problem: Can't import cards from other hashcards instances or Anki
- Blocks: Collaborative deck building, migrating from Anki
- Gaps: Anki importer, CSV importer, deck merging with conflict resolution

**No Backup Strategy:**
- Problem: If `.hashcards.db` corrupts, all scheduling data lost (cards recoverable from .md)
- Blocks: Users with critical learning schedules cannot guarantee data safety
- Gaps: Auto-backup on shutdown, backup history, restore functionality

**No Sync Across Devices:**
- Problem: README mentions Git sync possibility but not implemented
- Blocks: Mobile studying, multi-device learning
- Gaps: Git-based sync, conflict resolution, mobile app

## Test Coverage Gaps

**No Unit Tests for Core Scheduler:**
- What's not tested: FSRS algorithm correctness, parameter calculations, state transitions
- Files: `hashcards/scheduler.py` (entire module)
- Risk: Algorithm bugs go unnoticed. Parameter tuning breaks silently.
- Priority: HIGH - Scheduler is critical path for learning accuracy

**No Integration Tests for Web Routes:**
- What's not tested: Full review workflow, form validation, edge cases (missing ratings, invalid decks)
- Files: `hashcards/web/app.py` (all routes)
- Risk: Broken workflows discovered by users only
- Priority: HIGH

**Parser Edge Cases Untested:**
- What's not tested: Malformed Markdown, special characters, Unicode, empty questions/answers
- Files: `hashcards/parser.py`
- Risk: Parser crashes on unexpected input
- Priority: MEDIUM

**No Database Migration Tests:**
- What's not tested: Schema upgrades, data corruption recovery
- Files: `hashcards/storage.py`
- Risk: Cannot safely add columns/tables to existing .db files
- Priority: MEDIUM

**No Concurrent Access Tests:**
- What's not tested: Multiple review submissions in quick succession, simultaneous edits + reviews
- Files: `hashcards/web/app.py`, `hashcards/storage.py`
- Risk: Race conditions on card reload or concurrent schedule updates
- Priority: MEDIUM

---

*Concerns audit: 2026-03-30*
