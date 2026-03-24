#!/usr/bin/env bash
set -euo pipefail

PORT="${1:-2004}"
HOST="${BLITZ_BACKEND_HOST:-127.0.0.1}"
URL="http://${HOST}:${PORT}/health"

log() {
  echo "[blitz:healthcheck] $*"
}

fail() {
  echo "[blitz:healthcheck][error] $*" >&2
  exit 1
}

command -v curl >/dev/null 2>&1 || fail "未找到 curl，无法访问 $URL"

log "检查后端健康状态：$URL"

set +e
RESPONSE="$(curl --silent --show-error --max-time 5 --write-out $'\n%{http_code}' "$URL")"
CURL_EXIT=$?
set -e

if [ "$CURL_EXIT" -ne 0 ]; then
  fail "请求失败，无法连接 $URL。请先确认后端已启动，并检查端口或 HOST 配置。"
fi

HTTP_STATUS="$(printf '%s\n' "$RESPONSE" | tail -n 1 | tr -d '\r')"
BODY="$(printf '%s\n' "$RESPONSE" | sed '$d')"

if [ "$HTTP_STATUS" != "200" ]; then
  echo "$BODY"
  fail "健康检查失败，HTTP 状态码：$HTTP_STATUS"
fi

log "健康检查通过，HTTP 状态码：$HTTP_STATUS"
echo "$BODY"
