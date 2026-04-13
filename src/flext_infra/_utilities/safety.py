"""Copy-on-write safety primitives for file transformation with automatic rollback.

Provides static helpers for backing up files before transformation,
validating post-transform quality via gates, and restoring on failure.
"""

from __future__ import annotations

import shutil
from collections.abc import Callable, Sequence
from pathlib import Path

from flext_cli import u
from flext_core import p, r
from flext_infra import c, m


class FlextInfraUtilitiesSafety:
    """Static safety helpers for copy-on-write file protection."""

    @staticmethod
    def create_checkpoint(repo: Path, *, label: str = "checkpoint") -> p.Result[str]:
        """Create a git-stash checkpoint for dirty repositories.

        Returns an empty string for non-repositories or clean trees.
        """
        repo_check = u.Cli.run_raw(
            [c.Infra.GIT, "rev-parse", "--is-inside-work-tree"],
            cwd=repo,
        )
        if repo_check.failure or repo_check.value.exit_code != 0:
            return r[str].ok("")
        status_result = u.Cli.run_raw(
            [c.Infra.GIT, "status", "--porcelain"],
            cwd=repo,
        )
        if status_result.failure or status_result.value.exit_code != 0:
            return r[str].fail(status_result.error or "git status failed")
        if not status_result.value.stdout.strip():
            return r[str].ok("")
        stash_result = u.Cli.run_raw(
            [c.Infra.GIT, "stash", "push", "--include-untracked", "-m", label],
            cwd=repo,
        )
        if stash_result.failure or stash_result.value.exit_code != 0:
            return r[str].fail(stash_result.error or "git stash push failed")
        list_result = u.Cli.run_raw(
            [c.Infra.GIT, "stash", "list", "-1", "--format=%gd"],
            cwd=repo,
        )
        if list_result.failure or list_result.value.exit_code != 0:
            return r[str].fail(list_result.error or "git stash list failed")
        stash_ref = list_result.value.stdout.strip()
        if not stash_ref:
            return r[str].fail("git stash list returned no checkpoint ref")
        return r[str].ok(f"{label}: {stash_ref}")

    @staticmethod
    def rollback_to_checkpoint(repo: Path, checkpoint: str = "") -> p.Result[bool]:
        """Restore a previously-created git-stash checkpoint.

        Returns success for non-repositories or empty checkpoint strings.
        """
        if not checkpoint:
            return r[bool].ok(True)
        repo_check = u.Cli.run_raw(
            [c.Infra.GIT, "rev-parse", "--is-inside-work-tree"],
            cwd=repo,
        )
        if repo_check.failure or repo_check.value.exit_code != 0:
            return r[bool].ok(True)
        checkpoint_ref = checkpoint.split(":", 1)[-1].strip()
        apply_result = u.Cli.run_raw(
            [c.Infra.GIT, "stash", "apply", checkpoint_ref],
            cwd=repo,
        )
        if apply_result.failure or apply_result.value.exit_code != 0:
            return r[bool].fail(apply_result.error or "git stash apply failed")
        drop_result = u.Cli.run_raw(
            [c.Infra.GIT, "stash", "drop", checkpoint_ref],
            cwd=repo,
        )
        if drop_result.failure or drop_result.value.exit_code != 0:
            return r[bool].fail(drop_result.error or "git stash drop failed")
        return r[bool].ok(True)

    @staticmethod
    def backup_files(files: Sequence[Path]) -> Sequence[Path]:
        """Copy each file to .bak. Fail fast on any error."""
        bak_paths: list[Path] = []
        for file_path in files:
            if not file_path.exists():
                continue
            bak = file_path.with_suffix(
                file_path.suffix + c.Infra.SAFE_EXECUTION_BAK_SUFFIX,
            )
            shutil.copy2(file_path, bak)
            bak_paths.append(bak)
        return bak_paths

    @staticmethod
    def restore_files(bak_paths: Sequence[Path]) -> None:
        """Move .bak files back to originals. Fail fast."""
        for bak in bak_paths:
            original = Path(str(bak).removesuffix(c.Infra.SAFE_EXECUTION_BAK_SUFFIX))
            shutil.move(str(bak), str(original))

    @staticmethod
    def cleanup_backups(bak_paths: Sequence[Path]) -> None:
        """Remove .bak files after successful validation."""
        for bak in bak_paths:
            if bak.exists():
                bak.unlink()

    @staticmethod
    def execute_safely(
        files: Sequence[Path],
        transform: Callable[[Sequence[Path]], r[Sequence[Path]]],
        validate: Callable[[Sequence[Path]], r[bool]],
        *,
        mode: c.Infra.ExecutionMode = c.Infra.ExecutionMode.APPLY_SAFE,
    ) -> m.Infra.SafeExecutionResult:
        """Pipeline: backup -> transform -> validate -> (cleanup | rollback).

        Fail fast: any step failure = immediate rollback + raise.
        """
        file_strs = [str(f) for f in files]

        if mode == c.Infra.ExecutionMode.DRY_RUN:
            return m.Infra.SafeExecutionResult(
                mode=mode,
                files_backed_up=file_strs,
                gate_results=[],
                rolled_back=False,
            )

        bak_paths = FlextInfraUtilitiesSafety.backup_files(files)

        transform_result = transform(files)
        if transform_result.failure:
            FlextInfraUtilitiesSafety.restore_files(bak_paths)
            return m.Infra.SafeExecutionResult(
                mode=mode,
                files_backed_up=file_strs,
                gate_results=[transform_result.error or "transform failed"],
                rolled_back=True,
            )

        if mode == c.Infra.ExecutionMode.APPLY_FORCE:
            FlextInfraUtilitiesSafety.cleanup_backups(bak_paths)
            return m.Infra.SafeExecutionResult(
                mode=mode,
                files_backed_up=file_strs,
                gate_results=[],
                rolled_back=False,
            )

        validate_result = validate(files)
        if validate_result.failure:
            FlextInfraUtilitiesSafety.restore_files(bak_paths)
            return m.Infra.SafeExecutionResult(
                mode=mode,
                files_backed_up=file_strs,
                gate_results=[validate_result.error or "validation failed"],
                rolled_back=True,
            )

        FlextInfraUtilitiesSafety.cleanup_backups(bak_paths)
        return m.Infra.SafeExecutionResult(
            mode=mode,
            files_backed_up=file_strs,
            gate_results=[],
            rolled_back=False,
        )


__all__: list[str] = ["FlextInfraUtilitiesSafety"]
