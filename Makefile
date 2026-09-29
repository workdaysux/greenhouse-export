.PHONY: build build-exe clean release help test

VERSION ?= $(shell git describe --tags --always 2>/dev/null || echo "dev")
BUILD_DIR := build
DIST_DIR := dist
OS := $(shell uname -s)

help:
	@echo "Greenhouse Export Tool — Build Commands"
	@echo ""
	@echo "  make build        — Build ZIP distribution"
	@echo "  make build-exe    — Build standalone executable (PyInstaller)"
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

build-exe: test
	@echo "Building standalone executable (v$(VERSION))..."
	@pip install -q pyinstaller 2>/dev/null || true
	@pyinstaller --onefile --name greenhouse_export_$(VERSION) greenhouse_export.spec
	@mkdir -p $(DIST_DIR)
	@if [ "$(OS)" = "Darwin" ]; then \
		mv dist/greenhouse_export_$(VERSION) $(DIST_DIR)/greenhouse_export_$(VERSION)_macos; \
		ls -lh $(DIST_DIR)/greenhouse_export_$(VERSION)_macos; \
	else \
		mv dist/greenhouse_export_$(VERSION) $(DIST_DIR)/greenhouse_export_$(VERSION)_linux; \
		ls -lh $(DIST_DIR)/greenhouse_export_$(VERSION)_linux; \
	fi
	@rm -rf build dist greenhouse_export_$(VERSION).spec
	@echo "✓ Built standalone executable"

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
