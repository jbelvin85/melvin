# User Account Management - Quick Reference

## The 3 Account Request Endpoints

### 1️⃣ Users Request an Account
```bash
POST /api/auth/request
```
**Body**: `{ "username": "alice", "password": "pass123" }`
**Response**: `{ "id": 1, "username": "alice", "status": "pending" }`

---

### 2️⃣ Admin Views Pending Requests
```bash
GET /api/auth/requests
Header: Authorization: Bearer <admin_token>
```
**Response**: List of pending account requests

---

### 3️⃣ Admin Approves/Denies Requests
```bash
# APPROVE
POST /api/auth/requests/{id}/approve
Header: Authorization: Bearer <admin_token>

# DENY
POST /api/auth/requests/{id}/deny
Header: Authorization: Bearer <admin_token>
```

---

## How It Works

```
User submits: POST /api/auth/request
                     ↓
Admin reviews:  GET /api/auth/requests  
                     ↓
Admin decides:  POST /api/auth/requests/{id}/approve
                     ↓
User can now:   POST /api/auth/login
                     ↓
User gets:      access_token (for auth on protected endpoints)
```

---

## Example: Complete Flow

```bash
# 1. User requests account
curl -X POST http://localhost:8001/api/auth/request \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"pass123"}'
# → Returns: {"id": 1, "status": "pending"}

# 2. Admin gets pending requests
ADMIN_TOKEN="..."
curl -X GET http://localhost:8001/api/auth/requests \
  -H "Authorization: Bearer $ADMIN_TOKEN"
# → Returns: [{"id": 1, "username": "alice", "status": "pending"}]

# 3. Admin approves
curl -X POST http://localhost:8001/api/auth/requests/1/approve \
  -H "Authorization: Bearer $ADMIN_TOKEN"
# → Returns: {"id": 1, "status": "approved"}

# 4. User can now login
curl -X POST http://localhost:8001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"pass123"}'
# → Returns: {"access_token": "eyJ...", "token_type": "bearer"}
```

---

## Where These Are In Code

**API Routes**: `backend/app/api/auth.py`
- Line 20: `submit_account_request()` → POST /auth/request
- Line 66: `list_requests()` → GET /auth/requests
- Line 74: `approve_request()` → POST /auth/requests/{id}/approve
- Line 98: `deny_request()` → POST /auth/requests/{id}/deny

**Database Models**: 
- `backend/app/models/account_request.py` - AccountRequest model
- `backend/app/models/user.py` - User model

**Schemas**: 
- `backend/app/schemas/auth.py` - Request/response formats

---

## Frontend Components (in `frontend/src/components/`)

Look for:
- `PsychographicAssessment.tsx` - User signup form
- Other components that call auth endpoints

---

## Key Points

✅ **Anyone** can request an account (POST /auth/request)
✅ **Only admins** can approve/deny (GET /auth/requests, POST /auth/requests/{id}/approve/deny)
✅ Passwords are **hashed with bcrypt** (never stored plain)
✅ Auth tokens are **JWT tokens** (valid for 4 hours)
✅ **Initial admin** created automatically during startup (from .env)

