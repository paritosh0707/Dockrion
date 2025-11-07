from importlib import import_module
from typing import Dict, Any
from .base import AgentAdapter

class LangGraphAdapter(AgentAdapter):
    def __init__(self):
        self._runner = None

    def load(self, entrypoint: str) -> None:
        mod, factory = entrypoint.split(":")
        fn = getattr(import_module(mod), factory)
        self._runner = fn()  # expects object with .invoke(dict)->dict

    def invoke(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        assert self._runner is not None, "Adapter not loaded"
        return self._runner.invoke(payload)
