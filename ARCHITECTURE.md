# hashcards Architecture

## Design Philosophy

hashcards follows four core principles that guide every design decision:

### 1. Unix Philosophy
- **Do one thing well**: Each module has a single, clear responsibility
- **Text streams**: Cards are plain text Markdown files
- **Composability**: Use standard Unix tools (grep, awk, sed) with cards
- **Small tools**: Separate parsing, scheduling, storage, and UI concerns

### 2. Open Source Spirit
- **Transparency**: All algorithms and data formats are documented
- **Controllability**: Users can inspect and modify everything
- **Shareability**: Cards in Git repos for easy collaboration

### 3. Cognitive Engineering
- **Minimize friction**: Simplest possible card syntax
- **Optimize workflow**: Keyboard-driven interface
- **Fast feedback**: Instant card loading and review
- **Low cognitive load**: No manual scheduling decisions

### 4. Data Sovereignty
- **User ownership**: Cards in portable Markdown format
- **No vendor lock-in**: Exit strategy is `cp *.md /backup`
- **Privacy**: Everything runs locally
- **Longevity**: Plain text survives all software

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         User Layer                          │
│  CLI (cli.py)              Web Browser (templates/*.html)   │
└────────────────┬─────────────────────────┬──────────────────┘
                 │                         │
                 ▼                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                        │
│                    Flask App (web/app.py)                   │
└────┬──────────────┬────────────────┬─────────────┬──────────┘
     │              │                │             │
     ▼              ▼                ▼             ▼
┌─────────┐  ┌──────────┐  ┌──────────────┐  ┌─────────┐
│ Parser  │  │ Scheduler│  │   Storage    │  │ Hasher  │
│         │  │          │  │              │  │         │
│ .md →   │  │ FSRS     │  │  SQLite      │  │ Content │
│ Cards   │  │ Algorithm│  │  (schedules) │  │ Address │
└─────────┘  └──────────┘  └──────────────┘  └─────────┘
     │              │                │             │
     ▼              ▼                ▼             ▼
┌─────────────────────────────────────────────────────────────┐
│                        Data Layer                           │
│  Markdown Files (.md)          SQLite Database (.db)        │
│  Source of truth for cards    Ephemeral scheduling state    │
└─────────────────────────────────────────────────────────────┘
```

## Module Breakdown

### Core Modules

#### 1. parser.py - Card Parser
**Responsibility**: Convert Markdown text into structured card objects

**Design decisions**:
- Regex-based parsing for simplicity and speed
- Two card types: Q&A and Cloze
- Minimal syntax: `Q:`, `A:`, `C:`
- Line number tracking for error reporting

**Key functions**:
```python
CardParser.parse_file(filepath) -> List[Card]
CardParser.parse_content(text) -> List[Card]
CardParser.format_cloze_for_display(text, reveal_index)
```

**Why not use a full Markdown parser?**
- Overkill for our simple syntax
- Regex is fast and deterministic
- Direct control over parsing behavior

#### 2. hasher.py - Content Hasher
**Responsibility**: Generate unique identifiers for cards based on content

**Design decisions**:
- SHA-256 for cryptographic quality
- First 16 chars (64 bits) for human readability
- Whitespace normalization for robustness
- Content-addressable: hash = card identity

**Key insight**:
Content-addressability means:
- Same content = same card (deduplication)
- Changed content = new card (immutability)
- No ID collisions across decks

#### 3. scheduler.py - FSRS Scheduler
**Responsibility**: Implement state-of-the-art spaced repetition algorithm

**Design decisions**:
- FSRS (not SM-2) for better accuracy
- Four ratings: Again, Hard, Good, Easy
- Stability + Difficulty model
- Default 90% retention target

**Key data structures**:
```python
CardSchedule: Current state of a card
ReviewLog: Historical review record
State: NEW, LEARNING, REVIEW, RELEARNING
```

**Algorithm overview**:
1. Calculate memory retrievability from stability
2. Update stability based on rating and retrievability
3. Adjust difficulty based on performance
4. Compute next interval from stability

**Why FSRS over SM-2?**
- Models forgetting curves explicitly
- Adapts to card difficulty
- Better handles forgotten mature cards
- Research-backed improvements

#### 4. storage.py - Data Storage
**Responsibility**: Persist scheduling state in SQLite

**Design decisions**:
- SQLite for simplicity (no server required)
- Only scheduling data in DB, not cards
- Two tables: schedules + reviews
- Indexes for performance

**Schema**:
```sql
schedules: card_hash, state, stability, difficulty, due, ...
reviews: card_hash, rating, review_time, elapsed_days, ...
```

**Why separate cards from schedules?**
- Cards (content) should be version-controlled
- Schedules (state) are ephemeral
- Easy to reset by deleting .db file
- Clear separation of concerns

#### 5. web/app.py - Flask Application
**Responsibility**: HTTP interface for studying cards

**Design decisions**:
- Minimalist UI focused on review experience
- Keyboard shortcuts for speed
- Progressive enhancement (works without JS)
- In-memory card cache for performance

**Routes**:
- `/` - Dashboard with stats
- `/study` - Main review interface
- `/browse` - View all cards
- `/api/stats` - JSON statistics
- `/api/reload` - Refresh cards from disk

**Why Flask?**
- Lightweight (no complex dependencies)
- Standard Python web framework
- Easy to understand and modify
- Good enough for local-first app

#### 6. cli.py - Command Line Interface
**Responsibility**: Unix-friendly command line tool

**Commands**:
- `drill` - Start study session (launches web server)
- `stats` - Show learning statistics
- `validate` - Check card syntax
- `export` - (Future) Export to other formats

**Design decisions**:
- Simple subcommands
- Follows Unix conventions
- Composable with shell scripts
- Helpful error messages

## Data Flow

### 1. Starting a Study Session

```
User runs: hashcards drill ./Cards
         │
         ▼
   CLI parses arguments
         │
         ▼
   Load all .md files
         │
         ▼
   Parser extracts cards
         │
         ▼
   Hash each card's content
         │
         ▼
   Check DB for existing schedules
         │
         ├─ Found → Load schedule
         └─ Not found → Init new schedule
         │
         ▼
   Cache cards in memory
         │
         ▼
   Start Flask web server
         │
         ▼
   User opens browser → http://localhost:8000
```

### 2. Reviewing a Card

```
User visits /study
         │
         ▼
   Query DB for due cards
         │
         ▼
   Fetch next due card from cache
         │
         ▼
   Render card (hide answer initially)
         │
         ▼
   User presses Space
         │
         ▼
   Show answer
         │
         ▼
   User presses 1/2/3/4
         │
         ▼
   POST to /review with rating
         │
         ▼
   Load card's schedule from DB
         │
         ▼
   Scheduler.review_card(schedule, rating)
         │
         ├─ Calculate retrievability
         ├─ Update stability
         ├─ Update difficulty
         └─ Compute next interval
         │
         ▼
   Save new schedule to DB
         │
         ▼
   Log review to DB
         │
         ▼
   Redirect to /study (next card)
```

### 3. Editing Cards

```
User edits Math.md in editor
         │
         ▼
   Changes saved to disk
         │
         ▼
   User refreshes browser or restarts server
         │
         ▼
   Parser reads updated file
         │
         ▼
   New content → New hash
         │
         ├─ Hash doesn't exist in DB
         └─ → Treated as new card
         │
         ▼
   Old hash no longer in .md files
         │
         └─ → Remains in DB but won't appear in reviews
```

## Key Design Patterns

### 1. Content-Addressable Storage
Cards are identified by hash of their content:
```python
card_hash = sha256(normalize(card_text))[:16]
```

**Benefits**:
- Natural deduplication
- Immutable identity
- No ID management needed
- Git-friendly (content changes = hash changes)

### 2. Separation of Concerns
Clear boundaries between modules:
- Parser: Text → Cards
- Hasher: Content → ID
- Scheduler: Schedule → Next review
- Storage: State ↔ Database
- Web: Cards → HTML

### 3. Cache-First Architecture
Cards loaded into memory at startup:
```python
self.cards_cache = {card_hash: card, ...}
```

**Trade-offs**:
- ✅ Fast card access
- ✅ Simple code (no lazy loading)
- ❌ Memory usage for large collections
- ❌ Manual reload needed after edits

**Why acceptable**: Most users have <10,000 cards (~1MB memory)

### 4. Database as State Machine
SQLite stores only scheduling state:
```
NEW → LEARNING → REVIEW → RELEARNING → REVIEW → ...
```

Source of truth is always the Markdown files.

## Performance Characteristics

### Time Complexity
- Parse file: O(n) where n = file size
- Load all cards: O(m) where m = number of files
- Find due cards: O(log d) with index, where d = total cards
- Review card: O(1) lookup + O(1) computation

### Space Complexity
- Cards cache: O(n) where n = total cards
- Database: O(n + r) where r = total reviews

### Scalability Limits
- **Sweet spot**: 1,000 - 10,000 cards
- **Tested up to**: Not benchmarked yet
- **Bottleneck**: Database queries for large histories
- **Mitigation**: SQLite indexes, LIMIT queries

## Security Considerations

### Local-First = Inherently Secure
- No network requests
- No user accounts
- No cloud storage
- All data stays on device

### Potential Risks
1. **SQL Injection**: Mitigated by parameterized queries
2. **Path Traversal**: Limited by Flask's security
3. **XSS**: Minimal - no user-generated HTML rendering

### Not Concerns (Local-First)
- Authentication
- Authorization
- Rate limiting
- CSRF (single-user app)

## Testing Strategy

### Unit Tests (TODO)
- Parser: Various card formats
- Scheduler: FSRS algorithm correctness
- Storage: Database operations

### Integration Tests (TODO)
- Full review workflow
- Card editing and reloading
- Statistics computation

### Manual Testing
- Create example decks
- Review cards with all ratings
- Edit cards and reload
- Use CLI commands

## Future Enhancements

### Short Term
- [ ] Image support in cards
- [ ] Audio playback
- [ ] Better mobile interface
- [ ] Export to Anki format

### Medium Term
- [ ] Sync between devices (Git-based)
- [ ] Card statistics and heat maps
- [ ] Custom FSRS parameter tuning
- [ ] Import from Anki

### Long Term
- [ ] Collaborative deck sharing
- [ ] Plugin system
- [ ] Advanced statistics
- [ ] Desktop app (Electron/Tauri)

### Explicitly Out of Scope
- Cloud sync (use Git instead)
- Social features (share via Git repos)
- Mobile native apps (PWA sufficient)
- Complex rich text (keep it simple)

## Comparison to Alternatives

### vs. Anki
**hashcards advantages**:
- Simpler card creation (Markdown vs WYSIWYG)
- Git-friendly (text files vs database)
- Cleaner codebase (modular vs monolithic)

**Anki advantages**:
- Mature ecosystem
- Rich plugins
- Mobile apps
- Large community

### vs. Mochi
**hashcards advantages**:
- FSRS algorithm (vs simple multiplier)
- Open source
- More flexible syntax
- Unix tool integration

**Mochi advantages**:
- Polished UI
- Better onboarding
- Native apps

### vs. RemNote/Roam
**hashcards advantages**:
- Focused on flashcards only
- No vendor lock-in
- Simpler mental model

**RemNote/Roam advantages**:
- Integrated note-taking
- Bidirectional links
- Richer features

## Implementation Notes

### Why Python?
- Rapid prototyping
- Rich ecosystem (Flask, SQLite)
- Easy to understand and modify
- Good enough performance for local use

### Why Flask?
- Minimal dependencies
- Standard web framework
- Easy to extend
- Sufficient for local apps

### Why SQLite?
- No setup required
- Single file database
- Fast for local queries
- Good Python support

### Why Not React/Vue?
- Server-side rendering sufficient
- Simpler codebase
- Faster initial page load
- Progressive enhancement

## Lessons Learned (Design Rationale)

### 1. Markdown Over WYSIWYG
Early versions had rich text editing. Removed because:
- Slower to type
- Harder to version control
- More code complexity
- Users wanted plain text anyway

### 2. Content Hashing Over IDs
Could have used auto-increment IDs. Content hashing is better:
- Automatic deduplication
- No ID management
- Clear change detection
- Better for Git

### 3. Web Interface Over TUI
Considered terminal UI (curses). Web is better:
- Easier to style
- Better input handling
- More accessible
- Future mobile support

### 4. SQLite Over Plain Text Schedules
Could store schedules in YAML alongside cards. SQLite is better:
- Faster queries
- Transactional safety
- Less merge conflicts
- Standard tool support

## Contributing Guidelines

When adding features, ask:
1. Does it respect the four core principles?
2. Does it add essential value vs. bloat?
3. Can users opt out if they don't want it?
4. Is the code simple and maintainable?

**Good additions**:
- Better keyboard shortcuts
- More card format options
- Export/import utilities
- Performance improvements

**Bad additions**:
- Social features (use Git for sharing)
- Cloud sync (use Git for sync)
- Complex scheduling tweaks (use FSRS defaults)
- Proprietary formats

## Conclusion

hashcards is an exercise in principled design:
- Everything serves the four core principles
- Each module has one clear job
- The user owns their data completely
- Learning is the primary goal, not features

The architecture is intentionally simple because simplicity scales better than cleverness.