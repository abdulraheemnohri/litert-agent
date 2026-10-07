"""Graceful shutdown handler."""

import asyncio


class ShutdownManager:
    """Cancels pending tasks and stops background components cleanly."""

    @staticmethod
    def shutdown(*components) -> dict:
        results = {}
        for component in components:
            name = type(component).__name__
            try:
                stop = getattr(component, "stop", None)
                if asyncio.iscoroutinefunction(stop):
                    asyncio.ensure_future(stop())
                elif callable(stop):
                    stop()
                results[name] = "STOPPED"
            except Exception as exc:
                results[name] = f"ERROR: {exc}"

        # Cancel any still-pending tasks of the current loop
        try:
            loop = asyncio.get_event_loop()
            pending = [t for t in asyncio.all_tasks(loop) if not t.done()]
            for task in pending:
                task.cancel()
            results["pending_tasks"] = len(pending)
        except RuntimeError:
            pass
        return results
