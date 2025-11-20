"""Pytest configuration and fixtures for CLI tests."""
import pytest
from pathlib import Path
from typer.testing import CliRunner


@pytest.fixture
def runner():
    """Create CLI test runner."""
    return CliRunner()


@pytest.fixture
def sample_dockfile(tmp_path):
    """Create a sample Dockfile for testing."""
    dockfile_content = """version: "1.0"
agent:
  name: test-agent
  description: "Test agent for CLI testing"
  entrypoint: tests.mock_agent:build_agent
  framework: langgraph
model:
  provider: openai
  name: gpt-4o-mini
io_schema:
  input:
    type: object
    properties:
      text: { type: string }
  output:
    type: object
    properties:
      result: { type: string }
expose:
  port: 8080
  host: "0.0.0.0"
"""
    dockfile_path = tmp_path / "Dockfile.yaml"
    dockfile_path.write_text(dockfile_content)
    return str(dockfile_path)


@pytest.fixture
def invalid_dockfile(tmp_path):
    """Create an invalid Dockfile."""
    dockfile_path = tmp_path / "invalid.yaml"
    dockfile_path.write_text("invalid: yaml: syntax:")
    return str(dockfile_path)


@pytest.fixture
def test_payload(tmp_path):
    """Create a test payload JSON file."""
    import json
    payload = {"text": "test input"}
    payload_file = tmp_path / "payload.json"
    payload_file.write_text(json.dumps(payload))
    return str(payload_file)

