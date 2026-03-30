"""Tests for the card generator module"""
import pytest
from unittest.mock import MagicMock
from hashcards.generator import CardGenerator

SAMPLE_OUTPUT = """Q: What does FSRS stand for?
A: Free Spaced Repetition Scheduler

C: FSRS uses [stability] and [difficulty] to schedule cards.
"""

def make_generator():
    return CardGenerator(api_key="test-key")

def test_generator_init_sets_client():
    gen = make_generator()
    assert gen.client is not None

def test_generate_returns_string():
    gen = make_generator()
    mock_response = MagicMock()
    mock_response.choices[0].message.content = SAMPLE_OUTPUT
    gen.client.chat.completions.create = MagicMock(return_value=mock_response)
    result = gen.generate("Some text about spaced repetition.", existing_decks=[])
    assert isinstance(result, str)
    assert "Q:" in result
    assert "A:" in result

def test_generate_calls_qwen_max():
    gen = make_generator()
    mock_response = MagicMock()
    mock_response.choices[0].message.content = SAMPLE_OUTPUT
    create_mock = MagicMock(return_value=mock_response)
    gen.client.chat.completions.create = create_mock
    gen.generate("Some text.", existing_decks=["math", "science"])
    call_kwargs = create_mock.call_args.kwargs
    assert call_kwargs["model"] == "qwen-max"
    assert call_kwargs.get("extra_body", {}).get("enable_thinking") is False

def test_generate_returns_empty_string_on_empty_response():
    gen = make_generator()
    mock_response = MagicMock()
    mock_response.choices[0].message.content = ""
    gen.client.chat.completions.create = MagicMock(return_value=mock_response)
    result = gen.generate("text", existing_decks=[])
    assert result == ""
