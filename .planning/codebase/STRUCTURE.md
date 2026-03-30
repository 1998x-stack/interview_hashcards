# Codebase Structure

**Analysis Date:** 2026-03-30

## Directory Layout

```
hashcards_sonnet/
├── hashcards/                          # Main package
│   ├── __init__.py                     # Package initialization
│   ├── parser.py                       # Markdown parsing logic
│   ├── hasher.py                       # Content hashing (SHA-256)
│   ├── scheduler.py                    # FSRS algorithm implementation
│   ├── storage.py                      # SQLite database abstraction
│   ├── cli.py                          # Command-line interface
│   └── web/                            # Flask web application
│       ├── __init__.py                 # Package initialization
│       ├── app.py                      # Flask app and routes
│       └── templates/                  # Jinja2 HTML templates
│           ├── base.html               # Base template (CSS, nav, JS)
│           ├── index.html              # Home/dashboard
│           ├── study.html              # Main review interface
│           ├── browse.html             # Browse all cards
│           ├── no_cards.html           # "No cards due" message
│           ├── base_v1.html            # (Legacy variant)
│           ├── index_v1.html           # (Legacy variant)
│           ├── study_v1.html           # (Legacy variant)
│           ├── browse_v1.html          # (Legacy variant)
│           └── no_cards_v1.html        # (Legacy variant)
├── setup.py                            # Package installation config
├── ARCHITECTURE.md                     # Architecture documentation
├── README.md                           # Project documentation
├── KnowledgeCards/                     # Example card collections
│   ├── algo/                           # Algorithm cards
│   │   ├── 01-papers/                  # Research papers
│   │   ├── 02-ML/                      # Machine learning
│   │   ├── 03-AI/                      # Artificial intelligence
│   │   ├── 04-RL/                      # Reinforcement learning
│   │   ├── 05-Recommend/               # Recommendation systems
│   │   └── 06-LLM/                     # Large language models
│   └── economic/                       # Economics cards
├── images/                             # Screenshots/documentation images
├── .planning/                          # GSD planning directory (generated)
│   └── codebase/                       # Codebase analysis documents
│       ├── ARCHITECTURE.md             # This file
│       └── STRUCTURE.md                # Architecture analysis
└── .hashcards.db                       # SQLite database (generated at runtime)
```

## Directory Purposes

**`hashcards/`:**
- Purpose: Root package containing all application code
- Contains: Core modules (parser, scheduler, storage, hasher), CLI, and web application
- Key files: `cli.py` (entry point), `parser.py` (data extraction)

**`hashcards/web/`:**
- Purpose: Flask web application and UI templates
- Contains: Flask routes, request handlers, HTML templates
- Key files: `app.py` (Flask app class and routes)

**`hashcards/web/templates/`:**
- Purpose: Jinja2 templates for rendering HTML responses
- Contains: Five main views (base, index, study, browse, no_cards) + legacy variants
- Generated: No (hand-written templates)
- Committed: Yes (part of source code)

**`KnowledgeCards/`:**
- Purpose: Example deck collections demonstrating card format and organization
- Contains: Markdown files organized by topic (algo/ML/AI/RL/LLM, economics)
- Generated: No (user-created examples)
- Committed: Yes (part of repository)

**`.planning/codebase/`:**
- Purpose: GSD analysis documents (generated during development planning)
- Contains: ARCHITECTURE.md, STRUCTURE.md, CONVENTIONS.md, TESTING.md, CONCERNS.md
- Generated: Yes (by GSD orchestrator)
- Committed: Yes (useful for documentation)

## Key File Locations

**Entry Points:**

- `setup.py`: Package configuration; defines `hashcards` console script that calls `cli.py::main()`
- `hashcards/cli.py`: Main CLI entry point; parses arguments and routes to command handlers
- `hashcards/web/app.py::HashcardsApp.run()`: Flask server entry point (launched by `cmd_drill`)

**Core Logic:**

- `hashcards/parser.py`: CardParser class; parses Markdown → Card objects; regex-based extraction of Q/A and Cloze formats
- `hashcards/hasher.py`: CardHasher class; generates SHA-256 content hashes for card identification
- `hashcards/scheduler.py`: FSRSScheduler class; implements spaced repetition algorithm; computes next review dates
- `hashcards/storage.py`: CardStorage class; SQLite CRUD operations; manages schedules and review logs

**Web Application:**

- `hashcards/web/app.py`: HashcardsApp class wraps Flask; routes, card caching, database initialization
- `hashcards/web/templates/base.html`: Base template with global CSS, dark/light mode, nav bar, keyboard event handlers
- `hashcards/web/templates/study.html`: Main study interface; displays card and rating buttons
- `hashcards/web/templates/index.html`: Dashboard with statistics (total cards, due, by state, today's reviews)
- `hashcards/web/templates/browse.html`: Browse view; table of all cards with schedule info

**Configuration:**

- `setup.py`: Python package metadata, dependencies (Flask ≥ 2.3.0), entry points
- No .env files or environment configuration (local-first design)
- Database path: Defaults to `.hashcards.db` in cards directory (configurable via flag)

## Naming Conventions

**Files:**

- `parser.py`, `hasher.py`, `scheduler.py`, `storage.py`: Module names are `{noun}.py` (single responsibility)
- `cli.py`: CLI module
- `app.py`: Flask application module
- `base.html`, `index.html`, `study.html`, `browse.html`: Template names are semantic route names
- `*.md`: Markdown card files; named by deck name (Math.md, History.md, etc.)
- `.hashcards.db`: SQLite database; hidden file (dot prefix) to avoid cluttering user directory

**Directories:**

- `hashcards/`: Lowercase package name
- `KnowledgeCards/`: PascalCase for example data
- `web/`: Lowercase module directory
- `templates/`: Lowercase conventional name for Jinja2 templates

**Python Classes:**

- `CardParser`, `CardHasher`, `FSRSScheduler`, `CardStorage`: PascalCase class names
- `Card`, `CardSchedule`, `ReviewLog`: PascalCase dataclasses
- `CardType`, `State`, `Rating`: PascalCase enums

**Python Functions/Methods:**

- `parse_file()`, `get_schedule()`, `review_card()`: snake_case for all functions and methods
- `_private_method()`: Single underscore prefix for internal/helper methods
- `cmd_drill()`, `cmd_stats()`: CLI command handlers prefixed with `cmd_`

**Python Variables:**

- `cards_cache`, `card_hash`, `deck_name`: snake_case
- `stability`, `difficulty`, `elapsed_days`: snake_case for domain concepts
- `w` (FSRS weights): Single letter for mathematical parameters

**HTML/Templates:**

- `card-content`, `stat-box`, `keyboard-hint`: kebab-case for CSS classes
- `card_hash`, `card_type`: snake_case for template variable names (from Python)
- Navigation: `href="/"` (root), `href="/study"` (semantic paths)

## Where to Add New Code

**New Study Feature (e.g., time tracking, metrics):**
- Scheduling logic: Extend `FSRSScheduler` class in `hashcards/scheduler.py`
- Data storage: Add columns to `schedules` table in `CardStorage._init_db()` in `hashcards/storage.py`
- Web UI: Add route in `HashcardsApp._register_routes()` in `hashcards/web/app.py`; create new template in `hashcards/web/templates/`
- CLI: Add subcommand in `main()` function in `hashcards/cli.py`

**New Card Format (e.g., Multiple Choice):**
- Parsing: Add regex pattern to `CardParser` in `hashcards/parser.py`; extend `CardType` enum
- Display: Update `study.html` template to render new card format with conditional `{% if card.card_type == 'multiple_choice' %}`
- No database changes needed (card format is metadata in Card object, not stored in DB)

**New CLI Command:**
- Location: `hashcards/cli.py`
- Pattern: Create `cmd_newcommand(args)` function; register in `main()` with `subparsers.add_parser('newcommand')`
- Access cards: Use `CardParser.parse_file()` or `CardStorage` depending on what you need

**Utility Functions (shared helpers):**
- Location: Create new file `hashcards/utils.py` or add to existing module
- Pattern: Keep stateless; no global state
- Testing: Add tests in `tests/test_utils.py`

**Bug Fix or Enhancement to Existing Module:**
- Locate the module (`parser.py`, `scheduler.py`, etc.)
- Make changes in-place
- Update `ARCHITECTURE.md` if changing layer boundaries or data flow

## Special Directories

**`.planning/codebase/`:**
- Purpose: Contains GSD analysis documents
- Generated: Yes (created by GSD orchestrator during `gsd:map-codebase`)
- Committed: Yes (useful reference documentation)
- Structure:
  - `ARCHITECTURE.md`: Layer breakdown and data flow
  - `STRUCTURE.md`: File organization and where to add code
  - `CONVENTIONS.md`: Coding style and patterns
  - `TESTING.md`: Testing framework and patterns
  - `CONCERNS.md`: Technical debt and known issues

**`KnowledgeCards/`:**
- Purpose: Example card collections for users to learn from
- Structure: Organized by topic (algo/, economic/)
- Files: Markdown deck files (.md)
- Usage: Users can copy and modify; not auto-loaded by CLI
- Note: Requires explicit path: `hashcards drill ./KnowledgeCards`

**`.hashcards.db` (generated at runtime):**
- Purpose: SQLite database storing scheduling state and review history
- Created: On first `hashcards drill` command
- Location: Stored in cards directory (configurable via `--db-path` flag in future)
- Contents: Two tables (`schedules`, `reviews`) with indices
- Safe to delete: Yes; cards reload with fresh schedules
- Not committed: Git should ignore (usually .gitignore includes *.db)

---

*Structure analysis: 2026-03-30*
