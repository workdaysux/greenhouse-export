#!/bin/bash
# Build script for Greenhouse Export tool
# Creates distribution ZIP with all files

set -e

VERSION="${1:-$(git describe --tags --always 2>/dev/null || echo "dev")}"
BUILD_DIR="build"
DIST_DIR="dist"

echo "═══════════════════════════════════════"
echo "  Greenhouse Export — Build Tool"
echo "═══════════════════════════════════════"
echo ""

# Cleanup
if [ -d "$DIST_DIR" ]; then
    echo "Cleaning previous builds..."
    rm -rf "$DIST_DIR"
fi

mkdir -p "$DIST_DIR"

# Test syntax before building
echo "Running syntax checks..."
python3 -m py_compile greenhouse_export.py
bash -n greenhouse_export.sh
echo "✓ Syntax valid"
echo ""

# Build ZIP
ZIP_FILE="$DIST_DIR/greenhouse_export_${VERSION}.zip"
echo "Building: $ZIP_FILE"

zip -q "$ZIP_FILE" \
    greenhouse_export.py \
    greenhouse_export.sh \
    .env.template \
    README.md \
    QUICK_START.txt \
    .gitignore \
    -x ".git/*" "*.pyc" "__pycache__/*" "build/*" "dist/*"

chmod +x "$ZIP_FILE"

# Summary
SIZE=$(du -h "$ZIP_FILE" | cut -f1)
echo ""
echo "✓ Build complete!"
echo ""
echo "Distribution: $ZIP_FILE ($SIZE)"
echo "Version: $VERSION"
echo ""
echo "To create a GitHub release:"
echo "  gh release create $VERSION $ZIP_FILE"
echo ""
