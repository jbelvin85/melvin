#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)"
DATA_DIR="$REPO_ROOT/data"
RAW_DATA_DIR="$DATA_DIR/raw"
PROCESSED_DIR="$DATA_DIR/processed"
ENV_FILE="$REPO_ROOT/.env"
FRONTEND_DIR="$REPO_ROOT/frontend"
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
    echo "[melvin] Required command '$cmd' not found. Please install it."
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
  local secret
  secret="$(get_env_var "SECRET_KEY" || true)"
  if [[ -z "$secret" ]]; then
    set_env_var "SECRET_KEY" "$(read_secret)"
  fi
  local admin_username
  admin_username="$(get_env_var "INITIAL_ADMIN_USERNAME" || true)"
  if [[ -z "$admin_username" ]]; then
    prompt_credentials
    set_env_var "INITIAL_ADMIN_USERNAME" "$INITIAL_ADMIN_USERNAME_VALUE"
    set_env_var "INITIAL_ADMIN_PASSWORD" "$INITIAL_ADMIN_PASSWORD_VALUE"
  else
    export INITIAL_ADMIN_USERNAME_VALUE="$admin_username"
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
    print(f"[melvin] Failed to reach Scryfall bulk endpoint: {exc}", file=sys.stderr)
    sys.exit(1)

entries = metadata.get("data", [])
match = next((item for item in entries if item.get("type") == bulk_type), None)
if match is None:
    print(f"[melvin] Bulk data type '{bulk_type}' not found.", file=sys.stderr)
    sys.exit(1)

url = match.get("download_uri")
if not url:
    print(f"[melvin] Download URI missing for '{bulk_type}'.", file=sys.stderr)
    sys.exit(1)

print(f"[melvin] Downloading '{bulk_type}' from {url}")
try:
    with urllib.request.urlopen(url, timeout=600) as resp, open(destination, "wb") as handle:
        handle.write(resp.read())
except urllib.error.URLError as exc:
    print(f"[melvin] Failed to download '{bulk_type}': {exc}", file=sys.stderr)
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
      echo "[melvin] Attempting automatic download for '$filename'."
      if download_scryfall_bulk "$bulk_type" "$target"; then
        continue
      fi
    fi
    echo "[melvin] Please provide path to '$filename'."
    while [[ ! -f "$target" ]]; do
      read -r -p "File path: " source_path
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
  local retries=20
  local delay=3
  for ((i=1; i<=retries; i++)); do
    if curl -fsS http://localhost:8001/api/health >/dev/null 2>&1; then
      return 0
    fi
    sleep "$delay"
  done
  return 1
}

create_admin_account() {
  local username="$1"
  local password="$2"
  local payload="{\"username\": \"$username\", \"password\": \"$password\"}"
  echo "[melvin] Ensuring admin account exists..."
  curl -fsS -X POST \
    -H "Content-Type: application/json" \
    -d "$payload" \
    http://localhost:8001/api/auth/bootstrap || true
}

cmd_launch() {
  require_cmd docker
  require_cmd npm
  require_cmd node
  require_cmd python3
  require_cmd curl
  configure_env
  ensure_dirs
  ensure_data_files
  build_frontend
  docker compose up --build -d
  if wait_for_api; then
    create_admin_account "$INITIAL_ADMIN_USERNAME_VALUE" "$INITIAL_ADMIN_PASSWORD_VALUE"
    echo "[melvin] Melvin is running!"
    echo "Visit http://localhost:8001 to request an account or log in."
    echo "Admin login: ${INITIAL_ADMIN_USERNAME_VALUE}"
  else
    echo "[melvin] API did not become healthy in time. Check logs via './scripts/melvin.sh logs api'"
    exit 1
  fi
}

cmd_dev() {
  require_cmd docker
  configure_env
  ensure_dirs
  ensure_data_files
  build_frontend
  docker compose up --build
}

cmd_down() {
  docker compose down
}

cmd_logs() {
  docker compose logs -f "$@"
}

cmd_backup() {
  require_cmd docker
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

usage() {
  cat <<USAGE
Usage: scripts/melvin.sh <command>
  launch       Interactive setup + build + start stack
  dev          Run docker compose stack in foreground (rebuild frontend)
  down         Stop docker compose stack
  logs [svc]   Tail logs (optional service filter)
  backup       Dump Postgres and Mongo backups into ./backups
USAGE
}

command="${1:-launch}"
shift || true

case "$command" in
  launch) cmd_launch ;;
  dev) cmd_dev ;;
  down) cmd_down ;;
  logs) cmd_logs "$@" ;;
  backup) cmd_backup ;;
  *) usage; exit 1 ;;
esac
