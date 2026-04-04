# 3.3 Exit Codes

[Home](../../README.md) > [CLI Reference](README.md)

## Exit Code Reference

| Code | Meaning | Commands |
|------|---------|----------|
| `0` | Success | All commands on success; `run` on `Ctrl+C`; `doctor` always; user cancellation in `init`/`add` |
| `1` | Error | Missing files, validation failure, bad JSON, SDK import failure, build error, generic exceptions |
| `130` | Keyboard interrupt during execution | `build`, `test`, `inspect` when interrupted with `Ctrl+C` during agent execution |

### Notes

- **`dockrion run`** exits `0` on `Ctrl+C` (clean shutdown)
- **`dockrion doctor`** always exits `0`, even when checks fail (it reports results but doesn't fail)
- **`dockrion logs`** with `--follow` exits `0` on `Ctrl+C` (stops following)
- **Typer/Click help** (`--help`) exits `0`
- **Invalid usage** (wrong flags, missing args) follows Click conventions (typically exits `2`)

## Source Layout

For contributors — where each command is implemented:

```
packages/cli/dockrion_cli/
├── main.py          Root Typer app, command registration
├── init_cmd.py      dockrion init
├── validate_cmd.py  dockrion validate
├── run_cmd.py       dockrion run
├── build_cmd.py     dockrion build
├── test_cmd.py      dockrion test
├── inspect_cmd.py   dockrion inspect
├── add_cmd.py       dockrion add (streaming, auth, secrets)
├── info_cmd.py      dockrion version, dockrion doctor
├── logs_cmd.py      dockrion logs
└── deploy_cmd.py    dockrion deploy (placeholder)
```

> **Source:** `packages/cli/dockrion_cli/main.py`

---

**Previous:** [3.2 Utility Commands](utility-commands.md) | **Next:** [4. The Generated API →](../04-the-generated-api/README.md)
