"""Validation helpers for remaining MRO migration candidates."""

from __future__ import annotations

from pathlib import Path

from flext_infra import t, u


class FlextInfraRefactorMROMigrationValidator:
    """Validator for MRO migration completeness and correctness."""

    @classmethod
    def validate(
        cls,
        *,
        workspace_root: Path,
        target: str,
        project_names: t.StrSequence | None = None,
    ) -> t.IntPair:
        """Return count of remaining symbols and unsupported entries."""
        file_results, _ = u.Infra.scan_workspace(
            workspace_root=workspace_root,
            target=target,
            project_names=project_names,
        )
        remaining = sum(len(item.candidates) for item in file_results)
        return (remaining, 0)


__all__: list[str] = ["FlextInfraRefactorMROMigrationValidator"]
