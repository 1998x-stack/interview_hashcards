"""
Card Storage - Manage learning records in SQLite
Cards themselves live in Markdown files; only scheduling data is in DB

Design principle: Separation of concerns
- Markdown files = source of truth for card content
- SQLite = ephemeral scheduling state
"""

import sqlite3
from datetime import datetime
from typing import List, Optional
from pathlib import Path

from .scheduler import CardSchedule, ReviewLog, State, Rating


class CardStorage:
    """
    Manages SQLite database for card scheduling state
    
    Database schema:
    - schedules: Current scheduling state for each card
    - reviews: Historical review logs
    """
    
    def __init__(self, db_path: str = ".hashcards.db"):
        """
        Initialize storage
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_db()
    
    def _init_db(self):
        """Create database tables if they don't exist"""
        cursor = self.conn.cursor()
        
        # Card schedules table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schedules (
                card_hash TEXT PRIMARY KEY,
                deck_name TEXT NOT NULL,
                state INTEGER NOT NULL,
                stability REAL NOT NULL,
                difficulty REAL NOT NULL,
                elapsed_days INTEGER NOT NULL,
                scheduled_days INTEGER NOT NULL,
                reps INTEGER NOT NULL,
                lapses INTEGER NOT NULL,
                last_review TEXT,
                due TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        
        # Review logs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                card_hash TEXT NOT NULL,
                rating INTEGER NOT NULL,
                state INTEGER NOT NULL,
                review_time TEXT NOT NULL,
                scheduled_days INTEGER NOT NULL,
                elapsed_days INTEGER NOT NULL,
                FOREIGN KEY (card_hash) REFERENCES schedules(card_hash)
            )
        """)
        
        # Indexes for performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_schedules_due 
            ON schedules(due)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_schedules_deck 
            ON schedules(deck_name)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_reviews_card 
            ON reviews(card_hash)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_reviews_time 
            ON reviews(review_time)
        """)
        
        self.conn.commit()
    
    def save_schedule(self, schedule: CardSchedule, deck_name: str):
        """Save or update card schedule"""
        cursor = self.conn.cursor()
        now = datetime.now().isoformat()
        
        cursor.execute("""
            INSERT INTO schedules (
                card_hash, deck_name, state, stability, difficulty,
                elapsed_days, scheduled_days, reps, lapses,
                last_review, due, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(card_hash) DO UPDATE SET
                state = excluded.state,
                stability = excluded.stability,
                difficulty = excluded.difficulty,
                elapsed_days = excluded.elapsed_days,
                scheduled_days = excluded.scheduled_days,
                reps = excluded.reps,
                lapses = excluded.lapses,
                last_review = excluded.last_review,
                due = excluded.due,
                updated_at = excluded.updated_at
        """, (
            schedule.card_hash,
            deck_name,
            schedule.state,
            schedule.stability,
            schedule.difficulty,
            schedule.elapsed_days,
            schedule.scheduled_days,
            schedule.reps,
            schedule.lapses,
            schedule.last_review.isoformat() if schedule.last_review else None,
            schedule.due.isoformat(),
            now,
            now
        ))
        
        self.conn.commit()
    
    def get_schedule(self, card_hash: str) -> Optional[CardSchedule]:
        """Retrieve card schedule by hash"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM schedules WHERE card_hash = ?
        """, (card_hash,))
        
        row = cursor.fetchone()
        if not row:
            return None
        
        return CardSchedule(
            card_hash=row['card_hash'],
            state=State(row['state']),
            stability=row['stability'],
            difficulty=row['difficulty'],
            elapsed_days=row['elapsed_days'],
            scheduled_days=row['scheduled_days'],
            reps=row['reps'],
            lapses=row['lapses'],
            last_review=datetime.fromisoformat(row['last_review']) if row['last_review'] else None,
            due=datetime.fromisoformat(row['due'])
        )
    
    def log_review(self, log: ReviewLog):
        """Save review log"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO reviews (
                card_hash, rating, state, review_time,
                scheduled_days, elapsed_days
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            log.card_hash,
            log.rating,
            log.state,
            log.review_time.isoformat(),
            log.scheduled_days,
            log.elapsed_days
        ))
        
        self.conn.commit()
    
    def get_due_cards(self, deck_name: Optional[str] = None, limit: Optional[int] = None) -> List[str]:
        """
        Get card hashes that are due for review
        
        Args:
            deck_name: Filter by deck (None = all decks)
            limit: Maximum number of cards to return
            
        Returns:
            List of card hashes
        """
        cursor = self.conn.cursor()
        now = datetime.now().isoformat()
        
        query = """
            SELECT card_hash FROM schedules 
            WHERE due <= ?
        """
        params = [now]
        
        if deck_name:
            query += " AND deck_name = ?"
            params.append(deck_name)
        
        query += " ORDER BY due ASC"
        
        if limit:
            query += f" LIMIT {limit}"
        
        cursor.execute(query, params)
        return [row['card_hash'] for row in cursor.fetchall()]
    
    def get_stats(self, deck_name: Optional[str] = None) -> dict:
        """Get learning statistics"""
        cursor = self.conn.cursor()
        
        where_clause = "WHERE deck_name = ?" if deck_name else ""
        params = [deck_name] if deck_name else []
        
        # Total cards
        cursor.execute(f"""
            SELECT COUNT(*) as total FROM schedules {where_clause}
        """, params)
        total = cursor.fetchone()['total']
        
        # Due cards
        now = datetime.now().isoformat()
        cursor.execute(f"""
            SELECT COUNT(*) as due FROM schedules 
            {where_clause}
            {"AND" if where_clause else "WHERE"} due <= ?
        """, params + [now])
        due = cursor.fetchone()['due']
        
        # Cards by state
        cursor.execute(f"""
            SELECT state, COUNT(*) as count 
            FROM schedules {where_clause}
            GROUP BY state
        """, params)
        by_state = {State(row['state']).name: row['count'] for row in cursor.fetchall()}
        
        # Reviews today
        today = datetime.now().date().isoformat()
        cursor.execute("""
            SELECT COUNT(*) as reviews_today 
            FROM reviews 
            WHERE DATE(review_time) = ?
        """, (today,))
        reviews_today = cursor.fetchone()['reviews_today']
        
        return {
            'total_cards': total,
            'due_cards': due,
            'by_state': by_state,
            'reviews_today': reviews_today
        }
    
    def delete_card(self, card_hash: str):
        """Delete card and its review history"""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM schedules WHERE card_hash = ?", (card_hash,))
        cursor.execute("DELETE FROM reviews WHERE card_hash = ?", (card_hash,))
        self.conn.commit()
    
    def close(self):
        """Close database connection"""
        self.conn.close()