from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal, Dict, List

class IOSubSchema(BaseModel):
    type: Literal["object"] = "object"
    properties: Dict[str, dict] = {}
    required: List[str] = []

class IOSchema(BaseModel):
    input: Optional[IOSubSchema] = None
    output: Optional[IOSubSchema] = None

class AgentCfg(BaseModel):
    name: str
    description: Optional[str] = None
    entrypoint: str
    framework: Literal["langgraph","langchain"]

class ModelCfg(BaseModel):
    provider: Literal["openai","azure","anthropic","google","ollama","custom"]
    name: str
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    endpoint: Optional[str] = None
    extra: Dict[str, object] = {}

class ToolPolicy(BaseModel):
    allowed: List[str] = []
    deny_by_default: bool = True

class SafetyPolicy(BaseModel):
    redact_patterns: List[str] = []
    max_output_chars: Optional[int] = None
    block_prompt_injection: bool = True
    halt_on_violation: bool = False

class Policies(BaseModel):
    tools: Optional[ToolPolicy] = ToolPolicy()
    safety: Optional[SafetyPolicy] = SafetyPolicy()

class RoleCfg(BaseModel):
    name: str
    permissions: List[str]

class ApiKeysCfg(BaseModel):
    enabled: bool = True
    rotation_days: Optional[int] = 30

class AuthCfg(BaseModel):
    mode: Literal["jwt","api_key","oauth2"] = "api_key"
    api_keys: Optional[ApiKeysCfg] = ApiKeysCfg()
    roles: List[RoleCfg] = []
    rate_limits: Dict[str,str] = {}

class Observability(BaseModel):
    langfuse: Optional[Dict[str,str]] = None
    tracing: bool = True
    log_level: Literal["debug","info","warn","error"] = "info"
    metrics: Dict[str,bool] = {"latency": True, "tokens": True, "cost": True}

class Expose(BaseModel):
    rest: bool = True
    streaming: Literal["sse","websocket","none"] = "sse"
    port: int = 8080
    host: str = "0.0.0.0"
    cors: Optional[Dict[str, List[str]]] = None

class Metadata(BaseModel):
    maintainer: Optional[str] = None
    version: Optional[str] = None
    tags: List[str] = []

class DockSpec(BaseModel):
    version: Literal["1.0"]
    agent: AgentCfg
    model: ModelCfg
    io_schema: IOSchema
    arguments: Dict[str, object] = {}
    policies: Optional[Policies] = Policies()
    auth: AuthCfg
    observability: Optional[Observability] = Observability()
    expose: Expose
    metadata: Optional[Metadata] = Metadata()

    @field_validator("agent")
    @classmethod
    def _validate_entrypoint(cls, v: AgentCfg):
        if ":" not in v.entrypoint:
            raise ValueError("agent.entrypoint must be '<module>:<callable>'")
        return v
