# 5.1 Installation & Extras

[Home](../../README.md) > [Guides & Recipes](README.md)

## Prerequisites

- **Python 3.11+** (3.11 or 3.12)
- **pip** (or [uv](https://docs.astral.sh/uv/) for faster installs)
- **Docker** (required only for `dockrion build`)

## Install Dockrion

### Base Installation

```bash
pip install dockrion
```

This installs the CLI, SDK, schema validation, and all core dependencies:

- `typer` — CLI framework
- `rich` — terminal formatting
- `pyyaml` — YAML parsing
- `requests` — HTTP client
- `jinja2` — template rendering
- `pydantic` — schema validation

### Optional Extras

| Extra | Install command | What it adds |
|-------|----------------|-------------|
| `langgraph` | `pip install dockrion[langgraph]` | LangGraph + LangChain Core |
| `langchain` | `pip install dockrion[langchain]` | LangChain + LangChain Core |
| `runtime` | `pip install dockrion[runtime]` | FastAPI, uvicorn, prometheus-client |
| `jwt` | `pip install dockrion[jwt]` | PyJWT with crypto support |
| `all` | `pip install dockrion[all]` | Everything above |

### Recommended for Most Users

```bash
pip install dockrion[all]
```

This gives you LangGraph support, the full runtime, and JWT authentication.

### What Each Extra Includes

| Extra | Packages |
|-------|----------|
| `langgraph` | `langgraph>=0.0.20`, `langchain-core>=0.1.0` |
| `langchain` | `langchain>=0.1.0`, `langchain-core>=0.1.0` |
| `runtime` | `fastapi>=0.109.0`, `uvicorn[standard]>=0.27.0`, `prometheus-client>=0.20` |
| `jwt` | `PyJWT[crypto]>=2.8.0` |

## Verify Your Installation

### Check the Version

```bash
dockrion version
```

Expected output:

```
Dockrion CLI v0.1.0
SDK v0.1.0
Python 3.11.x
```

### Run the Doctor

```bash
dockrion doctor
```

This checks:

- Docker availability
- Dockfile presence (if in a project directory)
- Schema validation
- Package imports (`dockrion_adapters`, `dockrion_common`, `dockrion_schema`, `dockrion_sdk`)

### Show Available Commands

```bash
dockrion --help
```

## Development Setup (Contributors)

For contributing to Dockrion itself:

```bash
git clone https://github.com/paritosh0707/Dockrion.git
cd Dockrion
```

If you have `uv`:

```bash
uv pip install -e packages/common-py
uv pip install -e packages/schema
uv pip install -e packages/adapters
uv pip install -e packages/events
uv pip install -e packages/policy-engine
uv pip install -e packages/telemetry
uv pip install -e packages/runtime
uv pip install -e packages/sdk-python
uv pip install -e packages/cli
```

Or with pip:

```bash
pip install -e packages/common-py
pip install -e packages/schema
# ... same for each package
```

Install order matters — `common-py` and `schema` must be installed before packages that depend on them.

> **Source:** `packages/dockrion/pyproject.toml`

---

**Next:** [5.2 Environment & Secrets →](environment-and-secrets.md)
