"""LiteRT-LM CLI Provider implementation.

LiteRT-LM is the only production inference backend. The adapter never fabricates
responses and never falls back to another provider.
"""
import asyncio
from litert_agent.model.discovery import LiteRTCLIDiscovery
from litert_agent.model.parser import ProtocolParser
from litert_agent.model.protocol import ProtocolMessage
from litert_agent.model.provider import ModelProvider

class LiteRTLMProvider(ModelProvider):
    def __init__(self, cli_path: str = "litert-lm", model_path: str = "", timeout: float = 120.0):
        self.cli_path, self.model_path, self.timeout = cli_path, model_path, timeout
        self.discovery_info: dict | None = None
        self.initialized = False

    async def initialize(self):
        exec_path = LiteRTCLIDiscovery.find_executable(self.cli_path)
        if not exec_path:
            self.discovery_info = {"available": False, "error": "LiteRT-LM CLI executable not found"}
        else:
            self.discovery_info = await LiteRTCLIDiscovery.inspect_help(exec_path)
            self.discovery_info["executable"] = exec_path
            self.discovery_info["model_configured"] = bool(self.model_path)
        self.initialized = True

    @staticmethod
    def _error(message: str) -> ProtocolMessage:
        return ProtocolMessage(type="error", content=message)

    async def generate(self, prompt: str, system_prompt: str | None = None) -> ProtocolMessage:
        if not self.initialized:
            await self.initialize()
        info = self.discovery_info or {}
        exec_path = info.get("executable")
        if not exec_path:
            return self._error("LiteRT-LM CLI unavailable. No fallback provider is permitted.")
        prompt_flag = info.get("prompt_flag")
        if not prompt_flag:
            return self._error("LiteRT-LM prompt interface was not discovered from --help; command syntax will not be invented.")
        full_prompt = f"{system_prompt}\n{prompt}" if system_prompt else prompt
        cmd = [exec_path, prompt_flag, full_prompt]
        if self.model_path and info.get("model_flag"):
            cmd.extend([info["model_flag"], self.model_path])
        try:
            proc = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=self.timeout)
            out = stdout.decode("utf-8", errors="replace").strip()
            err = stderr.decode("utf-8", errors="replace").strip()
            if proc.returncode != 0:
                return self._error(f"LiteRT-LM exited with code {proc.returncode}: {err[-2000:]}")
            if not out:
                return self._error(f"LiteRT-LM returned no stdout: {err[-2000:]}")
            return ProtocolParser.parse(out)
        except TimeoutError:
            return self._error(f"LiteRT-LM execution timed out after {self.timeout}s")
        except Exception as exc:
            return self._error(f"LiteRT-LM execution error: {exc}")
