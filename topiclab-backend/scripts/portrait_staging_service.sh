#!/usr/bin/env bash

set -euo pipefail

ACTION="${1:-status}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
STAGING_ROOT="${TOPICLAB_STAGING_ROOT:-$(cd "${REPO_ROOT}/.." && pwd)}"

ENV_FILE="${TOPICLAB_ENV_FILE:-${REPO_ROOT}/.env}"
PYTHON_BIN="${TOPICLAB_PYTHON_BIN:-python3}"
APP_MODULE="${TOPICLAB_APP_MODULE:-main:app}"
HOST="${TOPICLAB_STAGING_HOST:-127.0.0.1}"
PORT="${TOPICLAB_STAGING_PORT:-6006}"
LOG_DIR="${TOPICLAB_LOG_DIR:-${STAGING_ROOT}/logs}"
RUN_DIR="${TOPICLAB_RUN_DIR:-${STAGING_ROOT}/run}"
PID_FILE="${TOPICLAB_PID_FILE:-${RUN_DIR}/topiclab_backend_${PORT}.pid}"
LOG_FILE="${TOPICLAB_LOG_FILE:-${LOG_DIR}/topiclab_backend_${PORT}.log}"
HEALTH_URL="${TOPICLAB_HEALTH_URL:-http://${HOST}:${PORT}/health}"
START_WAIT_SECONDS="${TOPICLAB_START_WAIT_SECONDS:-3}"
STOP_WAIT_SECONDS="${TOPICLAB_STOP_WAIT_SECONDS:-10}"

mkdir -p "${LOG_DIR}" "${RUN_DIR}"

load_env() {
  if [[ ! -f "${ENV_FILE}" ]]; then
    echo "missing env file: ${ENV_FILE}" >&2
    exit 1
  fi
  set -a
  # shellcheck disable=SC1090
  source "${ENV_FILE}"
  set +a
}

pid_from_file() {
  if [[ -f "${PID_FILE}" ]]; then
    tr -d '[:space:]' < "${PID_FILE}"
  fi
}

is_pid_running() {
  local pid="${1:-}"
  if [[ -z "${pid}" ]]; then
    return 1
  fi
  kill -0 "${pid}" 2>/dev/null
}

port_listener() {
  ss -tlnp 2>/dev/null | grep -F ":${PORT}" || true
}

listener_pids() {
  port_listener | grep -o 'pid=[0-9]\+' | cut -d= -f2 | sort -u || true
}

cleanup_stale_pid() {
  local pid
  pid="$(pid_from_file)"
  if [[ -n "${pid}" ]] && ! is_pid_running "${pid}"; then
    rm -f "${PID_FILE}"
  fi
}

start_service() {
  cleanup_stale_pid
  local existing_pid
  existing_pid="$(pid_from_file)"
  if is_pid_running "${existing_pid}"; then
    echo "already running pid=${existing_pid}"
    return 0
  fi

  if [[ -n "$(port_listener)" ]]; then
    echo "port ${PORT} is already in use; refusing to start blindly" >&2
    port_listener >&2
    exit 1
  fi

  load_env
  cd "${REPO_ROOT}"
  nohup "${PYTHON_BIN}" -m uvicorn "${APP_MODULE}" --host "${HOST}" --port "${PORT}" > "${LOG_FILE}" 2>&1 < /dev/null &
  local new_pid=$!
  echo "${new_pid}" > "${PID_FILE}"
  sleep "${START_WAIT_SECONDS}"

  if ! is_pid_running "${new_pid}"; then
    echo "failed to start service; recent log output:" >&2
    tail -n 80 "${LOG_FILE}" >&2 || true
    rm -f "${PID_FILE}"
    exit 1
  fi

  echo "started pid=${new_pid} host=${HOST} port=${PORT}"
}

stop_service() {
  cleanup_stale_pid
  local pid
  pid="$(pid_from_file)"
  if is_pid_running "${pid}"; then
    kill "${pid}"
    local waited=0
    while is_pid_running "${pid}"; do
      if (( waited >= STOP_WAIT_SECONDS )); then
        kill -9 "${pid}" 2>/dev/null || true
        break
      fi
      sleep 1
      waited=$(( waited + 1 ))
    done
    rm -f "${PID_FILE}"
    echo "stopped managed pid=${pid}"
    return 0
  fi

  local listeners
  listeners="$(listener_pids)"
  if [[ -z "${listeners}" ]]; then
    echo "not running"
    rm -f "${PID_FILE}"
    return 0
  fi

  local unmanaged_pid
  for unmanaged_pid in ${listeners}; do
    kill "${unmanaged_pid}" 2>/dev/null || true
  done

  local waited=0
  while [[ -n "$(listener_pids)" ]]; do
    if (( waited >= STOP_WAIT_SECONDS )); then
      for unmanaged_pid in ${listeners}; do
        kill -9 "${unmanaged_pid}" 2>/dev/null || true
      done
      break
    fi
    sleep 1
    waited=$(( waited + 1 ))
  done
  rm -f "${PID_FILE}"
  echo "stopped unmanaged pid=$(printf '%s\n' "${listeners}" | paste -sd, -)"
}

status_service() {
  cleanup_stale_pid
  local pid
  pid="$(pid_from_file)"
  if is_pid_running "${pid}"; then
    echo "running managed pid=${pid} host=${HOST} port=${PORT}"
  elif [[ -n "$(listener_pids)" ]]; then
    echo "running unmanaged pid=$(listener_pids | paste -sd, -) host=${HOST} port=${PORT}"
  else
    echo "stopped host=${HOST} port=${PORT}"
  fi
  port_listener
}

health_service() {
  curl -fsS "${HEALTH_URL}"
  printf "\n"
}

logs_service() {
  local lines="${2:-80}"
  tail -n "${lines}" "${LOG_FILE}"
}

case "${ACTION}" in
  start)
    start_service
    ;;
  stop)
    stop_service
    ;;
  restart)
    stop_service
    start_service
    ;;
  status)
    status_service
    ;;
  health)
    health_service
    ;;
  logs)
    logs_service "${@:2}"
    ;;
  *)
    echo "usage: $(basename "$0") {start|stop|restart|status|health|logs [lines]}" >&2
    exit 2
    ;;
esac
