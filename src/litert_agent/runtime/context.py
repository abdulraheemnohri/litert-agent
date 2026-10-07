"""Runtime context."""

from litert_agent.config import Config
from litert_agent.environment.capabilities import Capabilities


class AgentContext:
    def __init__(self, config: Config, capabilities: Capabilities):
        self.config = config
        self.capabilities = capabilities
