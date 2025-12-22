# Player Psychographic Profiles - Integration Guide

## Overview

Melvin now supports player psychographic profiling based on Mark Rosewater's player archetype framework from Magic: The Gathering. This system allows Melvin to:

1. **Classify players** into psychographic archetypes (Timmy/Tammy, Johnny/Jenny, Spike/Sheila, Vorthos, Melvin)
2. **Tailor conversations** to match each player's playstyle and preferences
3. **Provide personalized strategy guidance** based on player motivations

## Architecture

### Database Models

The system uses four main database tables:

- **player_profiles**: Stores user psychographic assessments and preference scores
- **psychographic_questions**: The 6-question assessment questionnaire
- **question_options**: Answer options with archetype weight mappings
- **assessment_responses**: Stores individual user responses for history

### Core Components

#### 1. Models (`backend/app/models/psychographic_profile.py`)
- `PlayerProfile`: Main profile storage
- `PsychographicType`: Enum for primary archetypes (Timmy/Tammy, Johnny/Jenny, Spike/Sheila, Vorthos, Melvin)
- `PsychographicSubtype`: Refined classification (Power Gamer, Combo Builder, Competitive, etc.)
- `PsychographicQuestion`: Assessment questions
- `QuestionOption`: Answer choices with weighted archetype scores

#### 2. Schemas (`backend/app/schemas/psychographic.py`)
- `PsychographicQuestionOut`: Question response schema
- `AssessmentQuestionnaireResponse`: Full questionnaire retrieval
- `AnswerSubmission`: Single question answer
- `AssessmentSubmission`: Complete assessment submission
- `PlayerProfileOut`: User profile details
- `AssessmentResultSummary`: Human-readable results

#### 3. Services

**`backend/app/services/assessment.py`** - Core assessment logic
- `process_assessment()`: Calculates archetype scores from responses
- `get_all_questions()`: Retrieves questionnaire
- `generate_result_summary()`: Creates readable profile summary
- Archetype guidance and descriptions

**`backend/app/services/assessment_bootstrap.py`** - Questionnaire data
- Pre-built 6-question assessment
- Question 1: Deck building motivation
- Question 2: Card evaluation criteria
- Question 3: In-game satisfaction sources
- Question 4: Learning style preferences
- Question 5: Losing response
- Question 6: Content engagement preferences

#### 4. API Endpoints (`backend/app/api/profiles.py`)
- `GET /api/profiles/questionnaire` - Get assessment questions (public)
- `POST /api/profiles/assess` - Submit answers and get classification (authenticated)
- `GET /api/profiles/me` - Retrieve user's full profile (authenticated)
- `GET /api/profiles/me/summary` - Get human-readable summary (authenticated)

#### 5. LLM Integration (`backend/app/services/melvin.py`)
- Extended to accept optional `user` parameter
- `_build_player_guidance()`: Generates context-aware instructions based on profile
- Automatically includes archetype guidance in LLM prompts

## API Usage

### 1. Getting the Questionnaire

```bash
curl http://localhost:8000/api/profiles/questionnaire
```

Response includes 6 questions with multiple-choice options:
```json
{
  "questions": [
    {
      "id": 1,
      "question_text": "When building a Magic deck, what excites you most?",
      "category": "deck_building",
      "order": 1,
      "options": [
        {
          "id": 1,
          "option_text": "Playing cards with huge numbers or dramatic effects...",
          "order": 1
        },
        ...
      ]
    },
    ...
  ],
  "total_questions": 6
}
```

### 2. Submitting Assessment

```bash
curl -X POST http://localhost:8000/api/profiles/assess \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "answers": [
      {
        "question_id": 1,
        "selected_option_id": 1
      },
      {
        "question_id": 2,
        "selected_option_id": 3
      },
      ...
    ]
  }'
```

Response example (Johnny/Jenny player):
```json
{
  "primary_type": "johnny_jenny",
  "primary_type_label": "Johnny/Jenny",
  "primary_score": 0.67,
  "secondary_type": "timmy_tammy",
  "secondary_type_label": "Timmy/Tammy",
  "secondary_score": 0.42,
  "subtype": "combo_builder",
  "subtype_label": "Combo Builder",
  "description": "You're driven by creativity and self-expression. Building unique decks and discovering clever interactions is what excites you.",
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

### 3. Retrieving User Profile

```bash
curl http://localhost:8000/api/profiles/me \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 4. Getting Profile Summary

```bash
curl http://localhost:8000/api/profiles/me/summary \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Player Archetypes

### Timmy/Tammy
- **Motivation**: Emotional experience and excitement
- **Enjoys**: Big plays, spectacle, memorable moments, social fun
- **Subtypes**: Power Gamer, Social Gamer, Adrenaline Gamer
- **Melvin Guidance**: Emphasize exciting outcomes, avoid over-optimization

### Johnny/Jenny
- **Motivation**: Creativity and self-expression
- **Enjoys**: Deckbuilding, clever interactions, winning with unique ideas
- **Subtypes**: Combo Builder, Offbeat Builder, Architect
- **Melvin Guidance**: Explore possibilities, celebrate unconventional approaches

### Spike/Sheila
- **Motivation**: Competition and optimization
- **Enjoys**: Winning, studying meta, executing perfectly
- **Subtypes**: Competitive, Technical, Meta Analyst
- **Melvin Guidance**: Focus on competitive advantage, technical depth

### Vorthos
- **Motivation**: Story and world-building
- **Enjoys**: Lore, flavor, thematic coherence
- **Subtypes**: Lore Enthusiast
- **Melvin Guidance**: Connect mechanics to story and flavor

### Melvin
- **Motivation**: Mechanical systems and design
- **Enjoys**: Rules interactions, elegant design, understanding systems
- **Subtypes**: Mechanics Enthusiast
- **Melvin Guidance**: Dive into mechanics and design principles

## Integration with Melvin Conversations

The Melvin service automatically uses player profiles:

```python
# In conversation handler
from sqlalchemy.orm import Session
from app.dependencies import get_current_user
from app.services.melvin import melvin_service

@router.post("/conversations/{conversation_id}/messages")
def send_message(
    conversation_id: int,
    message: MessageCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Melvin automatically adjusts based on user's profile
    response = melvin_service.answer_question(
        message.content,
        user=user  # Optional: pass user for profile-aware responses
    )
    return response
```

The service will automatically:
1. Check if user has a psychographic profile
2. Extract archetype guidance
3. Include guidance in the LLM prompt
4. Tailor responses to player's motivations

## Database Migration

To apply migrations:

```bash
cd backend
alembic upgrade head
```

The migration creates:
- `player_profiles` table with profile data
- `psychographic_questions` and `question_options` for questionnaire
- `assessment_responses` for tracking user responses
- Proper relationships and indexes

## Customization

### Adding New Questions

Edit `backend/app/services/assessment_bootstrap.py` and add to `ASSESSMENT_QUESTIONS`:

```python
{
    "question_text": "Your question here?",
    "category": "your_category",
    "order": 7,  # increment
    "options": [
        {
            "option_text": "Option text",
            "order": 1,
            "timmy_weight": 0.5,  # Weights sum to ~1.0 across all archetypes
            "johnny_weight": 0.2,
            ...
        }
    ]
}
```

Weights represent how much each answer contributes to each archetype.

### Updating Guidance

Edit archetype guidance in `backend/app/services/assessment.py`:

```python
ARCHETYPE_INFO = {
    PsychographicType.TIMMY_TAMMY: {
        "label": "Timmy/Tammy",
        "description": "...",
        "play_style": "...",
        "conversation_guidance": "Update this guidance text...",
    },
    ...
}
```

## Frontend Integration

### Example onboarding flow:

```typescript
// 1. Fetch questionnaire
const response = await fetch('/api/profiles/questionnaire');
const { questions } = await response.json();

// 2. Display questions to user
// ... render UI with questions

// 3. Submit answers
const assessment = await fetch('/api/profiles/assess', {
  method: 'POST',
  headers: { 'Authorization': `Bearer ${token}` },
  body: JSON.stringify({
    answers: [
      { question_id: 1, selected_option_id: selectedIds[0] },
      ...
    ]
  })
});

const profile = await assessment.json();

// 4. Display personalized results
console.log(`You're a ${profile.primary_type_label}!`);
console.log(profile.conversation_guidance);
```

## Testing

### Quick API test:

```bash
# Get questionnaire
curl http://localhost:8000/api/profiles/questionnaire | jq

# Create test user and get token (adjust to your auth method)
# Then submit assessment and retrieve profile
```

### Unit testing:

```python
from app.services.assessment import assessment_service

def test_assessment():
    # Create test user and responses
    answers = [
        {"question_id": 1, "option_id": 1},
        {"question_id": 2, "option_id": 3},
        ...
    ]
    
    profile = assessment_service.process_assessment(db, user, answers)
    assert profile.primary_type == PsychographicType.JOHNNY_JENNY
```

## Future Enhancements

1. **Adaptive Assessment**: Adjust question selection based on responses
2. **Profile Refinement**: Allow users to adjust their profile over time
3. **Conversation History Analysis**: Refine profile based on actual play patterns
4. **Strategy Generation**: Auto-generate deck suggestions based on archetype
5. **Community Analytics**: Aggregate stats on player type distributions
6. **A/B Testing**: Test different Melvin responses by player type

## References

- Mark Rosewater's Player Types: https://magic.wizards.com/en/news/making-magic/the-three-magic-psychographics
- MtG Psychographics Deep Dive
- Design Documents in `/docs/`

---

**Last Updated**: December 22, 2024
**Status**: Production Ready
