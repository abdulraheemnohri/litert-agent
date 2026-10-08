import pytest
from litert_agent.model.discovery import LiteRTCLIDiscovery


@pytest.mark.asyncio
async def test_discovery_detects_prompt_and_model_flags(tmp_path):
    script = tmp_path / "fake-litert"
    script.write_text("#!/bin/sh
echo '  -p, --prompt TEXT'
echo '  -m, --model PATH'
")
    script.chmod(0o755)
    info = await LiteRTCLIDiscovery.inspect_help(str(script))
    assert info["supports_prompt"] is True
    assert info["supports_model"] is True
    assert info["prompt_flag"] == "--prompt"
    assert info["model_flag"] == "--model"
