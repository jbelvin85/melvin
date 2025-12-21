#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)"
DATA_DIR="$REPO_ROOT/data"
PROCESSED_DIR="$DATA_DIR/processed"
ENV_FILE="$REPO_ROOT/.env"
FRONTEND_DIR="$REPO_ROOT/frontend"
FRONTEND_DIST="$FRONTEND_DIR/dist"

ensure_env() {
  if [[ ! -f "$ENV_FILE" ]]; then
    echo "[melvin] Creating .env from template"
    cp "$REPO_ROOT/.env.example" "$ENV_FILE"
  fi
}

ensure_dirs() {
  mkdir -p "$PROCESSED_DIR"
  mkdir -p "$REPO_ROOT/backups"
}

set_env_var() {
  local key="$1"
  local value="$2"
  python3 <<PY
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
  }
  set_env_var "FRONTEND_DIST" "/app/frontend/dist"
  echo "[melvin] .env ready."
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
  require_cmd docker
  require_cmd npm
  require_cmd curl
  configure_env
  ensure_dirs
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
  require_cmd docker
  require_cmd npm
  ensure_env
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
  launch      Interactive setup + build + start stack, then print access link
  dev         Run docker compose stack in foreground (rebuild frontend)
  down        Stop docker compose stack
  logs [svc]  Tail logs (optional service filter)
  backup      Dump Postgres and Mongo backups into ./backups
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
require_cmd() {
  local cmd="$1"
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "[melvin] Required command '$cmd' not found. Please install it."
    exit 1
  fi
}
