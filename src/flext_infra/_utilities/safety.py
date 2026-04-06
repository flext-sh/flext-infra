"""Copy-on-write safety primitives for file transformation with automatic rollback.

Provides static helpers for backing up files before transformation,
validating post-transform quality via gates, and restoring on failure.
"""

from __future__ import annotations

import shutil
from collections.abc import Callable, Sequence
from pathlib import Path

from flext_core import r
from flext_infra import c, m


class FlextInfraUtilitiesSafety:
    """Static safety helpers for copy-on-write file protection."""

    @staticmethod
    def backup_files(files: Sequence[Path]) -> Sequence[Path]:
        """Copy each file to .bak. Fail fast on any error."""
        bak_paths: list[Path] = []
        for file_path in files:
            if not file_path.exists():
                continue
            bak = file_path.with_suffix(
                file_path.suffix + c.Infra.SafeExecution.BAK_SUFFIX,
            )
            shutil.copy2(file_path, bak)
            bak_paths.append(bak)
        return bak_paths

    @staticmethod
    def restore_files(bak_paths: Sequence[Path]) -> None:
        """Move .bak files back to originals. Fail fast."""
        for bak in bak_paths:
            original = Path(str(bak).removesuffix(c.Infra.SafeExecution.BAK_SUFFIX))
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
        if transform_result.is_failure:
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
        if validate_result.is_failure:
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


__all__ = ["FlextInfraUtilitiesSafety"]
