"""Workspace Python file iteration helpers.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import fnmatch
from pathlib import Path

from flext_infra import c, p, r, t
from flext_infra._utilities.git_scope import FlextInfraUtilitiesGitScope
from flext_infra._utilities.namespace_config import FlextInfraUtilitiesNamespaceConfig
from flext_infra._utilities.project_discovery import FlextInfraUtilitiesProjectDiscovery


class FlextInfraUtilitiesFileIteration:
    """Static helpers for discovering and iterating Python files in workspace."""

    @classmethod
    def iter_matching_files(
        cls,
        root: Path,
        *,
        includes: t.StrSequence,
        excludes: t.StrSequence = (),
    ) -> t.SequenceOf[Path]:
        """Return files in one scope through the canonical git-aware selection path."""
        if not root.is_dir():
            return []
        tracked_files = FlextInfraUtilitiesGitScope.git_tracked_scope_paths(root)
        candidates = (
            tracked_files
            if tracked_files is not None
            else [path for path in root.rglob("*") if path.is_file()]
        )
        return sorted(
            {
                path
                for path in candidates
                if path.is_file()
                if (
                    not includes
                    or any(
                        fnmatch.fnmatch(path.relative_to(root).as_posix(), pattern)
                        for pattern in includes
                    )
                )
                if not any(
                    fnmatch.fnmatch(path.relative_to(root).as_posix(), pattern)
                    for pattern in excludes
                )
            },
        )

    @staticmethod
    def iter_directory_python_files(
        directory: Path,
        *,
        pattern: str | None = None,
        skip_pycache: bool = True,
    ) -> t.SequenceOf[Path]:
        """Iterate Python files in a single directory tree.

        Scoped to one directory (project src, subdirectory, etc.) — unlike
        ``iter_python_files`` which discovers across the whole workspace.

        Args:
            directory: Root directory to scan.
            pattern: Glob pattern (defaults to ``*.py``).
            skip_pycache: Exclude ``__pycache__`` paths (default True).

        Returns:
            Sorted list of matching file paths. Empty list if directory
            does not exist.

        """
        if not directory.is_dir():
            return []
        effective_pattern = pattern or c.Infra.EXT_PYTHON_GLOB
        tracked_files = FlextInfraUtilitiesGitScope.git_tracked_scope_paths(directory)
        files = (
            sorted(directory.rglob(effective_pattern))
            if tracked_files is None
            else [
                file_path
                for file_path in tracked_files
                if fnmatch.fnmatch(
                    file_path.relative_to(directory).as_posix(),
                    effective_pattern,
                )
            ]
        )
        ignored_parts = (
            c.Infra.ITERATION_EXCLUDED_PARTS
            if skip_pycache
            else c.Infra.ITERATION_EXCLUDED_PARTS - {c.Infra.DUNDER_PYCACHE}
        )
        return [
            file_path
            for file_path in files
            if FlextInfraUtilitiesFileIteration.matches_canonical_python_file(file_path)
            if not FlextInfraUtilitiesFileIteration._is_ignored_python_path(
                file_path,
                ignored_parts=ignored_parts,
            )
        ]

    @staticmethod
    def matches_canonical_python_file(path: Path) -> bool:
        """Return True only for real ``.py`` source files."""
        return (
            path.is_file()
            and path.suffix == c.Infra.EXT_PYTHON
            and path.suffixes == [c.Infra.EXT_PYTHON]
        )

    @staticmethod
    def _is_ignored_python_path(
        path: Path,
        *,
        ignored_parts: frozenset[str] | None = None,
    ) -> bool:
        """Return whether a Python path lives under an ignored directory tree."""
        effective_ignored_parts = ignored_parts or c.Infra.ITERATION_EXCLUDED_PARTS
        return any(
            part in effective_ignored_parts
            or (part.startswith(".") and part not in {".", ".."})
            for part in path.parts
        )

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
            FlextInfraUtilitiesFileIteration._iter_known_dirs(
                project_root,
                include_flags,
                selected_dirs,
                files,
            )
            if include_dynamic_dirs:
                FlextInfraUtilitiesFileIteration._iter_dynamic_dirs(
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
                    FlextInfraUtilitiesFileIteration.iter_directory_python_files(
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
            py_files = FlextInfraUtilitiesFileIteration.iter_directory_python_files(
                subdir,
            )
            if py_files:
                files.extend(py_files)

    @staticmethod
    def iter_workspace_python_modules(
        workspace_root: Path,
        *,
        exclude_packages: frozenset[str] | None = None,
        include_tests: bool = True,
    ) -> p.Result[t.SequenceOf[t.Pair[Path, Path]]]:
        """Discover all Python modules across workspace projects.

        Returns tuples of (project_root, file_path) for every Python file
        found in the workspace. Optionally excludes packages by name and
        can skip test directories.

        Args:
            workspace_root: Root directory of the workspace.
            exclude_packages: Project directory names to exclude.
            include_tests: Whether to include files under tests/ dirs.

        Returns:
            Result containing list of (project_root, file_path) tuples.

        """
        try:
            result = FlextInfraUtilitiesFileIteration._collect_workspace_python_modules(
                workspace_root=workspace_root,
                exclude_packages=exclude_packages,
                include_tests=include_tests,
            )
            return r[t.SequenceOf[t.Pair[Path, Path]]].ok(result)
        except OSError as exc:
            return r[t.SequenceOf[t.Pair[Path, Path]]].fail_op(
                "workspace python module iteration", exc
            )

    @staticmethod
    def _collect_workspace_python_modules(
        workspace_root: Path,
        exclude_packages: frozenset[str] | None,
        *,
        include_tests: bool,
    ) -> t.SequenceOf[t.Pair[Path, Path]]:
        """Collect (project_root, file_path) tuples across workspace projects."""
        roots = FlextInfraUtilitiesProjectDiscovery.discover_project_roots(
            workspace_root=workspace_root,
        )
        effective_exclude = exclude_packages or frozenset()
        result: t.MutableSequenceOf[t.Pair[Path, Path]] = []
        for project_root in roots:
            if project_root.name in effective_exclude:
                continue
            files_result = FlextInfraUtilitiesFileIteration.iter_python_files(
                workspace_root=workspace_root,
                project_roots=[project_root],
                include_tests=include_tests,
            )
            if files_result.failure:
                continue
            result.extend((project_root, file_path) for file_path in files_result.value)
        return result

    @staticmethod
    def resolve_project_root(file_path: Path) -> Path | None:
        """Walk up from file_path to find the project root containing pyproject.toml."""
        current = file_path.parent
        for _ in range(10):
            if (current / c.Infra.PYPROJECT_FILENAME).is_file():
                return current
            parent = current.parent
            if parent == current:
                break
            current = parent
        return None


__all__: list[str] = ["FlextInfraUtilitiesFileIteration"]
