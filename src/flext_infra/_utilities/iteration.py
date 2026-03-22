"""Workspace Python file iteration helpers.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_core import r
from flext_infra import c


class FlextInfraUtilitiesIteration:
    """Static helpers for discovering and iterating Python projects in workspace.

    Core concept: A "project" is a directory with Makefile (or go.mod)
    AND at least one configured source directory (src/, tests/, examples/, scripts/).

    Used by: build orchestration, validation, and code generation tools.
    """

    @staticmethod
    def discover_project_roots(
        workspace_root: Path,
        *,
        scan_dirs: frozenset[str] | None = None,
    ) -> list[Path]:
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
        roots: list[Path] = []
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
        if (
            len(roots) == 0
            and (workspace_root / c.Infra.Paths.DEFAULT_SRC_DIR).is_dir()
        ):
            return [workspace_root]
        return roots

    @staticmethod
    def iter_directory_python_files(
        directory: Path,
        *,
        pattern: str | None = None,
        skip_pycache: bool = True,
    ) -> list[Path]:
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
        if skip_pycache:
            return [f for f in files if "__pycache__" not in f.parts]
        return files

    @staticmethod
    def iter_python_files(
        workspace_root: Path,
        *,
        project_roots: list[Path] | None = None,
        include_tests: bool = True,
        include_examples: bool = True,
        include_scripts: bool = True,
        src_dirs: frozenset[str] | None = None,
    ) -> r[list[Path]]:
        """Discover and iterate all Python files across workspace projects.

        Unlike iter_directory_python_files() which scans a single directory,
        this discovers all projects in workspace and iterates dynamically:
          - Includes src/, tests/, examples/, scripts/ by default (with toggles)
          - ALSO dynamically discovers ANY other directories with Python files
          - Can exclude specific standard directories (e.g., skip tests)
          - Handles discovery failure gracefully (returns Result type)
          - Accepts pre-discovered project roots for caching

        Algorithm:
          1. Discover project roots (unless project_roots provided)
          2. For each root, collect files from:
             a. Explicitly specified directories (src, tests, examples, scripts)
                if enabled via include_* flags
             b. ANY other subdirectories containing Python files (dynamic)
          3. Deduplicate (set) and sort results

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
            Result[list[Path]] - Success contains sorted unique file paths.
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
            # Dynamic directory discovery: scan all subdirectories with Python files
            selected_dirs = src_dirs or frozenset(
                {
                    c.Infra.Paths.DEFAULT_SRC_DIR,
                    c.Infra.Directories.TESTS,
                    c.Infra.Directories.EXAMPLES,
                    c.Infra.Directories.SCRIPTS,
                },
            )
            # Build include flags for known directories
            include_flags = {
                c.Infra.Paths.DEFAULT_SRC_DIR: True,
                c.Infra.Directories.TESTS: include_tests,
                c.Infra.Directories.EXAMPLES: include_examples,
                c.Infra.Directories.SCRIPTS: include_scripts,
            }
            files: list[Path] = []
            for project_root in roots:
                # First: include explicitly specified directories if enabled
                for dir_name, enabled in include_flags.items():
                    if (not enabled) or (dir_name not in selected_dirs):
                        continue
                    directory = project_root / dir_name
                    if directory.is_dir():
                        files.extend(directory.rglob(c.Infra.Extensions.PYTHON_GLOB))

                # Second: dynamically discover any other directories with Python files
                # (for extensibility - docs/, tools/, etc.)
                for subdir in project_root.iterdir():
                    if not subdir.is_dir():
                        continue
                    dir_name = subdir.name
                    # Skip known system dirs and those already processed
                    if dir_name in {
                        "src",
                        "tests",
                        "examples",
                        "scripts",  # Already handled above
                        ".",
                        "..",
                        "__pycache__",
                        ".git",
                        ".venv",
                        "node_modules",
                        "vendor",
                        "build",
                        "dist",
                    }:
                        continue
                    # Skip dotfiles/hidden directories
                    if dir_name.startswith("."):
                        continue
                    # Check if directory contains Python files
                    py_files = list(subdir.rglob(c.Infra.Extensions.PYTHON_GLOB))
                    if py_files:
                        files.extend(py_files)

            return r[list[Path]].ok(sorted(set(files)))
        except OSError as exc:
            return r[list[Path]].fail(f"python file iteration failed: {exc}")

    @staticmethod
    def iter_workspace_python_modules(
        workspace_root: Path,
        *,
        exclude_packages: frozenset[str] | None = None,
        include_tests: bool = True,
    ) -> r[list[tuple[Path, Path]]]:
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
            result: list[tuple[Path, Path]] = []
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
                for file_path in files_result.value:
                    result.append((project_root, file_path))
            return r[list[tuple[Path, Path]]].ok(result)
        except OSError as exc:
            return r[list[tuple[Path, Path]]].fail(
                f"workspace python module iteration failed: {exc}"
            )


__all__ = ["FlextInfraUtilitiesIteration"]
