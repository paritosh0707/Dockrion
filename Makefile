.PHONY: bootstrap bootstrap-dev test test-cov test-verbose lint typecheck ci clean help build build-check

# Default target
help:
	@echo "Dockrion Development Commands"
	@echo "=============================="
	@echo ""
	@echo "Setup:"
	@echo "  make bootstrap     - Install all packages in editable mode (user mode)"
	@echo "  make bootstrap-dev - Install all packages with dev dependencies"
	@echo ""
	@echo "Testing:"
	@echo "  make test          - Run all tests"
	@echo "  make test-cov      - Run tests with coverage report"
	@echo "  make test-verbose  - Run tests with verbose output"
	@echo "  make test-fast     - Run tests excluding slow tests"
	@echo ""
	@echo "Quality:"
	@echo "  make lint          - Run linters (ruff)"
	@echo "  make typecheck     - Run type checker (mypy)"
	@echo "  make format        - Format code (ruff format)"
	@echo "  make ci            - Run all CI checks (lint, typecheck, test)"
	@echo ""
	@echo "Build & Publish:"
	@echo "  make build         - Build the dockrion package for distribution"
	@echo "  make build-check   - Build and verify package contents"
	@echo "  make publish-test  - Publish to TestPyPI (for testing)"
	@echo "  make publish       - Publish to PyPI (production)"
	@echo ""
	@echo "Package-specific testing:"
	@echo "  make test-adapters   - Run adapters tests"
	@echo "  make test-cli        - Run CLI tests"
	@echo "  make test-common     - Run common-py tests"
	@echo "  make test-schema     - Run schema tests"
	@echo "  make test-sdk        - Run SDK tests"
	@echo "  make test-runtime    - Run runtime tests"
	@echo "  make test-policy     - Run policy-engine tests"
	@echo "  make test-telemetry  - Run telemetry tests"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean         - Remove build artifacts and cache files"

# Install all packages in editable mode (for users)
bootstrap:
	pip install -e packages/common-py \
	            -e packages/schema \
	            -e packages/adapters \
	            -e packages/policy-engine \
	            -e packages/telemetry \
	            -e packages/runtime \
	            -e packages/sdk-python \
	            -e packages/cli

# Install all packages with dev dependencies (for developers)
bootstrap-dev:
	pip install -e "packages/common-py[dev]" \
	            -e "packages/schema[dev]" \
	            -e "packages/adapters[dev]" \
	            -e "packages/policy-engine[dev]" \
	            -e "packages/telemetry[dev]" \
	            -e "packages/runtime[dev]" \
	            -e "packages/sdk-python[dev]" \
	            -e "packages/cli[dev]"

# Install test dependencies only (for CI or quick testing)
bootstrap-test:
	pip install -e "packages/common-py[test]" \
	            -e "packages/schema[test]" \
	            -e "packages/adapters[test]" \
	            -e "packages/policy-engine[test]" \
	            -e "packages/telemetry[test]" \
	            -e "packages/runtime[test]" \
	            -e "packages/sdk-python[test]" \
	            -e "packages/cli[test]"

# Run all tests (sequentially per package to avoid import conflicts)
test:
	@echo "=== Testing common-py ===" && pytest packages/common-py/tests -q && \
	echo "=== Testing schema ===" && pytest packages/schema/tests -q && \
	echo "=== Testing adapters ===" && pytest packages/adapters/tests -q && \
	echo "=== Testing policy-engine ===" && pytest packages/policy-engine/tests -q && \
	echo "=== Testing telemetry ===" && pytest packages/telemetry/tests -q && \
	echo "=== Testing runtime ===" && pytest packages/runtime/tests -q && \
	echo "=== Testing sdk-python ===" && pytest packages/sdk-python/tests -q && \
	echo "=== Testing cli ===" && pytest packages/cli/tests -q && \
	echo "=== All tests passed! ==="

# Run tests with coverage
test-cov:
	pytest --cov=packages --cov-report=term-missing --cov-report=html

# Run tests with verbose output
test-verbose:
	pytest -v --tb=long

# Run tests excluding slow tests
test-fast:
	pytest -m "not slow"

# Run integration tests only
test-integration:
	pytest -m "integration"

# Package-specific test targets
test-adapters:
	pytest packages/adapters/tests -v

test-cli:
	pytest packages/cli/tests -v

test-common:
	pytest packages/common-py/tests -v

test-schema:
	pytest packages/schema/tests -v

test-sdk:
	pytest packages/sdk-python/tests -v

test-runtime:
	pytest packages/runtime/tests -v

test-policy:
	pytest packages/policy-engine/tests -v

test-telemetry:
	pytest packages/telemetry/tests -v

# Linting (ignore common acceptable patterns)
# E501: line too long (handled by formatter)
# E402: import not at top (needed in tests for path setup)
# F401: unused import (often intentional in __init__.py)
# F841: unused variable (sometimes intentional in tests)
# B904: raise from (stylistic preference)
# B008: function call in default arg (common FastAPI pattern)
# B017: blind exception (acceptable in tests)
# B027: empty method without abstract decorator (intentional)
lint:
	ruff check packages/ --ignore E501,E402,F401,F841,B904,B008,B017,B027

# Type checking
typecheck:
	mypy packages/common-py/dockrion_common \
	     packages/schema/dockrion_schema \
	     packages/adapters/dockrion_adapters \
	     packages/policy-engine/dockrion_policy \
	     packages/telemetry/dockrion_telemetry \
	     packages/runtime/dockrion_runtime \
	     packages/sdk-python/dockrion_sdk \
	     --ignore-missing-imports

# Format code
format:
	ruff format packages/

# Run all CI checks
ci: lint typecheck test
	@echo "=== All CI checks passed! ==="

# ============================================================================
# Build & Publish (only the dockrion meta-package is published)
# ============================================================================

# Build the dockrion package for distribution
build:
	@echo "Building dockrion package..."
	cd packages/dockrion && python build_package.py
	@echo ""
	@echo "Built packages:"
	@ls -la packages/dockrion/dist/

# Build and verify package contents
build-check: build
	@echo ""
	@echo "Verifying package contents..."
	@cd packages/dockrion && python -c "\
import zipfile, glob, sys; \
wheels = glob.glob('dist/*.whl'); \
wheel = wheels[0] if wheels else sys.exit('No wheel found'); \
print(f'Checking: {wheel}'); \
files = zipfile.ZipFile(wheel).namelist(); \
expected = ['dockrion_common/', 'dockrion_schema/', 'dockrion_adapters/', \
            'dockrion_policy/', 'dockrion_telemetry/', 'dockrion_runtime/', \
            'dockrion_sdk/', 'dockrion_cli/']; \
missing = [p for p in expected if not any(f.startswith(p) for f in files)]; \
sys.exit(f'Missing: {missing}') if missing else print('✓ All packages included'); \
print(f'Total files: {len(files)}')"
	@echo ""
	@echo "Checking with twine..."
	cd packages/dockrion && twine check dist/*

# Publish to TestPyPI (for testing before real publish)
publish-test: build-check
	@echo "Publishing to TestPyPI..."
	cd packages/dockrion && twine upload --repository testpypi dist/*

# Publish to PyPI (production)
publish: build-check
	@echo "Publishing to PyPI..."
	cd packages/dockrion && twine upload dist/*

# ============================================================================
# Cleanup
# ============================================================================

# Clean build artifacts
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "build" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	rm -rf dist/
	rm -rf packages/dockrion/dist/
