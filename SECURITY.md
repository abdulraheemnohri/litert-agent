# Security Policy

## Permission model
Every tool call passes through `SecurityPolicy`:
- **ALLOW** — reads and safe operations
- **ASK** — package installs, protected paths (`.env`, `id_rsa`, `.git`, passwd/shadow); requires approval
- **BLOCK** — `sudo`, `rm -rf /`; always denied

## Secrets
`SecretSanitizer` masks API keys, passwords, secrets and bearer tokens before anything is written to audit logs.

## Reporting
Open a private security advisory on GitHub (Security tab) or an issue marked **security**. Do not post exploitable details publicly.

## Hard rules
- No credential ever enters the model context or ordinary memory
- Safe mode blocks all destructive writes and network
- Security controls cannot be disabled by skills or self-modification
