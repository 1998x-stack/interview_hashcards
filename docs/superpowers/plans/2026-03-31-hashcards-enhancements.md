# hashcards Enhancements Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add recursive deck loading, a statistics dashboard, and AI-assisted card generation (via DashScope/qwen-max) to the existing hashcards Flask app.

**Architecture:** Three independent patches to the existing Flask app — each can be shipped and tested separately. No new abstractions beyond a `generator.py` module. All UI follows the existing Tailwind + Inter pattern in `base.html`.

**Tech Stack:** Python 3, Flask, SQLite, Tailwind CSS (CDN), Chart.js (CDN), openai SDK (DashScope-compatible endpoint), pytest

---

## File Map

| File | Status | Responsibility |
|---|---|---|
| `hashcards/parser.py` | Modify | Accept explicit `deck_name` in `parse_file()` |
| `hashcards/web/app.py` | Modify | `rglob`, relative deck names, `/stats`, `/generate`, `/generate/save` routes |
| `hashcards/storage.py` | Modify | `get_review_history()`, `get_deck_stats()` |
| `hashcards/generator.py` | Create | DashScope/qwen-max card generator |
| `hashcards/web/templates/base.html` | Modify | +Stats +Generate nav links |
| `hashcards/web/templates/stats.html` | Create | Heatmap + per-deck table + state chart |
| `hashcards/web/templates/generate.html` | Create | Paste form + preview step |
| `requirements.txt` | Modify | +`openai` |
| `tests/test_recursive.py` | Create | Recursive loading tests |
| `tests/test_storage_stats.py` | Create | New storage method tests |
| `tests/test_generator.py` | Create | Generator unit tests (mocked API) |

---

## Task 1: Recursive Deck Loading

**Files:**
- Modify: `hashcards/parser.py`
- Modify: `hashcards/web/app.py`
- Create: `tests/test_recursive.py`

- [ ] **Step 1.1: Create tests directory and write failing test**

```bash
mkdir -p tests
touch tests/__init__.py
```

Create `tests/test_recursive.py`:

```python
"""Tests for recursive deck loading"""
import os
import tempfile
import pytest
from pathlib import Path
from hashcards.parser import CardParser


def make_card_file(directory: Path, filename: str, content: str) -> Path:
    path = directory / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    return path


def test_parse_file_accepts_explicit_deck_name():
    with tempfile.TemporaryDirectory() as tmp:
        p = make_card_file(Path(tmp), "notes.md", "Q: What is 2+2?\nA: 4\n")
        cards = CardParser.parse_file(str(p), deck_name="math/basics")
        assert len(cards) == 1
        assert cards[0].deck_name == "math/basics"


def test_parse_file_falls_back_to_filename_when_no_deck_name():
    with tempfile.TemporaryDirectory() as tmp:
        p = make_card_file(Path(tmp), "notes.md", "Q: What is 2+2?\nA: 4\n")
        cards = CardParser.parse_file(str(p))
        assert cards[0].deck_name == "notes"


def test_app_loads_cards_from_subdirectories():
    """_load_all_cards uses rglob so nested .md files are found"""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        make_card_file(root, "top.md", "Q: Top level?\nA: Yes\n")
        make_card_file(root, "sub/deep.md", "Q: Nested?\nA: Yes\n")

        from hashcards.web.app import HashcardsApp
        db_path = str(root / ".test.db")
        app = HashcardsApp(str(root), db_path=db_path)

        # Both cards should be in cache
        assert len(app.cards_cache) == 2
        deck_names = {c.deck_name for c in app.cards_cache.values()}
        assert "top" in deck_names
        assert "sub/deep" in deck_names
```

- [ ] **Step 1.2: Install pytest and run to confirm failure**

```bash
pip install pytest
pytest tests/test_recursive.py -v
```

Expected: FAIL — `parse_file() got an unexpected keyword argument 'deck_name'`

- [ ] **Step 1.3: Modify `hashcards/parser.py` — add `deck_name` param to `parse_file()`**

Replace the existing `parse_file` classmethod (lines 49–63) with:

```python
@classmethod
def parse_file(cls, filepath: str, deck_name: Optional[str] = None) -> List[Card]:
    """
    Parse a Markdown file and extract all cards.

    Args:
        filepath: Path to the .md file
        deck_name: Override deck name (default: derived from filename)

    Returns:
        List of Card objects
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    if deck_name is None:
        deck_name = cls._extract_deck_name(filepath)
    return cls.parse_content(content, deck_name)
```

No other changes to `parser.py`.

- [ ] **Step 1.4: Modify `hashcards/web/app.py` — switch to `rglob` with relative deck names**

Replace the `_load_all_cards` method body (currently lines 51–64):

```python
def _load_all_cards(self):
    """Load all cards from Markdown files (recursive)"""
    self.cards_cache.clear()

    for md_file in self.cards_dir.rglob("*.md"):
        # Deck name = relative path without extension, e.g. "algo/papers/BatchNorm"
        deck_name = str(md_file.relative_to(self.cards_dir).with_suffix(''))
        cards = CardParser.parse_file(str(md_file), deck_name=deck_name)
        for card in cards:
            card_hash = card.get_hash()
            self.cards_cache[card_hash] = card

            if not self.storage.get_schedule(card_hash):
                schedule = self.scheduler.init_card(card_hash)
                self.storage.save_schedule(schedule, card.deck_name)
```

- [ ] **Step 1.5: Run tests — expect pass**

```bash
pytest tests/test_recursive.py -v
```

Expected: all 3 tests PASS

- [ ] **Step 1.6: Commit**

```bash
git add hashcards/parser.py hashcards/web/app.py tests/test_recursive.py tests/__init__.py
git commit -m "feat: recursive deck loading with relative path deck names"
```

---

## Task 2: Storage — `get_review_history()` and `get_deck_stats()`

**Files:**
- Modify: `hashcards/storage.py`
- Create: `tests/test_storage_stats.py`

- [ ] **Step 2.1: Write failing tests**

Create `tests/test_storage_stats.py`:

```python
"""Tests for new storage stats methods"""
import tempfile
import pytest
from datetime import datetime, timedelta
from hashcards.storage import CardStorage
from hashcards.scheduler import FSRSScheduler, Rating, State


def make_storage(tmp_path) -> CardStorage:
    return CardStorage(str(tmp_path / ".test.db"))


def seed_card(storage: CardStorage, card_hash: str, deck: str, state: State,
              difficulty: float = 5.0, lapses: int = 0):
    """Insert a minimal schedule row directly for testing."""
    import sqlite3
    from datetime import datetime
    now = datetime.now().isoformat()
    due = datetime.now().isoformat()
    conn = storage.conn
    conn.execute("""
        INSERT OR REPLACE INTO schedules
            (card_hash, deck_name, state, stability, difficulty,
             elapsed_days, scheduled_days, reps, lapses, last_review, due,
             created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (card_hash, deck, int(state), 1.0, difficulty,
          0, 1, 1, lapses, None, due, now, now))
    conn.commit()


def seed_review(storage: CardStorage, card_hash: str, review_time: datetime):
    """Insert a review row for testing."""
    storage.conn.execute("""
        INSERT INTO reviews (card_hash, rating, state, review_time, scheduled_days, elapsed_days)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (card_hash, 3, 2, review_time.isoformat(), 1, 0))
    storage.conn.commit()


def test_get_review_history_returns_daily_counts():
    with tempfile.TemporaryDirectory() as tmp:
        from pathlib import Path
        storage = make_storage(Path(tmp))
        now = datetime.now()
        seed_card(storage, "abc", "deck1", State.REVIEW)
        seed_review(storage, "abc", now)
        seed_review(storage, "abc", now)
        seed_review(storage, "abc", now - timedelta(days=1))

        history = storage.get_review_history(days=7)

        today_str = now.date().isoformat()
        yesterday_str = (now.date() - timedelta(days=1)).isoformat()
        assert history[today_str] == 2
        assert history[yesterday_str] == 1


def test_get_review_history_fills_zero_days():
    with tempfile.TemporaryDirectory() as tmp:
        from pathlib import Path
        storage = make_storage(Path(tmp))
        history = storage.get_review_history(days=7)
        assert len(history) == 7
        assert all(v == 0 for v in history.values())


def test_get_deck_stats_returns_per_deck_aggregates():
    with tempfile.TemporaryDirectory() as tmp:
        from pathlib import Path
        storage = make_storage(Path(tmp))
        seed_card(storage, "h1", "math", State.NEW, difficulty=3.0)
        seed_card(storage, "h2", "math", State.REVIEW, difficulty=7.0)
        seed_card(storage, "h3", "science", State.LEARNING, difficulty=5.0, lapses=1)

        stats = storage.get_deck_stats()
        decks = {d['deck_name']: d for d in stats}

        assert "math" in decks
        assert decks["math"]["total"] == 2
        assert decks["math"]["avg_difficulty"] == pytest.approx(5.0)
        assert "science" in decks
        assert decks["science"]["total"] == 1
        assert decks["science"]["lapse_rate"] == pytest.approx(1.0)
```

- [ ] **Step 2.2: Run to confirm failure**

```bash
pytest tests/test_storage_stats.py -v
```

Expected: FAIL — `CardStorage has no attribute 'get_review_history'`

- [ ] **Step 2.3: Add `get_review_history()` to `hashcards/storage.py`**

Add after the `get_stats` method (before `delete_card`):

```python
def get_review_history(self, days: int = 365) -> dict:
    """
    Return daily review counts for the last N days.

    Returns:
        {date_str: count} for every day in the range (zeros included)
    """
    from datetime import date, timedelta

    cursor = self.conn.cursor()
    cursor.execute("""
        SELECT DATE(review_time) as day, COUNT(*) as cnt
        FROM reviews
        WHERE review_time >= DATE('now', ? || ' days')
        GROUP BY day
    """, (f'-{days}',))

    counts = {row['day']: row['cnt'] for row in cursor.fetchall()}

    # Fill in zeros for days with no reviews
    result = {}
    today = date.today()
    for i in range(days - 1, -1, -1):
        d = (today - timedelta(days=i)).isoformat()
        result[d] = counts.get(d, 0)
    return result
```

- [ ] **Step 2.4: Add `get_deck_stats()` to `hashcards/storage.py`**

Add immediately after `get_review_history`:

```python
def get_deck_stats(self) -> list:
    """
    Return per-deck aggregates.

    Returns:
        List of dicts: deck_name, total, new, learning, review, relearning,
                       avg_difficulty, lapse_rate
    """
    cursor = self.conn.cursor()
    cursor.execute("""
        SELECT
            deck_name,
            COUNT(*) as total,
            SUM(CASE WHEN state = 0 THEN 1 ELSE 0 END) as new_count,
            SUM(CASE WHEN state = 1 THEN 1 ELSE 0 END) as learning,
            SUM(CASE WHEN state = 2 THEN 1 ELSE 0 END) as review,
            SUM(CASE WHEN state = 3 THEN 1 ELSE 0 END) as relearning,
            AVG(difficulty) as avg_difficulty,
            AVG(lapses) as lapse_rate
        FROM schedules
        GROUP BY deck_name
        ORDER BY deck_name
    """)

    rows = cursor.fetchall()
    return [
        {
            'deck_name': row['deck_name'],
            'total': row['total'],
            'new': row['new_count'],
            'learning': row['learning'],
            'review': row['review'],
            'relearning': row['relearning'],
            'avg_difficulty': round(row['avg_difficulty'] or 0, 1),
            'lapse_rate': round(row['lapse_rate'] or 0, 2),
        }
        for row in rows
    ]
```

- [ ] **Step 2.5: Run tests — expect pass**

```bash
pytest tests/test_storage_stats.py -v
```

Expected: all 4 tests PASS

- [ ] **Step 2.6: Commit**

```bash
git add hashcards/storage.py tests/test_storage_stats.py
git commit -m "feat: add get_review_history and get_deck_stats to storage"
```

---

## Task 3: Stats Page (`/stats`)

**Files:**
- Modify: `hashcards/web/app.py`
- Modify: `hashcards/web/templates/base.html`
- Create: `hashcards/web/templates/stats.html`

- [ ] **Step 3.1: Add `/stats` route to `hashcards/web/app.py`**

Inside `_register_routes`, add after the `/browse` route block (before the closing of `_register_routes`):

```python
@self.app.route('/stats')
def stats():
    """Statistics dashboard"""
    history = self.storage.get_review_history(days=365)
    deck_stats = self.storage.get_deck_stats()
    overall = self.storage.get_stats()
    return render_template(
        'stats.html',
        history=history,
        deck_stats=deck_stats,
        overall=overall
    )
```

- [ ] **Step 3.2: Add Stats link to `hashcards/web/templates/base.html`**

In `base.html`, find the nav links block (around line 107–119). After the Browse link, add:

```html
<a href="/stats" role="listitem"
   class="rounded-md px-3 py-1.5 text-sm font-medium text-slate-600 transition-colors duration-150 hover:bg-slate-100 hover:text-slate-900 focus:outline-none focus:ring-2 focus:ring-brand-500 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-slate-100">
    Stats
</a>
<a href="/generate" role="listitem"
   class="rounded-md px-3 py-1.5 text-sm font-medium text-slate-600 transition-colors duration-150 hover:bg-slate-100 hover:text-slate-900 focus:outline-none focus:ring-2 focus:ring-brand-500 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-slate-100">
    Generate
</a>
```

(Adding Generate here too saves a separate nav edit later.)

- [ ] **Step 3.3: Create `hashcards/web/templates/stats.html`**

```html
{% extends "base.html" %}

{% block title %}Stats — hashcards{% endblock %}

{% block extra_head %}
<script src="https://cdn.jsdelivr.net/npm/chart.js@4/dist/chart.umd.min.js"></script>
<style>
    .heat-grid { display: grid; grid-template-columns: repeat(53, 1fr); gap: 2px; }
    .heat-cell { aspect-ratio: 1; border-radius: 2px; }
    .heat-0  { background: #e2e8f0; }
    .heat-1  { background: #c7d2fe; }
    .heat-2  { background: #818cf8; }
    .heat-3  { background: #4f46e5; }
    .heat-4  { background: #312e81; }
    @media (prefers-color-scheme: dark) {
        .heat-0 { background: #1e293b; }
    }
</style>
{% endblock %}

{% block content %}

<div class="mb-8">
    <h1 class="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100">Statistics</h1>
    <p class="mt-1 text-sm text-slate-500 dark:text-slate-400">Your learning history</p>
</div>

<!-- Heatmap -->
<div class="mb-8 rounded-xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-900">
    <h2 class="mb-4 text-sm font-semibold uppercase tracking-widest text-slate-400 dark:text-slate-500">Review activity (last 365 days)</h2>
    <div class="heat-grid" aria-label="Review heatmap">
        {% for date, count in history.items() %}
            {% if count == 0 %}{% set level = 0 %}
            {% elif count <= 2 %}{% set level = 1 %}
            {% elif count <= 5 %}{% set level = 2 %}
            {% elif count <= 10 %}{% set level = 3 %}
            {% else %}{% set level = 4 %}{% endif %}
            <div class="heat-cell heat-{{ level }}" title="{{ date }}: {{ count }} review{% if count != 1 %}s{% endif %}"></div>
        {% endfor %}
    </div>
    <div class="mt-3 flex items-center gap-2 text-xs text-slate-400">
        <span>Less</span>
        <div class="heat-cell heat-0 h-3 w-3"></div>
        <div class="heat-cell heat-1 h-3 w-3"></div>
        <div class="heat-cell heat-2 h-3 w-3"></div>
        <div class="heat-cell heat-3 h-3 w-3"></div>
        <div class="heat-cell heat-4 h-3 w-3"></div>
        <span>More</span>
    </div>
</div>

<!-- State breakdown chart -->
<div class="mb-8 rounded-xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-900">
    <h2 class="mb-4 text-sm font-semibold uppercase tracking-widest text-slate-400 dark:text-slate-500">Collection by state</h2>
    <div class="relative h-40">
        <canvas id="stateChart"></canvas>
    </div>
</div>

<!-- Per-deck table -->
<div class="rounded-xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
    <div class="border-b border-slate-100 px-6 py-4 dark:border-slate-800">
        <h2 class="text-sm font-semibold uppercase tracking-widest text-slate-400 dark:text-slate-500">Per-deck breakdown</h2>
    </div>
    {% if deck_stats %}
    <div class="overflow-x-auto">
        <table class="w-full text-sm">
            <thead>
                <tr class="border-b border-slate-100 dark:border-slate-800 text-left text-xs font-semibold uppercase tracking-wider text-slate-400">
                    <th class="px-6 py-3">Deck</th>
                    <th class="px-4 py-3 text-right">Total</th>
                    <th class="px-4 py-3 text-right">New</th>
                    <th class="px-4 py-3 text-right">Learning</th>
                    <th class="px-4 py-3 text-right">Review</th>
                    <th class="px-4 py-3 text-right">Avg Diff</th>
                    <th class="px-4 py-3 text-right">Lapse Rate</th>
                </tr>
            </thead>
            <tbody class="divide-y divide-slate-100 dark:divide-slate-800">
                {% for d in deck_stats %}
                <tr class="hover:bg-slate-50 dark:hover:bg-slate-800/50">
                    <td class="px-6 py-3 font-medium text-slate-700 dark:text-slate-300">{{ d.deck_name }}</td>
                    <td class="px-4 py-3 text-right tabular-nums text-slate-600 dark:text-slate-400">{{ d.total }}</td>
                    <td class="px-4 py-3 text-right tabular-nums text-slate-500">{{ d.new }}</td>
                    <td class="px-4 py-3 text-right tabular-nums text-amber-600 dark:text-amber-400">{{ d.learning }}</td>
                    <td class="px-4 py-3 text-right tabular-nums text-emerald-600 dark:text-emerald-400">{{ d.review }}</td>
                    <td class="px-4 py-3 text-right tabular-nums text-slate-500">{{ d.avg_difficulty }}</td>
                    <td class="px-4 py-3 text-right tabular-nums text-slate-500">{{ d.lapse_rate }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
    {% else %}
    <p class="px-6 py-8 text-center text-sm text-slate-400">No data yet — start reviewing cards to see stats.</p>
    {% endif %}
</div>

{% endblock %}

{% block extra_scripts %}
<script>
(function() {
    const states = {{ overall.by_state | tojson }};
    const labels = ['New', 'Learning', 'Review', 'Relearning'];
    const keys   = ['NEW', 'LEARNING', 'REVIEW', 'RELEARNING'];
    const data   = keys.map(k => states[k] || 0);
    const colors = ['#6366f1', '#f59e0b', '#10b981', '#ef4444'];

    new Chart(document.getElementById('stateChart'), {
        type: 'bar',
        data: { labels, datasets: [{ data, backgroundColor: colors, borderRadius: 4 }] },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                x: { grid: { display: false }, ticks: { precision: 0 } },
                y: { grid: { display: false } }
            }
        }
    });
})();
</script>
{% endblock %}
```

- [ ] **Step 3.4: Smoke test in browser**

```bash
# from repo root, with a cards directory that has some data
python -m hashcards drill ./KnowledgeCards
# open http://localhost:8000/stats
```

Verify: heatmap renders, table shows decks, chart shows bars. No 500 errors.

- [ ] **Step 3.5: Commit**

```bash
git add hashcards/web/app.py hashcards/web/templates/base.html hashcards/web/templates/stats.html
git commit -m "feat: add /stats page with heatmap, deck breakdown, and state chart"
```

---

## Task 4: Generator Module

**Files:**
- Create: `hashcards/generator.py`
- Modify: `requirements.txt`
- Create: `tests/test_generator.py`

- [ ] **Step 4.1: Add `openai` to `requirements.txt`**

Replace the content of `requirements.txt`:

```
flask>=2.3.0
openai>=1.0.0
```

Install:

```bash
pip install openai
```

- [ ] **Step 4.2: Write failing tests**

Create `tests/test_generator.py`:

```python
"""Tests for the card generator module"""
import pytest
from unittest.mock import MagicMock, patch
from hashcards.generator import CardGenerator


SAMPLE_OUTPUT = """Q: What does FSRS stand for?
A: Free Spaced Repetition Scheduler

C: FSRS uses [stability] and [difficulty] to schedule cards.

Q: What rating resets a card's interval?
A: Again (rating 1)
"""


def make_generator():
    return CardGenerator(api_key="test-key")


def test_generator_init_sets_client():
    gen = make_generator()
    assert gen.client is not None


def test_generate_returns_string(monkeypatch):
    gen = make_generator()

    mock_response = MagicMock()
    mock_response.choices[0].message.content = SAMPLE_OUTPUT
    gen.client.chat.completions.create = MagicMock(return_value=mock_response)

    result = gen.generate("Some text about spaced repetition.", existing_decks=[])
    assert isinstance(result, str)
    assert "Q:" in result
    assert "A:" in result


def test_generate_calls_qwen_max(monkeypatch):
    gen = make_generator()

    mock_response = MagicMock()
    mock_response.choices[0].message.content = SAMPLE_OUTPUT
    create_mock = MagicMock(return_value=mock_response)
    gen.client.chat.completions.create = create_mock

    gen.generate("Some text.", existing_decks=["math", "science"])

    call_kwargs = create_mock.call_args.kwargs
    assert call_kwargs["model"] == "qwen-max"
    # thinking disabled
    assert call_kwargs.get("extra_body", {}).get("enable_thinking") is False


def test_generate_returns_empty_string_on_empty_response(monkeypatch):
    gen = make_generator()

    mock_response = MagicMock()
    mock_response.choices[0].message.content = ""
    gen.client.chat.completions.create = MagicMock(return_value=mock_response)

    result = gen.generate("text", existing_decks=[])
    assert result == ""
```

- [ ] **Step 4.3: Run to confirm failure**

```bash
pytest tests/test_generator.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'hashcards.generator'`

- [ ] **Step 4.4: Create `hashcards/generator.py`**

```python
"""
Card Generator — AI-assisted card creation via DashScope (qwen-max)
Uses the OpenAI-compatible endpoint.
"""

import openai


SYSTEM_PROMPT = """You are a flashcard generator for the hashcards system.

Output ONLY valid hashcards-format Markdown. No prose, no headings, no code fences.

Rules:
- Q&A format:  Q: <question>\\nA: <answer>
- Cloze format: C: Sentence with [key term] filled in.
- One blank line between cards.
- Use Q&A for conceptual questions, cloze for factual recall.
- One card per distinct concept. Be concise.
- Do not number cards. Do not add any other text.
"""


class CardGenerator:
    """Generate hashcards-format cards from free text using qwen-max."""

    def __init__(self, api_key: str):
        self.client = openai.OpenAI(
            api_key=api_key,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )

    def generate(self, source_text: str, existing_decks: list) -> str:
        """
        Generate cards from source_text.

        Args:
            source_text: Raw text to generate cards from.
            existing_decks: List of existing deck names (for context in prompt).

        Returns:
            Markdown string in hashcards format, or "" on empty response.
        """
        deck_hint = ""
        if existing_decks:
            deck_hint = f"\nExisting decks for context: {', '.join(existing_decks[:10])}."

        user_content = f"Generate flashcards from the following text.{deck_hint}\n\n---\n{source_text}"

        response = self.client.chat.completions.create(
            model="qwen-max",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            extra_body={"enable_thinking": False},
        )

        return response.choices[0].message.content or ""
```

- [ ] **Step 4.5: Run tests — expect pass**

```bash
pytest tests/test_generator.py -v
```

Expected: all 4 tests PASS

- [ ] **Step 4.6: Commit**

```bash
git add hashcards/generator.py tests/test_generator.py requirements.txt
git commit -m "feat: add CardGenerator with DashScope/qwen-max backend"
```

---

## Task 5: Generate Page (`/generate`)

**Files:**
- Modify: `hashcards/web/app.py`
- Create: `hashcards/web/templates/generate.html`

- [ ] **Step 5.1: Add `/generate` and `/generate/save` routes to `hashcards/web/app.py`**

Add the following imports at the top of `web/app.py` (after existing imports):

```python
import os
from datetime import date
```

Add these routes inside `_register_routes`, after the `/stats` route:

```python
@self.app.route('/generate', methods=['GET', 'POST'])
def generate():
    """AI card generation — input form and preview"""
    error = None
    preview = None
    deck_name = None

    if request.method == 'POST':
        source_text = request.form.get('source_text', '').strip()
        deck_name = request.form.get('deck_name', '').strip() or f"generated_{date.today().isoformat()}"

        api_key = os.environ.get('DASHSCOPE_API_KEY')
        if not api_key:
            error = "DASHSCOPE_API_KEY environment variable is not set."
        elif not source_text:
            error = "Please paste some text to generate cards from."
        else:
            try:
                from ..generator import CardGenerator
                gen = CardGenerator(api_key=api_key)
                existing_decks = list({c.deck_name for c in self.cards_cache.values()})
                preview = gen.generate(source_text, existing_decks=existing_decks)
                if not preview:
                    error = "The model returned no cards. Try with more detailed text."
            except Exception as exc:
                error = f"Generation failed: {exc}"

    return render_template('generate.html', preview=preview, deck_name=deck_name, error=error)


@self.app.route('/generate/save', methods=['POST'])
def generate_save():
    """Save generated cards to a .md file and reload"""
    content = request.form.get('content', '').strip()
    deck_name = request.form.get('deck_name', f"generated_{date.today().isoformat()}").strip()

    if content:
        # Sanitize deck_name to a safe filename (keep slashes for subdirs, strip dangerous chars)
        safe_name = "".join(c for c in deck_name if c.isalnum() or c in "-_/")
        target = self.cards_dir / f"{safe_name}.md"
        target.parent.mkdir(parents=True, exist_ok=True)

        # Append if same-day file already exists, otherwise create
        with open(target, 'a', encoding='utf-8') as f:
            f.write("\n" + content + "\n")

        self._load_all_cards()

    return redirect(url_for('index'))
```

- [ ] **Step 5.2: Create `hashcards/web/templates/generate.html`**

```html
{% extends "base.html" %}

{% block title %}Generate Cards — hashcards{% endblock %}

{% block content %}

<div class="mb-8">
    <h1 class="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100">Generate Cards</h1>
    <p class="mt-1 text-sm text-slate-500 dark:text-slate-400">Paste text and let AI create flashcards for you</p>
</div>

{% if error %}
<div class="mb-6 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-800 dark:bg-red-950 dark:text-red-300">
    {{ error }}
</div>
{% endif %}

{% if not preview %}
<!-- Step 1: Input form -->
<form method="POST" action="/generate">
    <div class="mb-6 rounded-xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-900">
        <label for="deck_name" class="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300">
            Deck name
        </label>
        <input type="text" id="deck_name" name="deck_name"
               placeholder="generated_{{ today }}"
               class="mb-5 w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-800 focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-300 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200">

        <label for="source_text" class="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300">
            Source text
        </label>
        <textarea id="source_text" name="source_text" rows="14" required
                  placeholder="Paste an article, notes, or any text here..."
                  class="w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-800 focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-300 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 font-mono"></textarea>
    </div>

    <div class="flex justify-end">
        <button type="submit"
                class="inline-flex cursor-pointer items-center gap-2 rounded-lg bg-indigo-600 px-6 py-2.5 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500">
            Generate cards
        </button>
    </div>
</form>

{% else %}
<!-- Step 2: Preview + save -->
<div class="mb-6 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800 dark:border-emerald-800 dark:bg-emerald-950 dark:text-emerald-300">
    Cards generated for deck <strong>{{ deck_name }}</strong>. Edit below then save.
</div>

<form method="POST" action="/generate/save">
    <input type="hidden" name="deck_name" value="{{ deck_name }}">

    <div class="mb-6 rounded-xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-900">
        <label for="content" class="mb-2 block text-sm font-medium text-slate-700 dark:text-slate-300">
            Edit generated cards
        </label>
        <textarea id="content" name="content" rows="20"
                  class="w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-800 focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-300 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 font-mono">{{ preview }}</textarea>
    </div>

    <div class="flex items-center justify-between">
        <a href="/generate" class="text-sm text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200">
            ← Start over
        </a>
        <button type="submit"
                class="inline-flex cursor-pointer items-center gap-2 rounded-lg bg-emerald-600 px-6 py-2.5 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-emerald-700 focus:outline-none focus:ring-2 focus:ring-emerald-500">
            Save to {{ deck_name }}.md
        </button>
    </div>
</form>
{% endif %}

{% endblock %}
```

- [ ] **Step 5.3: Fix missing `today` variable in template**

The template uses `{{ today }}` as a placeholder hint. Pass it from the route. In the `generate` route in `app.py`, update the `render_template` call:

```python
return render_template(
    'generate.html',
    preview=preview,
    deck_name=deck_name,
    error=error,
    today=date.today().isoformat()
)
```

- [ ] **Step 5.4: Smoke test**

```bash
# Start server (ensure DASHSCOPE_API_KEY is set)
export DASHSCOPE_API_KEY=your_key_here
python -m hashcards drill ./KnowledgeCards

# Open http://localhost:8000/generate
# Paste a paragraph of text, click Generate
# Verify preview appears with Q: / A: / C: cards
# Click Save — verify redirect to / and new deck appears
```

Also test the error path: unset the key and verify the banner appears instead of a crash.

```bash
unset DASHSCOPE_API_KEY
# reload /generate and submit form → should show error banner
```

- [ ] **Step 5.5: Commit**

```bash
git add hashcards/web/app.py hashcards/web/templates/generate.html
git commit -m "feat: add /generate page for AI-assisted card creation"
```

---

## Task 6: Final Integration Check

- [ ] **Step 6.1: Run full test suite**

```bash
pytest tests/ -v
```

Expected: all tests PASS (12 tests across 3 files)

- [ ] **Step 6.2: Manual end-to-end check**

```bash
python -m hashcards drill ./KnowledgeCards
```

Verify:
1. Cards in `KnowledgeCards/algo/01-papers/` subdirectories appear in the deck list with path-style names
2. `/stats` shows heatmap, deck table, and state chart
3. `/generate` produces cards and saves them to a new `.md` file
4. After saving, the new deck appears on the home page immediately

- [ ] **Step 6.3: Final commit**

```bash
git add .
git commit -m "chore: complete hashcards enhancements (recursive loading, stats, AI generation)"
```

---

## Self-Review Notes

**Spec coverage:**
- ✅ Recursive loading with relative path deck names (Task 1)
- ✅ `get_review_history()` + `get_deck_stats()` (Task 2)
- ✅ `/stats` with heatmap, per-deck table, state chart (Task 3)
- ✅ `generator.py` with DashScope/qwen-max, `enable_thinking=False` (Task 4)
- ✅ `/generate` form → preview → save to timestamped `.md` (Task 5)
- ✅ Nav links for Stats and Generate (Step 3.2)
- ✅ `openai` added to `requirements.txt` (Step 4.1)
- ✅ Appends to same-day file rather than overwriting (Step 5.1)

**Type consistency:**
- `get_review_history()` returns `dict` (str→int) — used as `history.items()` in template ✅
- `get_deck_stats()` returns `list[dict]` — iterated as `deck_stats` in template ✅
- `CardGenerator.generate()` signature matches test mocks ✅

**No placeholders:** All steps contain complete code. ✅
