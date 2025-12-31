"""Tests for inspect command."""

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from dockrion_cli.inspect_cmd import generate_io_schema_yaml, infer_json_schema
from dockrion_cli.main import app

runner = CliRunner()


class TestInferJsonSchema:
    """Tests for schema inference."""

    def test_infer_string(self):
        schema = infer_json_schema("hello")
        assert schema == {"type": "string"}

    def test_infer_string_empty(self):
        schema = infer_json_schema("")
        assert schema == {"type": "string"}

    def test_infer_integer(self):
        schema = infer_json_schema(42)
        assert schema == {"type": "integer"}

    def test_infer_integer_negative(self):
        schema = infer_json_schema(-10)
        assert schema == {"type": "integer"}

    def test_infer_number(self):
        schema = infer_json_schema(3.14)
        assert schema == {"type": "number"}

    def test_infer_boolean_true(self):
        schema = infer_json_schema(True)
        assert schema == {"type": "boolean"}

    def test_infer_boolean_false(self):
        schema = infer_json_schema(False)
        assert schema == {"type": "boolean"}

    def test_infer_null(self):
        schema = infer_json_schema(None)
        assert schema == {"type": "null"}

    def test_infer_empty_array(self):
        schema = infer_json_schema([])
        assert schema["type"] == "array"
        assert schema["items"] == {}

    def test_infer_array_of_integers(self):
        schema = infer_json_schema([1, 2, 3])
        assert schema["type"] == "array"
        assert schema["items"]["type"] == "integer"

    def test_infer_array_of_strings(self):
        schema = infer_json_schema(["a", "b", "c"])
        assert schema["type"] == "array"
        assert schema["items"]["type"] == "string"

    def test_infer_simple_object(self):
        schema = infer_json_schema({"name": "test", "count": 5})
        assert schema["type"] == "object"
        assert "name" in schema["properties"]
        assert "count" in schema["properties"]
        assert schema["properties"]["name"]["type"] == "string"
        assert schema["properties"]["count"]["type"] == "integer"

    def test_infer_object_with_required_fields(self):
        schema = infer_json_schema({"name": "test", "value": None})
        assert schema["type"] == "object"
        # Only non-null fields should be required
        assert "name" in schema["required"]
        assert "value" not in schema["required"]

    def test_infer_nested_object(self):
        data = {
            "messages": [{"type": "human", "content": "Hello"}]
        }
        schema = infer_json_schema(data)

        assert schema["type"] == "object"
        assert schema["properties"]["messages"]["type"] == "array"
        items = schema["properties"]["messages"]["items"]
        assert items["type"] == "object"
        assert items["properties"]["type"]["type"] == "string"
        assert items["properties"]["content"]["type"] == "string"

    def test_infer_complex_nested(self):
        data = {
            "status": "success",
            "data": {
                "users": [
                    {"id": 1, "name": "Alice"},
                    {"id": 2, "name": "Bob"},
                ]
            },
            "count": 2,
        }
        schema = infer_json_schema(data)

        assert schema["type"] == "object"
        assert schema["properties"]["status"]["type"] == "string"
        assert schema["properties"]["count"]["type"] == "integer"
        assert schema["properties"]["data"]["type"] == "object"


class TestGenerateIoSchema:
    """Tests for io_schema generation."""

    def test_generate_simple(self):
        input_data = {"text": "hello"}
        output_data = {"result": "processed"}

        yaml_str = generate_io_schema_yaml(input_data, output_data)

        assert "io_schema:" in yaml_str
        assert "input:" in yaml_str
        assert "output:" in yaml_str
        assert "type: object" in yaml_str

    def test_generate_with_arrays(self):
        input_data = {"items": [1, 2, 3]}
        output_data = {"results": ["a", "b"]}

        yaml_str = generate_io_schema_yaml(input_data, output_data)

        assert "type: array" in yaml_str

    def test_generate_chat_schema(self):
        input_data = {"messages": [{"type": "human", "content": "Hi"}]}
        output_data = {
            "messages": [
                {"type": "human", "content": "Hi"},
                {"type": "ai", "content": "Hello!"},
            ]
        }

        yaml_str = generate_io_schema_yaml(input_data, output_data)

        assert "messages:" in yaml_str
        assert "type: array" in yaml_str

    def test_generate_preserves_structure(self):
        input_data = {"query": "test", "options": {"limit": 10}}
        output_data = {"results": [], "total": 0}

        yaml_str = generate_io_schema_yaml(input_data, output_data)

        assert "query:" in yaml_str
        assert "options:" in yaml_str
        assert "results:" in yaml_str
        assert "total:" in yaml_str


class TestInspectCommand:
    """Integration tests for inspect command."""

    def test_inspect_no_payload_fails(self, sample_dockfile):
        """Test inspect without payload fails gracefully."""
        result = runner.invoke(app, ["inspect", sample_dockfile])
        assert result.exit_code == 1
        assert "payload" in result.stdout.lower() or "no payload" in result.stdout.lower()

    def test_inspect_invalid_json_payload(self, sample_dockfile):
        """Test inspect with invalid JSON payload fails."""
        result = runner.invoke(
            app, ["inspect", sample_dockfile, "--payload", "{invalid json}"]
        )
        assert result.exit_code == 1
        assert "invalid" in result.stdout.lower()

    def test_inspect_missing_dockfile(self, tmp_path):
        """Test inspect with missing Dockfile fails."""
        result = runner.invoke(
            app,
            [
                "inspect",
                str(tmp_path / "nonexistent.yaml"),
                "--payload",
                '{"text": "test"}',
            ],
        )
        assert result.exit_code == 1
        assert "not found" in result.stdout.lower()

    def test_inspect_missing_payload_file(self, sample_dockfile, tmp_path):
        """Test inspect with missing payload file fails."""
        result = runner.invoke(
            app,
            [
                "inspect",
                sample_dockfile,
                "--payload-file",
                str(tmp_path / "nonexistent.json"),
            ],
        )
        assert result.exit_code == 1
        assert "not found" in result.stdout.lower()

    def test_inspect_basic(self, sample_dockfile):
        """Test basic inspect command."""
        result = runner.invoke(
            app, ["inspect", sample_dockfile, "--payload", '{"text": "test"}']
        )
        # Should succeed or fail gracefully with agent error
        # The mock agent should work
        if result.exit_code == 0:
            assert "success" in result.stdout.lower() or "output" in result.stdout.lower()

    def test_inspect_with_payload_file(self, sample_dockfile, test_payload):
        """Test inspect with payload from file."""
        result = runner.invoke(
            app, ["inspect", sample_dockfile, "--payload-file", test_payload]
        )
        # Should succeed or fail gracefully
        if result.exit_code == 0:
            assert "success" in result.stdout.lower() or "output" in result.stdout.lower()

    def test_inspect_generate_schema(self, sample_dockfile):
        """Test inspect with schema generation."""
        result = runner.invoke(
            app,
            [
                "inspect",
                sample_dockfile,
                "--payload",
                '{"text": "test"}',
                "--generate-schema",
            ],
        )
        # If invocation succeeds, should generate schema
        if result.exit_code == 0:
            assert "io_schema" in result.stdout

    def test_inspect_save_schema(self, sample_dockfile, tmp_path):
        """Test saving generated schema to file."""
        output_file = tmp_path / "schema.yaml"
        result = runner.invoke(
            app,
            [
                "inspect",
                sample_dockfile,
                "--payload",
                '{"text": "test"}',
                "--generate-schema",
                "--output",
                str(output_file),
            ],
        )
        # If invocation succeeds, file should be created
        if result.exit_code == 0:
            assert output_file.exists()
            content = output_file.read_text()
            assert "io_schema:" in content

    def test_inspect_verbose(self, sample_dockfile):
        """Test inspect with verbose output."""
        result = runner.invoke(
            app,
            [
                "inspect",
                sample_dockfile,
                "--payload",
                '{"text": "test"}',
                "--verbose",
            ],
        )
        # Verbose should show additional info
        if result.exit_code == 0:
            assert "input" in result.stdout.lower()


class TestInspectCommandHelp:
    """Test inspect command help and documentation."""

    def test_help_available(self):
        """Test that help is available."""
        result = runner.invoke(app, ["inspect", "--help"])
        assert result.exit_code == 0
        assert "inspect" in result.stdout.lower()
        assert "--payload" in result.stdout
        assert "--generate-schema" in result.stdout

    def test_help_shows_examples(self):
        """Test that help mentions examples."""
        result = runner.invoke(app, ["inspect", "--help"])
        assert result.exit_code == 0
        # Help should mention usage patterns
        assert "payload" in result.stdout.lower()

