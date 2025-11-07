from agentdock_schema.dockfile_v1 import DockSpec
import yaml
def validate(path: str) -> dict:
    data = yaml.safe_load(open(path,"r"))
    DockSpec.model_validate(data)
    return {"valid": True}
