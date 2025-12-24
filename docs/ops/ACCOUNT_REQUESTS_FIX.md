# Account Requests Display Issue - Root Cause & Fix

## The Problem

When attempting to create a new user via the web interface, the form was showing:
> "Username already requested"

However, when checking the CLI (`manage_accounts.sh`), it showed:
> "No pending account requests."

This created a confusing experience where the user knew a request existed but couldn't see it to approve it.

## Root Cause Analysis

### 1. **Web Interface Correctly Detecting the Request**
The web form checks if a username exists in the `account_requests` table:
```python
# backend/app/api/auth.py - Line 26
existing_request = db.query(AccountRequest).filter(
    AccountRequest.username == payload.username
).first()
```

This query returns ANY request (pending, approved, or denied) - it doesn't filter by status. So when `rootweaver` was requested the first time, it was properly stored.

### 2. **CLI Missing Authentication**
The CLI function `view_pending_requests_cli()` in `manage_accounts.sh` was calling the API endpoint without providing authentication:

```bash
# WRONG - Missing Authorization header
response=$(curl -fsS -X GET "$API_URL/api/auth/requests" 2>/dev/null || echo "")
```

But the API endpoint requires admin authentication:
```python
# backend/app/api/auth.py - Line 66-73
@router.get("/requests", response_model=list[AccountRequestOut])
def list_requests(
    _: User = Depends(get_current_admin),  # ← Requires admin authentication
    db: Session = Depends(get_db),
) -> list[AccountRequestOut]:
    return db.query(AccountRequest).filter(
        AccountRequest.status == AccountRequestStatus.PENDING
    ).all()
```

Without authentication, the API returns a 401 error, which the CLI interpreted as "no requests."

## The Fix

### Changes Made to `scripts/manage_accounts.sh`

#### 1. Updated `view_pending_requests_cli()` Function
- Now prompts for admin login if not already authenticated
- Passes the `Authorization: Bearer $TOKEN` header to the API

#### 2. Updated `approve_request_cli()` Function
- Now prompts for admin login if needed
- Passes authentication token to approval endpoint

#### 3. Updated `deny_request_cli()` Function
- Now prompts for admin login if needed  
- Passes authentication token to deny endpoint

#### 4. Updated `login_admin_interactive()` Function
- Added detection for piped input (non-interactive mode)
- Skips the `pause_screen()` prompt when stdin is not a terminal
- Allows authentication to complete in scripted contexts

### How to Use the Fixed CLI

**Before (Failed):**
```bash
./scripts/manage_accounts.sh list
# "No pending account requests."
```

**After (Works):**
```bash
./scripts/manage_accounts.sh list
# Prompts: "Authentication required to view pending requests."
# Prompts: "Username: admin"
# Prompts: "Password: [hidden]"
# Shows: "[1] rootweaver - pending"
```

## Verification

### Database Check
```bash
docker-compose exec -T postgres psql -U melvin -d melvin \
  -c "SELECT id, username, status FROM account_requests WHERE status = 'pending';"
```

Result:
```
 id |  username  | status  
----+------------+---------
  1 | rootweaver | pending
(1 row)
```

### CLI Verification
```bash
cat <<'EOF' | bash scripts/manage_accounts.sh list
admin
ChangeMe!123
EOF
```

Result:
```
Authentication required to view pending requests.

┌─────────────────────────────────────────────────────────────────────────┐
│  ADMIN LOGIN
└─────────────────────────────────────────────────────────────────────────┘

ℹ Authenticating...
✓ Login successful! Welcome, admin.
[1] rootweaver - pending
```

## Admin Credentials

The default admin credentials are set in `backend/app/core/config.py`:
- **Username:** `admin`
- **Password:** `ChangeMe!123`

⚠️ **Security Note:** Change these credentials immediately in production!

## Summary

| Issue | Root Cause | Fix |
|-------|-----------|-----|
| CLI shows no pending requests | Missing auth header in API call | Added authentication prompts |
| Web interface shows request exists | API correctly blocks unauthenticated access | CLI now authenticates before calling API |
| Confusing user experience | CLI and web UI working differently | Unified behavior - both now require auth |

The fix ensures that pending account requests are properly visible and manageable from the CLI interface, just as they are from the web interface.
