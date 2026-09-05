"""Refactor orchestration scope mixin (project/workspace + safety flow)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra import c, u

if TYPE_CHECKING:
    from pathlib import Path

    from flext_infra import m, t
    from flext_infra.refactor.loader import FlextInfraRefactorRuleLoader
    from flext_infra.refactor.safety import FlextInfraRefactorSafetyManager


class FlextInfraRefactorOrchestratorScopeMixin:
    """Provide fail-fast project and workspace refactor scopes."""

    if TYPE_CHECKING:
        loader: FlextInfraRefactorRuleLoader
        safety_manager: FlextInfraRefactorSafetyManager

        def refactor_files(
            self, file_paths: t.SequenceOf[Path], *, dry_run: bool = False
        ) -> t.SequenceOf[m.Infra.Result]: ...

        @staticmethod
        def _error_result(fp: Path, error: str) -> m.Infra.Result: ...

        @staticmethod
        def _refactor_header(message: str) -> None: ...

    def _validate_results(
        self,
        *,
        target: Path,
        results: t.MutableSequenceOf[m.Infra.Result],
        dry_run: bool,
    ) -> None:
        """Validate retained changes once after successful transformation."""
        if dry_run or any(not result.success for result in results):
            return
        changed = tuple(result.file_path for result in results if result.modified)
        self.safety_manager.run_semantic_validation(target, changed).unwrap()

    def _refactor_project_results(
        self, project_path: Path, *, dry_run: bool, pattern: str
    ) -> t.MutableSequenceOf[m.Infra.Result]:
        """Transform one project's configured files without a second validation path."""
        collected = u.Infra.collect_refactor_project_files(
            self.loader.settings, project_path, pattern=pattern
        )
        if collected is None:
            msg = f"File iteration failed for {project_path}"
            raise RuntimeError(msg)
        u.Cli.info(f"Found {len(collected)} files to process")
        return list(self.refactor_files(collected, dry_run=dry_run))

    def refactor_project(
        self,
        project_path: Path,
        *,
        dry_run: bool = False,
        pattern: str = c.Infra.EXT_PYTHON_GLOB,
    ) -> t.SequenceOf[m.Infra.Result]:
        """Refactor files under configured project directories."""
        results = self._refactor_project_results(
            project_path, dry_run=dry_run, pattern=pattern
        )
        self._validate_results(target=project_path, results=results, dry_run=dry_run)
        return results

    def refactor_workspace(
        self,
        repository_root: Path,
        *,
        dry_run: bool = False,
        pattern: str = c.Infra.EXT_PYTHON_GLOB,
    ) -> t.SequenceOf[m.Infra.Result]:
        """Refactor all discoverable workspace projects."""
        root = repository_root.resolve()
        if not root.exists() or not root.is_dir():
            raise FileNotFoundError(repository_root)
        projects = u.Infra.discover_refactor_projects(self.loader.settings, root)
        if not projects:
            msg = f"No projects discovered under: {repository_root}"
            raise RuntimeError(msg)
        u.Cli.info(f"Discovered {len(projects)} projects in workspace")
        results: t.MutableSequenceOf[m.Infra.Result] = []
        for project in projects:
            self._refactor_header(f"Project: {project}")
            results.extend(
                self._refactor_project_results(
                    project, dry_run=dry_run, pattern=pattern
                )
            )
            if any(not result.success for result in results):
                return results
        self._validate_results(target=root, results=results, dry_run=dry_run)
        return results


__all__: list[str] = ["FlextInfraRefactorOrchestratorScopeMixin"]
