#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
MOBILE_DIR="$REPO_DIR/mobile-frontend"
WEB_ASSETS_DIR="$REPO_DIR/ios-app/EduMindIOS/EduMindIOS/WebAssets"

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
