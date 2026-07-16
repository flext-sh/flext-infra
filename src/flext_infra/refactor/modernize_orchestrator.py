"""Generic modernize orchestrator for source transformers.

Provides workspace/project scoped application of any transformer implementing
``apply_to_source(source: str) -> (str, list[str])``, with dry-run support and
reporting via ``m.Infra.Result``.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from flext_cli import cli
from flext_core import r
from flext_infra import c, m, p, t, u


class FlextInfraModernizeOrchestrator:
    """Apply a source transformer across workspace projects."""

    def __init__(
        self,
        transformer_factory: Callable[[], p.Infra.ChangeTracker],
        *,
        description: str,
    ) -> None:
        """Initialize with a factory that produces fresh transformer instances."""
        self._transformer_factory = transformer_factory
        self._description = description

    def run(
        self, params: p.Infra.ModernizeInput
    ) -> p.Result[t.SequenceOf[p.Infra.Result]]:
        """Run modernize across selected projects."""
        workspace_root = params.workspace_path
        project_roots = self._resolve_projects(workspace_root, params.projects)
        if not project_roots:
            return r[t.SequenceOf[p.Infra.Result]].fail(
                "No projects selected", error_code="MODERNIZE_NO_PROJECTS"
            )

        results: list[p.Infra.Result] = []
        with u.Infra.open_project(workspace_root) as rope_project:
            for project_root in project_roots:
                project_results = self._modernize_project(
                    rope_project=rope_project,
                    project_root=project_root,
                    apply=params.apply,
                )
                if project_results.failure:
                    return r[t.SequenceOf[p.Infra.Result]].fail(
                        f"Modernize failed for {project_root.name}: "
                        f"{project_results.error}",
                        error_code="MODERNIZE_PROJECT_FAILED",
                    )
                results.extend(project_results.value)

        return r[t.SequenceOf[p.Infra.Result]].ok(tuple(results))

    @classmethod
    def execute_command(
        cls,
        params: p.Infra.ModernizeInput,
        *,
        transformer_factory: Callable[[], p.Infra.ChangeTracker],
        description: str,
    ) -> p.Result[t.Cli.ResultValue]:
        """Execute one modernization for a CLI route."""
        # mro-r3r8: keep detailed results in run(); CLI routes expose one scalar
        # contract.
        orchestrator = cls(transformer_factory, description=description)
        result = orchestrator.run(params)
        if result.failure:
            return r[t.Cli.ResultValue].fail(result.error, error_code=result.error_code)
        cls._display_results(result.value, dry_run=not params.apply)
        return r[t.Cli.ResultValue].ok(True)

    def _resolve_projects(
        self, workspace_root: Path, project_names: t.StrSequence | None
    ) -> t.SequenceOf[Path]:
        """Resolve project roots, optionally filtered by name."""
        project_roots = u.Infra.discover_project_roots(workspace_root=workspace_root)
        if project_names:
            name_set = set(project_names)
            project_roots = [p for p in project_roots if p.name in name_set]
        return project_roots

    def _modernize_project(
        self, *, rope_project: t.Infra.RopeProject, project_root: Path, apply: bool
    ) -> p.Result[t.SequenceOf[p.Infra.Result]]:
        """Apply transformer to all Python files in a project."""
        results: list[p.Infra.Result] = []
        src_root = project_root / c.Infra.DEFAULT_SRC_DIR
        if not src_root.is_dir():
            return r[t.SequenceOf[p.Infra.Result]].ok(tuple(results))

        for resource in rope_project.get_python_files():
            file_path = Path(resource.real_path).resolve()
            if not file_path.is_relative_to(src_root.resolve()):
                continue
            file_result = self._modernize_file(file_path=file_path, apply=apply)
            if file_result.failure:
                return r[t.SequenceOf[p.Infra.Result]].fail(
                    f"Failed to modernize {file_path}: {file_result.error}",
                    error_code="MODERNIZE_FILE_FAILED",
                )
            results.append(file_result.value)

        return r[t.SequenceOf[p.Infra.Result]].ok(tuple(results))

    def _modernize_file(
        self, *, file_path: Path, apply: bool
    ) -> p.Result[p.Infra.Result]:
        """Apply transformer to a single file."""
        read_result = u.Cli.files_read_text(file_path)
        if read_result.failure:
            return r[p.Infra.Result].fail(
                f"Cannot read {file_path}: {read_result.error}",
                error_code="MODERNIZE_READ_FAILED",
            )

        source = read_result.value
        transformer = self._transformer_factory()
        transform_result = self._safe_transform(transformer, source)
        if transform_result.failure:
            return r[p.Infra.Result].fail(
                f"Transform failed for {file_path}: {transform_result.error}",
                error_code="MODERNIZE_TRANSFORM_FAILED",
            )

        updated, changes = transform_result.value
        modified = updated != source
        if apply and modified:
            write_result = u.Cli.atomic_write_text_file(file_path, updated)
            if write_result.failure:
                return r[p.Infra.Result].fail(
                    f"Cannot write {file_path}: {write_result.error}",
                    error_code="MODERNIZE_WRITE_FAILED",
                )

        return r[p.Infra.Result].ok(
            m.Infra.Result(
                file_path=file_path,
                success=True,
                modified=modified,
                changes=tuple(changes),
                refactored_code=updated if not apply and modified else None,
            )
        )

    @staticmethod
    def _safe_transform(
        transformer: p.Infra.ChangeTracker, source: str
    ) -> p.Result[t.Infra.TransformResult]:
        """Run transformer, catching syntax/runtime errors as failures."""
        try:
            return r[t.Infra.TransformResult].ok(transformer.apply_to_source(source))
        except SyntaxError as exc:
            return r[t.Infra.TransformResult].fail(
                f"Syntax error: {exc}", error_code="MODERNIZE_SYNTAX_ERROR"
            )
        except c.EXC_OS_RUNTIME_TYPE as exc:
            return r[t.Infra.TransformResult].fail(
                f"Runtime error during transform: {exc}",
                error_code="MODERNIZE_TRANSFORM_FAILED",
            )

    @staticmethod
    def _display_results(
        results: t.SequenceOf[p.Infra.Result], *, dry_run: bool
    ) -> None:
        """Render concise summary of modernize results."""
        modified = sum(1 for res in results if res.modified)
        failed = sum(1 for res in results if not res.success)
        mode = "dry-run" if dry_run else "applied"
        cli.display_text(
            f"Modernize {mode}: {len(results)} files, {modified} modified, "
            f"{failed} failed."
        )


__all__: list[str] = ["FlextInfraModernizeOrchestrator"]
