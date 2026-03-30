"""Tests for /generate and /generate/save routes"""
import tempfile
import pytest
from pathlib import Path
from hashcards.web.app import HashcardsApp


def make_app(tmp_path):
    return HashcardsApp(str(tmp_path), db_path=str(tmp_path / ".test.db"))


def test_generate_get_renders_form():
    with tempfile.TemporaryDirectory() as tmp:
        app = make_app(Path(tmp))
        client = app.app.test_client()
        resp = client.get('/generate')
        assert resp.status_code == 200
        assert b'Generate Cards' in resp.data
        assert b'source_text' in resp.data


def test_generate_post_missing_api_key_shows_error():
    import os
    import unittest.mock
    with tempfile.TemporaryDirectory() as tmp:
        app = make_app(Path(tmp))
        client = app.app.test_client()
        env_without_key = {k: v for k, v in os.environ.items() if k != 'DASHSCOPE_API_KEY'}
        with unittest.mock.patch.dict(os.environ, env_without_key, clear=True):
            resp = client.post('/generate', data={
                'source_text': 'some text',
                'deck_name': 'test'
            })
        assert resp.status_code == 200
        assert b'DASHSCOPE_API_KEY' in resp.data


def test_generate_save_writes_file_and_reloads():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        app = make_app(root)
        client = app.app.test_client()
        resp = client.post('/generate/save', data={
            'content': 'Q: Test?\nA: Yes\n',
            'deck_name': 'my-deck'
        })
        assert resp.status_code == 302  # redirect to /
        assert (root / 'my-deck.md').exists()
        assert 'Q: Test?' in (root / 'my-deck.md').read_text()


def test_generate_save_strips_leading_slash_from_deck_name():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        app = make_app(root)
        client = app.app.test_client()
        resp = client.post('/generate/save', data={
            'content': 'Q: Test?\nA: Yes\n',
            'deck_name': '/etc/passwd'
        })
        assert resp.status_code == 302
        # Should be contained within cards_dir
        assert not (Path('/etc') / 'passwd.md').exists()
        assert (root / 'etc' / 'passwd.md').exists()


def test_generate_save_empty_content_does_not_write():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        app = make_app(root)
        client = app.app.test_client()
        resp = client.post('/generate/save', data={
            'content': '',
            'deck_name': 'empty'
        })
        assert resp.status_code == 302
        assert not (root / 'empty.md').exists()
