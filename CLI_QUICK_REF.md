# ⚡ Melvin CLI - Quick Reference Card

## Start Here

```bash
./scripts/melvin.sh cli
```

## One-Page Cheat Sheet

### Tab Shortcuts (Press ONE Letter)

```
S → SYSTEM        E → SETUP         D → DEPLOYMENT
B → DATABASE      U → USERS         M → MAINTENANCE
```

### Menu Options (Press a Number)

Within any tab, press `1` through `7` to select options.

### Special Keys

```
0 = Jump to SYSTEM (home)
q = Quit
```

## Super Common Tasks

| What to Do | Keys | Example |
|-----------|------|---------|
| **Approve accounts** | `u` → `1` → `2` | "Show me pending requests, then approve one" |
| **Check API health** | `s` → `5` | "Is the system healthy?" |
| **Launch services** | `d` → `1` | "Start the application" |
| **Make a backup** | `b` → `2` | "Backup my databases" |
| **View logs** | `d` → `7` | "What's happening?" |
| **Edit settings** | `e` → `4` | "Change .env configuration" |

## Tab Menu at a Glance

### 🖥️ **S**YSTEM Tab
1. Check dependencies
2. Install missing deps
3. System resources
4. Container status
5. **API health** ⭐
6. Environment config

### ⚙️ **E**SETUP Tab
1. Initialize environment
2. Download data files
3. Configure Redis
4. Edit .env
5. Reset config

### 🚀 **D**EPLOYMENT Tab
1. **Launch (background)** ⭐
2. Launch (debug mode)
3. Development mode
4. Start service
5. Stop services
6. Restart services
7. View logs

### 💾 **B**DATABASE Tab
1. Run migrations
2. **Create backup** ⭐
3. Backup history
4. Restore backup
5. Postgres CLI
6. MongoDB CLI

### 👥 **U**SERS Tab ⭐ Most Important!
1. **View pending requests** ⭐⭐⭐
2. **Approve request** ⭐⭐⭐
3. Deny request
4. Create user
5. List users
6. Reset password
7. Manage permissions

### 🔧 **M**AINTENANCE Tab
1. Run evaluation
2. Clean Docker
3. View logs
4. Performance
5. Rebuild images
6. Factory reset

## Why This Design?

✅ **Fast** - Jump to any tab in 1 keypress
✅ **Intuitive** - Letters for tabs, numbers for options
✅ **Works Everywhere** - SSH, Docker, remote servers
✅ **Mnemonic** - S=System, U=Users, D=Deployment
✅ **No Cycling** - Get where you need in one go

## Examples

### Example 1: Approve an Account (30 seconds)
```
./scripts/melvin.sh cli
u              # USERS tab
1              # View pending
               # (Note down request ID 42)
2              # Approve request
               # Type: 42
               # ✓ Done!
```

### Example 2: Check System Health (10 seconds)
```
./scripts/melvin.sh cli
s              # SYSTEM tab (already default)
5              # View health
               # ✓ See if API is up
q              # Quit
```

### Example 3: Backup & Restore (1 minute)
```
./scripts/melvin.sh cli
b              # DATABASE tab
2              # Create backup (gets timestamp)
3              # View backup history
4              # Restore from backup (type timestamp)
```

## Keyboard Layout

```
┌──────────────────────────────────┐
│   TAB KEYS (Jump To)             │
│   S E D B U M                    │
│                                  │
│   OPTION KEYS (Within Tab)       │
│   1 2 3 4 5 6 7                  │
│                                  │
│   SPECIAL                        │
│   0=Home  Q=Quit                 │
└──────────────────────────────────┘
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Nothing happened" | Press Enter after your key |
| "Invalid choice" | Make sure you're pressing letters (s-m) or numbers (1-7) |
| "Wrong tab" | Press a different letter to jump |
| "Want to go home" | Press `s` to jump to SYSTEM |
| "Want to quit" | Press `q` |

## Keyboard Summary

| Key Type | Keys | Purpose |
|----------|------|---------|
| **Tab Jump** | s, e, d, b, u, m | Jump to specific tab |
| **Menu Select** | 1, 2, 3, 4, 5, 6, 7 | Select option within tab |
| **Special** | 0, q, Enter | Home, Quit, Confirm |

---

**Remember:** One letter = jump to tab instantly! 🚀

**Start:** `./scripts/melvin.sh cli`
**Approve account:** `u` → `1` → `2`
**Done:** `q`
