# Dockrion

[![PyPI version](https://badge.fury.io/py/dockrion.svg)](https://badge.fury.io/py/dockrion)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

**Deploy and manage AI agents with ease.**

Dockrion provides a complete toolkit for building, validating, and deploying AI agents powered by LangGraph, LangChain, and other frameworks.

## Installation

```bash
pip install dockrion
```

### With Optional Features

```bash
# LangGraph support
pip install dockrion[langgraph]

# LangChain support
pip install dockrion[langchain]

# Runtime (for deploying agents as a server)
pip install dockrion[runtime]

# JWT authentication for runtime
pip install dockrion[jwt]

# Everything
pip install dockrion[all]
```

## Quick Start

After installation, use the CLI:

```bash
# Initialize a new agent project
dockrion init my-agent

# Validate your Dockfile
dockrion validate

# Run your agent locally
dockrion run

# Deploy to production
dockrion deploy
```

## What's Included

The `dockrion` package bundles all the necessary components:

| Module | Description |
|--------|-------------|
| `dockrion_cli` | Command-line interface |
| `dockrion_sdk` | SDK for building agents |
| `dockrion_runtime` | FastAPI runtime for deployed agents |
| `dockrion_common` | Shared utilities |
| `dockrion_schema` | Dockfile schema validation |
| `dockrion_adapters` | Framework adapters (LangGraph, LangChain, etc.) |
| `dockrion_policy` | Policy engine for safety controls |
| `dockrion_telemetry` | Observability and metrics |

## Features

- 🚀 **Easy Deployment**: Define your agent in a simple YAML Dockfile
- 🔧 **Framework Agnostic**: Works with LangGraph, LangChain, and more
- 🛡️ **Built-in Safety**: Policy engine for redaction and tool gating
- 📊 **Observability**: Prometheus metrics and structured logging
- 🔐 **Security**: JWT authentication and API key support
- 🐳 **Container Ready**: Docker-first deployment strategy

## Documentation

For full documentation, visit the [GitHub repository](https://github.com/paritosh0707/Dockrion).

## License

Apache-2.0
