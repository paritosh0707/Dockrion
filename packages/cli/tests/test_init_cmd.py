"""Tests for init command."""

from pathlib import Path

import pytest
import yaml
from typer.testing import CliRunner

from dockrion_cli.main import app

runner = CliRunner()


# =============================================================================
# Basic Functionality Tests
# =============================================================================


def test_init_creates_dockfile(tmp_path, monkeypatch):
    """Test init command creates a Dockfile."""
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["init", "test-agent"])
    assert result.exit_code == 0
    assert Path("Dockfile.yaml").exists()
    assert "test-agent" in Path("Dockfile.yaml").read_text()


def test_init_with_custom_output(tmp_path, monkeypatch):
    """Test init with custom output path."""
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["init", "test-agent", "--output", "custom.yaml"])
    assert result.exit_code == 0
    assert Path("custom.yaml").exists()


def test_init_existing_file_no_force(tmp_path, monkeypatch):
    """Test init with existing file without force."""
    monkeypatch.chdir(tmp_path)
    Path("Dockfile.yaml").write_text("existing")
    result = runner.invoke(app, ["init", "test-agent"], input="n\n")
    assert result.exit_code == 0
    assert Path("Dockfile.yaml").read_text() == "existing"


def test_init_with_force(tmp_path, monkeypatch):
    """Test init with force flag."""
    monkeypatch.chdir(tmp_path)
    Path("Dockfile.yaml").write_text("existing")
    result = runner.invoke(app, ["init", "test-agent", "--force"])
    assert result.exit_code == 0
    assert "test-agent" in Path("Dockfile.yaml").read_text()


def test_init_creates_parent_directory(tmp_path, monkeypatch):
    """Test init creates parent directories if needed."""
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["init", "test-agent", "-o", "nested/dir/Dockfile.yaml"])
    assert result.exit_code == 0
    assert Path("nested/dir/Dockfile.yaml").exists()


# =============================================================================
# Agent Name Validation Tests
# =============================================================================


def test_init_invalid_agent_name(tmp_path, monkeypatch):
    """Test init rejects invalid agent names."""
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["init", "invalid@name!"])
    assert result.exit_code == 1
    assert "letters, numbers, hyphens" in result.output.lower()


def test_init_valid_agent_names(tmp_path, monkeypatch):
    """Test init accepts various valid agent names."""
    monkeypatch.chdir(tmp_path)
    # Agent names must be lowercase with hyphens and numbers only (no underscores)
    valid_names = ["my-agent", "agent123", "my-agent-v2", "a1b2c3"]
    for name in valid_names:
        result = runner.invoke(app, ["init", name, "-o", f"{name}.yaml", "-f"])
        assert result.exit_code == 0, f"Failed for name: {name}"


# =============================================================================
# Framework Option Tests
# =============================================================================


@pytest.mark.parametrize("framework", ["langgraph", "langchain", "custom"])
def test_init_with_framework(tmp_path, monkeypatch, framework):
    """Test init with different frameworks."""
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["init", "test-agent", "--framework", framework, "-f"])
    assert result.exit_code == 0
    content = yaml.safe_load(Path("Dockfile.yaml").read_text())
    assert content["agent"]["framework"] == framework


def test_init_invalid_framework(tmp_path, monkeypatch):
    """Test init rejects invalid framework."""
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["init", "test-agent", "--framework", "invalid"])
    assert result.exit_code == 1
    assert "invalid framework" in result.output.lower()


# =============================================================================
# Handler Mode Tests
# =============================================================================


def test_init_handler_mode(tmp_path, monkeypatch):
    """Test init with handler mode."""
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["init", "my-service", "--handler", "-f"])
    assert result.exit_code == 0
    content = yaml.safe_load(Path("Dockfile.yaml").read_text())
    assert "handler" in content["agent"]
    assert content["agent"]["framework"] == "custom"
    assert "entrypoint" not in content["agent"]
    assert "Mode: handler" in result.output


def test_init_handler_mode_description(tmp_path, monkeypatch):
    """Test handler mode uses 'service' in description."""
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["init", "my-service", "--handler", "-f"])
    assert result.exit_code == 0
    content = yaml.safe_load(Path("Dockfile.yaml").read_text())
    assert "service" in content["agent"]["description"]


# =============================================================================
# Authentication Option Tests
# =============================================================================


def test_init_with_api_key_auth(tmp_path, monkeypatch):
    """Test init with API key authentication."""
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["init", "test-agent", "--auth", "api_key", "-f"])
    assert result.exit_code == 0
    content = yaml.safe_load(Path("Dockfile.yaml").read_text())
    assert content["auth"]["mode"] == "api_key"
    assert "api_keys" in content["auth"]
    assert content["auth"]["api_keys"]["env_var"] == "MY_AGENT_KEY"
    assert "Auth: api_key" in result.output


def test_init_with_jwt_auth(tmp_path, monkeypatch):
    """Test init with JWT authentication."""
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["init", "test-agent", "--auth", "jwt", "-f"])
    assert result.exit_code == 0
    content = yaml.safe_load(Path("Dockfile.yaml").read_text())
    assert content["auth"]["mode"] == "jwt"
    assert "Auth: jwt" in result.output


def test_init_with_none_auth(tmp_path, monkeypatch):
    """Test init with no authentication (explicit)."""
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["init", "test-agent", "--auth", "none", "-f"])
    assert result.exit_code == 0
    content = yaml.safe_load(Path("Dockfile.yaml").read_text())
    # auth should be None or not present when mode is "none"
    assert content.get("auth") is None


def test_init_invalid_auth_mode(tmp_path, monkeypatch):
    """Test init rejects invalid auth mode."""
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["init", "test-agent", "--auth", "invalid"])
    assert result.exit_code == 1
    assert "invalid auth mode" in result.output.lower()


# =============================================================================
# Streaming Option Tests
# =============================================================================


@pytest.mark.parametrize("streaming", ["none", "sse", "websocket"])
def test_init_with_streaming(tmp_path, monkeypatch, streaming):
    """Test init with different streaming modes."""
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["init", "test-agent", "--streaming", streaming, "-f"])
    assert result.exit_code == 0
    content = yaml.safe_load(Path("Dockfile.yaml").read_text())
    assert content["expose"]["streaming"] == streaming


def test_init_invalid_streaming(tmp_path, monkeypatch):
    """Test init rejects invalid streaming mode."""
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["init", "test-agent", "--streaming", "invalid"])
    assert result.exit_code == 1
    assert "invalid streaming mode" in result.output.lower()


# =============================================================================
# Secrets Option Tests
# =============================================================================


def test_init_with_secrets(tmp_path, monkeypatch):
    """Test init with secrets section enabled."""
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["init", "test-agent", "--secrets", "-f"])
    assert result.exit_code == 0
    content = yaml.safe_load(Path("Dockfile.yaml").read_text())
    assert "secrets" in content
    assert "required" in content["secrets"]
    # Default secrets should include OPENAI_API_KEY
    secret_names = [s["name"] for s in content["secrets"]["required"]]
    assert "OPENAI_API_KEY" in secret_names
    assert "Secrets: enabled" in result.output


def test_init_with_custom_secret_names(tmp_path, monkeypatch):
    """Test init with custom secret names."""
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(
        app, ["init", "test-agent", "--secret-names", "MY_KEY,ANOTHER_KEY", "-f"]
    )
    assert result.exit_code == 0
    content = yaml.safe_load(Path("Dockfile.yaml").read_text())
    assert "secrets" in content
    secret_names = [s["name"] for s in content["secrets"]["required"]]
    assert "MY_KEY" in secret_names
    assert "ANOTHER_KEY" in secret_names


def test_init_secret_names_normalized(tmp_path, monkeypatch):
    """Test that secret names are normalized to uppercase."""
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(
        app, ["init", "test-agent", "--secret-names", "my-key,another-key", "-f"]
    )
    assert result.exit_code == 0
    content = yaml.safe_load(Path("Dockfile.yaml").read_text())
    secret_names = [s["name"] for s in content["secrets"]["required"]]
    assert "MY_KEY" in secret_names
    assert "ANOTHER_KEY" in secret_names


def test_init_auth_adds_secret(tmp_path, monkeypatch):
    """Test that api_key auth adds MY_AGENT_KEY to secrets when --secrets is used."""
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(
        app, ["init", "test-agent", "--auth", "api_key", "--secrets", "-f"]
    )
    assert result.exit_code == 0
    content = yaml.safe_load(Path("Dockfile.yaml").read_text())
    secret_names = [s["name"] for s in content["secrets"]["required"]]
    assert "MY_AGENT_KEY" in secret_names


# =============================================================================
# CORS Option Tests
# =============================================================================


def test_init_with_cors(tmp_path, monkeypatch):
    """Test init with CORS enabled."""
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["init", "test-agent", "--cors", "-f"])
    assert result.exit_code == 0
    content = yaml.safe_load(Path("Dockfile.yaml").read_text())
    assert "cors" in content["expose"]
    assert content["expose"]["cors"]["origins"] == ["*"]
    assert "GET" in content["expose"]["cors"]["methods"]
    assert "POST" in content["expose"]["cors"]["methods"]
    assert "CORS: enabled" in result.output


# =============================================================================
# Observability Option Tests
# =============================================================================


def test_init_with_observability(tmp_path, monkeypatch):
    """Test init with observability section."""
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["init", "test-agent", "--observability", "-f"])
    assert result.exit_code == 0
    content = yaml.safe_load(Path("Dockfile.yaml").read_text())
    assert "observability" in content
    assert content["observability"]["tracing"] is True
    assert content["observability"]["log_level"] == "info"
    assert "Observability: enabled" in result.output


def test_init_with_obs_short_flag(tmp_path, monkeypatch):
    """Test init with --obs shorthand for observability."""
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["init", "test-agent", "--obs", "-f"])
    assert result.exit_code == 0
    content = yaml.safe_load(Path("Dockfile.yaml").read_text())
    assert "observability" in content


# =============================================================================
# Metadata Option Tests
# =============================================================================


def test_init_with_metadata(tmp_path, monkeypatch):
    """Test init with metadata section."""
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["init", "test-agent", "--metadata", "-f"])
    assert result.exit_code == 0
    content = yaml.safe_load(Path("Dockfile.yaml").read_text())
    assert "metadata" in content
    assert "maintainer" in content["metadata"]
    assert content["metadata"]["version"] == "v0.1.0"
    assert "test-agent" in content["metadata"]["tags"]


# =============================================================================
# Full Option Tests
# =============================================================================


def test_init_with_full(tmp_path, monkeypatch):
    """Test init with --full flag enables all optional sections."""
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["init", "test-agent", "--full", "-f"])
    assert result.exit_code == 0
    content = yaml.safe_load(Path("Dockfile.yaml").read_text())

    # All optional sections should be present
    assert "auth" in content
    assert content["auth"]["mode"] == "api_key"
    assert "secrets" in content
    assert "cors" in content["expose"]
    assert "observability" in content
    assert "metadata" in content


def test_init_full_with_custom_auth(tmp_path, monkeypatch):
    """Test --full respects explicitly set auth mode."""
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["init", "test-agent", "--full", "--auth", "jwt", "-f"])
    assert result.exit_code == 0
    content = yaml.safe_load(Path("Dockfile.yaml").read_text())
    assert content["auth"]["mode"] == "jwt"


# =============================================================================
# Combined Options Tests
# =============================================================================


def test_init_combined_options(tmp_path, monkeypatch):
    """Test init with multiple options combined."""
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(
        app,
        [
            "init",
            "my-agent",
            "--framework",
            "langchain",
            "--auth",
            "api_key",
            "--streaming",
            "websocket",
            "--cors",
            "--observability",
            "-f",
        ],
    )
    assert result.exit_code == 0
    content = yaml.safe_load(Path("Dockfile.yaml").read_text())

    assert content["agent"]["framework"] == "langchain"
    assert content["auth"]["mode"] == "api_key"
    assert content["expose"]["streaming"] == "websocket"
    assert content["expose"]["cors"] is not None
    assert content["observability"]["tracing"] is True


def test_init_handler_with_auth(tmp_path, monkeypatch):
    """Test handler mode combined with authentication."""
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(
        app,
        ["init", "my-service", "--handler", "--auth", "api_key", "--secrets", "-f"],
    )
    assert result.exit_code == 0
    content = yaml.safe_load(Path("Dockfile.yaml").read_text())

    assert "handler" in content["agent"]
    assert content["agent"]["framework"] == "custom"
    assert content["auth"]["mode"] == "api_key"
    assert "secrets" in content


# =============================================================================
# Output Display Tests
# =============================================================================


def test_init_shows_configuration_summary(tmp_path, monkeypatch):
    """Test init shows configuration summary."""
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(
        app, ["init", "test-agent", "--auth", "api_key", "--cors", "-f"]
    )
    assert result.exit_code == 0
    assert "Configuration:" in result.output
    assert "Mode:" in result.output
    assert "Framework:" in result.output
    assert "Streaming:" in result.output


def test_init_shows_next_steps(tmp_path, monkeypatch):
    """Test init shows next steps guidance."""
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["init", "test-agent", "-f"])
    assert result.exit_code == 0
    assert "Next steps:" in result.output
    assert "dockrion validate" in result.output
    assert "dockrion test" in result.output


def test_init_handler_shows_handler_specific_guidance(tmp_path, monkeypatch):
    """Test handler mode shows handler-specific next steps."""
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["init", "my-service", "--handler", "-f"])
    assert result.exit_code == 0
    assert "Set the correct handler path" in result.output


def test_init_jwt_shows_jwt_specific_guidance(tmp_path, monkeypatch):
    """Test JWT auth shows JWT-specific configuration guidance."""
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["init", "test-agent", "--auth", "jwt", "-f"])
    assert result.exit_code == 0
    assert "jwks_url" in result.output or "JWT" in result.output


# =============================================================================
# Generated YAML Validity Tests
# =============================================================================


def test_init_generates_valid_yaml(tmp_path, monkeypatch):
    """Test that generated Dockfile is valid YAML."""
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["init", "test-agent", "--full", "-f"])
    assert result.exit_code == 0

    # Should not raise exception
    content = yaml.safe_load(Path("Dockfile.yaml").read_text())
    assert content is not None
    assert content["version"] == "1.0"


def test_init_generates_valid_schema(tmp_path, monkeypatch):
    """Test that generated Dockfile passes schema validation."""
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["init", "test-agent", "--full", "-f"])
    assert result.exit_code == 0

    # Validate using the schema
    from dockrion_schema import DockSpec

    content = yaml.safe_load(Path("Dockfile.yaml").read_text())
    spec = DockSpec.model_validate(content)
    assert spec.agent.name == "test-agent"
