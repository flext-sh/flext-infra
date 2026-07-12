"""Workspace-scoped Python file iteration mixin.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from flext_core import r
from flext_infra._iteration_directory import FlextInfraUtilitiesIterationDirectory
from flext_infra._utilities.git_scope import FlextInfraUtilitiesGitScope
from flext_infra._utilities.namespace_config import FlextInfraUtilitiesNamespaceConfig
from flext_infra._utilities.project_discovery import FlextInfraUtilitiesProjectDiscovery
from flext_infra.constants import c
from flext_infra.typings import t

if TYPE_CHECKING:
    from flext_infra.protocols import p


class FlextInfraUtilitiesIterationWorkspace:
    """Static helpers for discovering Python files across workspace projects."""

    @classmethod
    def iter_python_files(
        cls,
        workspace_root: Path,
        *,
        project_roots: t.SequenceOf[Path] | None = None,
        include_tests: bool = True,
        include_examples: bool = True,
        include_scripts: bool = True,
        include_dynamic_dirs: bool = True,
        src_dirs: frozenset[str] | None = None,
    ) -> p.Result[t.SequenceOf[Path]]:
        """Discover and iterate all Python files across workspace projects.

        Args:
            workspace_root: Workspace root to discover from.
            project_roots: Pre-discovered project paths to skip discovery phase.
                Useful for caching results across multiple calls.
            include_tests: Include tests/ directories (default True).
            include_examples: Include examples/ directories (default True).
            include_scripts: Include scripts/ directories (default True).
            include_dynamic_dirs: Include dynamic directories (default True).
            src_dirs: Which subdirectories to scan. Defaults to standard locations.
                src/ is always included regardless of include_* flags.

        Returns:
            Result[t.SequenceOf[Path]] - Success contains sorted unique file paths.
            Failure if: workspace inaccessible, discovery fails, or OSError.

        """
        try:
            files = cls._collect_python_files(
                workspace_root=workspace_root,
                project_roots=project_roots,
                include_tests=include_tests,
                include_examples=include_examples,
                include_scripts=include_scripts,
                include_dynamic_dirs=include_dynamic_dirs,
                src_dirs=src_dirs,
            )
            return r[t.SequenceOf[Path]].ok(files)
        except OSError as exc:
            return r[t.SequenceOf[Path]].fail_op("python file iteration", exc)

    @staticmethod
    def _collect_python_files(
        workspace_root: Path,
        project_roots: t.SequenceOf[Path] | None,
        *,
        include_tests: bool,
        include_examples: bool,
        include_scripts: bool,
        include_dynamic_dirs: bool,
        src_dirs: frozenset[str] | None,
    ) -> t.SequenceOf[Path]:
        """Collect Python files across workspace projects."""
        roots = (
            project_roots
            or FlextInfraUtilitiesProjectDiscovery.discover_project_roots(
                workspace_root=workspace_root,
            )
        )
        selected_dirs = src_dirs or frozenset(
            {
                c.Infra.DEFAULT_SRC_DIR,
                c.Infra.DIR_TESTS,
                c.Infra.DIR_EXAMPLES,
                c.Infra.DIR_SCRIPTS,
            },
        )
        include_flags = {
            c.Infra.DEFAULT_SRC_DIR: True,
            c.Infra.DIR_TESTS: include_tests,
            c.Infra.DIR_EXAMPLES: include_examples,
            c.Infra.DIR_SCRIPTS: include_scripts,
        }
        files: t.MutableSequenceOf[Path] = []
        for project_root in roots:
            FlextInfraUtilitiesIterationWorkspace._iter_known_dirs(
                project_root,
                include_flags,
                selected_dirs,
                files,
            )
            if include_dynamic_dirs:
                FlextInfraUtilitiesIterationWorkspace._iter_dynamic_dirs(
                    project_root,
                    files,
                )
        return sorted(set(files))

    @staticmethod
    def _iter_known_dirs(
        project_root: Path,
        include_flags: t.BoolMapping,
        selected_dirs: frozenset[str],
        files: t.MutableSequenceOf[Path],
    ) -> None:
        """Collect Python files from known project directories (src, tests, etc.)."""
        for dir_name, enabled in include_flags.items():
            if (not enabled) or (dir_name not in selected_dirs):
                continue
            directory = project_root / dir_name
            if directory.is_dir():
                files.extend(
                    FlextInfraUtilitiesIterationDirectory.iter_directory_python_files(
                        directory,
                    ),
                )

    @staticmethod
    def _iter_dynamic_dirs(
        project_root: Path,
        files: t.MutableSequenceOf[Path],
    ) -> None:
        """Discover additional directories with Python files (docs/, tools/, etc.)."""
        tracked_dir_names = FlextInfraUtilitiesGitScope.git_tracked_top_level_dir_names(
            project_root,
        )
        for subdir in project_root.iterdir():
            if not subdir.is_dir():
                continue
            dir_name = subdir.name
            if dir_name in FlextInfraUtilitiesNamespaceConfig.namespace_scan_dirs(
                project_root,
            ):
                continue
            if dir_name.startswith("."):
                continue
            if tracked_dir_names is not None and dir_name not in tracked_dir_names:
                continue
            py_files = (
                FlextInfraUtilitiesIterationDirectory.iter_directory_python_files(
                    subdir,
                )
            )
            if py_files:
                files.extend(py_files)


__all__: list[str] = ["FlextInfraUtilitiesIterationWorkspace"]
