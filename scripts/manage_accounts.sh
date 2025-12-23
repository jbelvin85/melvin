#!/usr/bin/env bash
# Melvin Account Management CLI
# A retro-style DOS-like interface for user and account request management

set -euo pipefail

API_URL="${API_URL:-http://localhost:8001}"
ADMIN_TOKEN=""
ADMIN_USER=""

# Colors for retro DOS styling
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# Clear screen and show header
show_header() {
  clear
  echo -e "${CYAN}╔════════════════════════════════════════════════════════════════════════════╗${NC}"
  echo -e "${CYAN}║${NC} ${WHITE}MELVIN - Magic Card AI Assistant${NC} ${CYAN}║${NC}"
  echo -e "${CYAN}╚════════════════════════════════════════════════════════════════════════════╝${NC}"
}

# Display menu with retro styling
show_menu() {
  echo ""
  echo "┌─────────────────────────────────────────────────────────────────────────┐"
  echo "│                          MAIN MENU                                      │"
  echo "├─────────────────────────────────────────────────────────────────────────┤"
  echo "│  [1] View Pending Account Requests                                      │"
  echo "│  [2] Approve Account Request                                            │"
  echo "│  [3] Deny Account Request                                               │"
  echo "│  [4] View Approved Users                                                │"
  echo "│  [5] Create New Admin Account                                           │"
  echo "│  [6] Login as Admin                                                     │"
  echo "│  [7] Logout                                                             │"
  echo "│  [0] Exit                                                               │"
  echo "└─────────────────────────────────────────────────────────────────────────┘"
  echo ""
}

# Helper: Print colored text
print_status() {
  local status=$1
  local message=$2
  case $status in
    "success") echo -e "${GREEN}✓${NC} $message" ;;
    "error") echo -e "${RED}✗${NC} $message" ;;
    "info") echo -e "${CYAN}ℹ${NC} $message" ;;
    "warn") echo -e "${YELLOW}⚠${NC} $message" ;;
  esac
}

# Helper: Print section header
print_section() {
  echo ""
  echo "┌─────────────────────────────────────────────────────────────────────────┐"
  echo "│  $1"
  echo "└─────────────────────────────────────────────────────────────────────────┘"
}

# Pause for user input
pause_screen() {
  read -r -p "Press ENTER to continue..."
}

# Authenticate admin
login_admin() {
  print_section "ADMIN LOGIN"
  read -r -p "Username: " username
  read -r -s -p "Password: " password
  echo ""
  
  print_status "info" "Authenticating..."
  
  local response
  response=$(curl -fsS -X POST "$API_URL/api/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"username\": \"$username\", \"password\": \"$password\"}" 2>/dev/null || echo "")
  
  if [[ -z "$response" ]]; then
    print_status "error" "Connection failed. Is the API running?"
    return 1
  fi
  
  ADMIN_TOKEN=$(echo "$response" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
  
  if [[ -z "$ADMIN_TOKEN" ]]; then
    print_status "error" "Authentication failed. Invalid credentials."
    return 1
  fi
  
  ADMIN_USER="$username"
  print_status "success" "Login successful! Welcome, $username."
  pause_screen
}

# Check if admin is logged in
check_auth() {
  if [[ -z "$ADMIN_TOKEN" ]]; then
    print_status "error" "You must login as admin first."
    pause_screen
    return 1
  fi
  return 0
}

# View pending account requests
view_pending_requests() {
  check_auth || return
  
  print_section "PENDING ACCOUNT REQUESTS"
  
  local response
  response=$(curl -fsS -X GET "$API_URL/api/auth/requests" \
    -H "Authorization: Bearer $ADMIN_TOKEN" 2>/dev/null || echo "")
  
  if [[ -z "$response" ]] || [[ "$response" == "[]" ]]; then
    print_status "info" "No pending account requests."
    pause_screen
    return
  fi
  
  # Parse and display requests
  echo ""
  echo "Request # │ Username         │ Status   │ Created"
  echo "───────────┼──────────────────┼──────────┼─────────────────────"
  
  local count=0
  while IFS= read -r line; do
    if [[ $line =~ \"id\":[[:space:]]*([0-9]+) ]]; then
      local id="${BASH_REMATCH[1]}"
      local username=$(echo "$line" | grep -o '"username":"[^"]*' | cut -d'"' -f4)
      local status=$(echo "$line" | grep -o '"status":"[^"]*' | cut -d'"' -f4)
      
      printf "%-10s │ %-16s │ %-8s │ %s\n" "$id" "$username" "$status" "$(date)"
      ((count++))
    fi
  done <<< "$response"
  
  echo "───────────┴──────────────────┴──────────┴─────────────────────"
  echo ""
  print_status "info" "Total pending requests: $count"
  pause_screen
}

# Approve account request
approve_request() {
  check_auth || return
  
  print_section "APPROVE ACCOUNT REQUEST"
  
  read -r -p "Enter request ID to approve: " request_id
  
  if ! [[ "$request_id" =~ ^[0-9]+$ ]]; then
    print_status "error" "Invalid request ID."
    pause_screen
    return
  fi
  
  echo ""
  read -r -p "Approve username as-is? (y/n) [y]: " use_original
  use_original="${use_original:-y}"
  
  local approved_username=""
  if [[ "$use_original" != "y" ]]; then
    read -r -p "Enter approved username: " approved_username
  fi
  
  print_status "info" "Processing approval..."
  
  local payload="{}"
  if [[ -n "$approved_username" ]]; then
    payload="{\"approved_username\": \"$approved_username\"}"
  fi
  
  local response
  response=$(curl -fsS -X POST "$API_URL/api/auth/requests/$request_id/approve" \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d "$payload" 2>/dev/null || echo "")
  
  if [[ -z "$response" ]]; then
    print_status "error" "Failed to approve request."
  elif echo "$response" | grep -q '"status":"approved"'; then
    local username=$(echo "$response" | grep -o '"username":"[^"]*' | cut -d'"' -f4)
    print_status "success" "Account approved! User: $username"
  else
    print_status "error" "Unexpected response from server."
  fi
  
  pause_screen
}

# Deny account request
deny_request() {
  check_auth || return
  
  print_section "DENY ACCOUNT REQUEST"
  
  read -r -p "Enter request ID to deny: " request_id
  
  if ! [[ "$request_id" =~ ^[0-9]+$ ]]; then
    print_status "error" "Invalid request ID."
    pause_screen
    return
  fi
  
  read -r -p "Are you sure? (y/n): " confirm
  if [[ "$confirm" != "y" ]]; then
    print_status "info" "Cancelled."
    pause_screen
    return
  fi
  
  print_status "info" "Processing denial..."
  
  local response
  response=$(curl -fsS -X POST "$API_URL/api/auth/requests/$request_id/deny" \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d "{}" 2>/dev/null || echo "")
  
  if [[ -z "$response" ]]; then
    print_status "error" "Failed to deny request."
  elif echo "$response" | grep -q '"status":"denied"'; then
    print_status "success" "Request denied."
  else
    print_status "error" "Unexpected response from server."
  fi
  
  pause_screen
}

# View approved users
view_users() {
  check_auth || return
  
  print_section "APPROVED USERS (Simulated)"
  
  echo ""
  echo "This would list all approved users from the database."
  echo "Note: The current API doesn't have a list-users endpoint."
  echo ""
  print_status "info" "To view users, check the database directly:"
  echo "  docker-compose exec postgres psql -U melvin -d melvin -c \"SELECT * FROM users;\""
  
  pause_screen
}

# Logout
logout() {
  if [[ -z "$ADMIN_TOKEN" ]]; then
    print_status "info" "Not logged in."
  else
    ADMIN_TOKEN=""
    ADMIN_USER=""
    print_status "success" "Logged out."
  fi
  pause_screen
}

# Main function - supports both interactive and CLI modes
main() {
  # Check if arguments were provided (CLI mode)
  if [[ $# -gt 0 ]]; then
    local command="$1"
    shift || true
    
    case "$command" in
      list)
        view_pending_requests_cli
        ;;
      approve)
        approve_request_cli "$@"
        ;;
      deny)
        deny_request_cli "$@"
        ;;
      list-users)
        view_users_cli
        ;;
      create-admin)
        create_admin_interactive
        ;;
      login)
        login_admin_interactive
        ;;
      logout)
        logout
        ;;
      *)
        echo "Unknown command: $command"
        echo "Usage: $0 [list|approve|deny|list-users|create-admin|login|logout]"
        exit 1
        ;;
    esac
  else
    # Interactive mode
    interactive_menu
  fi
}

# Interactive menu (original behavior)
interactive_menu() {
  while true; do
    show_header
    
    if [[ -n "$ADMIN_TOKEN" ]]; then
      echo "┌─────────────────────────────────────────────────────────────────────────┐"
      echo "│  Status: Logged in as: $ADMIN_USER"
      echo "│  API Server: $API_URL"
      echo "└─────────────────────────────────────────────────────────────────────────┘"
    else
      echo "┌─────────────────────────────────────────────────────────────────────────┐"
      echo "│  Status: Not logged in"
      echo "│  API Server: $API_URL"
      echo "└─────────────────────────────────────────────────────────────────────────┘"
    fi
    
    show_menu
    
    read -r -p "Enter selection [0-7]: " choice
    
    case $choice in
      1) view_pending_requests ;;
      2) approve_request ;;
      3) deny_request ;;
      4) view_users ;;
      5) create_admin_interactive ;;
      6) login_admin_interactive ;;
      7) logout ;;
      0) 
        echo ""
        print_status "info" "Thank you for using Melvin Account Management."
        echo ""
        exit 0
        ;;
      *)
        print_status "error" "Invalid selection. Please try again."
        sleep 1
        ;;
    esac
  done
}

# CLI mode functions
view_pending_requests_cli() {
  # Check if we have authentication token - if not, try to get it
  if [[ -z "$ADMIN_TOKEN" ]]; then
    echo "Authentication required to view pending requests."
    echo ""
    login_admin_interactive
    if [[ -z "$ADMIN_TOKEN" ]]; then
      echo "Error: Authentication failed."
      exit 1
    fi
  fi
  
  local response
  response=$(curl -fsS -X GET "$API_URL/api/auth/requests" \
    -H "Authorization: Bearer $ADMIN_TOKEN" 2>/dev/null || echo "")
  
  if [[ -z "$response" ]] || [[ "$response" == "[]" ]]; then
    echo "No pending account requests."
    return
  fi
  
  echo "$response" | jq -r '.[] | "[\(.id)] \(.username) - \(.status)"' 2>/dev/null || echo "$response"
}

approve_request_cli() {
  local request_id="$1"
  
  if [[ -z "$request_id" ]]; then
    echo "Error: Request ID required"
    exit 1
  fi
  
  # Check authentication - if not, try to get it
  if [[ -z "$ADMIN_TOKEN" ]]; then
    echo "Authentication required to approve requests."
    echo ""
    login_admin_interactive
    if [[ -z "$ADMIN_TOKEN" ]]; then
      echo "Error: Authentication failed."
      exit 1
    fi
  fi
  
  local response
  response=$(curl -fsS -X POST "$API_URL/api/auth/requests/$request_id/approve" \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d "{}" 2>/dev/null || echo "")
  
  if [[ -z "$response" ]]; then
    echo "Error: Failed to approve request"
    exit 1
  fi
  
  echo "$response" | jq . 2>/dev/null || echo "Request approved: $response"
}

deny_request_cli() {
  local request_id="$1"
  
  if [[ -z "$request_id" ]]; then
    echo "Error: Request ID required"
    exit 1
  fi
  
  # Check authentication - if not, try to get it
  if [[ -z "$ADMIN_TOKEN" ]]; then
    echo "Authentication required to deny requests."
    echo ""
    login_admin_interactive
    if [[ -z "$ADMIN_TOKEN" ]]; then
      echo "Error: Authentication failed."
      exit 1
    fi
  fi
  
  local response
  response=$(curl -fsS -X POST "$API_URL/api/auth/requests/$request_id/deny" \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d "{}" 2>/dev/null || echo "")
  
  if [[ -z "$response" ]]; then
    echo "Error: Failed to deny request"
    exit 1
  fi
  
  echo "$response" | jq . 2>/dev/null || echo "Request denied: $response"
}

view_users_cli() {
  echo "Users endpoint not implemented in API. Check database directly:"
  echo "docker-compose exec postgres psql -U melvin -d melvin -c \"SELECT username, created_at FROM users;\""
}

create_admin_interactive() {
  print_section "CREATE NEW ADMIN ACCOUNT"
  
  read -r -p "New admin username: " new_admin_user
  read -r -s -p "New admin password: " new_admin_pass
  echo ""
  read -r -s -p "Confirm password: " new_admin_pass_confirm
  echo ""
  
  if [[ "$new_admin_pass" != "$new_admin_pass_confirm" ]]; then
    print_status "error" "Passwords do not match."
    pause_screen
    return
  fi
  
  if [[ ${#new_admin_pass} -lt 8 ]]; then
    print_status "error" "Password must be at least 8 characters."
    pause_screen
    return
  fi
  
  print_status "info" "Creating admin account..."
  
  local response
  response=$(curl -fsS -X POST "$API_URL/api/auth/bootstrap" \
    -H "Content-Type: application/json" \
    -d "{\"username\": \"$new_admin_user\", \"password\": \"$new_admin_pass\"}" 2>/dev/null || echo "")
  
  if [[ -z "$response" ]] || [[ "$response" == "null" ]]; then
    print_status "success" "Admin account created successfully! Username: $new_admin_user"
  else
    print_status "error" "Failed to create admin account. Response: $response"
  fi
  
  pause_screen
}

login_admin_interactive() {
  print_section "ADMIN LOGIN"
  read -r -p "Username: " username
  read -r -s -p "Password: " password
  echo ""
  
  print_status "info" "Authenticating..."
  
  local response
  response=$(curl -fsS -X POST "$API_URL/api/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"username\": \"$username\", \"password\": \"$password\"}" 2>/dev/null || echo "")
  
  if [[ -z "$response" ]]; then
    print_status "error" "Connection failed. Is the API running?"
    return 1
  fi
  
  ADMIN_TOKEN=$(echo "$response" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
  
  if [[ -z "$ADMIN_TOKEN" ]]; then
    print_status "error" "Authentication failed. Invalid credentials."
    return 1
  fi
  
  ADMIN_USER="$username"
  print_status "success" "Login successful! Welcome, $username."
  # Only pause if stdin is a terminal (interactive mode)
  if [[ -t 0 ]]; then
    pause_screen
  fi
}

# Run main
main "$@"
