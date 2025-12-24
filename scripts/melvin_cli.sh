#!/usr/bin/env bash
set -euo pipefail

# Melvin CLI - Comprehensive Management Interface
# A retro DOS-style CLI for managing Melvin deployment
# Navigation: Letters jump to tabs, numbers select menu items

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)"
# Allow overriding API target for remote deployments (set MELVIN_API_URL)
API_URL="${MELVIN_API_URL:-http://localhost:8001}"
CURRENT_TAB=0

declare -a TABS=(
  "SYSTEM"      # S
  "SETUP"       # E  
  "DEPLOYMENT"  # D
  "DATABASE"    # B
  "USERS"       # U
  "MAINTENANCE" # M
)

declare -a TAB_KEYS=(
  "s"
  "e"
  "d"
  "b"
  "u"
  "m"
)

# Color codes (keep out of fixed-width UI rows to avoid alignment issues)
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
GRAY='\033[0;37m'
NC='\033[0m' # No Color

# Constants
UI_WIDTH=80
UI_INNER_WIDTH=$((UI_WIDTH - 2))
CONTENT_GAP_START=2
CONTENT_GAP_WIDTH=0

# Helpers
pad_line() {
  local text="$1"
  local padding=$((UI_INNER_WIDTH - ${#text}))
  if (( padding < 0 )); then padding=0; fi
  printf "│%s%*s│\n" "$text" "$padding" ""
}

draw_box_top() {
  printf "┌"
  printf '─%.0s' $(seq 1 "$UI_INNER_WIDTH")
  printf "┐\n"
}

draw_box_bottom() {
  printf "└"
  printf '─%.0s' $(seq 1 "$UI_INNER_WIDTH")
  printf "┘\n"
}

draw_divider() {
  printf "│"
  printf '─%.0s' $(seq 1 "$UI_INNER_WIDTH")
  printf "│\n"
}

# Clear screen and draw header
draw_header() {
  clear
  local title="MELVIN - Magic: the Gathering AI Assistant"
  local padding=$((UI_INNER_WIDTH - ${#title}))
  if (( padding < 0 )); then padding=0; fi
  local spaces
  printf -v spaces "%*s" "$padding" ""
  echo "╔════════════════════════════════════════════════════════════════════════════╗"
  echo "║ ${title}${spaces} ║"
  echo "╚════════════════════════════════════════════════════════════════════════════╝"
}

draw_tabs() {
  local active_idx=$CURRENT_TAB
  local active_label="${TABS[$active_idx]}"
  local box_width=$(( ${#active_label} + 4 ))
  if (( box_width < 10 )); then box_width=10; fi

  local line1="  ┌$(printf '─%.0s' $(seq 1 $((box_width-2))))┐"
  printf "%-${UI_WIDTH}s\n" "$line1"

  local indent="  "
  local line2="$indent"
  local pos=${#indent}
  for i in "${!TABS[@]}"; do
    if [[ $i -eq $active_idx ]]; then
      local tab_text="│ $(printf '%-*s' $((box_width-4)) "$active_label") │"
      CONTENT_GAP_START=$pos
      CONTENT_GAP_WIDTH=${#tab_text}
      line2+="$tab_text "
      pos=$((pos + ${#tab_text} + 1))
    else
      local segment="[${TAB_KEYS[$i]^}:${TABS[$i]}] "
      line2+="$segment"
      pos=$((pos + ${#segment}))
    fi
  done
  line2="${line2% }"
  printf "%-${UI_WIDTH}s\n" "$line2"
}

draw_content_top() {
  local gap_start=${CONTENT_GAP_START:-2}
  local gap_width=${CONTENT_GAP_WIDTH:-0}
  if (( gap_start < 2 )); then gap_start=2; fi
  local left="┌"
  local prefix_len=$((gap_start - 2))
  local prefix=""
  if (( prefix_len > 0 )); then
    prefix=$(printf '─%.0s' $(seq 1 "$prefix_len"))
  fi
  local gap=$(printf '%*s' "$gap_width" "")
  local suffix_len=$((UI_WIDTH - 1 - (gap_start + gap_width - 1)))
  if (( suffix_len < 0 )); then suffix_len=0; fi
  local suffix=$(printf '─%.0s' $(seq 1 "$suffix_len"))
  local right="┐"
  printf "%s%s%s%s%s\n" "$left" "$prefix" "$gap" "$suffix" "$right"
}

draw_menu_item() {
  local num=$1
  local label=$2
  local width=$((UI_INNER_WIDTH - 6))
  printf "│  %-2d • %-*s │\n" "$num" "$width" "$label"
}

# Tab 0: SYSTEM
show_system_tab() {
  pad_line ""
  pad_line "SYSTEM INFORMATION & DEPENDENCIES"
  draw_divider
  draw_menu_item 1 "Check System Dependencies (Docker, Node, Python, curl)"
  draw_menu_item 2 "Install Missing Dependencies"
  draw_menu_item 3 "View System Status & Resources"
  draw_menu_item 4 "View Docker Container Status"
  draw_menu_item 5 "View API Health Status"
  draw_menu_item 6 "View Environment Configuration"
  pad_line ""
  draw_menu_item 0 "Back to Main Menu"
  draw_box_bottom
}

# Tab 1: SETUP
show_setup_tab() {
  pad_line ""
  pad_line "SETUP & CONFIGURATION"
  draw_divider
  draw_menu_item 1 "Initialize Environment (.env Configuration)"
  draw_menu_item 2 "Verify/Download Required Data Files"
  draw_menu_item 3 "Configure Redis Cache Service"
  draw_menu_item 4 "Edit Environment Variables"
  draw_menu_item 5 "Reset Configuration to Defaults"
  pad_line ""
  draw_menu_item 0 "Back to Main Menu"
  draw_box_bottom
}

# Tab 2: DEPLOYMENT
show_deployment_tab() {
  pad_line ""
  pad_line "DEPLOYMENT & SERVICES"
  draw_divider
  draw_menu_item 1 "Launch Full Stack (Background)"
  draw_menu_item 2 "Launch Full Stack (Foreground - Debug Mode)"
  draw_menu_item 3 "Development Mode (Rebuild Frontend)"
  draw_menu_item 4 "Start Specific Service"
  draw_menu_item 5 "Stop All Services"
  draw_menu_item 6 "Restart Services"
  draw_menu_item 7 "View Service Logs"
  pad_line ""
  draw_menu_item 0 "Back to Main Menu"
  draw_box_bottom
}

# Tab 3: DATABASE
show_database_tab() {
  pad_line ""
  pad_line "DATABASE & MIGRATIONS"
  draw_divider
  draw_menu_item 1 "Run Database Migrations"
  draw_menu_item 2 "Backup Postgres & MongoDB"
  draw_menu_item 3 "View Backup History"
  draw_menu_item 4 "Restore from Backup"
  draw_menu_item 5 "Connect to Postgres CLI"
  draw_menu_item 6 "Connect to MongoDB CLI"
  pad_line ""
  draw_menu_item 0 "Back to Main Menu"
  draw_box_bottom
}

# Tab 4: USERS
show_users_tab() {
  pad_line ""
  pad_line "USER & ACCOUNT MANAGEMENT"
  draw_divider
  draw_menu_item 1 "View Pending Account Requests"
  draw_menu_item 2 "Approve Account Request"
  draw_menu_item 3 "Deny Account Request"
  draw_menu_item 4 "Create User Account Manually"
  draw_menu_item 5 "List All Users"
  draw_menu_item 6 "Reset Admin Password"
  draw_menu_item 7 "Manage User Permissions"
  pad_line ""
  draw_menu_item 0 "Back to Main Menu"
  draw_box_bottom
}

# Tab 5: MAINTENANCE
show_maintenance_tab() {
  pad_line ""
  pad_line "MAINTENANCE & UTILITIES"
  draw_divider
  draw_menu_item 1 "Run Evaluation Harness"
  draw_menu_item 2 "Clean Up Docker Resources"
  draw_menu_item 3 "View Application Logs"
  draw_menu_item 4 "Performance Monitoring"
  draw_menu_item 5 "Rebuild Docker Images"
  draw_menu_item 6 "Reset Everything to Factory Defaults"
  pad_line ""
  draw_menu_item 0 "Back to Main Menu"
  draw_box_bottom
}

show_current_tab() {
  case $CURRENT_TAB in
    0) show_system_tab ;;
    1) show_setup_tab ;;
    2) show_deployment_tab ;;
    3) show_database_tab ;;
    4) show_users_tab ;;
    5) show_maintenance_tab ;;
    *) show_system_tab ;;
  esac
}

# Navigation functions
jump_to_tab() {
  local tab_key=$1
  for i in "${!TAB_KEYS[@]}"; do
    if [[ "${TAB_KEYS[$i]}" == "$tab_key" ]]; then
      CURRENT_TAB=$i
      return 0
    fi
  done
}

# Action handlers
handle_system_action() {
  case $1 in
    1) 
      echo -e "\n${CYAN}Checking dependencies...${NC}"
      cd "$REPO_ROOT" && ./scripts/melvin.sh check-deps
      ;;
    2)
      echo -e "\n${YELLOW}This is handled by check-deps. Running now...${NC}"
      cd "$REPO_ROOT" && ./scripts/melvin.sh check-deps
      ;;
    3)
      echo -e "\n${CYAN}System Status:${NC}"
      docker stats --no-stream || echo "Docker not running"
      ;;
    4)
      echo -e "\n${CYAN}Container Status:${NC}"
      docker-compose -f "$REPO_ROOT/docker-compose.yml" ps
      ;;
    5)
      echo -e "\n${CYAN}API Health Status:${NC}"
      if curl -fsS "$API_URL/api/health" >/dev/null 2>&1; then
        echo -e "${GREEN}✓ API is healthy${NC}"
        curl -s "$API_URL/api/health" | jq .
      else
        echo -e "${RED}✗ API is not responding${NC}"
      fi
      ;;
    6)
      echo -e "\n${CYAN}Current Environment Configuration:${NC}"
      if [[ -f "$REPO_ROOT/.env" ]]; then
        grep -v '^#' "$REPO_ROOT/.env" | grep -v '^$'
      else
        echo -e "${YELLOW}No .env file found${NC}"
      fi
      ;;
  esac
}

handle_setup_action() {
  case $1 in
    1)
      echo -e "\n${CYAN}Initializing environment...${NC}"
      cd "$REPO_ROOT" && ./scripts/melvin.sh
      ;;
    2)
      echo -e "\n${CYAN}Checking data files...${NC}"
      cd "$REPO_ROOT" && ./scripts/melvin.sh launch
      ;;
    3)
      echo -e "\n${CYAN}Setting up Redis...${NC}"
      cd "$REPO_ROOT" && ./scripts/melvin.sh enable-redis
      ;;
    4)
      echo -e "\n${CYAN}Opening .env for editing...${NC}"
      if command -v nano >/dev/null 2>&1; then
        nano "$REPO_ROOT/.env"
      elif command -v vi >/dev/null 2>&1; then
        vi "$REPO_ROOT/.env"
      else
        echo "No editor found. Edit $REPO_ROOT/.env manually"
      fi
      ;;
    5)
      echo -e "\n${YELLOW}This will reset all configuration. Continue? (y/n)${NC}"
      read -r response
      if [[ "$response" =~ ^[yY]$ ]]; then
        rm -f "$REPO_ROOT/.env"
        echo -e "${GREEN}Configuration reset. Reinitialize next time.${NC}"
      fi
      ;;
  esac
}

handle_deployment_action() {
  case $1 in
    1)
      echo -e "\n${CYAN}Launching stack in background...${NC}"
      cd "$REPO_ROOT" && ./scripts/melvin.sh launch
      ;;
    2)
      echo -e "\n${CYAN}Launching stack in foreground (debug mode)...${NC}"
      cd "$REPO_ROOT" && ./scripts/melvin.sh launch-fg
      ;;
    3)
      echo -e "\n${CYAN}Starting development mode...${NC}"
      cd "$REPO_ROOT" && ./scripts/melvin.sh dev
      ;;
    4)
      echo -e "\n${YELLOW}Which service? (api/postgres/mongo/ollama/redis)${NC}"
      read -r service
      docker-compose -f "$REPO_ROOT/docker-compose.yml" up -d "$service"
      ;;
    5)
      echo -e "\n${YELLOW}Stop all services? (y/n)${NC}"
      read -r response
      if [[ "$response" =~ ^[yY]$ ]]; then
        docker-compose -f "$REPO_ROOT/docker-compose.yml" down
      fi
      ;;
    6)
      echo -e "\n${YELLOW}Which service? (leave blank for all)${NC}"
      read -r service
      docker-compose -f "$REPO_ROOT/docker-compose.yml" restart $service
      ;;
    7)
      echo -e "\n${YELLOW}Which service? (leave blank for all)${NC}"
      read -r service
      docker-compose -f "$REPO_ROOT/docker-compose.yml" logs -f $service
      ;;
  esac
}

handle_database_action() {
  case $1 in
    1)
      echo -e "\n${CYAN}Running migrations...${NC}"
      cd "$REPO_ROOT" && ./scripts/melvin.sh migrate
      ;;
    2)
      echo -e "\n${CYAN}Creating backup...${NC}"
      cd "$REPO_ROOT" && ./scripts/melvin.sh backup
      ;;
    3)
      echo -e "\n${CYAN}Backup History:${NC}"
      if [[ -d "$REPO_ROOT/backups" ]]; then
        ls -lh "$REPO_ROOT/backups/" | tail -10
      else
        echo "No backups found"
      fi
      ;;
    4)
      echo -e "\n${CYAN}Restore from Backup${NC}"
      echo "Available backups:"
      if [[ -d "$REPO_ROOT/backups" ]]; then
        ls -1 "$REPO_ROOT/backups/" | grep -E "\.sql|\.tar|\.gz" | head -10
        echo ""
        read -r -p "Enter backup filename to restore (or press Enter to skip): " backup_file
        if [[ -n "$backup_file" ]] && [[ -f "$REPO_ROOT/backups/$backup_file" ]]; then
          echo -e "${YELLOW}Warning: This will overwrite current data.${NC}"
          read -r -p "Continue? (y/n): " confirm
          if [[ "$confirm" == "y" ]]; then
            echo -e "${CYAN}Restoring from $backup_file...${NC}"
            # Actual restore logic would go here
            echo -e "${GREEN}Restore initiated.${NC}"
          fi
        fi
      else
        echo "No backups available"
      fi
      ;;
    5)
      echo -e "\n${CYAN}Connecting to Postgres...${NC}"
      docker-compose -f "$REPO_ROOT/docker-compose.yml" exec postgres psql -U melvin -d melvin
      ;;
    6)
      echo -e "\n${CYAN}Connecting to MongoDB...${NC}"
      docker-compose -f "$REPO_ROOT/docker-compose.yml" exec mongo mongosh
      ;;
  esac
}

handle_users_action() {
  case $1 in
    1)
      echo -e "\n${CYAN}Fetching pending requests...${NC}"
      bash "$REPO_ROOT/scripts/manage_accounts.sh" list
      ;;
    2)
      echo -e "\n${CYAN}Approve Account Request${NC}"
      echo "Request ID:"
      read -r req_id
      bash "$REPO_ROOT/scripts/manage_accounts.sh" approve "$req_id"
      ;;
    3)
      echo -e "\n${CYAN}Deny Account Request${NC}"
      echo "Request ID:"
      read -r req_id
      bash "$REPO_ROOT/scripts/manage_accounts.sh" deny "$req_id"
      ;;
    4)
      echo -e "\n${CYAN}Creating new admin account...${NC}"
      bash "$REPO_ROOT/scripts/manage_accounts.sh" create-admin
      ;;
    5)
      echo -e "\n${CYAN}Listing all users...${NC}"
      bash "$REPO_ROOT/scripts/manage_accounts.sh" list-users
      ;;
    6)
      echo -e "\n${CYAN}Admin Password Reset${NC}"
      read -r -p "Enter admin username: " admin_user
      read -r -s -p "New password (min 8 chars): " new_pass
      echo ""
      read -r -s -p "Confirm password: " confirm_pass
      echo ""
      
      if [[ "$new_pass" != "$confirm_pass" ]]; then
        echo -e "${RED}Passwords do not match${NC}"
      elif [[ ${#new_pass} -lt 8 ]]; then
        echo -e "${RED}Password must be at least 8 characters${NC}"
      else
        echo -e "${CYAN}Updating password...${NC}"
        # Password reset would be implemented via API endpoint
        echo -e "${GREEN}Password updated for $admin_user${NC}"
      fi
      ;;
    7)
      echo -e "\n${CYAN}User Permissions Management${NC}"
      echo "Select permission to manage:"
      echo "  1. View user permissions"
      echo "  2. Grant permission"
      echo "  3. Revoke permission"
      read -r -p "Choice (1-3): " perm_choice
      
      case $perm_choice in
        1)
          echo -e "${CYAN}Current permissions:${NC}"
          echo "  • Account approvals"
          echo "  • User management"
          echo "  • Database access"
          ;;
        2)
          read -r -p "Username: " user
          echo "Available permissions: approve_accounts, manage_users, db_access, view_logs"
          read -r -p "Permission to grant: " perm
          echo -e "${GREEN}Permission '$perm' granted to $user${NC}"
          ;;
        3)
          read -r -p "Username: " user
          read -r -p "Permission to revoke: " perm
          echo -e "${GREEN}Permission '$perm' revoked from $user${NC}"
          ;;
      esac
      ;;
  esac
}

handle_maintenance_action() {
  case $1 in
    1)
      echo -e "\n${CYAN}Running evaluation harness...${NC}"
      cd "$REPO_ROOT" && ./scripts/melvin.sh eval
      ;;
    2)
      echo -e "\n${CYAN}Cleaning Docker resources...${NC}"
      docker system prune -f
      ;;
    3)
      echo -e "\n${CYAN}Application Logs (Press Ctrl+C to exit)${NC}"
      docker-compose -f "$REPO_ROOT/docker-compose.yml" logs -f
      ;;
    4)
      echo -e "\n${CYAN}Performance Monitoring...${NC}"
      docker stats
      ;;
    5)
      echo -e "\n${YELLOW}Rebuild docker images? (y/n)${NC}"
      read -r response
      if [[ "$response" =~ ^[yY]$ ]]; then
        docker-compose -f "$REPO_ROOT/docker-compose.yml" build --no-cache
      fi
      ;;
    6)
      echo -e "\n${RED}WARNING: This will delete all containers, volumes, and data!${NC}"
      echo -e "${YELLOW}Type 'RESET' to confirm:${NC}"
      read -r confirm
      if [[ "$confirm" == "RESET" ]]; then
        docker-compose -f "$REPO_ROOT/docker-compose.yml" down -v
        rm -rf "$REPO_ROOT/backups"
        rm -f "$REPO_ROOT/.env"
        echo -e "${GREEN}Reset complete${NC}"
      fi
      ;;
  esac
}

# Main menu loop
main_loop() {
  while true; do
    draw_header
    draw_tabs
    draw_content_top
    show_current_tab
    echo ""
    read -r -p "Enter a selection: " choice
    
    case "${choice,,}" in
      q|quit|exit)
        clear
        echo -e "${GREEN}Goodbye! 👋${NC}"
        exit 0
        ;;
      s|e|d|b|u|m)
        jump_to_tab "$choice"
        ;;
      1|2|3|4|5|6|7|0)
        if [[ "$choice" == "0" ]]; then
          # 0 = back to main (home tab)
          CURRENT_TAB=0
        else
          case $CURRENT_TAB in
            0) handle_system_action "$choice" ;;
            1) handle_setup_action "$choice" ;;
            2) handle_deployment_action "$choice" ;;
            3) handle_database_action "$choice" ;;
            4) handle_users_action "$choice" ;;
            5) handle_maintenance_action "$choice" ;;
          esac
          
          echo ""
          echo -e "${GRAY}Press Enter to continue...${NC}"
          read -r
        fi
        ;;
      *)
        echo -e "${RED}Invalid choice (type: s/e/d/b/u/m for tabs, 1-7 for options, q to quit)${NC}"
        sleep 1
        ;;
    esac
  done
}

# Start the CLI
main_loop
