# Psychographic Profile System - Testing Checklist

## Pre-Deployment Testing

### ✅ Backend Setup
- [ ] Database migration runs without errors: `alembic upgrade head`
- [ ] Alembic version table exists and shows `001_add_psychographic_profiles`
- [ ] Backend starts without import errors
- [ ] Bootstrap loads 6 questions on startup (check logs)
- [ ] All 4 new tables exist in database:
  - [ ] `psychographic_questions` (6 rows)
  - [ ] `question_options` (25+ rows)
  - [ ] `player_profiles` (initially empty)
  - [ ] `assessment_responses` (initially empty)

### ✅ API - Questionnaire Endpoint

Test: `GET /api/profiles/questionnaire`

```bash
curl http://localhost:8000/api/profiles/questionnaire
```

Verify:
- [ ] Status code: 200
- [ ] Contains `questions` array
- [ ] Count: 6 questions
- [ ] Each question has:
  - [ ] `id` (1-6)
  - [ ] `question_text` (non-empty)
  - [ ] `category` (deck_building, card_evaluation, etc.)
  - [ ] `order` (1-6)
  - [ ] `options` array with 4-5 options
- [ ] Each option has:
  - [ ] `id` (unique)
  - [ ] `option_text` (non-empty)
  - [ ] `order` (sequential)
- [ ] `total_questions`: 6

### ✅ API - Assessment Submission

Test: `POST /api/profiles/assess`

```bash
# 1. Login and get token
TOKEN=$(curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"pass"}' | jq -r '.access_token')

# 2. Submit assessment (pick one answer per question)
curl -X POST http://localhost:8000/api/profiles/assess \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "answers": [
      {"question_id": 1, "selected_option_id": 1},
      {"question_id": 2, "selected_option_id": 2},
      {"question_id": 3, "selected_option_id": 3},
      {"question_id": 4, "selected_option_id": 1},
      {"question_id": 5, "selected_option_id": 2},
      {"question_id": 6, "selected_option_id": 4}
    ]
  }'
```

Verify response:
- [ ] Status code: 200
- [ ] Contains `primary_type` (one of: timmy_tammy, johnny_jenny, spike_sheila, vorthos, melvin)
- [ ] Contains `primary_score` (0.0-1.0)
- [ ] Contains `description` (non-empty string)
- [ ] Contains `play_style_summary` (non-empty string)
- [ ] Contains `conversation_guidance` (non-empty string)
- [ ] Contains `preference_breakdown` with all 5 keys:
  - [ ] `big_plays` (float 0.0-1.0)
  - [ ] `originality` (float 0.0-1.0)
  - [ ] `optimization` (float 0.0-1.0)
  - [ ] `lore` (float 0.0-1.0)
  - [ ] `mechanics` (float 0.0-1.0)
- [ ] `primary_score` + preference scores make sense together

### ✅ API - Profile Retrieval

Test: `GET /api/profiles/me`

```bash
curl http://localhost:8000/api/profiles/me \
  -H "Authorization: Bearer $TOKEN"
```

Verify:
- [ ] Status code: 200
- [ ] Contains `id`, `user_id`, `primary_type`, `primary_score`
- [ ] Contains `created_at` and `updated_at` timestamps
- [ ] All preference scores present
- [ ] Matches the profile we just created

### ✅ API - Profile Summary

Test: `GET /api/profiles/me/summary`

```bash
curl http://localhost:8000/api/profiles/me/summary \
  -H "Authorization: Bearer $TOKEN"
```

Verify:
- [ ] Status code: 200
- [ ] Contains human-readable `primary_type_label` (e.g., "Johnny/Jenny")
- [ ] Contains readable descriptions and guidance
- [ ] Same data as assess endpoint

### ✅ Authentication Tests

- [ ] `GET /api/profiles/questionnaire` works without auth ✓
- [ ] `POST /api/profiles/assess` requires auth:
  - [ ] Fails with 401 if no token
  - [ ] Fails with 401 if invalid token
  - [ ] Succeeds with valid token
- [ ] `GET /api/profiles/me` requires auth:
  - [ ] Fails with 401 if no token
  - [ ] Succeeds with valid token
- [ ] `GET /api/profiles/me/summary` requires auth:
  - [ ] Fails with 401 if no token
  - [ ] Succeeds with valid token

### ✅ Validation Tests

Test error handling:

```bash
# Missing answers
curl -X POST http://localhost:8000/api/profiles/assess \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"answers": []}'
# Should: 400 Bad Request

# Invalid question IDs
curl -X POST http://localhost:8000/api/profiles/assess \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"answers": [{"question_id": 999, "selected_option_id": 1}]}'
# Should: Process (ignores invalid, but ideally validates)

# Incomplete assessment
curl -X POST http://localhost:8000/api/profiles/assess \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"answers": [{"question_id": 1, "selected_option_id": 1}]}'
# Should: Process (creates profile with 1 answer)

# Valid assessment
# Should: 200 with complete profile
```

Verify:
- [ ] Server handles missing answers gracefully
- [ ] Invalid question IDs either ignored or validated
- [ ] Partial assessments are allowed (but all answers preferred)
- [ ] Validation messages are clear

### ✅ Scoring Algorithm Tests

Test different answer patterns:

**Test 1: Johnny/Jenny-type (Combo Builder)**
```json
{"answers": [
  {"question_id": 1, "selected_option_id": 2},  // "Creating unique synergies"
  {"question_id": 2, "selected_option_id": 2},  // "Interesting design space"
  {"question_id": 3, "selected_option_id": 2},  // "Pull off complex combo"
  {"question_id": 4, "selected_option_id": 2},  // "Experiment with interactions"
  {"question_id": 5, "selected_option_id": 2},  // "Not getting to show deck"
  {"question_id": 6, "selected_option_id": 2}   // "Brewing creative decks"
]}
```

Expected: `primary_type: johnny_jenny`, high `originality` score

**Test 2: Spike/Sheila-type (Meta Analyst)**
```json
{"answers": [
  {"question_id": 1, "selected_option_id": 3},  // "Finding optimal cards"
  {"question_id": 2, "selected_option_id": 3},  // "Performance in meta"
  {"question_id": 3, "selected_option_id": 3},  // "Play perfectly"
  {"question_id": 4, "selected_option_id": 3},  // "Study rules systematically"
  {"question_id": 5, "selected_option_id": 3},  // "Making a mistake"
  {"question_id": 6, "selected_option_id": 3}   // "Analyzing meta"
]}
```

Expected: `primary_type: spike_sheila`, high `optimization` score

**Test 3: Mixed Type**
```json
{"answers": [
  {"question_id": 1, "selected_option_id": 1},  // Timmy
  {"question_id": 2, "selected_option_id": 2},  // Johnny
  {"question_id": 3, "selected_option_id": 3},  // Spike
  {"question_id": 4, "selected_option_id": 4},  // Vorthos
  {"question_id": 5, "selected_option_id": 1},  // Timmy
  {"question_id": 6, "selected_option_id": 5}   // Melvin
]}
```

Expected: Balanced scores, no dominant archetype

Verify for each:
- [ ] `primary_type` matches expected
- [ ] Preference scores align with answers
- [ ] Secondary type makes sense
- [ ] Subtype is correctly identified

### ✅ Database Tests

Check after multiple assessments:

```bash
# Check questions loaded
sqlite3 melvin.db "SELECT COUNT(*) FROM psychographic_questions;"
# Should: 6

# Check options
sqlite3 melvin.db "SELECT COUNT(*) FROM question_options;"
# Should: 25 or more

# Check user profile created
sqlite3 melvin.db "SELECT * FROM player_profiles WHERE user_id=1;"
# Should: One row per user who took assessment

# Check responses stored
sqlite3 melvin.db "SELECT COUNT(*) FROM assessment_responses WHERE profile_id=1;"
# Should: 6 (if all questions answered)

# Check timestamps
sqlite3 melvin.db "SELECT created_at, updated_at FROM player_profiles WHERE user_id=1;"
# Should: Both set to current time (approximately)
```

Verify:
- [ ] All tables populated correctly
- [ ] Foreign keys are valid
- [ ] Timestamps are reasonable
- [ ] No orphaned records

### ✅ Integration Tests

**Test 1: Melvin uses profile in responses**

```python
from app.services.melvin import melvin_service
from app.models.user import User
from sqlalchemy.orm import Session

# Get user with profile
user = db.query(User).filter(User.id == 1).first()

# Ask Melvin a question
response = melvin_service.answer_question(
    "How should I build my deck?",
    user=user
)

# Check response (subjective, but should be influenced by profile)
print(response)
```

Verify:
- [ ] No errors thrown
- [ ] Response is generated
- [ ] If Johnny/Jenny: Emphasizes creativity
- [ ] If Spike/Sheila: Emphasizes optimization
- [ ] If Timmy/Tammy: Emphasizes excitement

**Test 2: Backward compatibility**

```python
# Call without user parameter (should still work)
response = melvin_service.answer_question(
    "What's the damage type of a Lightning Bolt?"
)
```

Verify:
- [ ] No errors
- [ ] Response generated correctly
- [ ] Works with or without user parameter

### ✅ Frontend Component Tests

If using React component:

```typescript
// Check component imports without errors
import PsychographicAssessment from './components/PsychographicAssessment';

// Verify in browser:
// - Questions load
// - Can select answers
// - Progress bar updates
// - Submit button state changes
// - Results display correctly
// - All preference bars show
```

Verify:
- [ ] Component renders without errors
- [ ] Questions display correctly
- [ ] Can select each answer option
- [ ] Progress indicator updates
- [ ] Submit button only active when all answered
- [ ] Results screen shows all data
- [ ] Preference breakdown charts display
- [ ] Styling looks good on mobile/desktop

### ✅ Error Handling Tests

- [ ] Server error (500):
  - [ ] Database disconnected
  - [ ] Invalid migration state
- [ ] Client error (400):
  - [ ] Missing required fields
  - [ ] Invalid data types
- [ ] Authentication error (401):
  - [ ] Missing/invalid token
  - [ ] Expired session
- [ ] Not found (404):
  - [ ] Questionnaire (before bootstrap) - shouldn't happen
  - [ ] Profile for user who didn't assess

Verify:
- [ ] Errors are descriptive
- [ ] Status codes are correct
- [ ] No sensitive info leaked in errors

### ✅ Performance Tests

- [ ] Questionnaire loads < 1s
- [ ] Assessment submission < 2s
- [ ] Profile retrieval < 500ms
- [ ] Can handle 100+ assessments without slowdown
- [ ] Database queries use indexes efficiently

### ✅ Migration Tests

- [ ] Fresh database: `alembic upgrade head` works
- [ ] Already migrated: Running again is safe (idempotent)
- [ ] Downgrade: `alembic downgrade base` works
- [ ] Upgrade after downgrade: Works correctly

### ✅ Documentation Tests

- [ ] PSYCHOGRAPHIC_QUICKSTART.md instructions work
- [ ] PSYCHOGRAPHIC_IMPLEMENTATION.md is accurate
- [ ] docs/psychographic-profiles.md covers all features
- [ ] Code examples actually execute
- [ ] Links and references are valid

---

## Regression Tests (Make Sure Nothing Broke)

- [ ] Regular auth still works
- [ ] Conversations still work
- [ ] Game state still works
- [ ] Banned cards still work
- [ ] No database conflicts
- [ ] No import errors
- [ ] Health check endpoint works
- [ ] CORS works as expected

---

## Sign-Off

- [ ] All tests passed
- [ ] Documentation is complete
- [ ] Code is clean and follows style guide
- [ ] No console errors or warnings
- [ ] Team has reviewed implementation
- [ ] Ready for production deployment

**Tested By**: ________________  
**Date**: ________________  
**Notes**: ________________________________________________

---

## Post-Deployment Monitoring

After deploying to production:

- [ ] Monitor error logs for any issues
- [ ] Check database for correct data storage
- [ ] Verify users can complete assessments
- [ ] Monitor API response times
- [ ] Collect sample profiles for validation
- [ ] Get user feedback on accuracy
- [ ] Refine guidance based on feedback

---

**Last Updated**: December 22, 2024
