"""Example: manage scheduler jobs (SQLite-backed).

Usage:
    python examples/scheduler_demo.py            # list jobs
    python examples/scheduler_demo.py add        # add a demo job
    python examples/scheduler_demo.py run <id>   # trigger a job
"""

import sys

from litert_agent.scheduler.queue import add_job, get_job, list_jobs


def main() -> None:
    command = sys.argv[1] if len(sys.argv) > 1 else "list"

    if command == "add":
        job = add_job(name="demo-job", goal="Run a quick self-test", cron="0 9 * * *")
        print("added:", job)
    elif command == "run":
        job = get_job(int(sys.argv[2]))
        print("job:", job)
        print("trigger it with: litert-agent schedule run", sys.argv[2])
    else:
        for job in list_jobs():
            print(job)


if __name__ == "__main__":
    main()
