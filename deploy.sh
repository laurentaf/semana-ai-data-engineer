#!/usr/bin/env bash
# Deploy ShopAgent to Render
# Usage: ./deploy.sh
#
# Requires RENDER_DEPLOY_HOOK env var (get it from Render Dashboard > Settings > Deploy Hook)
# Or pass it as argument: ./deploy.sh <deploy-hook-url>

set -e

HOOK="${1:-$RENDER_DEPLOY_HOOK}"

if [ -z "$HOOK" ]; then
    echo "ERROR: No deploy hook provided."
    echo ""
    echo "Usage:"
    echo "  RENDER_DEPLOY_HOOK=https://api.render.com/deploy/srv-xxx ./deploy.sh"
    echo "  ./deploy.sh https://api.render.com/deploy/srv-xxx"
    echo ""
    echo "Get your hook from: Render Dashboard > shopagent > Settings > Deploy Hook"
    exit 1
fi

echo "Deploying to Render..."
curl -sS -X POST "$HOOK" | head -1
echo ""
echo "Build: $(git rev-parse --short HEAD)"
echo "Check status at: https://dashboard.render.com"
