#!/usr/bin/env python3
"""
Utility script to manage banned cards.

Usage:
  python scripts/manage_banned_cards.py fetch         # Fetch latest from Wizards
  python scripts/manage_banned_cards.py load          # Load from JSON into DB
  python scripts/manage_banned_cards.py list          # List all banned cards
  python scripts/manage_banned_cards.py check <name>  # Check if card is banned
"""

import sys
import argparse
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.models.banned_card import BannedCard
from app.services.banned_cards import banned_cards_service
from app.services.bootstrap import load_banned_cards


def fetch_banned_list() -> None:
    """Fetch the latest banned list from Wizards."""
    print("Fetching banned list from Wizards of the Coast...")
    from fetch_banned_cards import fetch_banned_list as fetch_fn
    from fetch_banned_cards import parse_commander_bans, save_banned_list
    
    html = fetch_fn()
    if not html:
        print("Failed to fetch banned list.")
        return
    
    data = parse_commander_bans(html)
    settings = get_settings()
    output_path = settings.raw_data_dir / "banned-cards-commander.json"
    save_banned_list(data, output_path)


def load_banned_cards_to_db() -> None:
    """Load banned cards from JSON into database."""
    print("Loading banned cards into database...")
    db = SessionLocal()
    try:
        count = banned_cards_service.load_from_json(db)
        print(f"✓ Successfully loaded {count} banned cards")
    finally:
        db.close()


def list_banned_cards(format_name: str = "Commander") -> None:
    """List all banned cards in a format."""
    db = SessionLocal()
    try:
        cards = banned_cards_service.get_banned_cards(db, format_name)
        
        if not cards:
            print(f"No banned cards found for {format_name}")
            return
        
        print(f"\n{'Name':<35} {'Ban Date':<12} Reason")
        print("-" * 100)
        
        for card in cards:
            ban_date = card.ban_date.strftime("%Y-%m-%d") if card.ban_date else "Unknown"
            reason = (card.reason or "No reason provided")[:50] + "..."
            print(f"{card.card_name:<35} {ban_date:<12} {reason}")
        
        print(f"\nTotal: {len(cards)} banned cards in {format_name}")
    finally:
        db.close()


def check_card_banned(card_name: str, format_name: str = "Commander") -> None:
    """Check if a card is banned."""
    db = SessionLocal()
    try:
        is_banned = banned_cards_service.is_card_banned(db, card_name, format_name)
        
        if is_banned:
            print(f"✓ '{card_name}' is BANNED in {format_name}")
            card = db.query(BannedCard).filter(
                BannedCard.card_name == card_name,
                BannedCard.format == format_name
            ).first()
            if card:
                print(f"  Reason: {card.reason}")
                if card.ban_date:
                    print(f"  Banned: {card.ban_date.strftime('%Y-%m-%d')}")
        else:
            print(f"✗ '{card_name}' is NOT banned in {format_name}")
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(
        description="Manage banned cards for Magic: The Gathering",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/manage_banned_cards.py fetch         # Update from official source
  python scripts/manage_banned_cards.py load          # Load from JSON into database
  python scripts/manage_banned_cards.py list          # List all banned cards
  python scripts/manage_banned_cards.py check Hullbreacher  # Check specific card
        """
    )
    
    parser.add_argument(
        "command",
        choices=["fetch", "load", "list", "check"],
        help="Command to run"
    )
    
    parser.add_argument(
        "card_name",
        nargs="?",
        help="Card name (required for 'check' command)"
    )
    
    parser.add_argument(
        "--format",
        default="Commander",
        help="Magic format (default: Commander)"
    )
    
    args = parser.parse_args()
    
    if args.command == "fetch":
        fetch_banned_list()
    elif args.command == "load":
        load_banned_cards_to_db()
    elif args.command == "list":
        list_banned_cards(args.format)
    elif args.command == "check":
        if not args.card_name:
            print("Error: card_name is required for 'check' command")
            sys.exit(1)
        check_card_banned(args.card_name, args.format)


if __name__ == "__main__":
    main()
