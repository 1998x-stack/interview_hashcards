"""
Flask Web Application for hashcards
Minimalist interface focused on the review experience
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for
from pathlib import Path
from typing import Optional
import os

from ..parser import CardParser, Card
from ..scheduler import FSRSScheduler, Rating
from ..storage import CardStorage


class HashcardsApp:
    """
    Flask application wrapper
    
    Design principles:
    - Simple, keyboard-driven interface
    - Fast loading and response
    - Progressive enhancement (works without JS)
    """
    
    def __init__(self, cards_dir: str, db_path: Optional[str] = None):
        """
        Initialize application
        
        Args:
            cards_dir: Directory containing .md card files
            db_path: Path to SQLite database (default: .hashcards.db in cards_dir)
        """
        self.cards_dir = Path(cards_dir)
        
        if db_path is None:
            db_path = str(self.cards_dir / ".hashcards.db")
        
        self.storage = CardStorage(db_path)
        self.scheduler = FSRSScheduler()
        
        # Cache cards in memory for fast access
        self.cards_cache = {}
        self._load_all_cards()
        
        # Create Flask app
        self.app = Flask(__name__)
        self.app.secret_key = os.urandom(24)
        self._register_routes()
    
    def _load_all_cards(self):
        """Load all cards from Markdown files"""
        self.cards_cache.clear()
        
        for md_file in self.cards_dir.glob("*.md"):
            cards = CardParser.parse_file(str(md_file))
            for card in cards:
                card_hash = card.get_hash()
                self.cards_cache[card_hash] = card
                
                # Initialize schedule if new card
                if not self.storage.get_schedule(card_hash):
                    schedule = self.scheduler.init_card(card_hash)
                    self.storage.save_schedule(schedule, card.deck_name)
    
    def _register_routes(self):
        """Register Flask routes"""
        
        @self.app.route('/')
        def index():
            """Home page with statistics"""
            stats = self.storage.get_stats()
            decks = self._get_deck_list()
            return render_template('index.html', stats=stats, decks=decks)
        
        @self.app.route('/study')
        @self.app.route('/study/<deck_name>')
        def study(deck_name: Optional[str] = None):
            """Study session"""
            due_hashes = self.storage.get_due_cards(deck_name, limit=1)
            
            if not due_hashes:
                return render_template('no_cards.html', deck_name=deck_name)
            
            card_hash = due_hashes[0]
            card = self.cards_cache.get(card_hash)
            schedule = self.storage.get_schedule(card_hash)
            
            if not card:
                # Card file was deleted - remove from DB
                self.storage.delete_card(card_hash)
                return redirect(url_for('study', deck_name=deck_name))
            
            return render_template(
                'study.html',
                card=card,
                schedule=schedule,
                card_hash=card_hash,
                deck_name=deck_name
            )
        
        @self.app.route('/review', methods=['POST'])
        def review():
            """Process card review"""
            card_hash = request.form.get('card_hash')
            rating = int(request.form.get('rating'))
            deck_name = request.form.get('deck_name')
            
            schedule = self.storage.get_schedule(card_hash)
            if schedule:
                # Process review
                new_schedule, log = self.scheduler.review_card(schedule, Rating(rating))
                
                # Save to database
                card = self.cards_cache.get(card_hash)
                self.storage.save_schedule(new_schedule, card.deck_name)
                self.storage.log_review(log)
            
            # Continue to next card
            return redirect(url_for('study', deck_name=deck_name))
        
        @self.app.route('/api/stats')
        def api_stats():
            """API endpoint for statistics"""
            deck_name = request.args.get('deck')
            stats = self.storage.get_stats(deck_name)
            return jsonify(stats)
        
        @self.app.route('/api/reload')
        def api_reload():
            """Reload cards from files"""
            self._load_all_cards()
            return jsonify({'status': 'ok', 'cards_loaded': len(self.cards_cache)})
        
        @self.app.route('/browse')
        @self.app.route('/browse/<deck_name>')
        def browse(deck_name: Optional[str] = None):
            """Browse all cards"""
            if deck_name:
                cards = [c for c in self.cards_cache.values() if c.deck_name == deck_name]
            else:
                cards = list(self.cards_cache.values())
            
            # Add schedule info
            cards_with_schedule = []
            for card in cards:
                schedule = self.storage.get_schedule(card.get_hash())
                cards_with_schedule.append({
                    'card': card,
                    'schedule': schedule
                })
            
            return render_template('browse.html', cards=cards_with_schedule, deck_name=deck_name)
    
    def _get_deck_list(self) -> list:
        """Get list of all decks"""
        decks = {}
        for card in self.cards_cache.values():
            if card.deck_name not in decks:
                decks[card.deck_name] = 0
            decks[card.deck_name] += 1
        
        return [{'name': name, 'count': count} for name, count in sorted(decks.items())]
    
    def run(self, host: str = 'localhost', port: int = 8000, debug: bool = False):
        """Run Flask development server"""
        print(f"hashcards running at http://{host}:{port}")
        print(f"Cards directory: {self.cards_dir}")
        print(f"Total cards loaded: {len(self.cards_cache)}")
        self.app.run(host=host, port=port, debug=debug)