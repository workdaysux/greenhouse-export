#!/bin/bash
# Greenhouse Export — Turnkey Setup Wizard
# Just run: ./greenhouse_export.sh

set -e

echo ""
echo "╔════════════════════════════════════════╗"
echo "║  Greenhouse Export Tool                ║"
echo "║  (All candidates + applications +      ║"
echo "║   resumes organized by role/dept)      ║"
echo "╚════════════════════════════════════════╝"
echo ""

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
ENV_FILE="$SCRIPT_DIR/.env"

# Check if .env exists with valid credentials
if [ -f "$ENV_FILE" ]; then
    set -a
    source "$ENV_FILE"
    set +a

    if [ -n "$GREENHOUSE_V3_CLIENT_ID" ] && [ -n "$GREENHOUSE_V3_CLIENT_SECRET" ] && [ -n "$GREENHOUSE_USER_ID" ]; then
        echo "✓ Using saved credentials from .env"
        echo ""
    else
        echo "⚠ .env file exists but is incomplete. Reconfiguring..."
        rm "$ENV_FILE"
        unset GREENHOUSE_V3_CLIENT_ID GREENHOUSE_V3_CLIENT_SECRET GREENHOUSE_USER_ID
    fi
fi

# If still no credentials, prompt interactively
if [ -z "$GREENHOUSE_V3_CLIENT_ID" ]; then
    echo "═══════════════════════════════════════════════════════"
    echo "  FIRST TIME SETUP — Add Your Greenhouse Credentials"
    echo "═══════════════════════════════════════════════════════"
    echo ""
    echo "You'll need 3 pieces of info from your Greenhouse account."
    echo "This is a one-time setup — we'll save it for next time."
    echo ""
    echo "🔗 Where to find them:"
    echo ""
    echo "   CLIENT ID & SECRET:"
    echo "   • Click Settings (gear icon, top right)"
    echo "   • Select 'API Credentials'"
    echo "   • Look for 'OAuth2 Provider' or 'v3 OAuth'"
    echo "   • Copy the CLIENT ID and CLIENT SECRET"
    echo ""
    echo "   USER ID:"
    echo "   • Click your name/avatar (top right)"
    echo "   • Select 'Profile' or 'Account Settings'"
    echo "   • Look for 'User ID' (usually a number like 1234567890)"
    echo "   • If not visible there, go to Settings → Users → find your name"
    echo ""
    echo ""
    echo "Ready? Press Enter to continue..."
    read

    echo ""
    read -p "📋 Paste v3 CLIENT ID: " GREENHOUSE_V3_CLIENT_ID
    [ -z "$GREENHOUSE_V3_CLIENT_ID" ] && echo "❌ Cannot be empty" && exit 1

    echo ""
    read -sp "🔒 Paste v3 CLIENT SECRET (hidden): " GREENHOUSE_V3_CLIENT_SECRET
    echo ""
    [ -z "$GREENHOUSE_V3_CLIENT_SECRET" ] && echo "❌ Cannot be empty" && exit 1

    echo ""
    read -p "👤 Paste USER ID: " GREENHOUSE_USER_ID
    [ -z "$GREENHOUSE_USER_ID" ] && echo "❌ Cannot be empty" && exit 1

    # Save to .env
    cat > "$ENV_FILE" << EOF
# Greenhouse API Credentials (auto-saved from setup wizard)
# Generated: $(date)
GREENHOUSE_V3_CLIENT_ID=$GREENHOUSE_V3_CLIENT_ID
GREENHOUSE_V3_CLIENT_SECRET=$GREENHOUSE_V3_CLIENT_SECRET
GREENHOUSE_USER_ID=$GREENHOUSE_USER_ID
EOF

    echo ""
    echo "✓ Credentials saved to .env (next run will be faster!)"
    echo ""
fi

# Final validation
if [ -z "$GREENHOUSE_V3_CLIENT_ID" ] || [ -z "$GREENHOUSE_V3_CLIENT_SECRET" ] || [ -z "$GREENHOUSE_USER_ID" ]; then
    echo "❌ Error: Missing credentials"
    exit 1
fi

# Export env vars for Python script
export GREENHOUSE_V3_CLIENT_ID
export GREENHOUSE_V3_CLIENT_SECRET
export GREENHOUSE_USER_ID

# Find Python script in same directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PYTHON_SCRIPT="$SCRIPT_DIR/greenhouse_export.py"

if [ ! -f "$PYTHON_SCRIPT" ]; then
    echo "❌ Error: greenhouse_export.py not found in $SCRIPT_DIR"
    exit 1
fi

echo ""
echo "Starting export..."
echo ""

python3 "$PYTHON_SCRIPT"

echo ""
echo "✅ Done! Check the greenhouse_export folder."
if command -v open &> /dev/null; then
    open "$SCRIPT_DIR/greenhouse_export"
fi
echo ""
