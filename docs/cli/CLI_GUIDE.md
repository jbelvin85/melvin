# Melvin CLI - Comprehensive Management Interface

A retro DOS-style command-line interface for managing the Melvin application with organized tabs and menus.

## Quick Start

```bash
./scripts/melvin_cli.sh
```

## Features

### 🖥️ Tabbed Interface
The CLI is organized into 6 main tabs (pages) for logical grouping:

1. **SYSTEM** - Dependencies and system status
2. **SETUP** - Configuration and initialization
3. **DEPLOYMENT** - Service management
4. **DATABASE** - Migrations and backups
5. **USERS** - Account management
6. **MAINTENANCE** - Utilities and cleanup

### Navigation

| Key | Action |
|-----|--------|
| `h` | Previous tab (vim-style, works reliably) |
| `l` | Next tab (vim-style, works reliably) |
| `←` or `→` | Arrow keys also work (if supported) |
| `1-7` | Select menu item |
| `q` | Quit |
| `Enter` | Confirm action |

**Note:** Use `h` and `l` for reliable tab navigation if arrow keys don't work in your terminal.

## Tab Details

### 📋 SYSTEM Tab
Check and manage system dependencies and status.

**Options:**
1. Check System Dependencies (Docker, Node, Python, curl)
2. Install Missing Dependencies
3. View System Status & Resources
4. View Docker Container Status
5. View API Health Status
6. View Environment Configuration

**Use for:** Verifying your system is ready to run Melvin

### ⚙️ SETUP Tab
Initialize and configure Melvin.

**Options:**
1. Initialize Environment (.env Configuration)
2. Verify/Download Required Data Files
3. Configure Redis Cache Service
4. Edit Environment Variables
5. Reset Configuration to Defaults

**Use for:** First-time setup and configuration changes

### 🚀 DEPLOYMENT Tab
Start, stop, and manage services.

**Options:**
1. Launch Full Stack (Background)
2. Launch Full Stack (Foreground - Debug Mode)
3. Development Mode (Rebuild Frontend)
4. Start Specific Service
5. Stop All Services
6. Restart Services
7. View Service Logs

**Use for:** Running and monitoring Melvin services

### 💾 DATABASE Tab
Manage database operations and backups.

**Options:**
1. Run Database Migrations
2. Backup Postgres & MongoDB
3. View Backup History
4. Restore from Backup
5. Connect to Postgres CLI
6. Connect to MongoDB CLI

**Use for:** Database administration and maintenance

### 👥 USERS Tab
Manage user accounts and access.

**Options:**
1. View Pending Account Requests
2. Approve Account Request
3. Deny Account Request
4. Create User Account Manually
5. List All Users
6. Reset Admin Password
7. Manage User Permissions

**Use for:** Admin account management

### 🔧 MAINTENANCE Tab
Utilities and advanced operations.

**Options:**
1. Run Evaluation Harness
2. Clean Up Docker Resources
3. View Application Logs
4. Performance Monitoring
5. Rebuild Docker Images
6. Reset Everything to Factory Defaults

**Use for:** Optimization and troubleshooting

## Example Workflows

### First-Time Setup
```
1. Run SYSTEM → Check System Dependencies
2. Run SYSTEM → Install Missing Dependencies (if needed)
3. Go to SETUP tab
4. Run SETUP → Initialize Environment
5. Go to DEPLOYMENT tab
6. Run DEPLOYMENT → Launch Full Stack (Background)
```

### Manage User Requests
```
1. Go to USERS tab
2. Run USERS → View Pending Account Requests
3. Run USERS → Approve Account Request (or Deny)
4. Done! User can now login
```

### Debug Issues
```
1. Go to SYSTEM tab
2. Run SYSTEM → View API Health Status
3. If unhealthy, go to DEPLOYMENT tab
4. Run DEPLOYMENT → View Service Logs
5. Check the output for errors
```

### Perform Backups
```
1. Go to DATABASE tab
2. Run DATABASE → Backup Postgres & MongoDB
3. Run DATABASE → View Backup History
4. Backups are stored in ./backups/
```

## Keyboard Tips

### Navigation Tips
- Use arrow keys: `<` and `>`
- Type `q` to quit anytime
- All commands are case-insensitive
- Invalid choices show an error and allow retry

### Command Tips
- Some commands open interactive prompts (like editing .env)
- Long-running commands (logs) use `Ctrl+C` to stop
- Database connections open their respective CLI tools

## Color Coding

| Color | Meaning |
|-------|---------|
| 🔵 Blue | Borders and structure |
| ⚪ White | Section headers |
| 🟡 Yellow | Menu items and options |
| 🟢 Green | Success messages |
| 🔴 Red | Errors and warnings |
| ⚫ Gray | Help text and navigation |

## Integration with melvin.sh

The CLI works alongside the main melvin.sh script:
- Both can be used interchangeably
- CLI calls melvin.sh internally for core operations
- CLI adds user-friendly interface and organization

## Troubleshooting

### CLI Won't Start
```bash
# Make sure it's executable
chmod +x ./scripts/melvin_cli.sh

# Try with explicit bash
bash ./scripts/melvin_cli.sh
```

### Colors Look Wrong
```bash
# Ensure terminal supports ANSI colors
# Most modern terminals do - try exporting:
export TERM=xterm-256color
./scripts/melvin_cli.sh
```

### Some Features Show "Coming Soon"
These are placeholders for future enhancements:
- Manual user creation
- User permissions management
- Admin password reset
- Backup restore functionality

## Advanced Usage

### Run from Anywhere
```bash
cd /your/project/path
/home/user/Github/melvin/scripts/melvin_cli.sh
```

### Combine with Other Tools
```bash
# Run CLI in background, work in terminal
./scripts/melvin_cli.sh &

# View processes
jobs
fg  # Bring CLI back to foreground
```

## Feature Roadmap

- [ ] User creation wizard
- [ ] Permissions management UI
- [ ] Advanced monitoring dashboard
- [ ] Configuration file editor
- [ ] Automated health checks with notifications
- [ ] Log filtering and search
- [ ] Performance analytics
- [ ] One-click deployment to test/prod

## Support

For issues or feature requests, check:
- `QUICK_REF_USER_ACCOUNTS.md` - Account management
- `API_USER_MANAGEMENT.md` - API endpoints
- `REMOTE_SERVER_SETUP.md` - Remote deployment

---

**Tip:** The CLI is the easiest way to manage Melvin! Start with SYSTEM tab to check your setup.
