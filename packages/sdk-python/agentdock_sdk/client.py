import yaml, time
from agentdock_schema.dockfile_v1 import DockSpec

def load_dockspec(path: str) -> DockSpec:
    data = yaml.safe_load(open(path, "r"))
    return DockSpec.model_validate(data)

# In v1 this is a placeholder; v1.1+ will talk to Controller service.
class ControllerClient:
    def __init__(self, base_url: str | None = None):
        self.base_url = base_url

    def status(self):
        return {"ok": True, "ts": time.time()}
