"""Tests for lenient io_schema mode."""

import pytest
import yaml

from dockrion_schema import DockSpec, IOSchema, IOSubSchema


class TestStrictField:
    """Tests for strict/lenient io_schema mode."""

    def test_strict_defaults_to_true(self):
        """Test that strict defaults to True."""
        io_schema = IOSchema(
            input=IOSubSchema(type="object"),
            output=IOSubSchema(type="object"),
        )
        assert io_schema.strict is True

    def test_strict_explicit_true(self):
        """Test explicit strict=True."""
        io_schema = IOSchema(
            strict=True,
            input=IOSubSchema(type="object"),
            output=IOSubSchema(type="object"),
        )
        assert io_schema.strict is True

    def test_strict_false(self):
        """Test strict=False."""
        io_schema = IOSchema(
            strict=False,
            input=IOSubSchema(type="object"),
            output=IOSubSchema(type="object"),
        )
        assert io_schema.strict is False

    def test_strict_with_only_input(self):
        """Test strict=False with only input schema."""
        io_schema = IOSchema(
            strict=False,
            input=IOSubSchema(type="object"),
        )
        assert io_schema.strict is False
        assert io_schema.input is not None
        assert io_schema.output is None


class TestOptionalOutput:
    """Tests for optional output schema."""

    def test_output_can_be_none(self):
        """Test that output can be None."""
        io_schema = IOSchema(
            input=IOSubSchema(type="object"),
            output=None,
        )
        assert io_schema.output is None
        assert io_schema.input is not None

    def test_output_defaults_to_none(self):
        """Test that output defaults to None if not provided."""
        io_schema = IOSchema(
            input=IOSubSchema(type="object"),
        )
        assert io_schema.output is None

    def test_both_input_and_output_none(self):
        """Test that both can be None (edge case)."""
        io_schema = IOSchema()
        assert io_schema.input is None
        assert io_schema.output is None
        assert io_schema.strict is True


class TestFullDockSpecWithLenient:
    """Tests for full DockSpec with lenient mode."""

    def test_full_spec_with_lenient_mode(self):
        """Test full DockSpec with lenient mode."""
        spec = DockSpec(
            version="1.0",
            agent={
                "name": "test-agent",
                "entrypoint": "app.main:build_graph",
                "framework": "langgraph",
            },
            io_schema={
                "strict": False,
                "input": {"type": "object"},
                "output": {"type": "object"},
            },
            expose={"port": 8080},
        )
        assert spec.io_schema.strict is False
        assert spec.io_schema.input is not None
        assert spec.io_schema.output is not None

    def test_full_spec_with_strict_default(self):
        """Test full DockSpec with strict default."""
        spec = DockSpec(
            version="1.0",
            agent={
                "name": "test-agent",
                "entrypoint": "app.main:build_graph",
                "framework": "langgraph",
            },
            io_schema={
                "input": {"type": "object"},
                "output": {"type": "object"},
            },
            expose={"port": 8080},
        )
        assert spec.io_schema.strict is True

    def test_full_spec_with_no_output_schema(self):
        """Test full DockSpec with no output schema."""
        spec = DockSpec(
            version="1.0",
            agent={
                "name": "test-agent",
                "entrypoint": "app.main:build_graph",
                "framework": "langgraph",
            },
            io_schema={
                "input": {"type": "object"},
            },
            expose={"port": 8080},
        )
        assert spec.io_schema.input is not None
        assert spec.io_schema.output is None


class TestYamlParsing:
    """Tests for parsing YAML with lenient mode."""

    def test_parse_yaml_with_strict_false(self):
        """Test parsing YAML with strict=False."""
        yaml_str = """
io_schema:
  strict: false
  input:
    type: object
    properties:
      query:
        type: string
  output:
    type: object
"""
        data = yaml.safe_load(yaml_str)
        io_schema = IOSchema(**data["io_schema"])

        assert io_schema.strict is False
        assert io_schema.input is not None
        assert io_schema.output is not None

    def test_parse_yaml_without_output(self):
        """Test parsing YAML without output schema."""
        yaml_str = """
io_schema:
  input:
    type: object
    properties:
      text:
        type: string
"""
        data = yaml.safe_load(yaml_str)
        io_schema = IOSchema(**data["io_schema"])

        assert io_schema.input is not None
        assert io_schema.output is None
        assert io_schema.strict is True  # Default

    def test_parse_full_dockfile_lenient(self):
        """Test parsing full Dockfile with lenient mode."""
        yaml_str = """
version: "1.0"
agent:
  name: chat-agent
  entrypoint: app.graph:build_graph
  framework: langgraph
io_schema:
  strict: false
  input:
    type: object
    properties:
      messages:
        type: array
        items:
          type: object
  output:
    type: object
expose:
  port: 8080
"""
        data = yaml.safe_load(yaml_str)
        spec = DockSpec.model_validate(data)

        assert spec.io_schema.strict is False
        assert spec.io_schema.input is not None
        assert spec.io_schema.output is not None


class TestLenientModeUseCases:
    """Test real-world use cases for lenient mode."""

    def test_chat_agent_lenient_mode(self):
        """Test typical chat agent configuration with lenient mode."""
        spec = DockSpec(
            version="1.0",
            agent={
                "name": "chat-agent",
                "entrypoint": "app.graph:build_chat",
                "framework": "langgraph",
            },
            io_schema={
                "strict": False,
                "input": {
                    "type": "object",
                    "properties": {
                        "messages": {
                            "type": "array",
                            "items": {"type": "object"},
                        }
                    },
                    "required": ["messages"],
                },
                "output": {"type": "object"},
            },
            expose={"port": 8080},
        )

        assert spec.io_schema.strict is False
        assert "messages" in spec.io_schema.input.properties

    def test_discovery_mode_no_output(self):
        """Test schema discovery mode with no output schema."""
        spec = DockSpec(
            version="1.0",
            agent={
                "name": "new-agent",
                "entrypoint": "app.graph:build_agent",
                "framework": "langgraph",
            },
            io_schema={
                "input": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                    },
                },
                # output not specified - will be discovered
            },
            expose={"port": 8080},
        )

        assert spec.io_schema.input is not None
        assert spec.io_schema.output is None
        # Strict defaults to True but output is None so validation would be skipped

