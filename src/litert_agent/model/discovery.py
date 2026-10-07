"""CLI Help inspector and capability discovery for LiteRT-LM."""

import asyncio
import shutil

class LiteRTCLIDiscovery:
    @staticmethod
    def find_executable(configured_path: str = "litert-lm") -> str | None:
        return shutil.which(configured_path)

    @staticmethod
    async def inspect_help(cli_path: str) -> dict:
        try:
            proc = await asyncio.create_subprocess_exec(
                cli_path, "--help",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            help_text = (stdout + stderr).decode("utf-8", errors="replace")
            return {
                "available": proc.returncode == 0 or len(help_text) > 0,
                "help_text": help_text,
                "supports_prompt": "--prompt" in help_text or "-p" in help_text,
                "supports_model": "--model" in help_text or "-m" in help_text,
            }
        except Exception as e:
            return {"available": False, "error": str(e), "help_text": ""}
