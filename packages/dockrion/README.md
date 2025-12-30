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

For specific components:

```bash
# Just the SDK (for building agents)
pip install dockrion[sdk]

# Include the runtime (for deploying agents)
pip install dockrion[runtime]

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

## Packages

Dockrion is a collection of modular packages:

| Package | Description | Install |
|---------|-------------|---------|
| **dockrion** | Meta-package (this one) | `pip install dockrion` |
| **dockrion-cli** | Command-line interface | `pip install dockrion-cli` |
| **dockrion-sdk** | SDK for building agents | `pip install dockrion-sdk` |
| **dockrion-runtime** | FastAPI runtime for deployed agents | `pip install dockrion-runtime` |
| **dockrion-common** | Shared utilities | `pip install dockrion-common` |
| **dockrion-schema** | Dockfile schema validation | `pip install dockrion-schema` |
| **dockrion-adapters** | Framework adapters (LangGraph, etc.) | `pip install dockrion-adapters` |
| **dockrion-policy** | Policy engine for safety controls | `pip install dockrion-policy` |
| **dockrion-telemetry** | Observability and metrics | `pip install dockrion-telemetry` |

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

