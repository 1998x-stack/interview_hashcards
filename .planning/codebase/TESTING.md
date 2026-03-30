# Testing Patterns

**Analysis Date:** 2026-03-30

## Test Framework

**Status:** No testing framework currently present

**Framework:** Not detected
- No `pytest.ini`, `tox.ini`, `pyproject.toml`, or `setup.cfg` with test configuration
- No test dependencies in `requirements.txt` (currently only contains `flask>=2.3.0`)
- No test files found in codebase (no `test_*.py` or `*_test.py` files)
- No `conftest.py` or test fixtures present

**Run Commands:**
Testing infrastructure not yet established. When implemented, use:
```bash
pytest                          # Run all tests
pytest -v                       # Verbose mode
pytest --cov=hashcards         # With coverage report
pytest -k test_parser          # Run specific test file
pytest --watch                 # Watch mode (requires pytest-watch)
```

## Recommendation for Test Setup

**Suggested Framework:** `pytest`
- Add to `requirements.txt`: `pytest>=7.0`, `pytest-cov>=4.0`
- Create `tests/` directory in project root
- Create `tests/conftest.py` for shared fixtures

## Test File Organization

**Location Pattern (Recommended):**
```
tests/
├── conftest.py              # Shared fixtures
├── test_parser.py           # Tests for hashcards/parser.py
├── test_scheduler.py        # Tests for hashcards/scheduler.py
├── test_storage.py          # Tests for hashcards/storage.py
├── test_hasher.py           # Tests for hashcards/hasher.py
├── test_cli.py              # Tests for hashcards/cli.py
└── web/
    └── test_app.py          # Tests for hashcards/web/app.py
```

**Naming Convention:**
- File names: `test_<module>.py` (prefix with `test_`)
- Test functions: `test_<functionality>()` or `test_<class>_<method>()`
- Test classes (optional): `TestClassName` with `test_` prefixed methods

## Code Structure for Testing

**Codebase is well-suited for testing:**

### Dataclasses (Easy to Test)
- `Card` dataclass: `@dataclass` with simple fields - straightforward to instantiate for tests
- `CardSchedule`: Contains testable calculation inputs/outputs
- `ReviewLog`: Simple immutable record

### Class Methods (Testable)
```python
# From parser.py - classmethod pattern good for testing
@classmethod
def parse_file(cls, filepath: str) -> List[Card]:
    ...

@classmethod
def parse_content(cls, content: str, deck_name: str = "default") -> List[Card]:
    ...
```
- Classmethods can be called without instantiating class
- Reduces test setup overhead

### Pure Functions (Highly Testable)
- `CardHasher.hash_card(content: str) -> str`: Takes string, returns hash - deterministic
- `CardParser.format_cloze_for_display()`: Pure text transformation
- Static methods easily isolated

### Dependency Injection Pattern
- `FSRSScheduler.__init__()` accepts optional `params` dictionary - allows test override
- `CardStorage.__init__()` accepts `db_path` parameter - enables test database isolation
- `HashcardsApp.__init__()` accepts `cards_dir` and `db_path` - testable initialization

## Test Structure (Recommended Pattern)

**Suite Organization:**
```python
import pytest
from hashcards import CardParser, CardHasher
from hashcards.parser import Card, CardType

class TestCardParser:
    """Test CardParser functionality"""

    def test_parse_qa_card(self):
        content = "Q: What is Python?\nA: A programming language"
        cards = CardParser.parse_content(content)
        assert len(cards) == 1
        assert cards[0].card_type == CardType.QA
        assert cards[0].content["question"] == "What is Python?"

    def test_parse_cloze_card(self):
        content = "C: The capital of France is [Paris]"
        cards = CardParser.parse_content(content)
        assert len(cards) == 1
        assert cards[0].card_type == CardType.CLOZE
        assert "Paris" in cards[0].content["deletions"]
```

**Patterns to Use:**

1. **Arrange-Act-Assert (AAA)**
   ```python
   def test_hash_consistency():
       # Arrange
       content = "Q: Test\nA: Answer"

       # Act
       hash1 = CardHasher.hash_card(content)
       hash2 = CardHasher.hash_card(content)

       # Assert
       assert hash1 == hash2
   ```

2. **Fixtures (Recommended)**
   ```python
   # conftest.py
   @pytest.fixture
   def sample_markdown():
       return """Q: Question 1?\nA: Answer 1\n\nQ: Question 2?\nA: Answer 2"""

   # test_parser.py
   def test_parse_multiple_cards(sample_markdown):
       cards = CardParser.parse_content(sample_markdown)
       assert len(cards) == 2
   ```

3. **Parametrized Tests**
   ```python
   @pytest.mark.parametrize("content,expected_count", [
       ("Q: Q1\nA: A1", 1),
       ("Q: Q1\nA: A1\n\nQ: Q2\nA: A2", 2),
   ])
   def test_parse_various_inputs(content, expected_count):
       cards = CardParser.parse_content(content)
       assert len(cards) == expected_count
   ```

## Mocking

**Framework:** When implemented, use `unittest.mock` (stdlib) or `pytest-mock` plugin

**Patterns (Recommended):**

1. **Mock File Operations**
   ```python
   from unittest.mock import mock_open, patch

   def test_parse_file_with_mock():
       mock_data = "Q: Test\nA: Answer"
       with patch("builtins.open", mock_open(read_data=mock_data)):
           cards = CardParser.parse_file("test.md")
           assert len(cards) == 1
   ```

2. **Mock Database**
   ```python
   def test_get_schedule_not_found(mocker):
       mock_conn = mocker.MagicMock()
       storage = CardStorage(":memory:")  # Use in-memory DB for tests

       result = storage.get_schedule("nonexistent_hash")
       assert result is None
   ```

3. **Mock Flask Request Context**
   ```python
   from hashcards.web.app import HashcardsApp

   def test_study_route(tmp_path, mocker):
       # Create temporary card directory
       cards_dir = tmp_path / "cards"
       cards_dir.mkdir()

       app = HashcardsApp(str(cards_dir))
       client = app.app.test_client()

       response = client.get("/")
       assert response.status_code == 200
   ```

**What to Mock:**
- File system operations: Use `tmp_path` fixture instead
- Flask requests: Use `app.test_client()`
- Database: Use `:memory:` SQLite database for isolation
- DateTime: Mock `datetime.now()` for reproducible schedule tests

**What NOT to Mock:**
- Pure functions like `CardHasher.hash_card()` - test directly
- Enum values - use directly without mocking
- Dataclass instantiation - construct directly
- Configuration defaults - use actual default values

## Fixtures and Factories

**Test Data Pattern (Recommended in conftest.py):**

```python
import pytest
from hashcards.parser import Card, CardType
from datetime import datetime

@pytest.fixture
def sample_qa_card():
    """Single Q&A card for testing"""
    return Card(
        card_type=CardType.QA,
        content={"question": "What is 2+2?", "answer": "4"},
        deck_name="math",
        line_number=1,
        raw_text="Q: What is 2+2?\nA: 4"
    )

@pytest.fixture
def sample_cloze_card():
    """Single cloze card for testing"""
    return Card(
        card_type=CardType.CLOZE,
        content={"text": "The capital of France is [Paris]", "deletions": ["Paris"]},
        deck_name="geography",
        line_number=1,
        raw_text="C: The capital of France is [Paris]"
    )

@pytest.fixture
def sample_markdown_content():
    """Multi-card Markdown content"""
    return """Q: What is Python?
A: A programming language

Q: What is JavaScript?
A: A scripting language

C: The year [2025] is almost here"""

@pytest.fixture
def temp_cards_directory(tmp_path):
    """Create temporary directory with sample card files"""
    cards_dir = tmp_path / "cards"
    cards_dir.mkdir()

    # Write sample cards file
    cards_file = cards_dir / "sample.md"
    cards_file.write_text("""Q: Test Question?
A: Test Answer

C: Fill in the [blank]""")

    return cards_dir
```

**Location:**
- Fixtures live in `tests/conftest.py` - shared across all test files
- Module-specific fixtures in test file itself or in conftest organized by import pattern

## Coverage

**Requirements:** Not yet enforced (no coverage configuration present)

**Recommended Targets:**
- Parser: 90%+ (critical path for reading cards)
- Scheduler: 85%+ (complex algorithm but well-contained)
- Storage: 80%+ (database operations have environmental dependencies)
- CLI: 75%+ (some path requires manual testing)

**View Coverage (When Setup):**
```bash
pytest --cov=hashcards --cov-report=html
# Opens htmlcov/index.html in browser
```

**Add to CI/CD:**
```bash
pytest --cov=hashcards --cov-fail-under=80
```

## Test Types

**Unit Tests (Primary Focus):**
- Scope: Individual functions and classes in isolation
- Example: `test_parse_qa_card()` tests only `CardParser.parse_content()`
- Approach: Mock external dependencies (files, database)
- Location: `tests/test_parser.py`, `tests/test_scheduler.py`, etc.

**Integration Tests (Secondary):**
- Scope: Multiple components working together
- Example: Parser reading file → hashing content → storing schedule
- Approach: Use real temporary files and in-memory database
- Location: `tests/integration/` or marked with `@pytest.mark.integration`

**E2E Tests (Optional):**
- Framework: Not currently used, would use `pytest` with `Flask test client`
- Example: Full study session: load cards → get due card → submit rating → verify schedule updated
- Not critical for backend library, more important for web interface

## Common Test Patterns (Recommended)

**Async Testing:**
Not applicable - no async code in codebase

**Error Testing:**
```python
def test_parse_invalid_file_not_found():
    """Test handling of missing file"""
    with pytest.raises(FileNotFoundError):
        CardParser.parse_file("/nonexistent/path.md")

def test_storage_get_schedule_returns_none_for_missing():
    """Test graceful handling of missing schedule"""
    storage = CardStorage(":memory:")
    result = storage.get_schedule("nonexistent_hash")
    assert result is None

def test_cli_missing_directory_exits():
    """Test CLI error handling for missing directory"""
    from hashcards.cli import cmd_drill
    from argparse import Namespace

    args = Namespace(cards_dir="/nonexistent", host="localhost", port=8000, debug=False)
    with pytest.raises(SystemExit):
        cmd_drill(args)
```

**State Testing (Scheduler):**
```python
def test_scheduler_new_card_progress():
    """Test card state transitions through learning"""
    scheduler = FSRSScheduler()

    # Initialize
    schedule = scheduler.init_card("test_hash")
    assert schedule.state == State.NEW

    # First review
    schedule, log = scheduler.review_card(schedule, Rating.AGAIN)
    assert schedule.state == State.LEARNING

    # Graduate to review
    schedule, log = scheduler.review_card(schedule, Rating.GOOD)
    assert schedule.state == State.REVIEW
```

---

*Testing analysis: 2026-03-30*
