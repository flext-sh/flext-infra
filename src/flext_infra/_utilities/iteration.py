"""Workspace Python file iteration helpers.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import MutableSequence, Sequence
from pathlib import Path

from flext_core import r
from flext_infra import c, t


class FlextInfraUtilitiesIteration:
    """Static helpers for discovering and iterating Python projects in workspace.

    Core concept: A "project" is a directory with Makefile (or go.mod)
    AND at least one configured source directory (src/, tests/, examples/, scripts/).

    Used by: build orchestration, validation, and code generation tools.
    """

    _IGNORED_PATH_PARTS = frozenset({
        ".git",
        ".venv",
        "__pycache__",
        "build",
        "dist",
        "dist-packages",
        "node_modules",
        "site-packages",
        "vendor",
        "venv",
    })

    @staticmethod
    def discover_project_roots(
        workspace_root: Path,
        *,
        scan_dirs: frozenset[str] | None = None,
    ) -> Sequence[Path]:
        """Discover all project directories under workspace root.

        Algorithm:
          1. Check if workspace_root itself looks like a project
          2. Scan immediate children for project-like directories
          3. Return sorted list, or fallback to [workspace_root] if has src/

        The fallback handles workspaces where all code is in workspace_root/src
        rather than organized into subdirectory projects.

        Args:
            workspace_root: Root directory to start search from.
            scan_dirs: Directory names indicating a project exists (e.g., "src", "tests").
                Must be frozenset for use as constant. Defaults to standard project dirs.

        Returns:
            List of project root paths sorted by name.
            Includes workspace_root itself if it looks like a project.
            At minimum returns [workspace_root] if workspace_root/src/ exists.

        """
        roots: MutableSequence[Path] = []
        effective_scan_dirs = scan_dirs or c.Infra.MRO_SCAN_DIRECTORIES

        def _looks_like_project(path: Path) -> bool:
            if (
                not path.is_dir()
                or not (path / c.Infra.Files.MAKEFILE_FILENAME).exists()
            ):
                return False
            if (
                not (path / c.Infra.Files.PYPROJECT_FILENAME).exists()
                and not (path / c.Infra.Files.GO_MOD).exists()
            ):
                return False
            return any((path / dir_name).is_dir() for dir_name in effective_scan_dirs)

        if _looks_like_project(workspace_root):
            roots.append(workspace_root)
        roots.extend(
            [
                entry
                for entry in sorted(
                    workspace_root.iterdir(),
                    key=lambda item: item.name,
                )
                if entry.is_dir()
                and (not entry.name.startswith("."))
                and _looks_like_project(entry)
            ],
        )
        if not roots and (workspace_root / c.Infra.Paths.DEFAULT_SRC_DIR).is_dir():
            return [workspace_root]
        return roots

    @staticmethod
    def iter_directory_python_files(
        directory: Path,
        *,
        pattern: str | None = None,
        skip_pycache: bool = True,
    ) -> Sequence[Path]:
        """Iterate Python files in a single directory tree.

        Scoped to one directory (project src, subdirectory, etc.) — unlike
        ``iter_python_files`` which discovers across the whole workspace.

        Args:
            directory: Root directory to scan.
            pattern: Glob pattern (defaults to ``c.Infra.Extensions.PYTHON_GLOB``).
            skip_pycache: Exclude ``__pycache__`` paths (default True).

        Returns:
            Sorted list of matching file paths. Empty list if directory
            does not exist.

        """
        if not directory.is_dir():
            return []
        effective_pattern = pattern or c.Infra.Extensions.PYTHON_GLOB
        files = sorted(directory.rglob(effective_pattern))
        ignored_parts = (
            FlextInfraUtilitiesIteration._IGNORED_PATH_PARTS
            if skip_pycache
            else FlextInfraUtilitiesIteration._IGNORED_PATH_PARTS - {"__pycache__"}
        )
        return [
            file_path
            for file_path in files
            if not FlextInfraUtilitiesIteration._is_ignored_python_path(
                file_path,
                ignored_parts=ignored_parts,
            )
        ]

    @staticmethod
    def _is_ignored_python_path(
        path: Path,
        *,
        ignored_parts: frozenset[str] | None = None,
    ) -> bool:
        """Return whether a Python path lives under an ignored directory tree."""
        effective_ignored_parts = (
            ignored_parts or FlextInfraUtilitiesIteration._IGNORED_PATH_PARTS
        )
        return any(
            part in effective_ignored_parts
            or (part.startswith(".") and part not in {".", ".."})
            for part in path.parts
        )

    _KNOWN_DIRS: frozenset[str] = frozenset({
        "src",
        "tests",
        "examples",
        "scripts",
        ".",
        "..",
        "__pycache__",
        ".git",
        ".venv",
        "node_modules",
        "vendor",
        "build",
        "dist",
    })

    @staticmethod
    def iter_python_files(
        workspace_root: Path,
        *,
        project_roots: Sequence[Path] | None = None,
        include_tests: bool = True,
        include_examples: bool = True,
        include_scripts: bool = True,
        src_dirs: frozenset[str] | None = None,
    ) -> r[Sequence[Path]]:
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
            Result[Sequence[Path]] - Success contains sorted unique file paths.
            Failure if: workspace inaccessible, discovery fails, or OSError.

        Raises:
            None (all errors captured in Result.fail()).

        """
        try:
            roots = (
                project_roots
                or FlextInfraUtilitiesIteration.discover_project_roots(
                    workspace_root=workspace_root,
                )
            )
            selected_dirs = src_dirs or frozenset(
                {
                    c.Infra.Paths.DEFAULT_SRC_DIR,
                    c.Infra.Directories.TESTS,
                    c.Infra.Directories.EXAMPLES,
                    c.Infra.Directories.SCRIPTS,
                },
            )
            include_flags = {
                c.Infra.Paths.DEFAULT_SRC_DIR: True,
                c.Infra.Directories.TESTS: include_tests,
                c.Infra.Directories.EXAMPLES: include_examples,
                c.Infra.Directories.SCRIPTS: include_scripts,
            }
            files: MutableSequence[Path] = []
            for project_root in roots:
                FlextInfraUtilitiesIteration._iter_known_dirs(
                    project_root,
                    include_flags,
                    selected_dirs,
                    files,
                )
                FlextInfraUtilitiesIteration._iter_dynamic_dirs(
                    project_root,
                    files,
                )
            return r[Sequence[Path]].ok(sorted(set(files)))
        except OSError as exc:
            return r[Sequence[Path]].fail(f"python file iteration failed: {exc}")

    @staticmethod
    def _iter_known_dirs(
        project_root: Path,
        include_flags: t.BoolMapping,
        selected_dirs: frozenset[str],
        files: MutableSequence[Path],
    ) -> None:
        """Collect Python files from known project directories (src, tests, etc.)."""
        for dir_name, enabled in include_flags.items():
            if (not enabled) or (dir_name not in selected_dirs):
                continue
            directory = project_root / dir_name
            if directory.is_dir():
                files.extend(
                    FlextInfraUtilitiesIteration.iter_directory_python_files(
                        directory,
                    ),
                )

    @staticmethod
    def _iter_dynamic_dirs(
        project_root: Path,
        files: MutableSequence[Path],
    ) -> None:
        """Discover additional directories with Python files (docs/, tools/, etc.)."""
        for subdir in project_root.iterdir():
            if not subdir.is_dir():
                continue
            dir_name = subdir.name
            if dir_name in FlextInfraUtilitiesIteration._KNOWN_DIRS:
                continue
            if dir_name.startswith("."):
                continue
            py_files = FlextInfraUtilitiesIteration.iter_directory_python_files(
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
    ) -> r[Sequence[t.Infra.Pair[Path, Path]]]:
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
            roots = FlextInfraUtilitiesIteration.discover_project_roots(
                workspace_root=workspace_root,
            )
            effective_exclude = exclude_packages or frozenset()
            result: MutableSequence[t.Infra.Pair[Path, Path]] = []
            for project_root in roots:
                if project_root.name in effective_exclude:
                    continue
                files_result = FlextInfraUtilitiesIteration.iter_python_files(
                    workspace_root=workspace_root,
                    project_roots=[project_root],
                    include_tests=include_tests,
                )
                if files_result.is_failure:
                    continue
                result.extend(
                    (project_root, file_path) for file_path in files_result.value
                )
            return r[Sequence[t.Infra.Pair[Path, Path]]].ok(result)
        except OSError as exc:
            return r[Sequence[t.Infra.Pair[Path, Path]]].fail(
                f"workspace python module iteration failed: {exc}",
            )

    @staticmethod
    def resolve_project_root(file_path: Path) -> Path | None:
        """Walk up from file_path to find the project root containing pyproject.toml."""
        current = file_path.parent
        for _ in range(10):
            if (current / c.Infra.Files.PYPROJECT_FILENAME).is_file():
                return current
            parent = current.parent
            if parent == current:
                break
            current = parent
        return None


__all__ = ["FlextInfraUtilitiesIteration"]
