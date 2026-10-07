# Scheduler

The scheduler runs jobs in the background against the same agent runtime.

## Job store

Jobs persist in the `scheduler_jobs` SQLite table — a single source of
truth shared by the CLI and the Web API, so both interfaces always show
the same jobs.

## Worker lifecycle

```
claim_task → execute_task → release_task
```

- A claimed job that fails is re-queued (the failed list tracks it).
- Releasing a released job no longer leaves an un-awaited coroutine.
- The heartbeat supervises worker health.

## CLI

```bash
litert-agent schedule list
litert-agent schedule add "Daily report" --cron "0 9 * * *"
litert-agent schedule remove <job-id>
litert-agent schedule run <job-id>
```

## Web UI

The Scheduler page lists jobs, next execution, status and history, with
Run Now and Delete actions.
