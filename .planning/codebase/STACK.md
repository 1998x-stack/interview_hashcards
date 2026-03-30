# Technology Stack

**Analysis Date:** 2026-03-30

## Languages

**Primary:**
- Python 3.8+ - Core application language (spaced repetition engine, data processing, CLI)

**Secondary:**
- HTML/Jinja2 - Web templates for Flask interface
- Markdown - Card file format (source of truth for learning content)

## Runtime

**Environment:**
- Python 3.8, 3.9, 3.10, 3.11 (supported versions via `setup.py`)
- No Node.js or other runtimes required

**Package Manager:**
- pip/setuptools
- Lockfile: Not detected (single dependency declared manually)

## Frameworks

**Core:**
- Flask 2.3.0+ - Lightweight web application framework for study interface
  - Location: `hashcards/web/app.py`
  - Purpose: HTTP server, routing, template rendering, session management

**Algorithm:**
- FSRS (Free Spaced Repetition Scheduler) - Custom implementation (not a package)
  - Location: `hashcards/scheduler.py`
  - Purpose: Implements state-of-the-art spacing algorithm for optimal learning
  - Based on: https://github.com/open-spaced-repetition/fsrs4anki

**Testing:**
- Not detected - No test framework in use

**Build/Dev:**
- setuptools - Python package building and distribution
  - Entry point: `hashcards.cli:main` for console script installation

## Key Dependencies

**Critical:**
- flask>=2.3.0 - Web framework for study interface
  - Why it matters: Only external dependency; handles all HTTP/routing/templating

**Standard Library Used (No External Deps Needed):**
- sqlite3 - Local database for scheduling state (built-in)
- hashlib - Content-addressable card identification (built-in)
- re - Regular expression parsing of card format (built-in)
- argparse - CLI argument parsing (built-in)
- pathlib - File system operations (built-in)
- dataclasses - Type-safe data structures (built-in, Python 3.7+)
- datetime - Scheduling calculations (built-in)
- enum - Card states and ratings (built-in)
- math - FSRS algorithm calculations (built-in)

## Configuration

**Environment:**
- No required environment variables detected
- Flask secret key generated dynamically: `os.urandom(24)` in `hashcards/web/app.py:48`

**Build:**
- `setup.py` - Package metadata and dependencies

**Runtime Parameters:**
- Cards directory: Command-line argument (e.g., `hashcards drill ./Cards`)
- Database path: Auto-generated as `.hashcards.db` in cards directory (overridable)
- Flask host/port: CLI arguments with defaults (localhost:8000)
- Debug mode: Optional CLI flag

## Database

**Type:** SQLite
- Location: `.hashcards.db` (local file, auto-created)
- Scope: Stores only scheduling state and review history
- Content: Cards themselves stored as Markdown files, not in DB
- Initialization: Automatic schema creation in `CardStorage.__init_db()` (`hashcards/storage.py:39-97`)

**Tables:**
- `schedules` - Current scheduling state for each card (indexed on due, deck_name)
- `reviews` - Historical review logs (indexed on card_hash, review_time)

## File Storage

- **Cards:** Plain Markdown files (user-editable, no binary format)
  - Location: User-specified directory (e.g., `./Cards/` or `./KnowledgeCards/`)
  - Format: Markdown with Q&A or Cloze deletion syntax
  - Example: `Q: What is...` / `A: ...` or `C: Text with [answers]`

- **Templates:** Bundled Jinja2 HTML templates
  - Location: `hashcards/web/templates/*.html`
  - Included in package via `setup.py` `package_data`

## Platform Requirements

**Development:**
- Python 3.8+
- No build system required (pure Python, no C extensions)
- pip for dependency installation

**Production:**
- Python 3.8+
- Flask development server suitable for single-user/small-team use
- Can be deployed behind reverse proxy (nginx, etc.) if needed
- SQLite database file access required (local filesystem)

## Deployment Model

**Type:** Local-first, single-machine
- No cloud infrastructure required
- No external services required
- All data stored locally (Markdown + SQLite)
- Designed for individual users or small study groups
- Can be self-hosted on any machine with Python 3.8+

---

*Stack analysis: 2026-03-30*
