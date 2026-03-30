# hashcards Enhancement Design
**Date:** 2026-03-31
**Scope:** Three incremental enhancements to the existing Flask app
**Approach:** Approach A — self-contained patches, no architectural overhaul

---

## 1. Recursive Deck Loading

### Problem
`_load_all_cards()` uses `glob("*.md")`, which only scans the top level of the cards directory. Cards stored in subdirectories (e.g. `KnowledgeCards/algo/01-papers/BatchNorm.md`) are silently ignored.

### Change
Switch to `rglob("*.md")` in `HashcardsApp._load_all_cards()`.

Deck name derivation changes from `os.path.basename(filepath)` to the relative path from the cards directory, minus the `.md` extension:

```python
# Before
deck_name = os.path.splitext(os.path.basename(filepath))[0]

# After
deck_name = str(Path(filepath).relative_to(self.cards_dir).with_suffix(''))
# e.g. "algo/01-papers/BatchNorm"
```

This is updated in `CardParser._extract_deck_name()` — the method gains an optional `base_dir` parameter, or the caller computes the name before passing it in. The simpler approach: compute the relative deck name in `_load_all_cards()` directly and pass it to `CardParser.parse_file()`.

### Impact
- No schema changes
- Existing cards already loaded retain their schedule (hash is content-based, not path-based)
- Deck names for previously flat-loaded cards stay unchanged (filename = last path segment = same string)

---

## 2. Statistics Page (`/stats`)

### New route
`GET /stats` — full-page statistics dashboard. Added to `_register_routes()` in `web/app.py`. Nav bar gains a "Stats" link.

### Page layout (three sections)

#### 2a. Daily review heatmap
GitHub-style calendar grid covering the last 365 days. Each cell is a `<div>` colored by review count for that day (5 intensity levels: 0, 1–2, 3–5, 6–10, 11+). No JS library needed — pure CSS grid with inline `data-count` attributes, color set via Tailwind arbitrary values or a small `<style>` block.

#### 2b. Per-deck breakdown table
Columns: **Deck · Total · New · Learning · Review · Lapse Rate · Avg Difficulty**
Sorted alphabetically by deck name. Data sourced from a single aggregation query over `schedules`.

#### 2c. Collection state bar chart
Horizontal bar chart (Chart.js via CDN) showing card counts by state across the whole collection: New / Learning / Review / Relearning. Gives an at-a-glance view of collection maturity.

### New storage methods

```python
# storage.py

def get_review_history(self, days: int = 365) -> dict[str, int]:
    """Return {date_str: review_count} for the last N days."""

def get_deck_stats(self) -> list[dict]:
    """Return per-deck aggregates: total, state counts, avg_difficulty, lapse_rate."""
```

Both use existing tables (`reviews`, `schedules`) with no schema changes.

### Template
`web/templates/stats.html` — extends `base.html`, uses Tailwind classes consistent with existing templates. Chart.js loaded via CDN only on this page (`{% block extra_head %}`).

---

## 3. AI Card Generation (`/generate`)

### New route
`GET /generate` — input form
`POST /generate` — process text, show preview
`POST /generate/save` — write file, reload cards

### Flow

```
User pastes text + sets deck name
        ↓
POST /generate → generator.py → DashScope API (qwen-max)
        ↓
Preview: editable textarea with generated Markdown
        ↓
POST /generate/save → write <cards_dir>/<deck_name>.md → api/reload
        ↓
Redirect to / (cards now live)
```

### New module: `hashcards/generator.py`

```python
class CardGenerator:
    def __init__(self, api_key: str):
        # OpenAI-compatible client pointing at DashScope
        self.client = openai.OpenAI(
            api_key=api_key,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )

    def generate(self, source_text: str, existing_decks: list[str]) -> str:
        """
        Returns a Markdown string of hashcards-formatted cards.
        Mix of Q&A and Cloze. enable_thinking=False.
        """
```

**Model:** `qwen-max`
**Thinking:** disabled (`enable_thinking: false` in extra_body)
**API key:** `DASHSCOPE_API_KEY` env var
**Error handling:** if env var unset, `/generate` renders an error banner rather than crashing; network errors surfaced to the user as a flash message

### Prompt design
The system prompt instructs the model to:
- Produce only valid hashcards syntax (`Q:`/`A:` pairs and `C:` cloze lines)
- Aim for one card per distinct concept
- Use cloze for factual recall, Q&A for conceptual questions
- Output raw Markdown only (no prose, no code fences)

### Output
Generated cards saved to `<cards_dir>/<deck_name>.md` where `deck_name` defaults to `generated_YYYY-MM-DD` (date of generation). If a file with that name already exists, content is **appended**, not overwritten. After save, `_load_all_cards()` is called to make cards immediately reviewable.

### Template
`web/templates/generate.html` — extends `base.html`. Step 1 (form) and step 2 (preview) rendered on the same page, toggled by a hidden field. The preview textarea is fully editable so users can fix cards before saving.

### New dependency
`openai` added to `requirements.txt` (DashScope's compatible endpoint uses the OpenAI SDK).

---

## Nav changes
`base.html` nav gains two links: **Stats** (`/stats`) and **Generate** (`/generate`), placed after Browse.

---

## File changelist

| File | Change |
|---|---|
| `hashcards/web/app.py` | `rglob`, relative deck names, `/stats`, `/generate`, `/generate/save` routes |
| `hashcards/storage.py` | `get_review_history()`, `get_deck_stats()` |
| `hashcards/generator.py` | **New** — DashScope card generator |
| `hashcards/parser.py` | `parse_file()` accepts explicit `deck_name` param |
| `hashcards/web/templates/base.html` | +Stats +Generate nav links |
| `hashcards/web/templates/stats.html` | **New** — heatmap + table + chart |
| `hashcards/web/templates/generate.html` | **New** — form + preview |
| `requirements.txt` | +`openai` |

---

## What's explicitly out of scope
- No undo last review (not requested)
- No mobile-native changes
- No FSRS parameter tuning
- No Anki export
- No authentication or multi-user support
