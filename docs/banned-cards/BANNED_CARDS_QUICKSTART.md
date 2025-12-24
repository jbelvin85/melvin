# Banned Commander Cards - Quick Reference

## What's Implemented

A complete system to fetch and manage banned Magic: The Gathering Commander cards from the official Wizards of the Coast banned and restricted list.

## Quick Commands

### Fetch Latest Banned List
```bash
python scripts/fetch_banned_cards.py
```
Downloads the latest banned cards from https://magic.wizards.com/en/banned-restricted-list and saves to `data/raw/banned-cards-commander.json`

### Manage Banned Cards
```bash
# List all banned Commander cards
python scripts/manage_banned_cards.py list

# Check if a specific card is banned
python scripts/manage_banned_cards.py check "Card Name"

# Load from JSON into database
python scripts/manage_banned_cards.py load

# Fetch from official source
python scripts/manage_banned_cards.py fetch
```

## API Endpoints

Once the app is running on `http://localhost:8001`:

```bash
# Get all banned cards for Commander
curl http://localhost:8001/api/banned-cards?format=Commander

# Search for a card
curl "http://localhost:8001/api/banned-cards/search/by-name?name=Hullbreacher"

# Check specific card by ID
curl http://localhost:8001/api/banned-cards/1
```

## Files Created

| File | Purpose |
|------|---------|
| `scripts/fetch_banned_cards.py` | Fetch banned list from Wizards |
| `scripts/manage_banned_cards.py` | Utility to manage banned cards |
| `backend/app/models/banned_card.py` | Database model |
| `backend/app/schemas/banned_card.py` | API schemas |
| `backend/app/api/banned_cards.py` | API endpoints |
| `backend/app/services/banned_cards.py` | Business logic |
| `data/raw/banned-cards-commander.json` | Banned cards data |
| `docs/banned-cards.md` | Full documentation |

## Key Features

✅ Fetch from official Wizards source
✅ RESTful API with search and filtering
✅ Database persistence
✅ Auto-load on application startup
✅ Utility scripts for management
✅ Complete documentation

## Integration

The banned cards system is fully integrated:
- Auto-loads on app startup via `bootstrap.py`
- Available through REST API at `/api/banned-cards`
- Uses existing SQLAlchemy ORM and database
- Ready to use in production

## Next Steps

1. **Fetch the latest list**: `python scripts/fetch_banned_cards.py`
2. **Start the application**: `./scripts/melvin.sh launch`
3. **Query the API**: Use the endpoints to get banned cards
4. **Schedule updates**: Set up a cron job to run `fetch_banned_cards.py` regularly

## Documentation

For complete documentation including all API endpoints, database schema, and advanced usage, see [docs/banned-cards.md](docs/banned-cards.md).
