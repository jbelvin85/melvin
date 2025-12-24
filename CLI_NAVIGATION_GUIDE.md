# 🎮 Melvin CLI - Letter + Number Navigation Guide

## New Navigation System: Letters for Tabs, Numbers for Options

The improved Melvin CLI now uses an **intuitive two-key system**:
- **Letters** (a-z) jump directly to tabs
- **Numbers** (0-9) select menu items within the current tab

## Quick Reference

### Tab Navigation (Press a Letter)

| Key | Tab | Full Name |
|-----|-----|-----------|
| **`s`** | SYSTEM | System info & dependencies |
| **`e`** | SETUP | Configuration & initialization |
| **`d`** | DEPLOYMENT | Service management |
| **`b`** | DATABASE | Migrations & backups |
| **`u`** | USERS | Account management |
| **`m`** | MAINTENANCE | Utilities & cleanup |

### Menu Selection (Press a Number)

| Key | Action | Notes |
|-----|--------|-------|
| **`0`** | Back to SYSTEM tab | Available on all menus |
| **`1-7`** | Select option | Number depends on tab |
| **`q`** | Quit | Exit the CLI |

## Usage Examples

### Example 1: View & Approve Pending Account Requests

```bash
# Start CLI
./scripts/melvin.sh cli

# Navigation:
u                    # Jump to USERS tab
1                    # View Pending Account Requests
<Enter>              # When done, go back to menu
2                    # Approve Account Request
<Enter>              # Enter request ID when prompted
```

### Example 2: Launch Services (3 keypresses!)

```bash
./scripts/melvin.sh cli

d                    # Jump to DEPLOYMENT tab
1                    # Launch Full Stack (Background)
<Enter>              # Done!
```

### Example 3: Check System Health

```bash
./scripts/melvin.sh cli

s                    # Jump to SYSTEM tab (already default)
5                    # View API Health Status
<Enter>              # See health check result
0                    # Go back to menu (or any letter to jump tabs)
```

### Example 4: Database Migration

```bash
./scripts/melvin.sh cli

b                    # Jump to DATABASE tab
1                    # Run Database Migrations
<Enter>              # Wait for migration to complete
```

## Tab Overview with Shortcuts

### 🖥️ SYSTEM Tab (`s`)
Quick system status and health checks
- `1` Check dependencies
- `2` Install missing dependencies  
- `3` System resources (memory, CPU)
- `4` Docker container status
- `5` API health check
- `6` Environment config

### ⚙️ SETUP Tab (`e`)
Configuration and initialization
- `1` Initialize environment
- `2` Download data files
- `3` Configure Redis
- `4` Edit .env file
- `5` Reset configuration

### 🚀 DEPLOYMENT Tab (`d`)
Start and stop services
- `1` Launch full stack (background)
- `2` Launch full stack (foreground/debug)
- `3` Development mode
- `4` Start specific service
- `5` Stop all services
- `6` Restart services
- `7` View logs

### 💾 DATABASE Tab (`b`)
Database operations and backups
- `1` Run migrations
- `2` Create backup
- `3` View backup history
- `4` Restore from backup
- `5` Connect to Postgres CLI
- `6` Connect to MongoDB CLI

### 👥 USERS Tab (`u`) - Most Common!
User and account management
- `1` View pending account requests
- `2` Approve request
- `3` Deny request
- `4` Create user manually
- `5` List all users
- `6` Reset admin password
- `7` Manage permissions

### 🔧 MAINTENANCE Tab (`m`)
Cleanup and monitoring
- `1` Run evaluation harness
- `2` Clean Docker resources
- `3` View application logs
- `4` Performance monitoring
- `5` Rebuild images
- `6` Full factory reset

## Common Workflows

### First-Time Setup (5 steps)

```bash
./scripts/melvin.sh cli

s       # SYSTEM tab
1       # Check deps → shows what's needed

e       # Jump to SETUP
1       # Initialize environment
        # Answer prompts...

d       # Jump to DEPLOYMENT
1       # Launch full stack
        # Done! Services starting...
```

### Daily: Check Status & View Logs

```bash
./scripts/melvin.sh cli

s       # SYSTEM tab
5       # API health → see if healthy

d       # DEPLOYMENT tab
7       # View logs → watch for errors
```

### User Management Workflow

```bash
./scripts/melvin.sh cli

u       # Users tab
1       # See pending requests
        # Make note of request ID

2       # Approve request
        # Enter the ID, press Enter
        # User gets account!
```

### Database Backup & Restore

```bash
./scripts/melvin.sh cli

b       # DATABASE tab
2       # Create backup (saves to /backups/)
        # Get timestamp like "2025-12-23_145230"

3       # View backup history
        # Verify your backup exists

4       # Restore from backup
        # Type the backup name when prompted
```

## Pro Tips

### ⚡ Fastest Tab Navigation
- **From anywhere:** Press a letter (`s`, `e`, `d`, `b`, `u`, `m`) to jump instantly
- No need to count tabs or press arrow keys
- Direct access to any tab from anywhere

### 🎯 Menu Item Selection  
- Press the number for the menu item you want
- Numbers always follow the same order (1-7)
- Press `0` to return to SYSTEM tab from any menu

### 📋 Combining Commands
You can chain actions quickly:
```bash
./scripts/melvin.sh cli

u        # USERS tab
1        # View requests
         # <read the list>
         # <see request ID 42>
2        # Approve request
         # <type 42>
         # <request approved!>
0        # Back to SYSTEM
q        # Quit
```

## Common Mistakes & Fixes

| Problem | Solution |
|---------|----------|
| "Invalid choice" when pressing `u` | Make sure you pressed the key and hit Enter |
| Number not working | Check you're in the right tab first (letter jumps to tab) |
| Can't get back to start | Press `s` to jump to SYSTEM tab (the home tab) |
| Want to quit | Press `q` from anywhere |

## Keyboard Summary

```
┌─────────────────────────────────────┐
│      MELVIN CLI KEYBOARD MAP        │
├─────────────────────────────────────┤
│ TAB NAVIGATION (Jump Instantly)     │
│  s=System   e=Setup   d=Deployment  │
│  b=Database u=Users   m=Maintenance │
│                                     │
│ MENU SELECTION                      │
│  1-7=Choose option  0=System tab    │
│  q=Quit            Enter=Confirm    │
│                                     │
│ PHILOSOPHY: Letters→Tabs            │
│             Numbers→Options         │
└─────────────────────────────────────┘
```

## Why This Design?

✅ **Intuitive** - Letters jump to tabs, numbers pick items
✅ **Fast** - Direct tab access (no cycling)  
✅ **Reliable** - Works in all terminals (SSH, Docker, local)
✅ **Simple** - Only 2 types of input (letters & numbers)
✅ **Familiar** - Like DOS/Norton Commander
✅ **Terminal-friendly** - No special key codes needed

## Launch CLI

```bash
# From project root:
./scripts/melvin.sh cli

# Or directly:
./scripts/melvin_cli.sh

# That's it! Start pressing letters to navigate.
```

---

**Quick Start:** `./scripts/melvin.sh cli` → press `u` → press `1` → see pending account requests! 🚀
