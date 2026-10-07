# Installation

Requires Python 3.12+.

```bash
git clone https://github.com/abdulraheemnohri/litert-agent
cd litert-agent
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

Install the LiteRT-LM CLI separately and make sure `litert-lm` is on your `PATH`. Verify with:

```bash
litert-agent doctor
```

## Running

```bash
litert-agent run "your goal"
litert-agent web     # http://127.0.0.1:8765
litert-agent tui
```

## Tests

```bash
pytest
```
