# Self-X

Self-X is the bounded self-management layer of LiteRT Agent.

## Responsibilities

- Self identity and capability introspection
- Resource monitoring and safe concurrency
- Diagnostics and maintenance proposals
- Task-result reflection and lesson storage
- Web evidence ingestion with an explicit untrusted-data boundary
- Research missions, provenance, credibility and duplicate detection
- Persistent goals, dependencies and curiosity
- Self-skill proposal, approval, versioning, rollback and quarantine
- Snapshot/export and bounded recovery planning

## Safety boundaries

Self-X cannot:

1. modify LiteRT-LM model weights;
2. replace the LiteRT-LM CLI provider;
3. disable or rewrite security policy;
4. execute instructions obtained from the internet merely because they were fetched;
5. bypass an approval requirement;
6. silently switch to another AI provider.

Internet sources are evidence only. Commands, code and configuration found online must pass the normal parser, policy and approval pipeline before any execution.

## Research lifecycle

`mission -> source fetch -> provenance -> finding -> corroboration/contradiction -> lesson -> memory`

Every source records URL, SHA-256 hash, trust classification and credibility metadata.

## Goal lifecycle

`created -> dependency check -> active -> progress -> completed/paused/failed`

Curiosity items are queued separately and may be converted into bounded research missions.

## Skill lifecycle

`discover -> propose -> validate -> explicit approval -> register -> observe -> version/rollback/quarantine`

Security policy is never delegated to a skill.

## CLI

- `litert-agent self status`
- `litert-agent self diagnose`
- `litert-agent self cycle`
- `litert-agent self learn-web URL --lesson "..."`
- `litert-agent self overview`
- `litert-agent research mission ... --url ...`
- `litert-agent research collect MISSION_ID`
- `litert-agent research sources`
- `litert-agent research findings`
- `litert-agent research compare`
- `litert-agent goal create ...`
- `litert-agent goal dependency GOAL_ID DEPENDENCY_ID`
- `litert-agent goal generate-curiosity`
- `litert-agent goal next-curiosity`

## Autonomous mode

Autonomy remains bounded by security policy, approvals, resource limits,
iteration/time/tool-call limits, checkpoints and the kill switch.
