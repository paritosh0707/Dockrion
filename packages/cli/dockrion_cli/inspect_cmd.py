"""Inspect command - Analyze agent output and generate schemas."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import typer
from rich.panel import Panel
from rich.syntax import Syntax

from .utils import console, error, handle_error, info, success, warning

# Note: The inspect function is standalone, not using Typer app pattern
# because main.py uses app.command() decorator pattern


def infer_json_schema(value: Any, required: bool = True) -> Dict[str, Any]:
    """
    Infer JSON Schema from a Python value.
    
    Args:
        value: Any Python value (after serialization)
        required: Whether to mark fields as required
        
    Returns:
        JSON Schema dictionary
    """
    if value is None:
        return {"type": "null"}

    if isinstance(value, bool):
        return {"type": "boolean"}

    if isinstance(value, int):
        return {"type": "integer"}

    if isinstance(value, float):
        return {"type": "number"}

    if isinstance(value, str):
        return {"type": "string"}

    if isinstance(value, list):
        if not value:
            return {"type": "array", "items": {}}

        # Infer items schema from first element
        # (Could be smarter and merge schemas from all elements)
        items_schema = infer_json_schema(value[0], required=False)
        return {"type": "array", "items": items_schema}

    if isinstance(value, dict):
        properties = {}
        required_fields = []

        for k, v in value.items():
            properties[k] = infer_json_schema(v, required=False)
            if v is not None:
                required_fields.append(k)

        schema: Dict[str, Any] = {
            "type": "object",
            "properties": properties,
        }

        if required_fields:
            schema["required"] = sorted(required_fields)

        return schema

    # Fallback for any other type
    return {"type": "string"}


def generate_io_schema_yaml(
    input_data: Dict[str, Any],
    output_data: Dict[str, Any],
) -> str:
    """
    Generate io_schema YAML section from input/output data.
    
    Args:
        input_data: Sample input payload
        output_data: Actual output from agent
        
    Returns:
        YAML string for io_schema section
    """
    try:
        import yaml
    except ImportError:
        raise ImportError("PyYAML required. Install with: pip install pyyaml")

    input_schema = infer_json_schema(input_data)
    output_schema = infer_json_schema(output_data)

    io_schema = {
        "io_schema": {
            "input": input_schema,
            "output": output_schema,
        }
    }

    return yaml.dump(io_schema, default_flow_style=False, sort_keys=False)


def inspect(
    path: str = typer.Argument("Dockfile.yaml", help="Path to Dockfile"),
    payload: Optional[str] = typer.Option(
        None, "--payload", "-p", help="JSON payload as string"
    ),
    payload_file: Optional[str] = typer.Option(
        None, "--payload-file", "-f", help="Path to JSON file with payload"
    ),
    generate_schema: bool = typer.Option(
        False, "--generate-schema", "-g", help="Generate io_schema from output"
    ),
    output_file: Optional[str] = typer.Option(
        None, "--output", "-o", help="Save output/schema to file"
    ),
    show_raw: bool = typer.Option(
        False, "--raw", "-r", help="Show raw Python repr instead of JSON"
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed output"),
):
    """
    Inspect agent output and optionally generate io_schema.
    
    This command helps you understand what your agent returns and
    automatically generates the io_schema section for your Dockfile.
    
    Examples:
        # See what your agent returns (serialized)
        dockrion inspect --payload '{"text": "hello"}'
        
        # Generate io_schema from actual output
        dockrion inspect -p '{"text": "hello"}' --generate-schema
        
        # Save generated schema to file
        dockrion inspect -p '{"text": "hello"}' -g -o io_schema.yaml
        
        # With payload from file
        dockrion inspect -f input.json --generate-schema
    """
    try:
        # Validate Dockfile exists
        if not Path(path).exists():
            error(f"Dockfile not found: {path}")
            raise typer.Exit(1)

        # Load payload
        payload_data: Optional[Dict[str, Any]] = None
        if payload_file:
            try:
                with open(payload_file, "r") as f:
                    payload_data = json.load(f)
                if verbose:
                    info(f"Loaded payload from {payload_file}")
            except FileNotFoundError:
                error(f"Payload file not found: {payload_file}")
                raise typer.Exit(1)
            except json.JSONDecodeError as e:
                error(f"Invalid JSON in payload file: {str(e)}")
                raise typer.Exit(1)
        elif payload:
            try:
                payload_data = json.loads(payload)
            except json.JSONDecodeError as e:
                error(f"Invalid JSON payload: {str(e)}")
                raise typer.Exit(1)
        else:
            error("No payload provided")
            console.print("\n[dim]Provide input using either:[/dim]")
            console.print('  • [cyan]--payload \'{"key": "value"}\'[/cyan]')
            console.print("  • [cyan]--payload-file input.json[/cyan]")
            raise typer.Exit(1)

        # Show input
        if verbose:
            info(f"Inspecting agent from {path}")
            console.print("\n[bold]Input payload:[/bold]")
            syntax = Syntax(json.dumps(payload_data, indent=2), "json", theme="monokai")
            console.print(Panel(syntax, title="Input", border_style="blue"))

        # Import SDK and invoke agent
        try:
            from dockrion_sdk import invoke_local
        except ImportError:
            error("dockrion-sdk not installed. Install with: pip install dockrion-sdk")
            raise typer.Exit(1)

        # Invoke agent
        with console.status("[bold green]Invoking agent..."):
            result = invoke_local(path, payload_data)

        success("Agent invocation successful")
        console.print()

        # Display output
        if show_raw:
            # Raw Python representation
            console.print("[bold]Raw Output (repr):[/bold]")
            console.print(repr(result))
        else:
            # JSON output (uses deep_serialize from adapter)
            console.print("[bold]Serialized Output:[/bold]")
            try:
                output_json = json.dumps(result, indent=2)
                syntax = Syntax(output_json, "json", theme="monokai")
                console.print(Panel(syntax, title="Agent Output", border_style="green"))
            except TypeError as e:
                warning(f"Output contains non-serializable objects: {e}")
                console.print("[yellow]Falling back to repr():[/yellow]")
                console.print(repr(result))
                console.print(
                    "\n[dim]💡 Tip: Ensure your agent returns JSON-serializable output[/dim]"
                )
                raise typer.Exit(1)

        # Generate schema if requested
        if generate_schema:
            console.print()
            info("Generating io_schema from output...")

            try:
                schema_yaml = generate_io_schema_yaml(payload_data, result)

                console.print("\n[bold]Generated io_schema:[/bold]")
                syntax = Syntax(schema_yaml, "yaml", theme="monokai")
                console.print(Panel(syntax, title="io_schema", border_style="cyan"))

                # Save to file if requested
                if output_file:
                    with open(output_file, "w") as f:
                        f.write(schema_yaml)
                    success(f"Schema saved to {output_file}")
                    console.print(
                        f"\n[dim]💡 Copy the io_schema section to your Dockfile.yaml[/dim]"
                    )

            except ImportError as e:
                error(str(e))
                raise typer.Exit(1)

        # Save output to file (without schema generation)
        elif output_file:
            try:
                with open(output_file, "w") as f:
                    json.dump(result, f, indent=2)
                info(f"Output saved to {output_file}")
            except TypeError as e:
                warning(f"Failed to save output: {str(e)}")

    except typer.Exit:
        raise
    except KeyboardInterrupt:
        info("\nInspection cancelled by user")
        raise typer.Exit(130)
    except Exception as e:
        handle_error(e, verbose)
        raise typer.Exit(1)

