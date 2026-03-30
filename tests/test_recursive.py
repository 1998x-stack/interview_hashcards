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
