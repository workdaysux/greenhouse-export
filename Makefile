.PHONY: build clean release help

VERSION ?= $(shell git describe --tags --always 2>/dev/null || echo "dev")
BUILD_DIR := build
DIST_DIR := dist

help:
	@echo "Greenhouse Export Tool — Build Commands"
	@echo ""
	@echo "  make build        — Build ZIP distribution"
	@echo "  make release      — Create release ZIP with version tag"
	@echo "  make clean        — Remove build artifacts"
	@echo "  make test         — Run syntax checks"
	@echo ""

build: clean
	@echo "Building greenhouse_export_$(VERSION).zip..."
	@mkdir -p $(DIST_DIR)
	@cd $(shell pwd) && zip -q $(DIST_DIR)/greenhouse_export_$(VERSION).zip \
		greenhouse_export.py \
		greenhouse_export.sh \
		.env.template \
		README.md \
		QUICK_START.txt \
		.gitignore \
		-x ".git/*" "*.pyc" "__pycache__/*" "build/*" "dist/*"
	@chmod +x $(DIST_DIR)/greenhouse_export_$(VERSION).zip
	@ls -lh $(DIST_DIR)/greenhouse_export_$(VERSION).zip
	@echo "✓ Built: $(DIST_DIR)/greenhouse_export_$(VERSION).zip"

release: build
	@echo "Creating release $(VERSION)..."
	@echo "Run: gh release create $(VERSION) dist/greenhouse_export_$(VERSION).zip"

clean:
	@rm -rf $(BUILD_DIR) $(DIST_DIR)
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "✓ Cleaned build artifacts"

test:
	@echo "Testing Python syntax..."
	@python3 -m py_compile greenhouse_export.py
	@echo "Testing Bash syntax..."
	@bash -n greenhouse_export.sh
	@echo "✓ All syntax checks passed"

.DEFAULT_GOAL := help
