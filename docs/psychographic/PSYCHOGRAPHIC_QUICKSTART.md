# Psychographic Profiles - Quick Start Guide

## 🚀 Get Started in 5 Minutes

### 1. Apply Database Migration
```bash
cd backend/app
alembic upgrade head
```

### 2. Start the Backend
```bash
cd backend
python -m uvicorn app.main:app --reload
```

### 3. Get the Assessment Questionnaire
```bash
curl http://localhost:8000/api/profiles/questionnaire
```

### 4. Create a Test User and Get Token
```bash
# Register user
curl -X POST http://localhost:8000/api/auth/request \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "password123"}'

# (Admin approves the request in DB or via endpoint)

# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "password123"}'
  
# Save the access_token
```

### 5. Submit Assessment Answers
```bash
curl -X POST http://localhost:8000/api/profiles/assess \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "answers": [
      {"question_id": 1, "selected_option_id": 2},
      {"question_id": 2, "selected_option_id": 3},
      {"question_id": 3, "selected_option_id": 1},
      {"question_id": 4, "selected_option_id": 4},
      {"question_id": 5, "selected_option_id": 2},
      {"question_id": 6, "selected_option_id": 3}
    ]
  }'
```

### 6. Get Your Profile
```bash
curl http://localhost:8000/api/profiles/me/summary \
  -H "Authorization: Bearer YOUR_TOKEN"
```

You should see your player archetype classification! 🎉

---

## 📚 Key Concepts

### Player Types
- **Timmy/Tammy** (0.5): Emotional, exciting plays
- **Johnny/Jenny** (0.3): Creative, unique decks  
- **Spike/Sheila** (0.15): Competitive, optimized
- **Vorthos** (0.04): Lore and story
- **Melvin** (0.01): Mechanics and design

### Assessment Structure
```
6 Questions
└── Each with 4-5 Answer Options
    └── Each option has weighted scores for:
        ├── 5 Primary Archetypes
        └── 11 Subtypes
```

### What You Get Back
- Primary archetype (most matches)
- Secondary archetype (if significant)
- Refined subtype (specific player style)
- Preference breakdown (0.0-1.0 for each)
- Conversation guidance (for Melvin)

---

## 🧪 Testing Scenarios

### Johnny/Jenny Test (Creative Builder)
```json
{
  "answers": [
    {"question_id": 1, "selected_option_id": 2},
    {"question_id": 2, "selected_option_id": 2},
    {"question_id": 3, "selected_option_id": 2},
    {"question_id": 4, "selected_option_id": 2},
    {"question_id": 5, "selected_option_id": 2},
    {"question_id": 6, "selected_option_id": 2}
  ]
}
```

### Spike/Sheila Test (Competitive)
```json
{
  "answers": [
    {"question_id": 1, "selected_option_id": 3},
    {"question_id": 2, "selected_option_id": 3},
    {"question_id": 3, "selected_option_id": 3},
    {"question_id": 4, "selected_option_id": 3},
    {"question_id": 5, "selected_option_id": 3},
    {"question_id": 6, "selected_option_id": 3}
  ]
}
```

---

## 📖 Full Documentation

See [docs/psychographic-profiles.md](../docs/psychographic-profiles.md) for:
- Architecture overview
- Complete API reference
- Integration patterns
- Customization guide
- Frontend examples

See [PSYCHOGRAPHIC_IMPLEMENTATION.md](../PSYCHOGRAPHIC_IMPLEMENTATION.md) for:
- Implementation details
- File structure
- Database schema
- Testing checklist

---

## 💡 Using Profiles in Melvin Conversations

The system is already integrated! When users ask questions in conversations:

```python
# The conversation endpoint can pass user context
response = melvin_service.answer_question(
    question,
    user=current_user  # Melvin automatically uses their profile
)
```

Melvin will automatically:
1. Check if user has a profile
2. Extract their archetype guidance
3. Include it in the LLM prompt
4. Tailor the response to their playstyle

---

## 🔧 Common Tasks

### See All Questions in Database
```bash
sqlite3 melvin.db "SELECT id, category, question_text FROM psychographic_questions ORDER BY order;"
```

### Check User's Profile
```bash
sqlite3 melvin.db "SELECT id, user_id, primary_type, primary_score FROM player_profiles WHERE user_id=1;"
```

### Reset All Assessments
```bash
sqlite3 melvin.db "DELETE FROM assessment_responses; DELETE FROM player_profiles;"
```

### View Question with Options
```bash
sqlite3 melvin.db "
  SELECT 
    q.question_text,
    o.option_text,
    o.timmy_weight,
    o.johnny_weight,
    o.spike_weight
  FROM psychographic_questions q
  JOIN question_options o ON q.id = o.question_id
  WHERE q.id = 1
  ORDER BY o.order;
"
```

---

## 🐛 Troubleshooting

### Migration Failed
- Check Alembic is properly configured
- Run `alembic current` to see current version
- Check `alembic_version` table in DB

### Questionnaire Returns Empty
- Backend hasn't started yet (startup event runs bootstrap)
- Restart backend to trigger `bootstrap_assessment_questions()`

### Profile Not Found
- User hasn't completed assessment yet (normal)
- Check user is authenticated with correct token

### Wrong Profile Detected
- Answer weights may need tuning
- Review `assessment_bootstrap.py` question weights
- Consider adding more discriminating questions

---

## 📊 Profile Scoring Example

For a Johnny/Jenny-type player answering a questionnaire:

```
Question 1 (Deck Building):
  Selected: "Creating unique synergies" → johnny_weight: 0.5, timmy_weight: 0.1, ...
  
Question 2 (Card Evaluation):
  Selected: "Interesting design space" → johnny_weight: 0.5, timmy_weight: 0.2, ...

...after 6 questions...

Final Scores (normalized by 6):
  Johnny: (0.5+0.5+0.3+0.4+0.2+0.5)/6 = 0.40
  Timmy:  (0.1+0.2+0.3+0.2+0.4+0.2)/6 = 0.23
  Spike:  (0.1+0.2+0.2+0.1+0.3+0.1)/6 = 0.17
  
Result: Johnny/Jenny (Primary), Timmy (Secondary)
```

---

## 🎯 Next Steps

1. ✅ Run migration
2. ✅ Test API endpoints
3. ✅ Verify profiles are being created
4. ✅ Check Melvin includes guidance in responses
5. → Integrate into frontend onboarding UI
6. → Build analytics dashboard
7. → Add adaptive questioning

---

**Need Help?**
- API Docs: [docs/psychographic-profiles.md](../docs/psychographic-profiles.md)
- Implementation: [PSYCHOGRAPHIC_IMPLEMENTATION.md](../PSYCHOGRAPHIC_IMPLEMENTATION.md)
- Code: Check `backend/app/services/assessment.py`

**Last Updated**: December 22, 2024
