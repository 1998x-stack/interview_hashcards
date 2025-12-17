"""
Command-line interface for hashcards
Unix philosophy: simple, composable commands
"""

import argparse
import sys
from pathlib import Path

from .web.app import HashcardsApp
from .parser import CardParser
from .storage import CardStorage


def cmd_drill(args):
    """Start drill/study session with web interface"""
    cards_dir = Path(args.cards_dir).resolve()
    
    if not cards_dir.exists():
        print(f"Error: Directory not found: {cards_dir}", file=sys.stderr)
        sys.exit(1)
    
    # Count markdown files
    md_files = list(cards_dir.glob("*.md"))
    if not md_files:
        print(f"Warning: No .md files found in {cards_dir}", file=sys.stderr)
        print("Create some card files first!", file=sys.stderr)
    
    print(f"Loading cards from: {cards_dir}")
    print(f"Found {len(md_files)} deck file(s)")
    
    app = HashcardsApp(str(cards_dir))
    app.run(host=args.host, port=args.port, debug=args.debug)


def cmd_stats(args):
    """Show statistics about card collection"""
    cards_dir = Path(args.cards_dir).resolve()
    db_path = cards_dir / ".hashcards.db"
    
    if not db_path.exists():
        print("No database found. Run 'hashcards drill' first to initialize.", file=sys.stderr)
        sys.exit(1)
    
    storage = CardStorage(str(db_path))
    stats = storage.get_stats()
    
    print("\n📊 hashcards Statistics")
    print("=" * 40)
    print(f"Total cards:      {stats['total_cards']}")
    print(f"Due for review:   {stats['due_cards']}")
    print(f"Reviewed today:   {stats['reviews_today']}")
    
    if stats['by_state']:
        print("\nCards by state:")
        for state, count in stats['by_state'].items():
            print(f"  {state:12s}: {count}")
    
    print()
    storage.close()


def cmd_validate(args):
    """Validate card files for syntax errors"""
    cards_dir = Path(args.cards_dir).resolve()
    
    if not cards_dir.exists():
        print(f"Error: Directory not found: {cards_dir}", file=sys.stderr)
        sys.exit(1)
    
    md_files = list(cards_dir.glob("*.md"))
    total_cards = 0
    errors = []
    
    print(f"Validating {len(md_files)} file(s)...\n")
    
    for md_file in md_files:
        try:
            cards = CardParser.parse_file(str(md_file))
            total_cards += len(cards)
            print(f"✓ {md_file.name}: {len(cards)} cards")
        except Exception as e:
            errors.append((md_file.name, str(e)))
            print(f"✗ {md_file.name}: ERROR - {e}")
    
    print(f"\nTotal: {total_cards} cards across {len(md_files)} files")
    
    if errors:
        print(f"\n❌ {len(errors)} file(s) with errors")
        sys.exit(1)
    else:
        print("\n✅ All files valid!")


def cmd_export(args):
    """Export cards and schedules to different formats"""
    print("Export functionality coming soon!")
    print("For now, your cards are already in plain Markdown format.")
    print("Use standard Unix tools to process them:")
    print("  - grep: search cards")
    print("  - wc: count cards")
    print("  - cat: concatenate decks")


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        prog='hashcards',
        description='Local-first spaced repetition learning',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  hashcards drill ./Cards              # Start study session
  hashcards stats ./Cards              # Show statistics
  hashcards validate ./Cards           # Check card syntax
  
Your cards are plain Markdown files. Edit them with any text editor!
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # drill command
    drill_parser = subparsers.add_parser('drill', help='Start study session')
    drill_parser.add_argument('cards_dir', help='Directory containing .md card files')
    drill_parser.add_argument('--host', default='localhost', help='Host to bind to')
    drill_parser.add_argument('--port', type=int, default=8000, help='Port to bind to')
    drill_parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    drill_parser.set_defaults(func=cmd_drill)
    
    # stats command
    stats_parser = subparsers.add_parser('stats', help='Show statistics')
    stats_parser.add_argument('cards_dir', help='Directory containing .md card files')
    stats_parser.set_defaults(func=cmd_stats)
    
    # validate command
    validate_parser = subparsers.add_parser('validate', help='Validate card files')
    validate_parser.add_argument('cards_dir', help='Directory containing .md card files')
    validate_parser.set_defaults(func=cmd_validate)
    
    # export command
    export_parser = subparsers.add_parser('export', help='Export cards (future)')
    export_parser.add_argument('cards_dir', help='Directory containing .md card files')
    export_parser.set_defaults(func=cmd_export)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    args.func(args)


if __name__ == '__main__':
    main()