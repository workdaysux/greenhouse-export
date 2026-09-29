# Development & Release Guide

## Building Locally

### Using Make (Recommended)

```bash
make test     # Run syntax checks
make build    # Build greenhouse_export_dev.zip
make clean    # Remove build artifacts
make help     # Show all commands
```

### Using build.sh

```bash
bash build.sh          # Build greenhouse_export_dev.zip
bash build.sh v1.0.0   # Build greenhouse_export_v1.0.0.zip
```

## Creating a Release

### 1. Update VERSION file
```bash
echo "1.0.1" > VERSION
```

### 2. Commit and tag
```bash
git add VERSION
git commit -m "Bump version to 1.0.1"
git tag v1.0.1
git push origin main --tags
```

### 3. GitHub Actions auto-builds and releases
- Pushing a tag `v*` automatically triggers the release workflow
- Build artifact is created and attached to GitHub release
- Users can download `greenhouse_export_v1.0.1.zip` from Releases page

### Manual release (if CI fails)
```bash
make release   # Shows gh command to run
gh release create v1.0.1 dist/greenhouse_export_v1.0.1.zip
```

## Distribution

### For Clients:
1. Go to GitHub releases: https://github.com/hsunl/greenhouse-export/releases
2. Download latest `greenhouse_export_*.zip`
3. Extract and run `bash greenhouse_export.sh`

### For Internal (via ZIP):
```bash
make build
# dist/greenhouse_export_dev.zip is ready to distribute
```

## Version Management

- **VERSION file** — Source of truth for version
- **Git tags** — Trigger automated releases
- **GitHub Releases** — User-facing download links

## CI/CD Pipeline

`.github/workflows/release.yml` automatically:
1. Tests Python/Bash syntax
2. Builds ZIP distribution
3. Creates GitHub release
4. Attaches ZIP to release

No manual steps needed after pushing a tag.
