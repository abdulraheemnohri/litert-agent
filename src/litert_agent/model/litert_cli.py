"""LiteRT-LM CLI Provider implementation."""

import asyncio
from litert_agent.model.provider import ModelProvider
from litert_agent.model.protocol import ProtocolMessage
from litert_agent.model.parser import ProtocolParser
from litert_agent.model.discovery import LiteRTCLIDiscovery

class LiteRTLMProvider(ModelProvider):
    def __init__(self, cli_path: str = "litert-lm", model_path: str = "", timeout: float = 120.0):
        self.cli_path = cli_path
        self.model_path = model_path
        self.timeout = timeout
        self.discovery_info: dict | None = None

    async def initialize(self):
        exec_path = LiteRTCLIDiscovery.find_executable(self.cli_path)
        if not exec_path:
            self.discovery_info = {"available": False}
            return
        self.discovery_info = await LiteRTCLIDiscovery.inspect_help(exec_path)

    async def generate(self, prompt: str, system_prompt: str | None = None) -> ProtocolMessage:
        exec_path = LiteRTCLIDiscovery.find_executable(self.cli_path)
        if not exec_path:
            return ProtocolParser.parse(f'{{"type": "thought", "content": "LiteRT-LM CLI unavailable. Echoing prompt: {prompt[:50]}"}}')

        full_prompt = f"{system_prompt}\n{prompt}" if system_prompt else prompt

        cmd = [exec_path]
        if self.model_path:
            cmd.extend(["--model", self.model_path])
        cmd.extend(["--prompt", full_prompt])

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=self.timeout)
            out_str = stdout.decode("utf-8", errors="replace").strip()
            if not out_str:
                out_str = stderr.decode("utf-8", errors="replace").strip()
            return ProtocolParser.parse(out_str)
        except asyncio.TimeoutError:
            return ProtocolMessage(type="error", content=f"LiteRT-LM execution timed out after {self.timeout}s")
        except Exception as e:
            return ProtocolMessage(type="error", content=f"LiteRT-LM execution error: {str(e)}")
