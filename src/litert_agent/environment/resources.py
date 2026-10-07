"""System resource monitoring."""

import psutil

class ResourceMonitor:
    @staticmethod
    def get_cpu_usage() -> float:
        return psutil.cpu_percent(interval=0.1)

    @staticmethod
    def get_memory_info() -> dict:
        mem = psutil.virtual_memory()
        return {
            "total_gb": round(mem.total / (1024**3), 2),
            "available_gb": round(mem.available / (1024**3), 2),
            "used_percent": mem.percent,
        }

    @staticmethod
    def get_disk_info(path: str = ".") -> dict:
        disk = psutil.disk_usage(path)
        return {
            "total_gb": round(disk.total / (1024**3), 2),
            "free_gb": round(disk.free / (1024**3), 2),
            "used_percent": disk.percent,
        }
