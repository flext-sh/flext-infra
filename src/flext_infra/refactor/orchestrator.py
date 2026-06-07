"""Refactor orchestration layer for file/project/workspace execution."""

from __future__ import annotations

from pathlib import Path
from typing import override

from flext_infra import (
    FlextInfraClassNestingPostCheckGate,
    FlextInfraRefactorFileExecutor,
    FlextInfraRefactorRuleLoader,
    FlextInfraRefactorSafetyManager,
    FlextInfraRefactorTextExecutor,
    c,
    m,
    t,
    u,
)
from flext_infra.refactor._orchestrator_dispatch import (
    FlextInfraRefactorOrchestratorDispatchMixin,
)
from flext_infra.refactor._orchestrator_scope import (
    FlextInfraRefactorOrchestratorScopeMixin,
)

_log = u.fetch_logger(__name__)


class FlextInfraRefactorOrchestrator(
    FlextInfraRefactorTextExecutor,
    FlextInfraRefactorFileExecutor,
    FlextInfraRefactorOrchestratorDispatchMixin,
    FlextInfraRefactorOrchestratorScopeMixin,
):
    """Coordinate refactor execution using loaded rule selections and safety flow."""

    def __init__(
        self,
        loader: FlextInfraRefactorRuleLoader,
        *,
        safety_manager: FlextInfraRefactorSafetyManager | None = None,
    ) -> None:
        """Initialize the orchestrator with a loader and optional safety service."""
        self.loader = loader
        self.safety_manager = safety_manager or FlextInfraRefactorSafetyManager()
        self._class_nesting_config: t.Infra.ContainerDict | None = None
        self._class_nesting_policy_by_family: (
            t.MappingKV[str, m.Infra.ClassNestingPolicy] | None
        ) = None
        self._class_nesting_gate: FlextInfraClassNestingPostCheckGate | None = None

    @override
    def refactor_file(
        self,
        file_path: Path,
        *,
        dry_run: bool = False,
    ) -> m.Infra.Result:
        """Refactor one file using the loader's current rule selections."""
        result: m.Infra.Result
        try:
            if file_path.suffix != c.Infra.EXT_PYTHON:
                result = self._skip_result(file_path)
            else:
                workspace_root = u.Infra.project_root(file_path) or file_path.parent
                read = u.Cli.files_read_text(file_path)
                if read.failure:
                    return self._error_result(
                        file_path,
                        read.error or f"failed to read {file_path}",
                    )
                original = read.value
                current, all_changes = original, list[str]()
                error_result: m.Infra.Result | None = None
                if self.loader.file_rules:
                    with u.Infra.open_project(workspace_root) as rope_project:
                        resource = u.Infra.get_resource_from_path(
                            rope_project,
                            file_path,
                        )
                        if resource is None:
                            error_result = self._error_result(
                                file_path,
                                f"Could not resolve rope resource for {file_path}",
                            )
                        else:
                            for kind, settings in self.loader.file_rules:
                                file_rule_result = self._apply_file_rule_selection(
                                    kind,
                                    settings,
                                    rope_project,
                                    resource,
                                    dry_run=True,
                                )
                                if not file_rule_result.success:
                                    error_result = m.Infra.Result(
                                        file_path=file_path,
                                        success=False,
                                        modified=False,
                                        error=file_rule_result.error,
                                        changes=file_rule_result.changes,
                                        refactored_code=None,
                                    )
                                    break
                                if (
                                    file_rule_result.modified
                                    and file_rule_result.refactored_code
                                ):
                                    current = file_rule_result.refactored_code
                                all_changes.extend(file_rule_result.changes)
                if error_result is None:
                    for kind, settings in self.loader.rules:
                        if not bool(settings.get(c.Infra.RK_ENABLED, True)):
                            continue
                        current, changes = self._apply_text_rule_selection(
                            kind,
                            settings,
                            current,
                            file_path,
                        )
                        all_changes.extend(changes)
                    modified = current != original
                    if not dry_run and modified:
                        ok, report = u.Infra.protected_source_write(
                            file_path,
                            request=m.Infra.ProtectedSourceWriteRequest(
                                workspace=workspace_root,
                                updated_source=current,
                                keep_backup=True,
                            ),
                        )
                        all_changes.extend(report)
                        if not ok:
                            error_result = m.Infra.Result(
                                file_path=file_path,
                                success=False,
                                modified=False,
                                error="Protected refactor validation failed",
                                changes=all_changes,
                                refactored_code=original,
                            )
                    result = error_result or m.Infra.Result(
                        file_path=file_path,
                        success=True,
                        modified=modified,
                        changes=all_changes,
                        refactored_code=current,
                    )
                else:
                    result = error_result
        except Exception as exc:
            result = self._error_result(file_path, str(exc))
        return result

    @override
    def refactor_files(
        self,
        file_paths: t.SequenceOf[Path],
        *,
        dry_run: bool = False,
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
                _log.debug(
                    "refactor_noop",
                    file=str(result.file_path),
                )
                self._refactor_debug(f"Unchanged: {file_path.name}")
            else:
                u.Cli.error(f"Failed: {file_path.name} - {result.error}")
        return results


__all__: list[str] = ["FlextInfraRefactorOrchestrator"]
