# 3. CLI Reference

[Home](../README.md)

The `dockrion` CLI is built with Typer (on top of Click). All commands accept `--help` for detailed usage.

## Command Overview

| Command | Purpose |
|---------|---------|
| `dockrion init` | Scaffold a new Dockfile interactively |
| `dockrion validate` | Validate a Dockfile without running |
| `dockrion run` | Start a local dev server (uvicorn) |
| `dockrion build` | Generate runtime files and build a Docker image |
| `dockrion test` | Invoke the agent locally without an HTTP server |
| `dockrion inspect` | Invoke and inspect output, optionally generate `io_schema` |
| `dockrion add` | Add or update Dockfile sections (streaming, auth, secrets) |
| `dockrion doctor` | Run environment diagnostics |
| `dockrion logs` | View agent logs |
| `dockrion version` | Show version info |

## In This Section

| Page | Commands Covered |
|------|-----------------|
| [3.1 Core Commands](core-commands.md) | `init`, `validate`, `run`, `build`, `test` |
| [3.2 Utility Commands](utility-commands.md) | `inspect`, `add`, `doctor`, `logs`, `version` |
| [3.3 Exit Codes](exit-codes.md) | Exit code reference and source layout |

> **Source:** `packages/cli/dockrion_cli/main.py` and command modules

---

**Previous:** [2. The Dockfile](../02-the-dockfile/README.md) | **Next:** [4. The Generated API →](../04-the-generated-api/README.md)
