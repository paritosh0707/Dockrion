"""Mock agent for testing purposes."""
from typing import Dict, Any


class MockAgent:
    """A simple mock agent that echoes input."""
    
    def invoke(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Echo the input back with a result field."""
        return {
            "result": f"Processed: {payload.get('text', 'no input')}",
            "status": "success"
        }


def build_agent():
    """Factory function to build the mock agent."""
    return MockAgent()

