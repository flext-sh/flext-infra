"""Safety management for refactor operations: checkpoints, rollback, and validation."""

from __future__ import annotations

from pathlib import Path

from flext_infra import c, m, p, r, t, u


class FlextInfraRefactorSafetyManager:
    """Orchestrate pre-/post-transform safety: stash, validate, rollback."""

    def __init__(
        self,
        runner: p.Infra.SafetyRunner | None = None,
        checkpoint_path: Path | None = None,
        test_command: t.StrSequence | None = None,
    ) -> None:
        """Initialize safety manager with runner, checkpoint path, and test command."""
        self._runner: p.Infra.SafetyRunner | None = runner
        self._checkpoint_path = checkpoint_path or Path(
            ".sisyphus/refactor/safety-checkpoint.json",
        )
        self._test_command = test_command or [
            c.Infra.PYTHON,
            "-m",
            c.Infra.PYTEST,
            "-q",
        ]
        self._emergency_stop_reason = ""
        self._last_workspace_root: Path | None = None

    def _run_checked(self, cmd: t.StrSequence, cwd: Path) -> r[bool]:
        if self._runner is not None:
            return self._runner.run_checked(cmd, cwd=cwd)
        return u.run_checked(cmd, cwd=cwd)

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
        """Stash uncommitted changes and return the stash reference."""
        self._last_workspace_root = workspace_root
        return u.create_checkpoint(workspace_root, label=label)

    def rollback(self, workspace_root: Path, stash_ref: str = "") -> r[bool]:
        """Restore previously stashed state."""
        self._last_workspace_root = workspace_root
        return self._rollback_to_stash(workspace_root, stash_ref)

    def run_semantic_validation(self, workspace_root: Path) -> r[bool]:
        """Run import checks and tests against the workspace root."""
        self._last_workspace_root = workspace_root
        if self._emergency_stop_reason:
            return r[bool].fail(
                f"Emergency stop: {self._emergency_stop_reason}",
            )
        if not u.git_is_repo(workspace_root):
            out2: r[bool] = r[bool].ok(True)
            return out2
        import_cmd = [
            c.Infra.PYTHON,
            "-m",
            c.Infra.PYTEST,
            "--collect-only",
            "-q",
        ]
        ic = self._run_checked(import_cmd, workspace_root)
        if ic.is_failure:
            out3: r[bool] = r[bool].fail(ic.error or "import validation failed")
            return out3
        tc = self._run_checked(self._test_command, workspace_root)
        if tc.is_failure:
            out4: r[bool] = r[bool].fail(tc.error or "test validation failed")
            return out4
        out5: r[bool] = r[bool].ok(True)
        return out5

    def save_checkpoint_state(
        self,
        workspace_root: Path,
        *,
        status: str,
        stash_ref: str,
        processed_targets: t.StrSequence,
    ) -> r[bool]:
        """Build and persist a checkpoint from individual state components."""
        checkpoint = m.Infra.Checkpoint(
            workspace_root=str(workspace_root),
            status=status,
            stash_ref=stash_ref,
            processed_targets=processed_targets,
        )
        payload = checkpoint.model_dump()
        payload["updated_at"] = u.generate_iso_timestamp()
        return u.write_json(
            self._checkpoint_path,
            payload,
            ensure_ascii=True,
        )

    def clear_checkpoint(self) -> r[bool]:
        """Remove the on-disk checkpoint file."""
        if not self._checkpoint_path.exists():
            out: r[bool] = r[bool].ok(True)
            return out
        try:
            self._checkpoint_path.unlink()
            out2: r[bool] = r[bool].ok(True)
            return out2
        except OSError as exc:
            out3: r[bool] = r[bool].fail(str(exc))
            return out3

    def _rollback_to_stash(self, workspace_root: Path, stash_ref: str) -> r[bool]:
        return u.rollback_to_checkpoint(
            workspace_root,
            stash_ref,
        )


__all__ = ["FlextInfraRefactorSafetyManager"]
