"""Safety management for refactor operations: backup, validate, rollback."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from flext_infra import c, r, t, u


class FlextInfraRefactorSafetyManager:
    """Orchestrate pre-/post-transform safety: .bak backup, validate, rollback."""

    def __init__(
        self,
        *,
        test_command: t.StrSequence | None = None,
    ) -> None:
        """Initialize safety manager with test command."""
        self._test_command = test_command or [
            c.Infra.PYTHON,
            "-m",
            c.Infra.PYTEST,
            "-q",
        ]
        self._emergency_stop_reason = ""
        self._bak_paths: Sequence[Path] = []

    def request_emergency_stop(self, reason: str) -> None:
        """Record an emergency stop reason for later inspection."""
        self._emergency_stop_reason = reason.strip() or "unspecified"

    def is_emergency_stop_requested(self) -> bool:
        """Return True if an emergency stop has been requested."""
        return bool(self._emergency_stop_reason)

    def create_pre_transformation_stash(
        self,
        workspace_root: Path,
        *,
        label: str = "flext-refactor-pre-transform",
    ) -> r[str]:
        """Back up files in workspace root and return label as reference."""
        _ = label
        py_files = list(workspace_root.rglob(c.Infra.Extensions.PYTHON_GLOB))
        self._bak_paths = u.Infra.backup_files(py_files)
        return r[str].ok(str(workspace_root))

    def rollback(self, workspace_root: Path, stash_ref: str = "") -> r[bool]:
        """Restore previously backed up files."""
        _ = workspace_root, stash_ref
        u.Infra.restore_files(self._bak_paths)
        self._bak_paths = []
        return r[bool].ok(True)

    def run_semantic_validation(self, workspace_root: Path) -> r[bool]:
        """Run import checks and tests against the workspace root."""
        if self._emergency_stop_reason:
            return r[bool].fail(
                f"Emergency stop: {self._emergency_stop_reason}",
            )
        ic = u.Infra.run_checked(
            [c.Infra.PYTHON, "-m", c.Infra.PYTEST, "--collect-only", "-q"],
            cwd=workspace_root,
        )
        if ic.is_failure:
            return r[bool].fail(ic.error or "import validation failed")
        tc = u.Infra.run_checked(self._test_command, cwd=workspace_root)
        if tc.is_failure:
            return r[bool].fail(tc.error or "test validation failed")
        return r[bool].ok(True)

    def clear_checkpoint(self) -> r[bool]:
        """Clean up backup files after successful validation."""
        u.Infra.cleanup_backups(self._bak_paths)
        self._bak_paths = []
        return r[bool].ok(True)


__all__ = ["FlextInfraRefactorSafetyManager"]
