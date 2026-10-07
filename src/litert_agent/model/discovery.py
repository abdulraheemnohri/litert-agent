"""CLI help/capability discovery for LiteRT-LM without undocumented assumptions."""
import asyncio
import re
import shutil

class LiteRTCLIDiscovery:
    @staticmethod
    def find_executable(configured_path: str = "litert-lm") -> str | None:
        return shutil.which(configured_path)

    @staticmethod
    async def inspect_help(cli_path: str) -> dict:
        try:
            proc = await asyncio.create_subprocess_exec(cli_path, "--help", stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            stdout, stderr = await proc.communicate()
            help_text = (stdout + stderr).decode("utf-8", errors="replace")
            prompt_flag = None
            model_flag = None
            if re.search(r"(?m)^\\s*(-p|--prompt)(?:[=\\s]|,)", help_text):
                prompt_flag = "--prompt" if "--prompt" in help_text else "-p"
            if re.search(r"(?m)^\\s*(-m|--model)(?:[=\\s]|,)", help_text):
                model_flag = "--model" if "--model" in help_text else "-m"
            return {"available": proc.returncode == 0 or bool(help_text), "help_text": help_text,
                    "supports_prompt": prompt_flag is not None, "supports_model": model_flag is not None,
                    "prompt_flag": prompt_flag, "model_flag": model_flag, "returncode": proc.returncode}
        except Exception as exc:
            return {"available": False, "error": str(exc), "help_text": ""}
