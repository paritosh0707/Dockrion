# Dockrion Installation Guide

Complete guide for installing and using Dockrion.

---

## For Users: Install from PyPI

```bash
# Install the dockrion package
pip install dockrion
```

### With Optional Features

```bash
# LangGraph framework support
pip install dockrion[langgraph]

# LangChain framework support
pip install dockrion[langchain]

# Runtime (for deploying agents as a server)
pip install dockrion[runtime]

# JWT authentication for runtime
pip install dockrion[jwt]

# Everything
pip install dockrion[all]
```

### Verify Installation

```bash
# Check CLI is working
dockrion --help
dockrion version

# Test in Python
python -c "from dockrion_sdk import DockfileLoader; print('✓ SDK available')"
python -c "from dockrion_schema import DockSpec; print('✓ Schema available')"
```

---

## For Developers: Local Development Setup

### Prerequisites

- Python 3.11+
- `uv` package manager (recommended) or `pip`
- Git repository cloned

### Quick Start

```bash
# Clone the repository
git clone https://github.com/paritosh0707/Dockrion.git
cd Dockrion

# Create and activate virtual environment
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install all packages in editable mode
make bootstrap

# Or with dev dependencies
make bootstrap-dev
```

### Manual Installation (Without Make)

```bash
# Create virtual environment
uv venv
source .venv/bin/activate

# Install packages in dependency order
uv pip install -e packages/common-py
uv pip install -e packages/schema
uv pip install -e packages/adapters
uv pip install -e packages/policy-engine
uv pip install -e packages/telemetry
uv pip install -e packages/runtime
uv pip install -e packages/sdk-python
uv pip install -e packages/cli

# Install test dependencies
uv pip install pytest pytest-cov pytest-mock pytest-asyncio
```

### Using uv sync (Recommended)

```bash
# From project root - installs everything from uv.lock
uv sync
```

---

## Development Workflow

### Running Tests

```bash
# Run all tests
make test

# Run tests with coverage
make test-cov

# Run specific package tests
make test-cli
make test-sdk
make test-runtime
# ... etc
```

### Code Quality

```bash
# Lint code
make lint

# Type checking
make typecheck

# Format code
make format

# Run all CI checks
make ci
```

### Using the CLI

```bash
# Initialize a new agent project
dockrion init my-agent

# Validate a Dockfile
dockrion validate

# Run an agent locally
dockrion run

# Check system status
dockrion doctor
```

---

## Building for Distribution

> **Note:** Only the `dockrion` meta-package should be published. Individual sub-packages are internal and bundled automatically.

```bash
# Build the package
make build

# Build and verify contents
make build-check

# Publish to TestPyPI (for testing)
make publish-test

# Publish to PyPI (production)
make publish
```

---

## Package Structure

The `dockrion` package bundles all components:

| Module | Description |
|--------|-------------|
| `dockrion_cli` | Command-line interface |
| `dockrion_sdk` | SDK for building agents |
| `dockrion_runtime` | FastAPI runtime for deployed agents |
| `dockrion_common` | Shared utilities |
| `dockrion_schema` | Dockfile schema validation |
| `dockrion_adapters` | Framework adapters (LangGraph, LangChain) |
| `dockrion_policy` | Policy engine for safety controls |
| `dockrion_telemetry` | Observability and metrics |

---

## Troubleshooting

### Problem: "No module named 'dockrion_common'"

```bash
# Reinstall packages
make bootstrap
```

### Problem: Changes to code not reflected

```bash
# Make sure you used editable install
uv pip install -e packages/common-py  # Note the -e flag
```

### Problem: Dependency conflicts

```bash
# Check for conflicts
uv pip check

# Recreate environment
rm -rf .venv
uv venv
source .venv/bin/activate
make bootstrap
```

### Problem: Build fails

```bash
# Clean and rebuild
make clean
make build
```

---

## Quick Reference

| Task | Command |
|------|---------|
| Install (user) | `pip install dockrion` |
| Install (dev) | `make bootstrap-dev` |
| Run tests | `make test` |
| Build package | `make build` |
| Publish | `make publish` |
| Clean | `make clean` |

---

**Python Version**: 3.11+  
**Package Manager**: uv (recommended) or pip
