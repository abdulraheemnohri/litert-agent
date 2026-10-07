"""Rollback support for files, workspace and checkpoints."""

import shutil
from pathlib import Path


class RollbackManager:
    """Safely rolls back files, directories and checkpoint state."""

    def __init__(self, checkpoint_manager=None):
        self.checkpoint_manager = checkpoint_manager

    def backup_file(self, path: Path) -> Path | None:
        if not path.exists():
            return None
        backup = path.with_suffix(path.suffix + ".agentbak")
        shutil.copy2(path, backup)
        return backup

    def restore_file(self, backup: Path, target: Path) -> bool:
        if not backup.exists():
            return False
        shutil.copy2(backup, target)
        backup.unlink(missing_ok=True)
        return True

    def restore_directory(self, backup_dir: Path, target_dir: Path) -> bool:
        if not backup_dir.exists():
            return False
        if target_dir.exists():
            shutil.rmtree(target_dir)
        shutil.copytree(backup_dir, target_dir)
        return True

    def restore_checkpoint_state(self, checkpoint_id: str) -> dict | None:
        if self.checkpoint_manager is None:
            return None
        return self.checkpoint_manager.restore_checkpoint(checkpoint_id)
