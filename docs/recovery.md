# Recovery

## Checkpoints
`CheckpointManager` stores task/plan/workspace state snapshots in the SQLite `checkpoints` table. Create, list, inspect, restore, delete.

## Rollback
`RollbackManager` supports file backup/restore (`.agentbak` suffix), directory restore and checkpoint state restore. It never overwrites unrelated user modifications.

## Self-healing
`Healer` classifies errors (transient / tool / model / policy / fatal) and chooses RETRY, RESTART_COMPONENT or ESCALATE with bounded retries (never infinite loops).

## Crash recovery
`CrashRecovery` persists a `crash-<task_id>` snapshot (current step, plan, iteration) and on startup decides RESUME or PAUSE.
