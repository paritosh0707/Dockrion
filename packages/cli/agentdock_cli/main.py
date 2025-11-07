import typer
from agentdock_sdk.validate import validate
from agentdock_sdk.deploy import deploy, run_local

app = typer.Typer(help="AgentDock CLI")

@app.command()
def validate_cmd(path: str = "Dockfile.yaml"):
    res = validate(path)
    typer.echo("✅ Dockfile valid" if res["valid"] else "❌ Invalid")

@app.command()
def build(path: str = "Dockfile.yaml"):
    info = deploy(path, target="local")
    typer.echo(f"Built image: {info['image']}")

@app.command()
def run(path: str = "Dockfile.yaml"):
    proc = run_local(path)
    typer.echo("Runtime started. Ctrl+C to stop.")
    try:
        proc.wait()
    except KeyboardInterrupt:
        proc.terminate()
