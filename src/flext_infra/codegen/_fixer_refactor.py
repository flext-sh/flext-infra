"""Refactor pass helper for the codegen fixer service."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra import c, m
from flext_infra.codegen._fixer_results import FlextInfraCodegenFixerResultsMixin
from flext_infra.refactor.service import FlextInfraRefactorService

if TYPE_CHECKING:
    from pathlib import Path


class FlextInfraCodegenFixerRefactorMixin(FlextInfraCodegenFixerResultsMixin):
    """Private refactor-service pass for codegen fixer composition."""

    @staticmethod
    def _run_refactor_service(ctx: m.Infra.FixContext, project_path: Path) -> None:
        """Load refactor rules and run the service; record fixed/skipped violations."""
        service = FlextInfraRefactorService()
        service.load_config().unwrap()
        service.load_rules().unwrap()
        refactor_results = tuple(service.refactor_project(project_path, dry_run=False))
        failures = tuple(result for result in refactor_results if not result.success)
        if failures:
            raise RuntimeError("\n".join(result.error or "" for result in failures))
        ctx.files_modified |= {
            str(result.file_path) for result in refactor_results if result.success
        }
        ctx.violations_fixed.extend(
            m.Infra.CensusViolation(
                module=str(result.file_path),
                rule="REFACTOR",
                line=1,
                message=change,
                fixable=True,
            )
            for result in refactor_results
            if result.modified
            for change in (tuple(result.changes) or ("refactor applied",))
        )


__all__: list[str] = ["FlextInfraCodegenFixerRefactorMixin"]
