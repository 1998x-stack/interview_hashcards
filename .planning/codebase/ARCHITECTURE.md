# Architecture

**Analysis Date:** 2026-03-30

## Pattern Overview

**Overall:** Layered three-tier architecture with content-addressable storage

**Key Characteristics:**
- Clear separation between data layer (Markdown files), scheduling layer (SQLite), and application layer (Flask + CLI)
- Content-based card identification using SHA-256 hashing for natural deduplication
- Unix philosophy: each module has a single, well-defined responsibility
- Memory-cached card data with on-disk persistent scheduling state
- Local-first design with no external dependencies beyond Flask

## Layers

**Presentation Layer (Web UI & CLI):**
- Purpose: Provide user interfaces for studying cards and managing decks
- Location: `hashcards/web/app.py`, `hashcards/cli.py`, `hashcards/web/templates/`
- Contains: Flask routes, HTML templates, command-line parsers, CLI commands
- Depends on: Application layer (parser, scheduler, storage)
- Used by: End users via web browser or terminal

**Application Layer (Core Logic):**
- Purpose: Orchestrate parsing, scheduling, and storage operations
- Location: `hashcards/parser.py`, `hashcards/scheduler.py`, `hashcards/storage.py`, `hashcards/hasher.py`
- Contains: Card parsing, FSRS algorithm, database management, content hashing
- Depends on: Data layer (Markdown files and SQLite database)
- Used by: Web and CLI layers

**Data Layer:**
- Purpose: Persist card content and scheduling state
- Location: Markdown files (`.md`) and SQLite database (`.hashcards.db`)
- Contains: Card definitions in Markdown, scheduling metadata in relational database
- Depends on: Nothing (bottom layer)
- Used by: Application layer for all data operations

## Data Flow

**Card Loading (Startup):**

```
User runs: hashcards drill ./Cards
    ↓
CLI parses arguments (cli.py)
    ↓
HashcardsApp.__init__() loads cards
    ↓
CardParser.parse_file() reads each .md file
    ↓
CardHasher.hash_card() generates content hash for each card
    ↓
CardStorage.get_schedule() looks up existing schedule in SQLite
    ├─ If found → Load schedule from database
    └─ If not found → FSRSScheduler.init_card() creates new schedule
    ↓
All cards cached in memory (self.cards_cache = {hash: card, ...})
    ↓
Flask server starts on http://localhost:8000
```

**Card Review Workflow:**

```
User visits /study endpoint
    ↓
Flask route handlers:
  1. query get_due_cards() from database
  2. fetch next card from in-memory cache
  3. render study.html template
    ↓
User presses Space to reveal answer
    ↓
JavaScript updates DOM (no server request)
    ↓
User rates card (1-4 keys or button click)
    ↓
POST /review with:
  - card_hash: Content hash of card
  - rating: 1-4 (AGAIN, HARD, GOOD, EASY)
  - deck_name: Source deck name
    ↓
Flask review handler:
  1. Retrieve schedule from SQLite
  2. Call FSRSScheduler.review_card(schedule, rating)
  3. Algorithm updates stability, difficulty, next interval
  4. CardStorage.save_schedule() updates database
  5. CardStorage.log_review() records review history
    ↓
Redirect to /study for next due card
```

**Card Editing Flow:**

```
User edits Math.md in text editor
    ↓
File saved to disk
    ↓
User clicks /api/reload endpoint (or restarts server)
    ↓
_load_all_cards() re-parses all .md files
    ↓
New content → CardHasher produces new hash
    ├─ Different hash = Card treated as new
    │   └─ FSRSScheduler.init_card() creates fresh schedule
    └─ Same hash = Card recognized as existing
        └─ Existing schedule in database preserved
    ↓
cards_cache updated with new hashes
    ↓
Old hashes no longer in files remain in database but invisible in study/browse
```

**State Management:**

**Transient State (in-memory):**
- `HashcardsApp.cards_cache`: Dictionary mapping card_hash → Card object
- Loaded at startup, refreshed only on `/api/reload` call or server restart
- Enables O(1) card lookups during study sessions

**Persistent State (SQLite):**
- `schedules` table: Current learning state (stability, difficulty, due date, etc.)
- `reviews` table: Complete history of all card reviews
- Indexed on: `due` (for finding cards due for review), `deck_name`, `card_hash`
- Source of truth for scheduling state; survives server restarts

**Immutable State (Markdown files):**
- Raw card content: Q/A pairs and cloze deletions
- Cards are version-controlled as plain text
- Source of truth for card content; hashes derived from this

## Key Abstractions

**Card (dataclass):**
- Purpose: Represents a single flashcard with metadata
- Location: `hashcards/parser.py`
- Fields: `card_type` (QA/CLOZE), `content` (dict), `deck_name`, `line_number`, `raw_text`
- Usage: Passed through system from parser → cache → web templates
- Pattern: Immutable; same Card instance used throughout session

**CardSchedule (dataclass):**
- Purpose: Tracks learning state for a single card
- Location: `hashcards/scheduler.py`
- Fields: `state` (NEW/LEARNING/REVIEW/RELEARNING), `stability`, `difficulty`, `due`, `reps`, `lapses`
- Usage: Retrieved from database before review, updated by FSRS algorithm, saved back
- Pattern: Copied on modification to maintain immutability during update

**FSRSScheduler:**
- Purpose: Implement Free Spaced Repetition Scheduling algorithm
- Location: `hashcards/scheduler.py`
- Key methods:
  - `init_card(hash)` → CardSchedule: Initialize new card with default parameters
  - `review_card(schedule, rating)` → (CardSchedule, ReviewLog): Process a review and return updated state
- Pattern: Pure functions; no side effects; takes current state and returns new state
- Algorithm: Four-parameter model (stability, difficulty, retrievability, forgetting curve)

**CardStorage:**
- Purpose: Manage SQLite database operations
- Location: `hashcards/storage.py`
- Key methods:
  - `save_schedule()` / `get_schedule()`: CRUD for card schedules
  - `get_due_cards()`: Query due cards with optional deck/limit filters
  - `log_review()`: Append review to history
  - `get_stats()`: Compute learning statistics
- Pattern: Database abstraction layer; translates between Python objects and SQL

**CardParser:**
- Purpose: Extract card objects from Markdown text
- Location: `hashcards/parser.py`
- Key methods:
  - `parse_file(filepath)` / `parse_content(text)`: Parse Markdown → List[Card]
  - `format_cloze_for_display(text, reveal_index)`: Render cloze with one deletion revealed
- Pattern: Regex-based; stateless; deterministic
- Supported formats:
  - Q&A: `Q: question\nA: answer`
  - Cloze: `C: Text with [deletion] and [another]`

**CardHasher:**
- Purpose: Generate content-addressed identifiers for cards
- Location: `hashcards/hasher.py`
- Algorithm: SHA-256 hash of whitespace-normalized raw_text, first 16 hex characters
- Guarantee: Same content → same hash; different content → different hash
- Usage: Primary key in database; unique identifier across system

## Entry Points

**CLI Entry Point:**
- Location: `hashcards/cli.py::main()`
- Invoked: Via `hashcards` console script (defined in `setup.py`)
- Responsibilities:
  1. Parse command-line arguments (drill, stats, validate, export)
  2. Route to appropriate command handler
  3. Create HashcardsApp or CardStorage as needed
- Commands:
  - `drill CARDS_DIR`: Start web server for studying
  - `stats CARDS_DIR`: Display learning statistics
  - `validate CARDS_DIR`: Check Markdown syntax
  - `export CARDS_DIR`: Placeholder for future formats

**Web Entry Point:**
- Location: `hashcards/web/app.py::HashcardsApp.run()`
- Invoked: By `cmd_drill()` after app initialization
- Routes registered (all in `_register_routes()`):
  - `/` (GET): Home page with statistics
  - `/study[/<deck_name>]` (GET): Main study interface
  - `/review` (POST): Process card review submission
  - `/browse[/<deck_name>]` (GET): Browse all cards
  - `/api/stats` (GET): JSON statistics endpoint
  - `/api/reload` (GET): Reload cards from disk

## Error Handling

**Strategy:** Graceful degradation with informative messages

**Patterns:**

1. **File Operations:**
   - Missing directory: CLI exits with error message
   - Invalid .md file: CardParser raises exception, caught by validate command
   - Missing card in cache during review: Deleted card detected, removed from DB, user redirected

2. **Database Operations:**
   - Connection errors: SQLite handles atomically
   - Schema creation: Idempotent (CREATE TABLE IF NOT EXISTS)
   - Data integrity: Foreign keys on reviews → schedules

3. **Scheduling Logic:**
   - Invalid rating: Flask request validation (int conversion)
   - Missing schedule: Impossible in normal flow (schedules initialized on card load)
   - Numerical bounds: FSRS clamps difficulty to [1, 10], stability to ≥ 0.1

4. **Web Layer:**
   - Missing due cards: Render no_cards.html instead of 500
   - Invalid deck_name: Safely filtered in browse/study routes

## Cross-Cutting Concerns

**Logging:**
- Strategy: stdout/stderr only; no logging framework
- Patterns: CLI commands print status messages; web layer has no logging
- Example: `print(f"Loading cards from: {cards_dir}")` in cmd_drill()

**Validation:**
- Happens at boundaries between layers
- CLI validates directory exists before proceeding
- CardParser validates card format during parsing
- Web validates rating integer in POST handler
- No strict validation of card content (supports any Markdown)

**Authentication:**
- Not applicable; local-first design
- No user accounts, no authorization, no multi-user concerns
- Flask secret_key generated randomly each session (stateless)

---

*Architecture analysis: 2026-03-30*
