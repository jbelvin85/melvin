#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)"
DATA_DIR="$REPO_ROOT/data"
RAW_DATA_DIR="$DATA_DIR/raw"
PROCESSED_DIR="$DATA_DIR/processed"
ENV_FILE="$REPO_ROOT/.env"
FRONTEND_DIR="$REPO_ROOT/frontend"
FRONTEND_DIST="$FRONTEND_DIR/dist"
REQUIRED_DATA_FILES=("MagicCompRules 20251114.txt" "oracle-cards-20251221100301.json" "rulings-20251221100031.json")

ensure_env() {
  if [[ ! -f "$ENV_FILE" ]]; then
    echo "[melvin] Creating .env from template"
    cp "$REPO_ROOT/.env.example" "$ENV_FILE"
  fi
    check_and_install_docker

ensure_dirs() {
  mkdir -p "$PROCESSED_DIR"
  mkdir -p "$RAW_DATA_DIR"
  mkdir -p "$REPO_ROOT/backups"
    check_and_install_docker

find_existing_data_file() {
  local filename="$1"

  cmd_launch_bg() {
    check_dependencies
    configure_env
    ensure_dirs
    ensure_data_files
    build_frontend
    echo "[melvin] Starting Melvin in background..."
    docker compose up --build -d
    echo "[melvin] Services started in background. Waiting for API..."
    if wait_for_api; then
      echo "[melvin] ✓ Melvin is running!"
      echo "Visit http://localhost:8000 to request an account or log in."
      echo "Admin login: ${INITIAL_ADMIN_USERNAME_VALUE}"
    else
      echo "[melvin] API did not become healthy in time. Check logs via './scripts/melvin.sh logs api'"
      exit 1
    fi
  }
  local candidates=(
    "$RAW_DATA_DIR/$filename"
    "/data/raw/$filename"
    "$HOME/data/raw/$filename"
    "$REPO_ROOT/$filename"
      echo "1) Launch (build & start, background)"
      echo "1b) Launch (foreground) [slow, for debugging]"
      echo "2) Dev (foreground, rebuild frontend)"
    if [[ -f "$candidate" ]]; then
      echo "$candidate"
      return 0
    fi
  done
  return 1
}
      echo "10) Check dependencies"

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
    print(f"[melvin] Failed to reach Scryfall bulk endpoint: {exc}", file=sys.stderr)
    sys.exit(1)

entries = metadata.get("data", [])
match = next((item for item in entries if item.get("type") == bulk_type), None)
if match is None:
    print(f"[melvin] Bulk data type '{bulk_type}' not found in Scryfall response.", file=sys.stderr)
    sys.exit(1)

download_url = match.get("download_uri")
if not download_url:
    print(f"[melvin] Download URI missing for bulk type '{bulk_type}'.", file=sys.stderr)
    sys.exit(1)

print(f"[melvin] Downloading '{bulk_type}' from {download_url}")
try:
    with urllib.request.urlopen(download_url, timeout=600) as resp, open(destination, "wb") as handle:
        handle.write(resp.read())
except urllib.error.URLError as exc:
    print(f"[melvin] Failed to download bulk data '{bulk_type}': {exc}", file=sys.stderr)
    sys.exit(1)

print(f"[melvin] Saved '{bulk_type}' bulk data to {destination}")
PY
}

bulk_type_for_filename() {
  local filename="$1"
  case "$filename" in
    oracle-cards*) echo "oracle_cards" ;;
    rulings*) echo "rulings" ;;
    *) echo "" ;;
  esac
}

require_cmd() {
  local cmd="$1"
  if ! command -v "$cmd" >/dev/null 2>&1; then
        1b) cmd_launch ;;
    return 1
  fi
  return 0
}

check_and_install_docker() {
  if require_cmd docker; then
    echo "[melvin] Docker is installed: $(docker --version)"
        10) check_dependencies ;;
    return 0
  fi
  echo "[melvin] Docker not found. Installing Docker..."
  if command -v apt-get >/dev/null 2>&1; then
    sudo apt-get update && sudo apt-get install -y docker.io docker-compose
    echo "[melvin] Docker installed via apt."
  elif command -v brew >/dev/null 2>&1; then
    brew install docker docker-compose
    echo "[melvin] Docker installed via Homebrew."
  else
    echo "[melvin] Could not auto-install Docker. Please visit https://docs.docker.com/get-docker/"
    exit 1
  fi
}

check_and_install_nodejs() {
  if require_cmd node && require_cmd npm; then
    echo "[melvin] Node.js is installed: $(node --version), npm: $(npm --version)"
    return 0
  fi
  echo "[melvin] Node.js/npm not found. Installing..."
  if command -v apt-get >/dev/null 2>&1; then
    sudo apt-get update && sudo apt-get install -y nodejs npm
    echo "[melvin] Node.js/npm installed via apt."
  elif command -v brew >/dev/null 2>&1; then
    brew install node
    echo "[melvin] Node.js/npm installed via Homebrew."
  else
    echo "[melvin] Could not auto-install Node.js. Please visit https://nodejs.org/"
    exit 1
  fi
}

check_and_install_python() {
  if require_cmd python3; then
    echo "[melvin] Python 3 is installed: $(python3 --version)"
    return 0
  fi
  echo "[melvin] Python 3 not found. Installing..."
  if command -v apt-get >/dev/null 2>&1; then
    sudo apt-get update && sudo apt-get install -y python3 python3-pip python3-venv
    echo "[melvin] Python 3 installed via apt."
  elif command -v brew >/dev/null 2>&1; then
    brew install python3
    echo "[melvin] Python 3 installed via Homebrew."
  else
    echo "[melvin] Could not auto-install Python 3. Please visit https://www.python.org/"
    exit 1
  fi
}

check_dependencies() {
  echo "[melvin] Checking dependencies..."
  check_and_install_docker
  check_and_install_nodejs
  check_and_install_python
  require_cmd curl || { echo "[melvin] curl is required."; exit 1; }
  echo "[melvin] All dependencies satisfied."
}

confirm() {
  local prompt="$1"
  local response
  read -r -p "$prompt (y/n): " response
  [[ "$response" =~ ^[yY]$ ]]
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
env = os.environ["ENV_FILE_PATH"]
key = "$1"
if os.path.exists(env):
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
      echo "Passwords do not match. Try again."
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
    local secret
    secret=$(read_secret)
    set_env_var "SECRET_KEY" "$secret"
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

ensure_data_files() {
  ensure_dirs
  for filename in "${REQUIRED_DATA_FILES[@]}"; do
    local target="$RAW_DATA_DIR/$filename"
    if [[ -f "$target" ]]; then
      continue
    fi
    local auto_source
    auto_source="$(find_existing_data_file "$filename" || true)"
    if [[ -n "$auto_source" && "$auto_source" != "$target" ]]; then
      mkdir -p "$(dirname "$target")"
      cp "$auto_source" "$target"
      echo "[melvin] Copied '$filename' from '$auto_source' to '$target'."
      continue
    fi
    local bulk_type
    bulk_type="$(bulk_type_for_filename "$filename")"
    if [[ -n "$bulk_type" ]]; then
      echo "[melvin] Attempting automatic download of '$filename' from Scryfall."
      if download_scryfall_bulk "$bulk_type" "$target"; then
        continue
      else
        echo "[melvin] Automatic download failed for '$filename'."
      fi
    fi
    echo "[melvin] Missing data file: $target"
    while [[ ! -f "$target" ]]; do
      read -r -p "Enter path to '${filename}': " source_path
      if [[ -z "$source_path" ]]; then
        echo "Path is required to proceed."
        continue
      fi
      if [[ ! -f "$source_path" ]]; then
        echo "File not found at '$source_path'."
        continue
      fi
      mkdir -p "$(dirname "$target")"
      cp "$source_path" "$target"
      echo "[melvin] Copied '$filename' into data/raw."
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
  local retries=20
  local delay=3
  for ((i=1; i<=retries; i++)); do
    if curl -fsS http://localhost:8000/api/health >/dev/null 2>&1; then
      return 0
    fi
    sleep "$delay"
  done
  return 1
}

cmd_launch() {
  check_dependencies
  configure_env
  ensure_dirs
  ensure_data_files
  build_frontend
  docker compose up --build -d
  if wait_for_api; then
    echo "[melvin] Melvin is running!"
    echo "Visit http://localhost:8000 to request an account or log in."
    echo "Admin login: ${INITIAL_ADMIN_USERNAME_VALUE}"
  else
    echo "[melvin] API did not become healthy in time. Check logs via './scripts/melvin.sh logs api'"
    exit 1
  fi
}

cmd_dev() {
  check_dependencies
  ensure_env
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
  if confirm "[melvin] Create backups of Postgres and MongoDB?"; then
    :
  else
    echo "[melvin] Cancelled."
    return 0
  fi
  check_and_install_docker
  ensure_dirs
  timestamp="$(date +%Y%m%d-%H%M%S)"
  backup_root="$REPO_ROOT/backups/$timestamp"
  mkdir -p "$backup_root"
  echo "[melvin] Running Postgres backup"
  docker compose exec -T postgres pg_dump -U melvin -d melvin > "$backup_root/postgres.sql" || echo "[melvin] Postgres backup failed"
  echo "[melvin] Running MongoDB backup"
  docker compose exec mongo mongodump --archive="/tmp/mongo-$timestamp.archive"
  docker compose cp mongo:/tmp/mongo-$timestamp.archive "$backup_root/mongo.archive"
  echo "[melvin] Backups stored in $backup_root"
}

usage() {
  cat <<USAGE
Usage: scripts/melvin.sh <command>
  launch            Interactive setup + build + start stack, then print access link
  launch-bg         Interactive setup + build + start stack in background
  dev               Run docker compose stack in foreground (rebuild frontend)
  down              Stop docker compose stack
  logs [svc]        Tail logs (optional service filter)
  backup            Dump Postgres and Mongo backups into ./backups
  enable-redis      Add redis service to docker-compose and enable REDIS_URL in .env
  add-redis-service Append a redis service to docker-compose.yml (idempotent)
  migrate           Run Alembic migrations inside the api container
  eval              Run evaluation harness (scripts/evaluate.py) inside api container
  check-deps        Check and install dependencies (Docker, Node.js, Python)
  ui                Interactive menu-driven UI
USAGE
}

cmd_add_redis_service() {
  # idempotently append a redis service to docker-compose.yml if missing
  if grep -q "^  redis:" "$REPO_ROOT/docker-compose.yml"; then
    echo "[melvin] docker-compose already contains a redis service"
    return 0
  fi
  cat >> "$REPO_ROOT/docker-compose.yml" <<'YAML'
  redis:
    image: redis:7
    restart: unless-stopped
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"

volumes:
  redis_data:
YAML
  echo "[melvin] Added redis service to docker-compose.yml."
}

cmd_enable_redis() {
  ensure_env
  export ENV_FILE_PATH="$ENV_FILE"
  set_env_var "REDIS_URL" "redis://redis:6379/0"
  echo "[melvin] Set REDIS_URL in .env to 'redis://redis:6379/0'"
  cmd_add_redis_service
  echo "[melvin] Starting redis via docker compose..."
  docker compose up -d redis || echo "[melvin] Failed to start redis via docker compose"
}

cmd_migrate() {
  require_cmd docker
  echo "[melvin] Running Alembic migrations (api container)"
  docker compose exec -T api alembic upgrade head || echo "[melvin] Alembic migration failed"
}

cmd_eval() {
  require_cmd docker
  echo "[melvin] Running evaluation harness inside api container"
  docker compose exec -T api python -u scripts/evaluate.py || echo "[melvin] Evaluation script failed"
}

cmd_ui() {
  while true; do
    echo
    echo "Melvin management UI"
    echo "1) Launch (build & start)"
    echo "2) Dev (foreground)"
    echo "3) Stop stack"
    echo "4) Tail logs"
    echo "5) Backup databases"
    echo "6) Enable Redis (add service + set REDIS_URL)"
    echo "7) Run DB migrations"
    echo "8) Run evaluation harness"
    echo "9) Add redis service to docker-compose.yml"
    echo "0) Exit"
    read -r -p "Select an option: " choice
    case "$choice" in
      1) cmd_launch ;;
      2) cmd_dev ;;
      3) cmd_down ;;
      4) read -r -p "Service (leave blank for all): " svc; cmd_logs "$svc" ;;
      5) cmd_backup ;;
      6) cmd_enable_redis ;;
      7) cmd_migrate ;;
      8) cmd_eval ;;
      9) cmd_add_redis_service ;;
      0) exit 0 ;;
      *) echo "Invalid choice" ;;
    esac
  done
}

command="${1:-launch}"
shift || true

case "$command" in
  launch) cmd_launch ;;
  launch-bg) cmd_launch_bg ;;
  dev) cmd_dev ;;
  down) cmd_down ;;
  logs) cmd_logs "$@" ;;
  backup) cmd_backup ;;
  enable-redis) cmd_enable_redis ;;
  add-redis-service) cmd_add_redis_service ;;
  migrate) cmd_migrate ;;
  eval) cmd_eval ;;
  check-deps) check_dependencies ;;
  ui) cmd_ui ;;
  *) usage; exit 1 ;;
esac
