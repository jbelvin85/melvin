# Banned Cards Management

This system maintains an up-to-date list of banned Magic: The Gathering cards for various formats, with a focus on Commander format.

## Overview

The banned cards system consists of:

1. **Data Source**: Official list from [Wizards of the Coast](https://magic.wizards.com/en/banned-restricted-list)
2. **Fetch Script**: Python script to pull the latest banned list
3. **Database Model**: SQLAlchemy model (`BannedCard`) to store banned cards
4. **API Endpoints**: RESTful API to query and manage banned cards
5. **Service Layer**: Business logic for banned cards operations

## Quick Start

### Fetching the Latest Banned List

Run the fetch script to download the latest banned cards from the official source:

```bash
python scripts/fetch_banned_cards.py
```

This will:
- Fetch the HTML content from the Wizards of the Coast banned list page
- Parse the Commander format banned cards
- Save the data to `data/raw/banned-cards-commander.json`
- Display the total number of banned Commander cards

### Loading into Database

The banned cards are automatically loaded into the database on application startup via the `bootstrap.py` initialization script. If you manually add cards to the JSON file, restart the application to load them.

To manually trigger loading:

```python
from app.core.database import SessionLocal
from app.services.banned_cards import banned_cards_service

db = SessionLocal()
count = banned_cards_service.load_from_json(db)
print(f"Loaded {count} banned cards")
db.close()
```

## API Endpoints

All endpoints are prefixed with `/api/banned-cards`.

### Get All Banned Cards by Format

```
GET /api/banned-cards?format=Commander
```

**Response:**
```json
{
  "format": "Commander",
  "cards": [
    {
      "id": 1,
      "format": "Commander",
      "card_name": "Hullbreacher",
      "reason": "This card turns a common Magic occurrence — a player drawing extra cards — into a deterministic and frequent way to win the game out of nowhere. It warps deckbuilding choices and the kinds of gameplay that can happen in the format.",
      "ban_date": "2021-06-28",
      "created_at": "2025-12-21T10:30:00",
      "updated_at": "2025-12-21T10:30:00"
    },
    ...
  ],
  "count": 42
}
```

### Get Specific Banned Card

```
GET /api/banned-cards/{card_id}
```

**Response:**
```json
{
  "id": 1,
  "format": "Commander",
  "card_name": "Hullbreacher",
  "reason": "...",
  "ban_date": "2021-06-28",
  "created_at": "2025-12-21T10:30:00",
  "updated_at": "2025-12-21T10:30:00"
}
```

### Search Banned Cards by Name

```
GET /api/banned-cards/search/by-name?name=Hulk&format=Commander
```

**Response:**
```json
[
  {
    "id": 15,
    "format": "Commander",
    "card_name": "Protean Hulk",
    "reason": "...",
    "ban_date": "2020-03-16",
    "created_at": "2025-12-21T10:30:00",
    "updated_at": "2025-12-21T10:30:00"
  }
]
```

### Create Banned Card Entry

```
POST /api/banned-cards
```

**Request Body:**
```json
{
  "format": "Commander",
  "card_name": "New Banned Card",
  "reason": "Reason for ban",
  "ban_date": "2025-12-21"
}
```

### Update Banned Card Entry

```
PUT /api/banned-cards/{card_id}
```

**Request Body:**
```json
{
  "reason": "Updated reason"
}
```

### Delete Banned Card Entry

```
DELETE /api/banned-cards/{card_id}
```

## Service Usage

### Check if Card is Banned

```python
from app.core.database import SessionLocal
from app.services.banned_cards import banned_cards_service

db = SessionLocal()
is_banned = banned_cards_service.is_card_banned(db, "Hullbreacher", format_name="Commander")
print(f"Hullbreacher is banned in Commander: {is_banned}")
db.close()
```

### Get All Banned Cards for a Format

```python
banned_cards = banned_cards_service.get_banned_cards(db, format_name="Commander")
for card in banned_cards:
    print(f"{card.card_name}: {card.reason}")
```

## Data File Structure

The `data/raw/banned-cards-commander.json` file has the following structure:

```json
{
  "format": "Commander",
  "last_updated": "2025-12-21",
  "source": "https://magic.wizards.com/en/banned-restricted-list",
  "banned_cards": [
    {
      "name": "Hullbreacher",
      "reason": "This card turns a common Magic occurrence — a player drawing extra cards — into a deterministic and frequent way to win the game out of nowhere.",
      "ban_date": "2021-06-28"
    },
    ...
  ]
}
```

## Database Schema

The `BannedCard` model includes:

- **id**: Primary key
- **format**: Format name (e.g., "Commander", "Standard")
- **card_name**: Name of the banned card
- **reason**: Reason for the ban
- **ban_date**: Date the card was banned
- **created_at**: When the record was created
- **updated_at**: When the record was last updated

## Updating the Banned List

To keep the banned list current:

1. **Manually**: Run `python scripts/fetch_banned_cards.py` periodically
2. **Automated**: Set up a cron job or scheduled task to run the script daily
3. **On Startup**: The application automatically loads any new cards from the JSON file when it starts

Example cron job (runs daily at 6 AM):
```bash
0 6 * * * cd /path/to/melvin && python scripts/fetch_banned_cards.py
```

## Troubleshooting

### No Banned Cards Loaded
- Verify the JSON file exists at `data/raw/banned-cards-commander.json`
- Check that the JSON file is valid (use `python -m json.tool data/raw/banned-cards-commander.json`)
- Review application logs for any loading errors

### Fetch Script Fails
- Ensure you have internet connectivity
- Check that the Wizards website is accessible
- The script may need updates if the HTML structure of the banned list page changes

### Duplicate Cards
- The system checks for duplicates before inserting, so re-running the fetch is safe
- Existing cards won't be overwritten by the JSON loader

## Future Improvements

- [ ] Support for other formats (Standard, Modern, Pioneer, etc.)
- [ ] Detailed HTML parsing with Beautiful Soup for more accurate data extraction
- [ ] Web interface to view and manage banned cards
- [ ] Discord/Slack integration to notify about ban updates
- [ ] Historical tracking of ban/unban changes
- [ ] Integration with Scryfall API for additional card metadata
