"""Fail-fast semantic validation for retained refactor changes."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra.detectors.lsp_diagnostics import FlextInfraLspDiagnosticsDetector

if TYPE_CHECKING:
    from pathlib import Path

    from flext_infra import p, t


class FlextInfraRefactorSafetyManager:
    """Validate refactor output without rollback, backups, or direct test runs."""

    @staticmethod
    def run_semantic_validation(
        repository_root: Path, files: t.SequenceOf[Path]
    ) -> p.Result[bool]:
        """Require real language-server diagnostics for retained edits."""
        return FlextInfraLspDiagnosticsDetector.validate(repository_root, files)


__all__: list[str] = ["FlextInfraRefactorSafetyManager"]
