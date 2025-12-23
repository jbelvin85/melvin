#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)"
DATA_DIR="$REPO_ROOT/data"
RAW_DATA_DIR="$DATA_DIR/raw"
PROCESSED_DIR="$DATA_DIR/processed"
ENV_FILE="$REPO_ROOT/.env"
FRONTEND_DIR="$REPO_ROOT/frontend"
API_URL="http://localhost:8001"
REQUIRED_DATA_FILES=(
  "MagicCompRules 20251114.txt"
  "oracle-cards-20251221100301.json"
  "rulings-20251221100031.json"
)

ensure_env() {
  if [[ ! -f "$ENV_FILE" ]]; then
    echo "[melvin] Creating .env from template"
    cp "$REPO_ROOT/.env.example" "$ENV_FILE"
  fi
}

ensure_dirs() {
  mkdir -p "$RAW_DATA_DIR" "$PROCESSED_DIR" "$REPO_ROOT/backups"
}

require_cmd() {
  local cmd="$1"
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "[melvin] Required command '$cmd' not found. Aborting."
    exit 1
  fi
}

set_env_var() {
  local key="$1"
  local value="$2"
  python3 - "$key" "$value" <<'PY'
import os
import sys

env_file = os.environ["ENV_FILE_PATH"]
key = sys.argv[1]
value = sys.argv[2]
lines = []
found = False
if os.path.exists(env_file):
    with open(env_file, "r", encoding="utf-8") as handle:
        for line in handle:
            if line.startswith(f"{key}="):
                lines.append(f"{key}={value}\n")
                found = True
            else:
                lines.append(line)
else:
    lines = []
if not found:
    lines.append(f"{key}={value}\n")
with open(env_file, "w", encoding="utf-8") as handle:
    handle.writelines(lines)
PY
}

get_env_var() {
  local key="$1"
  python3 <<PY
import os
env = os.environ.get("ENV_FILE_PATH")
key = "$1"
if env and os.path.exists(env):
    with open(env, "r", encoding="utf-8") as handle:
        for line in handle:
            if line.startswith(f"{key}="):
                print(line.split("=", 1)[1].strip())
                break
PY
}

read_secret() {
  if command -v openssl >/dev/null 2>&1; then
    openssl rand -hex 32
  else
    python3 - <<'PY'
import secrets
print(secrets.token_hex(32))
PY
  fi
}

prompt_credentials() {
  read -r -p "Admin username [admin]: " admin_user
  admin_user="${admin_user:-admin}"
  while true; do
    read -r -s -p "Admin password (min 8 chars w/ upper/lower/number/symbol): " admin_pass
    echo
    read -r -s -p "Confirm admin password: " admin_confirm
    echo
    if [[ "$admin_pass" != "$admin_confirm" ]]; then
      echo "Passwords do not match."
      continue
    fi
    if [[ ${#admin_pass} -lt 8 ]]; then
      echo "Password too short."
      continue
    fi
    break
  done
  export INITIAL_ADMIN_USERNAME_VALUE="$admin_user"
  export INITIAL_ADMIN_PASSWORD_VALUE="$admin_pass"
}

configure_env() {
  ensure_env
  export ENV_FILE_PATH="$ENV_FILE"
  local current_secret
  current_secret="$(get_env_var "SECRET_KEY" || true)"
  if [[ -z "$current_secret" ]]; then
    set_env_var "SECRET_KEY" "$(read_secret)"
  fi
  local current_admin
  current_admin="$(get_env_var "INITIAL_ADMIN_USERNAME" || true)"
  if [[ -z "$current_admin" ]]; then
    prompt_credentials
    set_env_var "INITIAL_ADMIN_USERNAME" "$INITIAL_ADMIN_USERNAME_VALUE"
    set_env_var "INITIAL_ADMIN_PASSWORD" "$INITIAL_ADMIN_PASSWORD_VALUE"
  else
    export INITIAL_ADMIN_USERNAME_VALUE="$current_admin"
    export INITIAL_ADMIN_PASSWORD_VALUE="$(get_env_var "INITIAL_ADMIN_PASSWORD")"
  fi
  set_env_var "FRONTEND_DIST" "/app/frontend/dist"
  echo "[melvin] .env ready."
}

find_existing_data_file() {
  local filename="$1"
  local candidates=(
    "$RAW_DATA_DIR/$filename"
    "/data/raw/$filename"
    "$HOME/data/raw/$filename"
    "$REPO_ROOT/$filename"
  )
  for candidate in "${candidates[@]}"; do
    if [[ -f "$candidate" ]]; then
      echo "$candidate"
      return 0
    fi
  done
  return 1
}

bulk_type_for_filename() {
  case "$1" in
    oracle-cards*) echo "oracle_cards" ;;
    rulings*) echo "rulings" ;;
    *) echo "" ;;
  esac
}

download_scryfall_bulk() {
  local bulk_type="$1"
  local destination="$2"
  python3 - "$bulk_type" "$destination" <<'PY'
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

bulk_type = sys.argv[1]
destination = Path(sys.argv[2])

try:
    with urllib.request.urlopen("https://api.scryfall.com/bulk-data", timeout=60) as resp:
        metadata = json.load(resp)
except urllib.error.URLError as exc:
    print(f"[melvin] Failed to reach Scryfall: {exc}", file=sys.stderr)
    sys.exit(1)

entries = metadata.get("data", [])
match = next((entry for entry in entries if entry.get("type") == bulk_type), None)
if match is None:
    print(f"[melvin] Bulk type '{bulk_type}' not found.", file=sys.stderr)
    sys.exit(1)

download_uri = match.get("download_uri")
if not download_uri:
    print(f"[melvin] No download URI for '{bulk_type}'.", file=sys.stderr)
    sys.exit(1)

print(f"[melvin] Downloading '{bulk_type}' from {download_uri}")
try:
    with urllib.request.urlopen(download_uri, timeout=600) as resp, open(destination, "wb") as handle:
        handle.write(resp.read())
except urllib.error.URLError as exc:
    print(f"[melvin] Download failed: {exc}", file=sys.stderr)
    sys.exit(1)

print(f"[melvin] Saved '{bulk_type}' to {destination}")
PY
}

ensure_data_files() {
  ensure_dirs
  for filename in "${REQUIRED_DATA_FILES[@]}"; do
    local target="$RAW_DATA_DIR/$filename"
    if [[ -f "$target" ]]; then
      continue
    fi
    local existing
    existing="$(find_existing_data_file "$filename" || true)"
    if [[ -n "$existing" && "$existing" != "$target" ]]; then
      cp "$existing" "$target"
      echo "[melvin] Copied '$filename' from '$existing'."
      continue
    fi
    local bulk_type
    bulk_type="$(bulk_type_for_filename "$filename")"
    if [[ -n "$bulk_type" ]]; then
      echo "[melvin] Attempting automatic download of '$filename'."
      if download_scryfall_bulk "$bulk_type" "$target"; then
        continue
      else
        echo "[melvin] Automatic download failed for '$filename'."
      fi
    fi
    echo "[melvin] Please provide a path to '$filename'."
    while [[ ! -f "$target" ]]; do
      read -r -p "Path: " source_path
      if [[ -z "$source_path" ]]; then
        echo "Path is required."
        continue
      fi
      if [[ ! -f "$source_path" ]]; then
        echo "File not found at '$source_path'."
        continue
      fi
      cp "$source_path" "$target"
      echo "[melvin] Copied '$filename'."
    done
  done
}

ensure_frontend_dependencies() {
  if [[ -f "$FRONTEND_DIR/package.json" ]]; then
    (cd "$FRONTEND_DIR" && npm install)
  fi
}

build_frontend() {
  if [[ -f "$FRONTEND_DIR/package.json" ]]; then
    ensure_frontend_dependencies
    (cd "$FRONTEND_DIR" && npm run build)
  fi
}

wait_for_api() {
  local retries=120
  local delay=2
  for ((i=1; i<=retries; i++)); do
    if curl -fsS "$API_URL/api/health" >/dev/null 2>&1; then
      echo "[melvin] API is healthy"
      return 0
    fi
    if ((i % 10 == 0)); then
      echo "[melvin] Waiting for API to become healthy... ($i/$retries attempts, ~$((i*delay))s elapsed)"
    fi
    sleep "$delay"
  done
  return 1
}

create_admin_account() {
  local username="$1"
  local password="$2"
  local payload="{\"username\": \"$username\", \"password\": \"$password\"}"
  curl -fsS -X POST \
    -H "Content-Type: application/json" \
    -d "$payload" \
    "$API_URL/api/auth/bootstrap" >/dev/null 2>&1 || true
}

confirm() {
  local prompt="$1"
  local response
  read -r -p "$prompt (y/n): " response
  [[ "$response" =~ ^[yY]$ ]]
}

check_and_install_docker() {
  if command -v docker >/dev/null 2>&1; then
    return 0
  fi
  echo "[melvin] Docker missing. Attempting installation..."
  if command -v apt-get >/dev/null 2>&1; then
    sudo apt-get update && sudo apt-get install -y docker.io docker-compose-plugin
  elif command -v brew >/dev/null 2>&1; then
    brew install docker docker-compose
  else
    echo "[melvin] Please install Docker manually."
    exit 1
  fi
}

check_and_install_nodejs() {
  if command -v node >/dev/null 2>&1 && command -v npm >/dev/null 2>&1; then
    return 0
  fi
  echo "[melvin] Node.js/npm missing. Attempting installation..."
  if command -v apt-get >/dev/null 2>&1; then
    sudo apt-get update && sudo apt-get install -y nodejs npm
  elif command -v brew >/dev/null 2>&1; then
    brew install node
  else
    echo "[melvin] Please install Node.js + npm manually."
    exit 1
  fi
}

check_and_install_python() {
  if command -v python3 >/dev/null 2>&1; then
    return 0
  fi
  echo "[melvin] Python 3 missing. Attempting installation..."
  if command -v apt-get >/dev/null 2>&1; then
    sudo apt-get update && sudo apt-get install -y python3 python3-pip python3-venv
  elif command -v brew >/dev/null 2>&1; then
    brew install python3
  else
    echo "[melvin] Please install Python 3 manually."
    exit 1
  fi
}

check_dependencies() {
  check_and_install_docker
  check_and_install_nodejs
  check_and_install_python
  require_cmd curl
}

cmd_launch_bg() {
  check_dependencies
  configure_env
  ensure_dirs
  ensure_data_files
  build_frontend
  docker compose up --build -d
  if wait_for_api; then
    create_admin_account "$INITIAL_ADMIN_USERNAME_VALUE" "$INITIAL_ADMIN_PASSWORD_VALUE"
    echo "[melvin] Melvin is running!"
    echo "Visit $API_URL to request an account or log in."
    echo "Admin login: ${INITIAL_ADMIN_USERNAME_VALUE}"
  else
    echo "[melvin] API did not become healthy in time. Check logs via './scripts/melvin.sh logs api'"
    exit 1
  fi
}

cmd_launch_fg() {
  check_dependencies
  configure_env
  ensure_dirs
  ensure_data_files
  build_frontend
  echo "[melvin] Starting services in foreground (Ctrl+C to stop)..."
  docker compose up --build &
  local compose_pid=$!
  if wait_for_api; then
    create_admin_account "$INITIAL_ADMIN_USERNAME_VALUE" "$INITIAL_ADMIN_PASSWORD_VALUE"
    echo "[melvin] ✓ Melvin is running at $API_URL"
  else
    echo "[melvin] API did not become healthy in time."
  fi
  wait "$compose_pid"
}

cmd_dev() {
  check_dependencies
  configure_env
  ensure_dirs
  ensure_data_files
  build_frontend
  docker compose up --build
}

cmd_down() {
  if confirm "[melvin] Stop docker compose stack?"; then
    docker compose down
    echo "[melvin] Stack stopped."
  else
    echo "[melvin] Cancelled."
  fi
}

cmd_logs() {
  docker compose logs -f "$@"
}

cmd_backup() {
  if ! confirm "[melvin] Create backups of Postgres and MongoDB?"; then
    echo "[melvin] Cancelled."
    return
  fi
  ensure_dirs
  local ts="$(date +%Y%m%d-%H%M%S)"
  local backup_root="$REPO_ROOT/backups/$ts"
  mkdir -p "$backup_root"
  echo "[melvin] Running Postgres backup"
  docker compose exec -T postgres pg_dump -U melvin -d melvin > "$backup_root/postgres.sql" || echo "[melvin] Postgres backup failed"
  echo "[melvin] Running MongoDB backup"
  docker compose exec mongo mongodump --archive="/tmp/mongo-$ts.archive"
  docker compose cp mongo:/tmp/mongo-$ts.archive "$backup_root/mongo.archive"
  echo "[melvin] Backups stored in $backup_root"
}

cmd_add_redis_service() {
  if grep -q "^[[:space:]]*redis:" "$REPO_ROOT/docker-compose.yml"; then
    echo "[melvin] docker-compose already defines a redis service."
    return
  fi
  python3 - "$REPO_ROOT/docker-compose.yml" <<'PY'
import sys
from pathlib import Path

path = Path(sys.argv[1])
text = path.read_text()
service_snippet = """
  redis:
    image: redis:7
    restart: unless-stopped
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
"""

if "  redis:" not in text:
    if "\nvolumes:" in text:
        text = text.replace("\nvolumes:", f"\n{service_snippet}\nvolumes:", 1)
    else:
        text += f"\n{service_snippet}\nvolumes:\n"

if "  redis_data:" not in text:
    if "  ollama_data:" in text:
        text = text.replace("  ollama_data:\n", "  ollama_data:\n  redis_data:\n", 1)
    elif "\nvolumes:\n" in text:
        text = text.replace("\nvolumes:\n", "\nvolumes:\n  redis_data:\n", 1)
    else:
        text += "\nvolumes:\n  redis_data:\n"

path.write_text(text)
PY
  echo "[melvin] Added redis service to docker-compose.yml."
}

cmd_enable_redis() {
  ensure_env
  export ENV_FILE_PATH="$ENV_FILE"
  set_env_var "REDIS_URL" "redis://redis:6379/0"
  echo "[melvin] REDIS_URL set to redis://redis:6379/0"
  cmd_add_redis_service
  docker compose up -d redis || echo "[melvin] Failed to start redis"
}

cmd_migrate() {
  require_cmd docker
  docker compose exec -T api alembic upgrade head || echo "[melvin] Alembic migration failed"
}

cmd_eval() {
  require_cmd docker
  docker compose exec -T api python -u scripts/evaluate.py || echo "[melvin] Evaluation script failed"
}

cmd_accounts() {
  local script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  "$script_dir/manage_accounts.sh"
}

cmd_ui() {
  while true; do
    cat <<MENU

Melvin management UI
1) Launch (background)
2) Launch (foreground)
3) Dev (foreground, rebuild frontend)
4) Stop stack
5) Tail logs
6) Backup databases
7) Enable Redis service
8) Run DB migrations
9) Run evaluation harness
10) Check dependencies
11) Add redis service to docker-compose.yml
0) Exit
MENU
    read -r -p "Select an option: " choice
    case "$choice" in
      1) cmd_launch_bg ;;
      2) cmd_launch_fg ;;
      3) cmd_dev ;;
      4) cmd_down ;;
      5) read -r -p "Service (blank=all): " svc; cmd_logs "$svc" ;;
      6) cmd_backup ;;
      7) cmd_enable_redis ;;
      8) cmd_migrate ;;
      9) cmd_eval ;;
      10) check_dependencies ;;
      11) cmd_add_redis_service ;;
      0) exit 0 ;;
      *) echo "Invalid choice" ;;
    esac
  done
}

usage() {
  cat <<USAGE
Usage: scripts/melvin.sh <command>
  launch         Interactive setup + build + start stack (background)
  launch-fg      Same as launch but keeps docker compose in foreground
  dev            Run docker compose up with rebuilds in foreground
  down           Stop docker compose stack
  logs [svc]     Tail logs (optional service filter)
  backup         Backup Postgres and MongoDB data
  enable-redis   Configure REDIS_URL and start redis service
  add-redis-service  Append redis service definition to docker-compose.yml
  migrate        Run Alembic migrations inside api container
  eval           Run evaluation harness inside api container
  check-deps     Check/install Docker, Node.js, Python, curl
  accounts       Retro-style account management CLI (view/approve/deny requests)
  cli            Comprehensive management interface (RECOMMENDED - tabbed UI)
  ui             Interactive text UI
USAGE
}

command="${1:-launch}"
shift || true

case "$command" in
  launch) cmd_launch_bg ;;
  launch-bg) cmd_launch_bg ;;
  launch-fg) cmd_launch_fg ;;
  dev) cmd_dev ;;
  down) cmd_down ;;
  logs) cmd_logs "$@" ;;
  backup) cmd_backup ;;
  enable-redis) cmd_enable_redis ;;
  add-redis-service) cmd_add_redis_service ;;
  migrate) cmd_migrate ;;
  eval) cmd_eval ;;
  check-deps) check_dependencies ;;
  accounts) cmd_accounts ;;
  cli) bash "$REPO_ROOT/scripts/melvin_cli.sh" ;;
  ui) cmd_ui ;;
  *) usage; exit 1 ;;
esac
