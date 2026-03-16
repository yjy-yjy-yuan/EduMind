#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
MOBILE_DIR="$REPO_DIR/mobile-frontend"
WEB_ASSETS_DIR="$REPO_DIR/ios-app/EduMindIOS/EduMindIOS/WebAssets"
BACKEND_ENV_FILE="$REPO_DIR/backend_fastapi/.env"
IOS_PROJECT_FILE="$REPO_DIR/ios-app/EduMindIOS/EduMindIOS.xcodeproj/project.pbxproj"

BACKEND_PORT="2004"
if [ -f "$BACKEND_ENV_FILE" ]; then
  DETECTED_PORT="$(awk -F= '/^PORT=/{print $2; exit}' "$BACKEND_ENV_FILE" | tr -d '[:space:]')"
  if [ -n "${DETECTED_PORT:-}" ]; then
    BACKEND_PORT="$DETECTED_PORT"
  fi
fi

LOCAL_HOSTNAME="$(scutil --get LocalHostName 2>/dev/null || true)"
if [ -z "${LOCAL_HOSTNAME:-}" ]; then
  LOCAL_HOSTNAME="$(hostname -s 2>/dev/null || true)"
fi

IOS_API_BASE_URL=""
if [ -n "${LOCAL_HOSTNAME:-}" ]; then
  IOS_API_BASE_URL="http://${LOCAL_HOSTNAME}.local:${BACKEND_PORT}"
fi

if [ -n "$IOS_API_BASE_URL" ] && [ -f "$IOS_PROJECT_FILE" ]; then
  perl -0pi -e "s|INFOPLIST_KEY_EDUMIND_API_BASE_URL = \"[^\"]*\";|INFOPLIST_KEY_EDUMIND_API_BASE_URL = \"$IOS_API_BASE_URL\";|g" "$IOS_PROJECT_FILE"
fi

cd "$MOBILE_DIR"

if [ ! -d "node_modules" ]; then
  npm install
fi

# Some environments lose executable bits in node_modules/.bin.
if [ -f "node_modules/.bin/vite" ] && [ ! -x "node_modules/.bin/vite" ]; then
  chmod +x node_modules/.bin/vite || true
fi
if [ -f "node_modules/vite/bin/vite.js" ] && [ ! -x "node_modules/vite/bin/vite.js" ]; then
  chmod +x node_modules/vite/bin/vite.js || true
fi

npm run build:ios

mkdir -p "$WEB_ASSETS_DIR"
rsync -a --delete "$MOBILE_DIR/dist/" "$WEB_ASSETS_DIR/"

echo "Web assets synced to: $WEB_ASSETS_DIR"
if [ -n "$IOS_API_BASE_URL" ]; then
  echo "iOS native API base synced to: $IOS_API_BASE_URL"
fi
