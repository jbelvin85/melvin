#!/usr/bin/env python3
"""
Fetch the official Magic: The Gathering banned and restricted list.

This script fetches the current banned/restricted list from Wizards of the Coast
and saves it to a JSON file for use by the Melvin application.

The list includes information about banned cards for various formats including Commander.
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Optional
from urllib.request import urlopen
from urllib.error import URLError


def fetch_banned_list() -> Optional[dict]:
    """Fetch the banned and restricted list from Wizards of the Coast."""
    url = "https://magic.wizards.com/en/banned-restricted-list"
    
    try:
        print(f"Fetching banned list from {url}...")
        with urlopen(url, timeout=10) as response:
            html_content = response.read().decode('utf-8')
        return html_content
    except URLError as e:
        print(f"Error fetching banned list: {e}")
        return None


def parse_commander_bans(html_content: str) -> dict:
    """
    Parse the HTML content to extract Commander format banned cards.
    
    Returns a dictionary with the structure:
    {
        "format": "Commander",
        "last_updated": "2025-12-21",
        "banned_cards": [
            {
                "name": "Card Name",
                "reason": "reason for ban",
                "ban_date": "date"
            },
            ...
        ]
    }
    """
    # This is a basic implementation that extracts Commander section
    # In a production system, you might want to use a proper HTML parser like BeautifulSoup
    
    result = {
        "format": "Commander",
        "last_updated": datetime.now().isoformat()[:10],
        "source": "https://magic.wizards.com/en/banned-restricted-list",
        "banned_cards": []
    }
    
    # Look for the Commander section in the HTML
    commander_pattern = r'(?:Commander|Brawl).*?(?=<h3|<h2|$)'
    matches = re.findall(commander_pattern, html_content, re.IGNORECASE | re.DOTALL)
    
    if matches:
        # Extract card names and reasons from the matches
        # This is a simplified approach - a full implementation would need
        # better HTML parsing to reliably extract all information
        card_pattern = r'<strong>([^<]+)</strong>.*?(?:<p>([^<]+)</p>)?'
        for match in matches:
            card_matches = re.findall(card_pattern, match)
            for card_name, reason in card_matches:
                if card_name.strip():
                    result["banned_cards"].append({
                        "name": card_name.strip(),
                        "reason": reason.strip() if reason else "No reason provided",
                        "ban_date": None
                    })
    
    return result


def save_banned_list(data: dict, output_path: Path) -> None:
    """Save the banned list to a JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"Saved banned list to {output_path}")
    print(f"Total banned Commander cards: {len(data.get('banned_cards', []))}")


def main():
    """Main entry point."""
    # Determine output path
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    output_path = project_root / "data" / "raw" / "banned-cards-commander.json"
    
    # Fetch the HTML
    html_content = fetch_banned_list()
    if not html_content:
        print("Failed to fetch banned list. Exiting.")
        return
    
    # Parse the content
    banned_data = parse_commander_bans(html_content)
    
    # Save to file
    save_banned_list(banned_data, output_path)
    
    print("Done!")


if __name__ == "__main__":
    main()
