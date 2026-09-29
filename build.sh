#!/bin/bash
# Build script for Greenhouse Export tool
# Usage: bash build.sh [version] [zip|exe]
# Examples:
#   bash build.sh v1.0.0       # Build ZIP
#   bash build.sh v1.0.0 exe   # Build executable

set -e

VERSION="${1:-$(git describe --tags --always 2>/dev/null || echo "dev")}"
BUILD_TYPE="${2:-zip}"  # Default to ZIP
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
python3 -m py_compile launcher.py
bash -n greenhouse_export.sh
echo "✓ Syntax valid"
echo ""

if [ "$BUILD_TYPE" = "zip" ]; then
    # Build ZIP
    ZIP_FILE="$DIST_DIR/greenhouse_export_${VERSION}.zip"
    echo "Building ZIP: $ZIP_FILE"

    zip -q "$ZIP_FILE" \
        greenhouse_export.py \
        launcher.py \
        greenhouse_export.sh \
        .env.template \
        README.md \
        QUICK_START.txt \
        .gitignore \
        -x ".git/*" "*.pyc" "__pycache__/*" "build/*" "dist/*"

    chmod +x "$ZIP_FILE"

    SIZE=$(du -h "$ZIP_FILE" | cut -f1)
    echo ""
    echo "✓ Build complete!"
    echo ""
    echo "Distribution: $ZIP_FILE ($SIZE)"
    echo "Version: $VERSION"

elif [ "$BUILD_TYPE" = "exe" ]; then
    # Build executable with PyInstaller
    echo "Building executable: greenhouse_export_${VERSION}"

    if ! command -v pyinstaller &> /dev/null; then
        echo "Installing PyInstaller..."
        pip install -q pyinstaller
    fi

    pyinstaller --onefile --name "greenhouse_export_${VERSION}" greenhouse_export.spec > /dev/null 2>&1

    mkdir -p "$DIST_DIR"
    if [ "$(uname -s)" = "Darwin" ]; then
        mv "dist/greenhouse_export_${VERSION}" "$DIST_DIR/greenhouse_export_${VERSION}_macos"
        EXE_FILE="$DIST_DIR/greenhouse_export_${VERSION}_macos"
    else
        mv "dist/greenhouse_export_${VERSION}" "$DIST_DIR/greenhouse_export_${VERSION}_linux"
        EXE_FILE="$DIST_DIR/greenhouse_export_${VERSION}_linux"
    fi

    chmod +x "$EXE_FILE"
    rm -rf build dist

    SIZE=$(du -h "$EXE_FILE" | cut -f1)
    echo ""
    echo "✓ Build complete!"
    echo ""
    echo "Executable: $EXE_FILE ($SIZE)"
    echo "Version: $VERSION"
fi

echo ""
echo "To create a GitHub release:"
echo "  gh release create $VERSION $DIST_DIR/greenhouse_export_*"
echo ""
