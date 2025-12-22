# Psychographic Profile System - Implementation Summary

## What Was Built

A complete **player psychographic profiling system** for Melvin that classifies users into Magic: The Gathering player archetypes and tailors Melvin's responses to match their playstyle.

## Core Features

### 1. ✅ Player Classification Engine
- Classifies users into **5 primary archetypes**:
  - Timmy/Tammy (emotional, exciting plays)
  - Johnny/Jenny (creative, unique decks)
  - Spike/Sheila (competitive, optimized)
  - Vorthos (lore, story-focused)
  - Melvin (mechanics, design-focused)

- Supports **11 refined subtypes** for granular profiling

### 2. ✅ Assessment Questionnaire
- **6-question onboarding flow** covering:
  - Deck building motivation
  - Card evaluation criteria
  - In-game satisfaction sources
  - Learning style preferences
  - Losing response patterns
  - Content engagement preferences

### 3. ✅ RESTful API Endpoints
- `GET /api/profiles/questionnaire` - Public questionnaire access
- `POST /api/profiles/assess` - Submit responses and get classification
- `GET /api/profiles/me` - Retrieve user's full profile
- `GET /api/profiles/me/summary` - Get human-readable results

### 4. ✅ Database Schema
- `player_profiles` - User profile scores and preferences
- `psychographic_questions` - Question bank
- `question_options` - Answer options with archetype weights
- `assessment_responses` - User response history
- Extended `users` table with profile relationship

### 5. ✅ Melvin Integration
- Melvin service updated to accept optional user context
- Automatic profile-aware prompt generation
- Conversation guidance injected into LLM prompts
- Responses tailored to player motivations

### 6. ✅ Documentation
- Comprehensive [psychographic-profiles.md](../docs/psychographic-profiles.md)
- Architecture overview
- API usage examples
- Integration guidelines
- Customization instructions

## File Structure

```
backend/app/
├── models/
│   ├── psychographic_profile.py        # ✨ NEW: Profile models
│   └── user.py                         # UPDATED: Added profile relationship
├── schemas/
│   └── psychographic.py                # ✨ NEW: Response schemas
├── services/
│   ├── assessment.py                   # ✨ NEW: Classification logic
│   ├── assessment_bootstrap.py         # ✨ NEW: Questionnaire data
│   └── melvin.py                       # UPDATED: Profile-aware responses
├── api/
│   ├── profiles.py                     # ✨ NEW: Profile endpoints
│   └── routes.py                       # UPDATED: Registered profiles router
├── alembic/                            # ✨ NEW: Database migrations
│   ├── env.py
│   ├── script.py.mako
│   ├── versions/
│   │   └── 001_add_psychographic_profiles.py
│   └── __init__.py
└── main.py                             # UPDATED: Bootstrap questionnaire

docs/
└── psychographic-profiles.md           # ✨ NEW: Complete guide
```

## Key Implementation Details

### Score Calculation
Each question option has weighted contributions to:
- **5 Primary Archetypes**: Timmy/Tammy, Johnny/Jenny, Spike/Sheila, Vorthos, Melvin
- **11 Subtypes**: Power Gamer, Social Gamer, Adrenaline Gamer, Combo Builder, etc.

Scores are normalized across all responses (0.0-1.0 scale).

### Profile Results Include
- Primary type + score
- Secondary type + score (if >0.2 points)
- Refined subtype + score
- 5 preference scores (big_plays, originality, optimization, lore, mechanics)
- Human-readable descriptions
- Conversation guidance for Melvin

### Assessment Service
```python
# Process answers
profile = assessment_service.process_assessment(db, user, answers)

# Get summary
summary = assessment_service.generate_result_summary(profile)

# Build LLM guidance
guidance = melvin_service._build_player_guidance(user)
```

## How It Works

### 1. User Onboarding
```
User → Fetches Questionnaire → Answers 6 Questions → Submits Assessment
                                                            ↓
                                    Scores Calculated & Profile Stored
                                                            ↓
                                    User Receives Personalized Results
```

### 2. Conversation Adaptation
```
User Asks Question → Melvin Service
                            ↓
                    Check User Profile
                            ↓
            Build Profile-Aware Guidance
                            ↓
            Include in LLM Prompt
                            ↓
        Generate Profile-Tailored Response
```

### 3. Example Profile Outcomes
- **Timmy/Tammy**: "Focus on exciting possibilities and memorable moments"
- **Johnny/Jenny**: "Explore creative directions and synergies"
- **Spike/Sheila**: "Analyze competitive advantage and optimal plays"
- **Vorthos**: "Connect to story and world-building context"
- **Melvin**: "Explain mechanical elegance and design principles"

## Database Migration

The system uses Alembic for schema management:

```bash
# Apply migration
alembic upgrade head

# Creates 4 new tables with proper relationships
# Adds profile_id to users table
# Bootstraps 6 default assessment questions
```

## API Response Example

```json
{
  "primary_type": "johnny_jenny",
  "primary_type_label": "Johnny/Jenny",
  "primary_score": 0.673,
  "secondary_type": "timmy_tammy",
  "secondary_score": 0.412,
  "subtype": "combo_builder",
  "subtype_label": "Combo Builder",
  "description": "You're driven by creativity and self-expression...",
  "play_style_summary": "You're drawn to deckbuilding as an art form...",
  "conversation_guidance": "Explore possibilities, brainstorm creative directions...",
  "preference_breakdown": {
    "big_plays": 0.25,
    "originality": 0.67,
    "optimization": 0.15,
    "lore": 0.20,
    "mechanics": 0.45
  }
}
```

## Configuration & Customization

### Adding New Questions
Edit `assessment_bootstrap.py` and add to `ASSESSMENT_QUESTIONS` with archetype weights.

### Updating Guidance
Modify `ARCHETYPE_INFO` in `assessment.py` to change conversation instructions.

### Changing Weights
Adjust question option weights to shift emphasis on different subtypes.

## Testing Checklist

- [ ] Run database migration: `alembic upgrade head`
- [ ] Start backend
- [ ] Test `GET /api/profiles/questionnaire`
- [ ] Test `POST /api/profiles/assess` with valid answers
- [ ] Verify `GET /api/profiles/me` returns profile
- [ ] Confirm Melvin includes guidance in responses
- [ ] Check database has bootstrap questions (6 questions × 4-5 options)

## Future Enhancements

1. **Adaptive Testing**: Adjust questions based on responses
2. **Profile Refinement**: Allow users to retake assessment
3. **Play Pattern Analysis**: Infer profile from actual game data
4. **Strategy Suggestions**: Generate deck recommendations by archetype
5. **Analytics Dashboard**: See community psychographic distributions
6. **Multi-language**: Translate questionnaire and guidance

## Architecture Benefits

✅ **Scalable**: New archetypes/subtypes can be added easily
✅ **Customizable**: Question weights and guidance are data-driven
✅ **Non-intrusive**: Optional profile parameter in Melvin service
✅ **Type-safe**: Full Pydantic schema validation
✅ **Well-documented**: Comprehensive API and implementation docs
✅ **Testable**: Service-based architecture enables unit testing
✅ **Maintainable**: Clean separation of concerns

## Integration Points

- **User Model**: Extended with profile relationship
- **Melvin Service**: Accepts optional user parameter
- **API Routes**: New `/profiles` endpoint group
- **Database**: 4 new tables with proper migrations
- **Main App**: Bootstraps questions on startup

---

**Status**: ✅ Complete and Ready for Testing
**Date**: December 22, 2024
**Components**: 6 new files, 3 modified files, 1 migration
