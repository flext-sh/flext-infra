"""Enforcement phase methods for namespace enforcer."""

from __future__ import annotations

import difflib
from collections.abc import (
    Callable,
    MutableMapping,
)
from pathlib import Path

from flext_infra.detectors.facade_scanner import FlextInfraScanner
from flext_infra.models import m
from flext_infra.typings import t
from flext_infra.utilities import u


class FlextInfraNamespaceEnforcerPhasesMixin:
    """Project enforcement and diff methods for namespace enforcer."""

    _workspace_root: Path
    _rope_project: t.Infra.RopeProject

    def _resolve_project_roots(
        self,
        *,
        project_names: t.StrSequence | None = None,
    ) -> t.SequenceOf[Path]:
        """Resolve project roots."""
        msg = "_resolve_project_roots must be provided by the concrete enforcer"
        raise NotImplementedError(msg)

    def _detect_and_apply[V](
        self,
        *,
        py_files: t.SequenceOf[Path],
        detect_fn: Callable[[Path], t.SequenceOf[V]],
        rewrite_fn: Callable[[t.MutableSequenceOf[V]], None] | None,
        apply: bool,
    ) -> t.MutableSequenceOf[V]:
        """Detect and apply."""
        _ = self, py_files, detect_fn, rewrite_fn, apply
        msg = "_detect_and_apply must be provided by the concrete enforcer"
        raise NotImplementedError(msg)

    def enforce(
        self,
        *,
        apply: bool = False,
        project_names: t.StrSequence | None = None,
    ) -> m.Infra.WorkspaceEnforcementReport:
        """Enforce namespace rules across the workspace."""
        _ = apply, project_names
        msg = "enforce must be provided by the concrete enforcer"
        raise NotImplementedError(msg)

    @staticmethod
    def _scan_facades(
        *,
        project: tuple[Path, str],
        rope_project: t.Infra.RopeProject,
        apply: bool,
        workspace_root: Path,
    ) -> t.SequenceOf[m.Infra.FacadeStatus]:
        """Scan facades and optionally create missing ones."""
        project_root, project_name = project
        facade_statuses = FlextInfraScanner.scan_project(
            project_root=project_root,
            rope_project=rope_project,
        )
        if not apply:
            return facade_statuses
        u.Infra.ensure_missing_facades(
            project_root=project_root,
            project_name=project_name,
            facade_statuses=facade_statuses,
            workspace_root=workspace_root,
        )
        return FlextInfraScanner.scan_project(
            project_root=project_root,
            rope_project=rope_project,
        )

    @staticmethod
    def _collect_py_files(*, project_root: Path) -> t.SequenceOf[Path]:
        """Collect Python files for scanning."""
        py_files_result = u.Infra.iter_python_files(
            workspace_root=project_root,
            project_roots=[project_root],
            include_dynamic_dirs=u.Infra.namespace_include_dynamic_dirs(project_root),
            src_dirs=u.Infra.namespace_scan_dirs(project_root),
        )
        if py_files_result.failure:
            return []
        files: t.SequenceOf[Path] = py_files_result.value
        return files

    def diff(
        self,
        *,
        project_names: t.StrSequence | None = None,
    ) -> str:
        """Run enforce with apply in diff mode: apply, capture diff, restore originals.

        WARNING: NOT read-only. This mode rewrites files in place with
        ``enforce(apply=True)``, captures the unified diff, then restores the
        original contents; files created during the run are deleted on the
        restore path. Never use it for read-only baselines — use
        ``enforce(apply=False)`` (the default dry-run scan) instead.

        Returns:
            Unified diff string showing all changes that --apply would make.

        """
        project_roots = self._resolve_project_roots(project_names=project_names)
        all_py_files: t.MutableSequenceOf[Path] = []
        for project_root in project_roots:
            all_py_files.extend(self._collect_py_files(project_root=project_root))
        snapshots: MutableMapping[Path, str] = {}
        for py_file in all_py_files:
            if py_file.is_file():
                snapshots[py_file] = u.Cli.files_read_text(py_file).unwrap()
        try:
            self.enforce(apply=True, project_names=project_names)
        finally:
            diff_lines: t.MutableSequenceOf[str] = []
            for py_file, original in snapshots.items():
                if not py_file.is_file():
                    continue
                modified = u.Cli.files_read_text(py_file).unwrap()
                if modified != original:
                    rel = py_file.relative_to(self._workspace_root)
                    diff_lines.extend(
                        difflib.unified_diff(
                            original.splitlines(keepends=True),
                            modified.splitlines(keepends=True),
                            fromfile=f"a/{rel}",
                            tofile=f"b/{rel}",
                        ),
                    )
                _ = u.Cli.atomic_write_text_file(py_file, original).unwrap()
            for project_root in project_roots:
                for py_file in self._collect_py_files(project_root=project_root):
                    if py_file not in snapshots and py_file.is_file():
                        rel = py_file.relative_to(self._workspace_root)
                        content = u.Cli.files_read_text(py_file).unwrap()
                        diff_lines.extend(
                            difflib.unified_diff(
                                [],
                                content.splitlines(keepends=True),
                                fromfile="/dev/null",
                                tofile=f"b/{rel}",
                            ),
                        )
                        py_file.unlink()
        return "".join(diff_lines)


__all__: list[str] = ["FlextInfraNamespaceEnforcerPhasesMixin"]
