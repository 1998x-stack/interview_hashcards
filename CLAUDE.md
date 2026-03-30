# hashcards — Claude Code Guidelines

Local-first spaced repetition app: Markdown cards → FSRS scheduling → Flask web UI.

## Project Layout

```
hashcards/
  parser.py       # CardParser — Markdown → Card objects (QA + Cloze)
  hasher.py       # SHA-256 content-addressable card identity
  scheduler.py    # FSRS algorithm — State: NEW/LEARNING/REVIEW/RELEARNING
  storage.py      # SQLite (schedules + reviews tables); check_same_thread=False
  generator.py    # CardGenerator — DashScope/qwen-max via openai SDK
  cli.py          # CLI entry point
  web/
    app.py        # HashcardsApp (Flask wrapper)
    templates/    # Jinja2 + Tailwind CSS + Inter font (CDN)
KnowledgeCards/   # Live card files (.md) — source of truth for content
tests/            # pytest, no mocking of SQLite (use tempfile + real DB)
```

## Architecture Invariants

- **Content-addressable cards**: card identity = SHA-256 of `raw_text`. Never change a card's text without understanding it creates a new card.
- **Markdown is source of truth**: SQLite stores only scheduling state, never card content.
- **Deck names are posix paths**: `algo/01-papers/Transformer` — always `.as_posix()`, never OS-native separators.
- **Hidden dirs skipped**: `rglob("*.md")` must filter `parts` starting with `.` to avoid `.claude/`, `.planning/` etc.
- **Flask route path vars**: nested deck names contain slashes — always use `<path:deck_name>`, never `<deck_name>`.
- **SQLite threading**: connection opened with `check_same_thread=False`; Flask dev server is threaded.
- **Jinja2 auto-escape**: JSON injected into `<script>` blocks must use `| tojson | safe` (not just `| tojson`).

## Running the App

```bash
# Start server
python -c "from hashcards.web.app import HashcardsApp; HashcardsApp('./KnowledgeCards').run(port=5001)"

# Run tests
python -m pytest tests/ -v

# Install editable
pip install -e .
```

## AI Card Generation

- API key: `$DASHSCOPE_API_KEY` (env var, never hardcode)
- Model: `qwen-max` via DashScope OpenAI-compatible endpoint
- Base URL: `https://dashscope.aliyuncs.com/compatible-mode/v1`
- Always pass `extra_body={"enable_thinking": False}`
- Use `openai` SDK (not `dashscope` SDK)

## Testing Rules

- Use `tempfile.TemporaryDirectory()` + real SQLite, never mock the DB
- Mock external API calls (CardGenerator) with `unittest.mock.MagicMock`
- To remove an env var in a test: `unittest.mock.patch.dict(os.environ, env_without_key, clear=True)` — `environ_base` does NOT override real env vars
- Run `pytest tests/ -v` after every change; all 16 tests must pass

## Card Format

```
Q: What is X?
A: The answer.

C: The [mitochondria] is the powerhouse of the cell.
```

One blank line between cards. No numbering, no headings, no code fences in card content.

## Path Safety (generate/save)

Sanitize deck names before writing files:
```python
safe_name = "".join(c for c in deck_name if c.isalnum() or c in "-_/").lstrip("/")
target = cards_dir / f"{safe_name}.md"
```
The `.lstrip("/")` is critical — without it a name like `/etc/passwd` escapes the cards dir.

## Git Workflow

```
feat: add X
fix: Y
refactor: Z
test: add tests for W
```

Branch: `main`. SSH only (`git@github.com:1998x-stack/interview_hashcards.git`).

## UI Conventions

- Tailwind CSS + Inter font via CDN — no build step
- Chart.js via CDN for stats visualizations
- Templates: `base.html` → all pages extend it
- Keep pages keyboard-navigable; JS is progressive enhancement only

## Common Pitfalls

| Symptom | Root Cause | Fix |
|---|---|---|
| 404 on nested deck URL | Used `<deck_name>` not `<path:deck_name>` | Change route converter |
| 500 SQLite thread error | Connection created in main thread | `check_same_thread=False` |
| Chart.js data breaks | `\| tojson` without `\| safe` | Add `\| safe` filter |
| Hidden dir cards loaded | Missing `.startswith('.')` filter | Filter `rglob` parts |
| Path traversal on save | Sanitizer allows `/` but no lstrip | Add `.lstrip("/")` |
| Test env var not cleared | Used `environ_base` | Use `patch.dict(..., clear=True)` |
