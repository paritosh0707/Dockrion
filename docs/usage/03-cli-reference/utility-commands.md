# 3.2 Utility Commands

[Home](../../README.md) > [CLI Reference](README.md)

Commands for inspection, Dockfile modification, diagnostics, and info.

---

## `dockrion inspect`

Invoke the agent and inspect its output, optionally generating `io_schema` from the result.

```bash
dockrion inspect [path] [options]
```

| Argument/Option | Flag | Type | Default | Description |
|-----------------|------|------|---------|-------------|
| `path` | *(positional)* | `str` | `Dockfile.yaml` | Path to Dockfile |
| `--payload` | `-p` | `str` | `null` | JSON payload as string |
| `--payload-file` | `-f` | `str` | `null` | Path to JSON file |
| `--generate-schema` | `-g` | `bool` | `false` | Generate `io_schema` YAML from output |
| `--output` | `-o` | `str` | `null` | Save output or schema to file |
| `--raw` | `-r` | `bool` | `false` | Show raw Python `repr` instead of JSON |
| `--verbose` | `-v` | `bool` | `false` | Detailed output |

### Schema Generation

When `--generate-schema` is set, inspect invokes the agent, examines the output structure, and generates a YAML `io_schema` block that matches the output shape. This is useful for bootstrapping your Dockfile's `io_schema` from actual agent output.

```bash
dockrion inspect -p '{"query": "test"}' --generate-schema -o schema.yaml
```

---

## `dockrion add`

Add or update sections in an existing Dockfile. Three subcommands are available.

### `dockrion add streaming`

```bash
dockrion add streaming [dockfile] [options]
```

| Argument/Option | Flag | Type | Default | Description |
|-----------------|------|------|---------|-------------|
| `dockfile` | *(positional)* | `str` | `Dockfile.yaml` | Path to Dockfile |
| `--events` | `-E` | `str` | `null` | Events preset (`all`, `chat`, `debug`, `minimal`) or comma-separated list |
| `--async-runs` | `-A` | `bool` | `false` | Enable async `/runs` endpoint |
| `--backend` | `-b` | `str` | `memory` | Backend: `memory` or `redis` |
| `--heartbeat` | | `int` | `15` | Heartbeat interval (seconds) |
| `--max-duration` | | `int` | `3600` | Max run duration (seconds) |
| `--force` | `-f` | `bool` | `false` | Overwrite existing streaming config |

### `dockrion add auth`

```bash
dockrion add auth [dockfile] [options]
```

| Argument/Option | Flag | Type | Default | Description |
|-----------------|------|------|---------|-------------|
| `dockfile` | *(positional)* | `str` | `Dockfile.yaml` | Path to Dockfile |
| `--mode` | `-m` | `str` | `api_key` | Auth mode: `api_key`, `jwt`, or `none` |
| `--env-var` | | `str` | `API_KEY` | Env var for API key (api_key mode) |
| `--header` | | `str` | `X-API-Key` | HTTP header for API key |
| `--force` | `-f` | `bool` | `false` | Overwrite existing auth config |

Using `--mode none` removes the auth section from the Dockfile.

### `dockrion add secrets`

```bash
dockrion add secrets [dockfile] <names> [options]
```

| Argument/Option | Flag | Type | Default | Description |
|-----------------|------|------|---------|-------------|
| `dockfile` | *(positional)* | `str` | `Dockfile.yaml` | Path to Dockfile |
| `names` | *(positional)* | `str` | **required** | Comma-separated secret names |
| `--optional` | | `bool` | `false` | Mark secrets as optional |
| `--force` | `-f` | `bool` | `false` | Overwrite existing secrets config |

New secrets are merged into the existing `secrets` section. If a secret already exists, it is skipped (unless `--force`).

```bash
dockrion add secrets OPENAI_API_KEY,DATABASE_URL
dockrion add secrets LANGFUSE_PUBLIC_KEY --optional
```

---

## `dockrion doctor`

Run environment diagnostics to check that your setup is healthy.

```bash
dockrion doctor
```

No arguments or options.

### What It Checks

| Check | What it tests |
|-------|--------------|
| Docker | `docker --version` runs successfully |
| Dockfile | `Dockfile.yaml` exists in the current directory |
| Schema validation | The Dockfile passes `validate_dockspec()` |
| Package imports | `dockrion_adapters`, `dockrion_common`, `dockrion_schema`, `dockrion_sdk` are importable |

Doctor always exits with code 0, even if checks fail. It reports pass/fail for each check with guidance on how to fix failures.

---

## `dockrion logs`

View agent logs.

```bash
dockrion logs <agent> [options]
```

| Argument/Option | Flag | Type | Default | Description |
|-----------------|------|------|---------|-------------|
| `agent` | *(positional)* | `str` | **required** | Agent name |
| `--lines` | `-n` | `int` | `100` | Number of log lines to show |
| `--follow` | `-f` | `bool` | `false` | Follow log output in real-time |
| `--verbose` | `-v` | `bool` | `false` | Detailed output |

Logs are read from `.dockrion_runtime/logs/{agent}.log`. The `--follow` flag streams new lines as they appear (press `Ctrl+C` to stop).

---

## `dockrion version`

Show version information.

```bash
dockrion version
```

No arguments or options. Displays:

- SDK version (`dockrion_sdk.__version__`)
- CLI version
- Python version

---

## `dockrion deploy`

> **Status: Not implemented.** This command is reserved for future controller integration. Running it will display a "not yet implemented" message.

> **Source:** `packages/cli/dockrion_cli/inspect_cmd.py`, `add_cmd.py`, `info_cmd.py`, `logs_cmd.py`

---

**Previous:** [3.1 Core Commands](core-commands.md) | **Next:** [3.3 Exit Codes →](exit-codes.md)
