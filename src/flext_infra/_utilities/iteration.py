"""Workspace Python file iteration helpers.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping, MutableSequence, Sequence
from functools import cache
from pathlib import Path

from flext_cli import u
from flext_infra import (
    FlextInfraUtilitiesParsing,
    c,
    r,
    t,
)
from flext_infra._utilities.toml_parse import FlextInfraUtilitiesTomlParse


class FlextInfraUtilitiesIteration:
    """Static helpers for discovering and iterating Python projects in workspace.

    Core concept: A "project" is a directory with Makefile (or go.mod)
    AND at least one configured source directory (src/, tests/, examples/, scripts/).

    Used by: build orchestration, validation, and code generation tools.
    """

    _ITERATION_EXCLUDED_PARTS = c.Infra.Excluded.ITERATION_EXCLUDED_PARTS
    _ITERATION_KNOWN_DIRS = frozenset({
        c.Infra.Paths.DEFAULT_SRC_DIR,
        c.Infra.Directories.TESTS,
        c.Infra.Directories.EXAMPLES,
        c.Infra.Directories.SCRIPTS,
    })

    @staticmethod
    @cache
    def _pyproject_payload(
        pyproject_path: str,
    ) -> t.Infra.ContainerDict:
        """Return one parsed ``pyproject.toml`` payload cached by absolute path."""
        path = Path(pyproject_path)
        if not path.is_file():
            return {}
        result = u.Cli.toml_read_json(path)
        if result.is_failure:
            return {}
        payload = result.value
        return payload if isinstance(payload, dict) else {}

    @staticmethod
    def _tool_flext_meta(
        project_root: Path,
    ) -> t.Infra.ContainerDict:
        """Return the normalized ``tool.flext`` table from a project root."""
        payload = FlextInfraUtilitiesIteration._pyproject_payload(
            str(project_root / c.Infra.Files.PYPROJECT_FILENAME),
        )
        tool = payload.get(c.Infra.TOOL)
        if not isinstance(tool, dict):
            return {}
        flext = tool.get("flext")
        return flext if isinstance(flext, dict) else {}

    @staticmethod
    def _workspace_member_names(workspace_root: Path) -> Sequence[str]:
        """Return configured workspace members from ``tool.flext`` or ``tool.uv``."""
        flext_meta = FlextInfraUtilitiesIteration._tool_flext_meta(workspace_root)
        flext_workspace = flext_meta.get("workspace")
        if isinstance(flext_workspace, dict):
            members = flext_workspace.get("members")
            if isinstance(members, list):
                normalized = [
                    str(member).strip() for member in members if str(member).strip()
                ]
                if normalized:
                    return normalized

        payload = FlextInfraUtilitiesIteration._pyproject_payload(
            str(workspace_root / c.Infra.Files.PYPROJECT_FILENAME),
        )
        tool = payload.get(c.Infra.TOOL)
        if not isinstance(tool, dict):
            return []
        uv = tool.get("uv")
        if not isinstance(uv, dict):
            return []
        uv_workspace = uv.get("workspace")
        if not isinstance(uv_workspace, dict):
            return []
        members = uv_workspace.get("members")
        if not isinstance(members, list):
            return []
        return [str(member).strip() for member in members if str(member).strip()]

    @staticmethod
    def workspace_member_names(workspace_root: Path) -> Sequence[str]:
        """Return canonical workspace members for public utility consumers."""
        return FlextInfraUtilitiesIteration._workspace_member_names(workspace_root)

    @staticmethod
    def namespace_meta(project_root: Path) -> t.Infra.ContainerDict:
        """Return optional ``tool.flext.namespace`` metadata for one project."""
        flext_meta = FlextInfraUtilitiesIteration._tool_flext_meta(project_root)
        namespace = flext_meta.get("namespace")
        return namespace if isinstance(namespace, dict) else {}

    @staticmethod
    def namespace_enabled(project_root: Path) -> bool:
        """Return whether namespace enforcement is enabled for a project."""
        enabled = FlextInfraUtilitiesIteration.namespace_meta(project_root).get(
            "enabled",
            True,
        )
        return enabled if isinstance(enabled, bool) else True

    @staticmethod
    def namespace_scan_dirs(project_root: Path) -> frozenset[str]:
        """Return configured scan dirs for namespace enforcement."""
        configured = FlextInfraUtilitiesIteration.namespace_meta(project_root).get(
            "scan_dirs",
        )
        if isinstance(configured, list):
            normalized = frozenset(
                str(item).strip() for item in configured if str(item).strip()
            )
            if normalized:
                return normalized
        return frozenset(c.Infra.MRO_SCAN_DIRECTORIES)

    @staticmethod
    def namespace_include_dynamic_dirs(project_root: Path) -> bool:
        """Return whether namespace enforcement should scan non-canonical dirs."""
        include_dynamic_dirs = FlextInfraUtilitiesIteration.namespace_meta(
            project_root,
        ).get("include_dynamic_dirs")
        return include_dynamic_dirs if isinstance(include_dynamic_dirs, bool) else False

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
        effective_scan_dirs = scan_dirs or frozenset(c.Infra.MRO_SCAN_DIRECTORIES)
        configured_members = FlextInfraUtilitiesIteration._workspace_member_names(
            workspace_root,
        )
        configured_member_set = set(configured_members)

        def _looks_like_project(path: Path) -> bool:
            if not path.is_dir():
                return False
            pyproject_path = path / c.Infra.Files.PYPROJECT_FILENAME
            go_mod_path = path / c.Infra.Files.GO_MOD
            if not pyproject_path.exists() and not go_mod_path.exists():
                return False
            if go_mod_path.exists():
                return any(
                    (path / dir_name).is_dir() for dir_name in effective_scan_dirs
                )
            if path.name in configured_member_set:
                return True
            if (path / c.Infra.Files.MAKEFILE_FILENAME).exists():
                return True
            document_result = FlextInfraUtilitiesParsing.toml_read_document(
                pyproject_path,
            )
            if document_result.is_failure:
                return False
            dependency_names: set[str] = set(
                FlextInfraUtilitiesTomlParse.declared_dependency_names(
                    document_result.value,
                )
            )
            if c.Infra.Packages.CORE in dependency_names:
                return True
            return any((path / dir_name).is_dir() for dir_name in effective_scan_dirs)

        if configured_members:
            configured_roots = [
                (workspace_root / member).resolve()
                for member in configured_members
                if _looks_like_project((workspace_root / member).resolve())
            ]
            if configured_roots:
                return configured_roots

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
            pattern: Glob pattern (defaults to ``*.py``).
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
            FlextInfraUtilitiesIteration._ITERATION_EXCLUDED_PARTS
            if skip_pycache
            else FlextInfraUtilitiesIteration._ITERATION_EXCLUDED_PARTS
            - {c.Infra.Dunders.PYCACHE}
        )
        return [
            file_path
            for file_path in files
            if FlextInfraUtilitiesIteration.is_canonical_python_file(file_path)
            if not FlextInfraUtilitiesIteration._is_ignored_python_path(
                file_path,
                ignored_parts=ignored_parts,
            )
        ]

    @staticmethod
    def is_canonical_python_file(path: Path) -> bool:
        """Return True only for real ``.py`` source files."""
        return (
            path.is_file()
            and path.suffix == c.Infra.Extensions.PYTHON
            and path.suffixes == [c.Infra.Extensions.PYTHON]
        )

    @staticmethod
    def _is_ignored_python_path(
        path: Path,
        *,
        ignored_parts: frozenset[str] | None = None,
    ) -> bool:
        """Return whether a Python path lives under an ignored directory tree."""
        effective_ignored_parts = (
            ignored_parts or FlextInfraUtilitiesIteration._ITERATION_EXCLUDED_PARTS
        )
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
        project_roots: Sequence[Path] | None = None,
        include_tests: bool = True,
        include_examples: bool = True,
        include_scripts: bool = True,
        include_dynamic_dirs: bool = True,
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

        """
        try:
            roots = project_roots or cls.discover_project_roots(
                workspace_root=workspace_root,
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
                cls._iter_known_dirs(
                    project_root,
                    include_flags,
                    selected_dirs,
                    files,
                )
                if include_dynamic_dirs:
                    cls._iter_dynamic_dirs(
                        project_root,
                        files,
                    )
            return r[Sequence[Path]].ok(sorted(set(files)))
        except OSError as exc:
            return r[Sequence[Path]].fail(f"python file iteration failed: {exc}")

    @staticmethod
    def _iter_known_dirs(
        project_root: Path,
        include_flags: Mapping[str, bool],
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
            if dir_name in FlextInfraUtilitiesIteration._ITERATION_KNOWN_DIRS:
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
