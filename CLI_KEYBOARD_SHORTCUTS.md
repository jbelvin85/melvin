# 🎮 Melvin CLI - Keyboard Shortcuts

## ⚡ NEW Navigation System: Letters Jump to Tabs!

Press **letters** to jump to tabs instantly, then **numbers** to select menu items:

### Tab Navigation (Letters)

| Key | Tab | Action |
|-----|-----|--------|
| **`s`** | **SYSTEM** | Jump to System info & dependencies |
| **`e`** | **SETUP** | Jump to Configuration & initialization |
| **`d`** | **DEPLOYMENT** | Jump to Service management |
| **`b`** | **DATABASE** | Jump to Migrations & backups |
| **`u`** | **USERS** | Jump to Account management |
| **`m`** | **MAINTENANCE** | Jump to Utilities & cleanup |

### Menu Selection (Numbers)

| Key | Action | When |
|-----|--------|------|
| **`1-7`** | **Select menu item** | Within any tab |
| **`0`** | **Return to SYSTEM tab** | From any menu |
| **`q`** | **Quit CLI** | Anytime |
| **`Enter`** | **Confirm action** | After commands complete |

## Why Letters + Numbers?

✅ **Instant Tab Access** - Press one letter to jump to any tab (no cycling!)
✅ **Works Everywhere** - SSH, Docker, remote servers, all terminals  
✅ **Intuitive** - Letters for tabs, numbers for options
✅ **Fast** - Minimal keypresses for common tasks
✅ **Terminal-Friendly** - No special key codes, just plain ASCII

## Common Workflows

### View Pending Account Requests
```bash
./scripts/melvin.sh cli
u           # Jump to USERS tab
1           # Select "View Pending Requests"
<Enter>     # See the list!
```

### Approve an Account
```bash
u           # USERS tab
2           # "Approve Account Request"
<Enter>     # Type request ID when prompted
```

### Launch Full Stack
```bash
d           # DEPLOYMENT tab
1           # "Launch Full Stack"
<Enter>     # Services start!
```

### Check API Health
```bash
s           # SYSTEM tab
5           # "View API Health Status"
<Enter>     # See if API is healthy
```

## Tab-by-Tab Guide

### 🖥️ System (`s`)
- `1` Check dependencies
- `2` Install missing deps
- `3` System resources
- `4` Container status
- `5` API health check
- `6` Environment config

### ⚙️ Setup (`e`)
- `1` Initialize environment
- `2` Download data files
- `3` Configure Redis
- `4` Edit .env
- `5` Reset config

### 🚀 Deployment (`d`)
- `1` Launch (background)
- `2` Launch (debug mode)
- `3` Development mode
- `4` Start service
- `5` Stop services
- `6` Restart services
- `7` View logs

### 💾 Database (`b`)
- `1` Run migrations
- `2` Create backup
- `3` Backup history
- `4` Restore backup
- `5` Postgres CLI
- `6` MongoDB CLI

### 👥 Users (`u`) ⭐ Most Used
- `1` **View pending requests** ⭐
- `2` **Approve request** ⭐
- `3` Deny request
- `4` Create user
- `5` List users
- `6` Reset password
- `7` Manage permissions

### 🔧 Maintenance (`m`)
- `1` Run evaluation
- `2` Clean Docker
- `3` View logs
- `4` Performance
- `5` Rebuild images
- `6` Factory reset

## Comparison: Old vs New

| Feature | Old (`h`/`l`) | New (`s`/`e`/`d`/`b`/`u`/`m`) |
|---------|---------------|------|
| Jump to tab 5 | `l l l l` (4 presses) | `u` (1 press!) |
| Return to start | `h h h h` | `s` (1 press!) |
| Intuitive | Medium | High ✅ |
| Speed | Moderate | Fast ✅ |
| Learning curve | Short | Easier ✅ |

## Super Quick Start

```bash
cd /home/user/Github/melvin
./scripts/melvin.sh cli

# Examples:
u           # View/approve account requests
d           # Launch or manage services  
s           # Check system health
b           # Database operations
e           # Configuration
m           # Maintenance & cleanup

q           # Quit anytime
```

## Keyboard Map

```
┌────────────────────────────────────┐
│   MELVIN CLI KEYBOARD LAYOUT       │
├────────────────────────────────────┤
│ TAB JUMP (Letters)                 │
│  S E D B U M - Press one letter    │
│                                    │
│ MENU SELECT (Numbers)              │
│  1 2 3 4 5 6 7 - Within any tab    │
│                                    │
│ SPECIAL                            │
│  0=System  Q=Quit  Enter=Confirm   │
└────────────────────────────────────┘
```

---

**Start now:** `./scripts/melvin.sh cli` → `u` → `1` ✅

