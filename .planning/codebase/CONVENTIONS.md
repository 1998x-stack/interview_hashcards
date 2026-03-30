# Coding Conventions

**Analysis Date:** 2026-03-30

## Naming Patterns

**Files:**
- Lowercase with underscores: `parser.py`, `scheduler.py`, `storage.py`, `hasher.py`
- Web subpackage: `hashcards/web/app.py`, `hashcards/web/__init__.py`
- Template files: `study.html`, `browse.html`, `index.html` (lowercase, no underscores)

**Functions:**
- snake_case: `parse_file()`, `parse_content()`, `save_schedule()`, `get_due_cards()`, `review_card()`
- Private functions (internal use): prefixed with `_`: `_extract_deck_name()`, `_init_db()`, `_register_routes()`, `_load_all_cards()`
- Command functions in CLI: `cmd_drill()`, `cmd_stats()`, `cmd_validate()`, `cmd_export()`

**Variables:**
- snake_case: `card_hash`, `deck_name`, `card_type`, `elapsed_days`, `scheduled_days`, `learning_steps`
- Constants (uppercase): `DEFAULT_PARAMS`, `QA_PATTERN`, `CLOZE_PATTERN`, `CLOZE_DELETION`
- Private module imports within methods: use lazy imports where needed (`from .hasher import CardHasher` inside method)

**Types and Classes:**
- PascalCase: `Card`, `CardParser`, `CardStorage`, `FSRSScheduler`, `CardSchedule`, `ReviewLog`, `Rating`, `State`, `CardType`, `CardHasher`, `HashcardsApp`
- Enums: `class Rating(IntEnum):`, `class State(IntEnum):`, `class CardType(Enum):`
- Dataclasses: `@dataclass` decorator for `Card`, `CardSchedule`, `ReviewLog`

## Code Style

**Formatting:**
- No explicit linter/formatter detected (no `.eslintrc`, `pyproject.toml`, `.prettierrc`)
- Follow PEP 8 implicitly observed in codebase
- Consistent spacing: 4 spaces for indentation
- Line length: generally 80-100 characters (SQL queries may be longer)

**Imports Organization:**
Order follows:
1. Standard library imports: `import re`, `import sys`, `from datetime import datetime`, `from typing import List, Dict, Optional`
2. Third-party imports: `from flask import Flask, render_template, request, jsonify, redirect, url_for`
3. Relative imports: `from .parser import CardParser`, `from ..parser import CardParser`

**Import style:**
- Use relative imports for package imports: `from .parser import CardParser` (same package), `from ..parser import CardParser` (parent package)
- Lazy imports in methods: `from .hasher import CardHasher` inside `get_hash()` method to avoid circular dependencies
- Import both classes and functions together: `from .scheduler import CardSchedule, ReviewLog, State, Rating`
- No `import *` patterns observed

## Error Handling

**Pattern:**
- CLI uses `try-except` block in `cmd_validate()` at `hashcards/cli.py:78-84` to catch parsing errors
- File not found errors checked explicitly: `if not cards_dir.exists():`
- Database checks: `if not db_path.exists():`
- Exit codes: Use `sys.exit(1)` for error conditions (see `hashcards/cli.py:21, 43, 69, 90, 150`)

**Error Communication:**
- Write errors to stderr: `print(f"Error: ...", file=sys.stderr)`
- Warnings also to stderr: `print(f"Warning: ...", file=sys.stderr)`
- Success messages to stdout (implicit)
- Include context in error messages: `f"Error: Directory not found: {cards_dir}"`

**Exception Handling:**
- Catch broad `Exception` in CLI: `except Exception as e:` at line 82 of `cli.py`
- Store error info: `errors.append((md_file.name, str(e)))`
- Report summary after processing: Print error count and file names at end

**Validation errors not raised:**
- Methods return data or None, not exceptions
- Storage `get_schedule()` returns `Optional[CardSchedule]` (None if not found)
- Parser collects deletions if they exist: `if deletions:` before creating cloze card

## Logging

**Framework:** No external logging framework (console.print patterns not used)

**Pattern:**
- Use `print()` for all user-facing output
- Print informational messages to stdout
- Print errors/warnings to stderr with `file=sys.stderr` parameter
- Status messages in CLI: `print(f"Loading cards from: {cards_dir}")`
- Progress in validation: `print(f"✓ {md_file.name}: {len(cards)} cards")`

**No structured logging:**
- No log levels (INFO, DEBUG, ERROR as separate methods)
- No log formatting configuration
- Direct print statements with user-friendly messages

## Comments

**When to Comment:**
- Module docstrings: Always present, explains purpose and design philosophy
- Class docstrings: Always present, explains what class does and design intent
- Method docstrings: Always present with Args and Returns sections
- Inline comments: Minimal, used for complex logic or important design notes
- Design principle comments: Explain "why" not "what" (see `parser.py:3` "Follows Unix philosophy: do one thing well - parse text")

**Documentation Style:**
- Module level: Triple-quoted docstrings at file start explaining purpose and design
- Class level: Triple-quoted docstrings explaining class purpose and major behavior
- Method level: Triple-quoted docstrings with Args, Returns, and occasionally design notes
- Lines too long: If docstring explains design, it comes first (before implementation details)

**Examples:**
```python
"""
Card Parser - Parse Markdown files into card objects
Follows Unix philosophy: do one thing well - parse text
"""

class CardParser:
    """
    Parse Markdown files containing flashcards

    Format:
    Q: What is the atomic number of carbon?
    A: 6

    C: The atomic number of [carbon] is [6].
    """

    @classmethod
    def parse_file(cls, filepath: str) -> List[Card]:
        """
        Parse a Markdown file and extract all cards

        Args:
            filepath: Path to the .md file

        Returns:
            List of Card objects
        """
```

## Function Design

**Size:** Functions are generally 10-40 lines, keeping related logic together

**Parameters:**
- Type hints always present: `def parse_file(cls, filepath: str) -> List[Card]:`
- Use Optional for nullable parameters: `Optional[str]`, `Optional[int]`, `Optional[datetime]`
- Default parameters in constructors: `db_path: str = ".hashcards.db"`, `host: str = 'localhost'`
- Dataclass fields have type hints: `card_hash: str`, `due: datetime`

**Return Values:**
- Explicit type hints: `-> List[Card]`, `-> Optional[CardSchedule]`, `-> tuple[CardSchedule, ReviewLog]`, `-> dict`
- Tuple returns with multiple types: Use `tuple[Type1, Type2]` syntax (see `scheduler.py:98`)
- None returns for failures: `if not row: return None`
- Dictionary returns for stats: `get_stats()` returns `dict` with keys like `'total_cards'`, `'by_state'`

## Module Design

**Exports:**
- Use `__all__` list in `__init__.py` files: `__all__ = ["CardParser", "FSRSScheduler", "CardStorage", "CardHasher"]`
- Barrel files: Core module `hashcards/__init__.py` re-exports main classes for convenient imports
- Web module: `hashcards/web/__init__.py` exports `HashcardsApp`

**Barrel Files:**
- `hashcards/__init__.py`: Central import point for main classes
- Reduces import complexity: Users can `from hashcards import CardParser` instead of `from hashcards.parser import CardParser`
- `__version__` and `__author__` metadata at module level

**Organization Principles:**
- One class per file (general rule): Parser class in `parser.py`, Scheduler in `scheduler.py`, etc.
- Exception: `scheduler.py` contains `Rating`, `State` enums alongside `FSRSScheduler` and data classes
- Data classes grouped with related logic: `CardSchedule` and `ReviewLog` in `scheduler.py` with the scheduler

## Type Hints

**Coverage:** Comprehensive throughout codebase

**Patterns:**
- Function arguments: Always type-hinted
- Return types: Always specified
- Class attributes: Type-hinted in dataclasses
- Imports from typing: `List`, `Dict`, `Optional` (Python 3.8-3.11 compatible, doesn't use `list[str]` syntax)
- Union types: Use `Optional[X]` for `Union[X, None]`

---

*Convention analysis: 2026-03-30*
