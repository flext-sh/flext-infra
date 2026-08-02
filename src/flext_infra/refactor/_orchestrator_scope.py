"""Refactor orchestration scope mixin for project and workspace execution."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra import c, u

if TYPE_CHECKING:
    from pathlib import Path

    from flext_infra import m, t
    from flext_infra.refactor.loader import FlextInfraRefactorRuleLoader


class FlextInfraRefactorOrchestratorScopeMixin:
    """Provide project and workspace refactor scopes."""

    if TYPE_CHECKING:
        loader: FlextInfraRefactorRuleLoader

        def refactor_files(
            self, file_paths: t.SequenceOf[Path], *, dry_run: bool = False
        ) -> t.SequenceOf[m.Infra.Result]: ...

        @staticmethod
        def _error_result(fp: Path, error: str) -> m.Infra.Result: ...

        @staticmethod
        def _refactor_header(message: str) -> None: ...

    def refactor_project(
        self,
        project_path: Path,
        *,
        dry_run: bool = False,
        pattern: str = c.Infra.EXT_PYTHON_GLOB,
    ) -> t.SequenceOf[m.Infra.Result]:
        """Refactor files under configured project directories."""
        collected = u.Infra.collect_refactor_project_files(
            self.loader.settings, project_path, pattern=pattern
        )
        if collected is None:
            return [
                self._error_result(
                    project_path, f"File iteration failed for {project_path}"
                )
            ]
        u.Cli.info(f"Found {len(collected)} files to process")
        results: t.MutableSequenceOf[m.Infra.Result] = []
        results.extend(self.refactor_files(collected, dry_run=dry_run))
        results.extend(u.Infra.run_rope_post_hooks(project_path, dry_run=dry_run))
        return results

    def refactor_workspace(
        self,
        workspace_root: Path,
        *,
        dry_run: bool = False,
        pattern: str = c.Infra.EXT_PYTHON_GLOB,
    ) -> t.SequenceOf[m.Infra.Result]:
        """Refactor all discoverable workspace projects."""
        root = workspace_root.resolve()
        if not root.exists() or not root.is_dir():
            u.Cli.error(f"Invalid workspace root: {workspace_root}")
            return []
        projects = u.Infra.discover_refactor_projects(self.loader.settings, root)
        if not projects:
            u.Cli.error(f"No projects discovered under: {workspace_root}")
            return []
        u.Cli.info(f"Discovered {len(projects)} projects in workspace")
        results: t.MutableSequenceOf[m.Infra.Result] = []
        for project in projects:
            self._refactor_header(f"Project: {project}")
            results.extend(
                self.refactor_project(project, dry_run=dry_run, pattern=pattern)
            )
        results.extend(u.Infra.run_rope_post_hooks(root, dry_run=dry_run))
        return results


__all__: list[str] = ["FlextInfraRefactorOrchestratorScopeMixin"]
