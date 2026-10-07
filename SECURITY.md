# Security Policy

## Supported versions

Only the latest `main` branch is supported.

## Local-first design

litert-agent is fully local-first. The agent, its tools, its SQLite state, and
the LiteRT-LM model backend all run on your machine. No telemetry is collected.

## Reporting a vulnerability

Please open a private security advisory on GitHub
(`Security > Report a vulnerability`) instead of a public issue. Include:

- a minimal reproduction,
- the affected component (cognition, runtime, tools, web, api, tui),
- the LiteRT-LM CLI version.

## Hard rules

- LiteRT-LM CLI is the only model backend. No fallback provider will be added.
- Never commit secrets, credentials, `.env` files, or private keys.
- Dangerous tool actions require explicit human approval (allow-once /
  allow-session / deny) unless a profile explicitly opts out.
