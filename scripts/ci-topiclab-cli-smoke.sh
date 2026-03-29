#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

CLI_SOURCE=""

usage() {
  cat <<EOF
Usage: $(basename "$0") --cli-source <package|submodule>
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --cli-source)
      CLI_SOURCE="${2:-}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

if [[ "$CLI_SOURCE" != "package" && "$CLI_SOURCE" != "submodule" ]]; then
  echo "Missing or invalid --cli-source. Expected package or submodule." >&2
  exit 1
fi

TMP_ENV_DIR="$(mktemp -d "${TMPDIR:-/tmp}/topiclab-cli-ci.XXXXXX")"
TMP_ENV_FILE="$TMP_ENV_DIR/topiclab-cli-ci.env"
cp .env.example "$TMP_ENV_FILE"
cat >>"$TMP_ENV_FILE" <<'EOF'
ANTHROPIC_API_KEY=test
AI_GENERATION_BASE_URL=https://example.com
AI_GENERATION_API_KEY=test
AI_GENERATION_MODEL=test-model
CONTENT_MODERATION_ENABLED=false
DATABASE_URL=sqlite:////app/workspace/topiclab-ci.sqlite
REGISTER_SKIP_SMS_UNTIL=2099-01-01T00:00:00+08:00
EOF

export TOPICLAB_BACKEND_PORT=8001
export BACKEND_PORT=8000

cleanup_compose() {
  ENV_FILE="$TMP_ENV_FILE" docker compose --env-file "$TMP_ENV_FILE" down -v --remove-orphans >/dev/null 2>&1 || true
}

cleanup() {
  cleanup_compose
  rm -f "$TMP_ENV_FILE"
  rm -rf "$TMP_ENV_DIR"
  if [[ -n "${TOPICLAB_CLI_HOME:-}" && -d "${TOPICLAB_CLI_HOME:-}" ]]; then
    rm -rf "$TOPICLAB_CLI_HOME"
  fi
}
trap cleanup EXIT

wait_for_health() {
  local url="$1"
  local label="$2"
  local attempts="${3:-60}"
  for ((i = 1; i <= attempts; i++)); do
    if curl --fail --silent --show-error "$url" >/dev/null 2>&1; then
      echo "[ci-smoke] $label is healthy at $url"
      return 0
    fi
    sleep 2
  done
  echo "[ci-smoke] $label failed health check at $url" >&2
  return 1
}

echo "[ci-smoke] starting services for $CLI_SOURCE"
ENV_FILE="$TMP_ENV_FILE" docker compose --env-file "$TMP_ENV_FILE" up -d --build --force-recreate topiclab-backend backend
wait_for_health "http://127.0.0.1:${TOPICLAB_BACKEND_PORT}/health" "topiclab-backend"
wait_for_health "http://127.0.0.1:${BACKEND_PORT}/health" "backend"

case "$CLI_SOURCE" in
  package)
    echo "[ci-smoke] installing published topiclab-cli package"
    npm install -g topiclab-cli@latest
    TOPICLAB_CLI_BIN="topiclab"
    TOPICLAB_CLI_PREFIX_JSON="[]"
    npm list -g topiclab-cli --depth=0 || true
    ;;
  submodule)
    echo "[ci-smoke] building submodule topiclab-cli"
    pushd topiclab-cli >/dev/null
    npm ci
    npm run build
    popd >/dev/null
    TOPICLAB_CLI_BIN="node"
    TOPICLAB_CLI_PREFIX_JSON="[\"$ROOT_DIR/topiclab-cli/dist/cli.js\"]"
    node -p "require('./topiclab-cli/package.json').version"
    git -C topiclab-cli rev-parse HEAD
    ;;
esac

export TOPICLAB_BASE_URL="http://127.0.0.1:${TOPICLAB_BACKEND_PORT}"
export TOPICLAB_CLI_BIN
export TOPICLAB_CLI_PREFIX_JSON
export TOPICLAB_CLI_HOME="$(mktemp -d "${TMPDIR:-/tmp}/topiclab-cli-ci-home.XXXXXX")"
export TOPICLAB_SMOKE_SKIP_MEDIA_UPLOAD="${TOPICLAB_SMOKE_SKIP_MEDIA_UPLOAD:-0}"

node scripts/topiclab-cli-protocol-smoke.mjs
