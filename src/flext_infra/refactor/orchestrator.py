"""Refactor orchestration layer for file/project/workspace execution."""

from __future__ import annotations

from typing import TYPE_CHECKING, override

from flext_infra import c, m, u
from flext_infra.refactor._orchestrator_dispatch import (
    FlextInfraRefactorOrchestratorDispatchMixin,
)
from flext_infra.refactor._orchestrator_scope import (
    FlextInfraRefactorOrchestratorScopeMixin,
)
from flext_infra.refactor.safety import FlextInfraRefactorSafetyManager
from flext_infra.refactor.text_executor import FlextInfraRefactorTextExecutor

if TYPE_CHECKING:
    from pathlib import Path

    from flext_infra import t
    from flext_infra.refactor.loader import FlextInfraRefactorRuleLoader

_log = u.fetch_logger(__name__)


class FlextInfraRefactorOrchestrator(
    FlextInfraRefactorTextExecutor,
    FlextInfraRefactorOrchestratorDispatchMixin,
    FlextInfraRefactorOrchestratorScopeMixin,
):
    """Coordinate refactor execution using loaded rule selections and safety flow."""

    def __init__(
        self,
        loader: FlextInfraRefactorRuleLoader,
        *,
        safety_manager: FlextInfraRefactorSafetyManager,
    ) -> None:
        """Initialize the orchestrator with explicitly injected services."""
        self.loader = loader
        self.safety_manager = safety_manager

    @override
    def refactor_file(
        self, file_path: Path, *, dry_run: bool = False
    ) -> m.Infra.Result:
        """Refactor one file using the loader's current rule selections."""
        if file_path.suffix != c.Infra.EXT_PYTHON:
            return self._skip_result(file_path)
        return self._refactor_python_file(file_path, dry_run=dry_run)

    def _refactor_python_file(
        self, file_path: Path, *, dry_run: bool
    ) -> m.Infra.Result:
        """Refactor one Python source file after caller-level exception handling."""
        repository_root = u.Infra.project_root(file_path) or file_path.parent
        original = u.Cli.files_read_text(file_path).unwrap()
        current, all_changes = original, list[str]()
        current = self._apply_text_rules(file_path, current, all_changes)
        modified = current != original
        error_result = None
        if not dry_run and modified:
            error_result = self._write_refactored_source(
                file_path=file_path,
                repository_root=repository_root,
                current=current,
                all_changes=all_changes,
            )
        return error_result or m.Infra.Result(
            file_path=file_path,
            success=True,
            modified=modified,
            changes=all_changes,
            refactored_code=current,
        )

    def _apply_text_rules(
        self, file_path: Path, current: str, all_changes: t.MutableSequenceOf[str]
    ) -> str:
        """Apply enabled text rules and collect changes."""
        updated_source = current
        for kind, settings in self.loader.rules:
            if not bool(settings.get(c.Infra.RK_ENABLED, True)):
                continue
            updated_source, changes = self._apply_text_rule_selection(
                kind, settings, updated_source, file_path
            )
            all_changes.extend(changes)
        return updated_source

    def _write_refactored_source(
        self,
        *,
        file_path: Path,
        repository_root: Path,
        current: str,
        all_changes: t.MutableSequenceOf[str],
    ) -> m.Infra.Result | None:
        """Write transformed source once; later validation retains it on failure."""
        _ = repository_root, all_changes
        u.Cli.files_write_text(file_path, current).unwrap()
        return None

    @override
    def refactor_files(
        self, file_paths: t.SequenceOf[Path], *, dry_run: bool = False
    ) -> t.SequenceOf[m.Infra.Result]:
        """Refactor many files and collect individual results."""
        results: t.MutableSequenceOf[m.Infra.Result] = []
        for file_path in file_paths:
            result = self.refactor_file(file_path, dry_run=dry_run)
            results.append(result)
            if result.success and result.modified:
                u.Cli.info(
                    f"{'[DRY-RUN] ' if dry_run else ''}Modified: {file_path.name}"
                )
                for change in result.changes:
                    u.Cli.info(f"  - {change}")
            elif result.success:
                _log.debug("refactor_noop", file=str(result.file_path))
                self._refactor_debug(f"Unchanged: {file_path.name}")
            else:
                u.Cli.error(f"Failed: {file_path.name} - {result.error}")
                return results
        return results


__all__: list[str] = ["FlextInfraRefactorOrchestrator"]
