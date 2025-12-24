# 🎮 New Comprehensive CLI Interface for Melvin

## Overview

I've created a **new tabbed, retro DOS-style CLI interface** for Melvin that's much more organized and user-friendly than the previous menu system. It organizes all commands into 6 logical tabs for easy navigation.

## Launch the New CLI

```bash
./scripts/melvin.sh cli
```

Or directly:
```bash
./scripts/melvin_cli.sh
```

## What's New

### ✨ Tabbed Interface (6 Main Tabs)

Instead of a single menu, commands are organized into logical groups:

1. **SYSTEM** - Check dependencies and system status
2. **SETUP** - Configure environment and initialization
3. **DEPLOYMENT** - Start/stop services and view logs
4. **DATABASE** - Migrations, backups, and direct access
5. **USERS** - Account requests, approvals, and management
6. **MAINTENANCE** - Utilities, monitoring, and cleanup

### 🎨 Retro DOS Styling

```
╔════════════════════════════════════════════════════════════════════════════╗
║                         MELVIN - Magic Card AI Assistant                   ║
╚════════════════════════════════════════════════════════════════════════════╝

┌─────────────────────────────────────────────────────────────────────────────┐
│ [ SYSTEM ] │ [ SETUP ] │ [ DEPLOYMENT ] │ [ DATABASE ] │ [ USERS ] │ [ MAINTENANCE ] │
└─────────────────────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════════
SYSTEM INFORMATION & DEPENDENCIES
═══════════════════════════════════════════════════════════════════════════

  1  • Check System Dependencies (Docker, Node, Python, curl)           
  2  • Install Missing Dependencies                                     
  3  • View System Status & Resources                                   
  4  • View Docker Container Status                                     
  5  • View API Health Status                                           
  6  • View Environment Configuration                                   

  0  • Back to Main Menu
```

### 🧭 Easy Navigation: Letters Jump to Tabs!

**No more arrow keys or cycling!** Press a **letter** to jump directly to any tab:

| Key | Jump to Tab | Purpose |
|-----|-------------|---------|
| **`s`** | SYSTEM | Check health & dependencies |
| **`e`** | SETUP | Configure environment |
| **`d`** | DEPLOYMENT | Launch/manage services |
| **`b`** | DATABASE | Backups & migrations |
| **`u`** | **USERS** ⭐ | Approve account requests (most used!) |
| **`m`** | MAINTENANCE | Cleanup & monitoring |

Then press **numbers** `1-7` to select menu items within that tab.

**Example:** Want to approve account requests?
```
./scripts/melvin.sh cli
u              # Jump to USERS tab (1 keypress!)
1              # View pending requests
2              # Approve one
```

### 📋 Organized Commands

**Before**: Long flat menu with 11 commands
**After**: 6 tabs with 6-7 organized commands each

Everything is now grouped by function, making it much easier to find what you need.

## Tab Contents

### 📋 SYSTEM Tab (Check your setup)
```
1. Check System Dependencies (Docker, Node, Python, curl)
2. Install Missing Dependencies
3. View System Status & Resources
4. View Docker Container Status
5. View API Health Status
6. View Environment Configuration
```

### ⚙️ SETUP Tab (Configure Melvin)
```
1. Initialize Environment (.env Configuration)
2. Verify/Download Required Data Files
3. Configure Redis Cache Service
4. Edit Environment Variables
5. Reset Configuration to Defaults
```

### 🚀 DEPLOYMENT Tab (Run services)
```
1. Launch Full Stack (Background)
2. Launch Full Stack (Foreground - Debug Mode)
3. Development Mode (Rebuild Frontend)
4. Start Specific Service
5. Stop All Services
6. Restart Services
7. View Service Logs
```

### 💾 DATABASE Tab (Manage databases)
```
1. Run Database Migrations
2. Backup Postgres & MongoDB
3. View Backup History
4. Restore from Backup
5. Connect to Postgres CLI
6. Connect to MongoDB CLI
```

### 👥 USERS Tab (User management)
```
1. View Pending Account Requests
2. Approve Account Request
3. Deny Account Request
4. Create User Account Manually
5. List All Users
6. Reset Admin Password
7. Manage User Permissions
```

### 🔧 MAINTENANCE Tab (Optimize & clean)
```
1. Run Evaluation Harness
2. Clean Up Docker Resources
3. View Application Logs
4. Performance Monitoring
5. Rebuild Docker Images
6. Reset Everything to Factory Defaults
```

## Common Workflows

### First-Time Setup (Easiest Path)
```
1. ./scripts/melvin.sh cli
2. SYSTEM tab → Check System Dependencies
3. SYSTEM tab → Install Missing Dependencies (if needed)
4. → next → SETUP tab → Initialize Environment
5. → → → DEPLOYMENT tab → Launch Full Stack
```

### User Management
```
1. ./scripts/melvin.sh cli
2. → → → → → USERS tab (5x right arrow)
3. View Pending Account Requests
4. Approve Account Request (user gets account)
```

### Troubleshooting
```
1. SYSTEM tab → View API Health Status
2. If unhealthy → DEPLOYMENT tab → View Service Logs
3. Check logs for errors
```

## Comparison: Old vs New

| Feature | Old `ui` | New `cli` |
|---------|----------|----------|
| Navigation | Single menu | 6 tabs |
| Organization | Flat list | Logical grouping |
| Styling | Basic | Retro DOS-style |
| Commands | 11 options | 36 options across 6 tabs |
| Ease of Use | Medium | Easy |
| Visual Appeal | Simple | Modern retro |
| Tab switching | Not available | Arrow keys |

## Integration

The new CLI is fully integrated into `melvin.sh`:

```bash
# Old way - still works
./scripts/melvin.sh ui

# New way - recommended
./scripts/melvin.sh cli

# Direct call
./scripts/melvin_cli.sh
```

## Files Created

- **`scripts/melvin_cli.sh`** - The new comprehensive CLI (580 lines)
- **`CLI_GUIDE.md`** - Complete documentation with workflows
- Integration added to `scripts/melvin.sh`

## Features Highlight

✅ **6 Organized Tabs** - Group related commands together
✅ **DOS-Style UI** - Retro look with modern functionality
✅ **Color-Coded** - Blue borders, yellow menus, green success, red errors
✅ **Easy Navigation** - Arrow keys, number selection, clear instructions
✅ **Full Feature Set** - All melvin.sh commands accessible via UI
✅ **User Management** - Dedicated USERS tab for account approvals
✅ **Database Tools** - Direct PostgreSQL and MongoDB access
✅ **Service Control** - Full Docker Compose integration
✅ **Monitoring** - Health checks, logs, resource monitoring
✅ **Configuration** - Full environment setup and editing

## Future Enhancements

Coming soon (marked as "Coming Soon" in current version):
- Manual user creation wizard
- User permissions management UI
- Admin password reset tool
- Backup restore functionality
- Advanced monitoring dashboard

## Recommendation

**For most users, we recommend the new CLI:**

```bash
./scripts/melvin.sh cli
```

It's:
- ✅ More organized
- ✅ Easier to navigate
- ✅ Better looking
- ✅ Covers all operations
- ✅ Perfect for system administrators
- ✅ Great for learning the system

The old `melvin.sh` command line is still fully functional if you prefer direct commands.

## Quick Start

```bash
# Launch the new comprehensive CLI
cd /home/user/Github/melvin
./scripts/melvin.sh cli

# Use arrow keys to navigate tabs
# Use 1-7 numbers to select menu items
# Type 'q' to quit
```

---

**Next Step**: Try it out! Run `./scripts/melvin.sh cli` to see the new interface in action.
