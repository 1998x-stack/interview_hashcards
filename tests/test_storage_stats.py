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
