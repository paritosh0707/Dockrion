from .langgraph_adapter import LangGraphAdapter

def get_adapter(framework: str):
    if framework == "langgraph":
        return LangGraphAdapter()
    raise ValueError(f"Unsupported framework: {framework}")
