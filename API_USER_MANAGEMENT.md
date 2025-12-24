# User Account Management API Endpoints

## Overview
The Melvin API provides a complete user account workflow: users can request accounts, admins can review/approve/deny requests, and users can login.

## Endpoints Reference

### 1. **Submit Account Request** (Public)
**Endpoint**: `POST /api/auth/request`

Users submit a request for a new account.

**Request Body**:
```json
{
  "username": "john_doe",
  "password": "SecurePass123!"
}
```

**Response** (201 Created):
```json
{
  "id": 1,
  "username": "john_doe",
  "status": "pending"
}
```

**Use Case**: New user registration form

**Example**:
```bash
curl -X POST http://localhost:8001/api/auth/request \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "password": "SecurePass123!"
  }'
```

---

### 2. **Login** (Public)
**Endpoint**: `POST /api/auth/login`

Users login with username/password to get access token.

**Request Body**:
```json
{
  "username": "john_doe",
  "password": "SecurePass123!"
}
```

**Response** (200 OK):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Use Case**: User authentication

**Example**:
```bash
curl -X POST http://localhost:8001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "password": "SecurePass123!"
  }'
```

---

### 3. **List Pending Requests** (Admin Only)
**Endpoint**: `GET /api/auth/requests`

Admins view all pending account requests.

**Request Headers**:
```
Authorization: Bearer <admin_token>
```

**Response** (200 OK):
```json
[
  {
    "id": 1,
    "username": "john_doe",
    "status": "pending"
  },
  {
    "id": 2,
    "username": "jane_smith",
    "status": "pending"
  }
]
```

**Use Case**: Admin dashboard showing pending approvals

**Example**:
```bash
curl -X GET http://localhost:8001/api/auth/requests \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

---

### 4. **Approve Account Request** (Admin Only)
**Endpoint**: `POST /api/auth/requests/{request_id}/approve`

Admins approve a pending account request, creating the user account.

**URL Parameters**:
- `request_id`: ID of the request to approve

**Request Body** (Optional):
```json
{
  "approved_username": "john_doe_final"
}
```
If not provided, uses the original requested username.

**Response** (200 OK):
```json
{
  "id": 1,
  "username": "john_doe",
  "status": "approved"
}
```

**Use Case**: Admin approves user signup

**Example**:
```bash
# Approve with original username
curl -X POST http://localhost:8001/api/auth/requests/1/approve \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# Approve with modified username
curl -X POST http://localhost:8001/api/auth/requests/1/approve \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "approved_username": "john_doe_modified"
  }'
```

---

### 5. **Deny Account Request** (Admin Only)
**Endpoint**: `POST /api/auth/requests/{request_id}/deny`

Admins reject a pending account request.

**URL Parameters**:
- `request_id`: ID of the request to deny

**Response** (200 OK):
```json
{
  "id": 1,
  "username": "john_doe",
  "status": "denied"
}
```

**Use Case**: Admin rejects inappropriate signup

**Example**:
```bash
curl -X POST http://localhost:8001/api/auth/requests/1/deny \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

---

### 6. **Bootstrap Admin Account** (Internal)
**Endpoint**: `POST /api/auth/bootstrap`

Automatically called during startup to create the initial admin account. Can also be used to upgrade an existing user to admin.

**Request Body**:
```json
{
  "username": "admin",
  "password": "AdminPass123!"
}
```

**Response** (204 No Content)

**Note**: This is called automatically by the startup script with credentials from `.env`.

---

## Complete Workflow Example

### Step 1: User Requests Account
```bash
curl -X POST http://localhost:8001/api/auth/request \
  -H "Content-Type: application/json" \
  -d '{
    "username": "alice",
    "password": "AlicePass123!"
  }'
# Response: { "id": 5, "username": "alice", "status": "pending" }
```

### Step 2: Admin Views Pending Requests
```bash
curl -X GET http://localhost:8001/api/auth/requests \
  -H "Authorization: Bearer $ADMIN_TOKEN"
# Response: [{ "id": 5, "username": "alice", "status": "pending" }]
```

### Step 3: Admin Approves Request
```bash
curl -X POST http://localhost:8001/api/auth/requests/5/approve \
  -H "Authorization: Bearer $ADMIN_TOKEN"
# Response: { "id": 5, "username": "alice", "status": "approved" }
```

### Step 4: User Logs In
```bash
curl -X POST http://localhost:8001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "alice",
    "password": "AlicePass123!"
  }'
# Response: { "access_token": "eyJ...", "token_type": "bearer" }
```

### Step 5: User Uses Access Token
```bash
curl -X GET http://localhost:8001/api/some-endpoint \
  -H "Authorization: Bearer eyJ..."
# Now user can access protected endpoints
```

---

## Account Request Status Flow

```
┌─────────────┐
│  PENDING    │  ← User submits request
└──────┬──────┘
       │
       ├─→ APPROVED  ← Admin approves (user created)
       │
       └─→ DENIED    ← Admin denies
```

## Frontend Integration

### Request Account Form
```javascript
async function requestAccount(username, password) {
  const response = await fetch('/api/auth/request', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password })
  });
  return response.json();
}
```

### Get Pending Requests (Admin Dashboard)
```javascript
async function getPendingRequests(adminToken) {
  const response = await fetch('/api/auth/requests', {
    headers: { 'Authorization': `Bearer ${adminToken}` }
  });
  return response.json();
}
```

### Approve Request
```javascript
async function approveRequest(requestId, adminToken) {
  const response = await fetch(`/api/auth/requests/${requestId}/approve`, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${adminToken}` }
  });
  return response.json();
}
```

### Login
```javascript
async function login(username, password) {
  const response = await fetch('/api/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password })
  });
  const data = await response.json();
  localStorage.setItem('token', data.access_token);
  return data;
}
```

---

## Database Models

### AccountRequest Model
```python
class AccountRequest(Base):
    __tablename__ = "account_requests"
    
    id: int          # Primary key
    username: str    # Requested username
    password_hash: str  # Hashed password
    status: str      # "pending", "approved", or "denied"
    created_at: datetime
```

### User Model
```python
class User(Base):
    __tablename__ = "users"
    
    id: int          # Primary key
    username: str    # Unique username
    password_hash: str  # Hashed password
    is_admin: bool   # Admin privileges
    created_at: datetime
```

---

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Username already requested"
}
```

### 401 Unauthorized
```json
{
  "detail": "Invalid credentials"
}
```

### 403 Forbidden
```json
{
  "detail": "Admin privileges required"
}
```

### 404 Not Found
```json
{
  "detail": "Request not found"
}
```

---

## Security Notes

1. **Passwords** are hashed using bcrypt (never stored plain text)
2. **JWT Tokens** expire after 4 hours by default
3. **Admin endpoints** require valid admin token
4. **Username validation** prevents duplicate requests
5. **Rate limiting** should be added in production

---

## Quick Reference

| Operation | Endpoint | Method | Auth | Status |
|-----------|----------|--------|------|--------|
| Request account | `/auth/request` | POST | None | Public |
| Login | `/auth/login` | POST | None | Public |
| List requests | `/auth/requests` | GET | Admin | Protected |
| Approve request | `/auth/requests/{id}/approve` | POST | Admin | Protected |
| Deny request | `/auth/requests/{id}/deny` | POST | Admin | Protected |
| Bootstrap admin | `/auth/bootstrap` | POST | None | Internal |

