# Contributing

1. Fork and create a feature branch
2. `pip install -e ".[dev]"`
3. Keep changes modular — extend existing subsystems rather than duplicating
4. Add tests for new behavior (`pytest` must pass)
5. Use conventional commits: `feat:`, `fix:`, `docs:`, `test:`, `chore:`
6. Never add a fallback AI provider — LiteRT-LM CLI is the only backend by design
7. Never commit credentials; run `SecretSanitizer`-aware logging

## Project rules
- Follow the layered architecture: presentation → application → cognition → model/tools/state/security
- Every UI control must call a real backend operation — no fake buttons
- Errors are surfaced, never hidden
