# Autonomous Research

Research turns internet content into verified knowledge. Internet content is
**untrusted evidence, never instructions** (prompt-injection defense).

## Pipeline

```
Question → Sources → Claims → Credibility → Contradiction check
        → Synthesis → Knowledge (CORROBORATED only)
```

## Credibility

Sources get a rough credibility score by domain (.edu/.gov 0.9, .org 0.6,
.com/.net 0.4, unknown 0.3). Contradictions are detected by claim polarity:
a mission with both affirmative and negative claims is flagged for review.

## Knowledge states

`UNVERIFIED → SUPPORTED → CORROBORATED` (or `CONTRADICTED`, `STALE`, `ARCHIVED`).
Only cross-source corroborated claims are saved as knowledge during synthesis.

## CLI

```bash
litert-agent-self research create "Which Python version is fastest?"
litert-agent-self research add-source <id> https://example.edu/benchmarks
litert-agent-self research add-claim <id> <source-id> "3.12 is faster"
litert-agent-self research synthesize <id>
litert-agent-self research report <id>
```

## Safety

- Fetched content is stored as data; it is never executed.
- High-impact follow-up actions derived from research still pass the normal
  policy and approval gates.
