# Security

## Permission levels
- **ALLOW** — read operations, safe commands
- **ASK** — package installs, protected paths (`.env`, `id_rsa`, `.git`, passwd/shadow)
- **BLOCK** — `sudo`, `rm -rf /`, and in safe mode all filesystem/terminal writes

## Safe mode
`SecurityPolicy(safe_mode=True)` blocks destructive writes and system modifications.

## Principles
- Credentials and secrets are never logged, stored in ordinary memory, or sent to the model context
- Blocked operations return structured errors; they never execute silently
- Security policies cannot be disabled by skills or self-modification
