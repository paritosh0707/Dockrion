import subprocess, json, os, time, http.server, socketserver, threading
from agentdock_sdk.client import load_dockspec

def deploy(dockfile_path: str, target: str="local", **_):
    spec = load_dockspec(dockfile_path)
    # v1: build a local image name and docker run
    image = f"agentdock/{spec.agent.name}:dev"
    subprocess.check_call(["docker","build","-t",image,"-f","-","."], input=_render_dockerfile(spec).encode(), cwd=".")
    return {"image": image, "status": "built"}

def run_local(dockfile_path: str):
    spec = load_dockspec(dockfile_path)
    code = _render_runtime(spec)
    os.makedirs(".agentdock_runtime", exist_ok=True)
    with open(".agentdock_runtime/main.py", "w") as f:
        f.write(code)
    # simple run via uvicorn
    subprocess.check_call(["python","-m","pip","install","fastapi","uvicorn","prometheus-client"])
    host, port = spec.expose.host, str(spec.expose.port)
    return subprocess.Popen(["python","-m","uvicorn","main:app","--host",host,"--port",port], cwd=".agentdock_runtime")

def _render_dockerfile(spec):
    return f"""FROM python:3.11-slim
    RUN pip install fastapi uvicorn prometheus-client
    WORKDIR /app
    COPY .agentdock_runtime /app
    EXPOSE {spec.expose.port}
    CMD ["python","-m","uvicorn","main:app","--host","0.0.0.0","--port","{spec.expose.port}"]
    """

def _render_runtime(spec):
    # Minimal FastAPI runtime honoring /invoke /schema /health /metrics
    return f"""from fastapi import FastAPI, Request, HTTPException
    from typing import Dict, Any
    import time
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    from agentdock_common.auth_utils import validate_api_key
    from agentdock_adapters.registry import get_adapter
    from agentdock_policy.policy_engine import PolicyEngine

    app = FastAPI()
    SPEC = {json.dumps(spec.model_dump())}

    ADAPTER = get_adapter(SPEC['agent']['framework'])
    ADAPTER.load(SPEC['agent']['entrypoint'])
    POLICY = PolicyEngine.from_dockspec(type("X",(object,), {{"policies": type("Y",(object,), {{
        "tools": type("T",(object,), {{"allowed":SPEC.get("policies",{{}}).get("tools",{{}}).get("allowed",[]), "deny_by_default": SPEC.get("policies",{{}}).get("tools",{{}}).get("deny_by_default", True)}})(),
        "safety": type("S",(object,), {{"redact_patterns": SPEC.get("policies",{{}}).get("safety",{{}}).get("redact_patterns", []),
                                       "max_output_chars": SPEC.get("policies",{{}}).get("safety",{{}}).get("max_output_chars", None)}})()
    }})()}})() )

    @app.get("/health")
    async def health():
        return {{"status":"ok"}}

    @app.get("/schema")
    async def schema():
        return SPEC.get("io_schema",{{}})

    @app.get("/metrics")
    async def metrics():
        data = generate_latest()
        return Response(content=data, media_type=CONTENT_TYPE_LATEST)

    from fastapi.responses import JSONResponse, Response

    @app.post("/invoke")
    async def invoke(req: Request):
        api_key = req.headers.get("X-API-Key")
        validate_api_key(api_key, os.environ.get("AGENTDOCK_API_KEY"))
        payload = await req.json()
        t0 = time.time()
        out = ADAPTER.invoke(payload)
        # simple string post-policy if notes exist
        if isinstance(out, dict) and "notes" in out and isinstance(out["notes"], str):
            out["notes"] = POLICY.post_invoke(out["notes"])
        dt = time.time()-t0
        return JSONResponse({{"output": out, "latency_s": dt}})
    """
