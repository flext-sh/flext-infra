"""Project discovery utilities for workspace scanning.

All methods are static — exposed via u.Infra.discover_projects() through MRO.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import re
from pathlib import Path

from flext_core import r
from flext_infra._utilities.iteration import FlextInfraUtilitiesIteration
from flext_infra.constants import FlextInfraConstants as c
from flext_infra.models import FlextInfraModels as m


class FlextInfraUtilitiesDiscovery:
    @staticmethod
    def _identify_project_by_roots(
        file_path: Path,
        project_roots: list[Path],
    ) -> str:
        """Identify project name for a file path (most-specific root wins)."""
        best: Path | None = None
        for root in project_roots:
            try:
                file_path.relative_to(root)
            except ValueError:
                continue
            if best is None or len(root.parts) > len(best.parts):
                best = root
        return best.name if best else c.Infra.Defaults.UNKNOWN

    @staticmethod
    def _is_git_project(path: Path) -> bool:
        """Check if a directory is a Git repository."""
        return (path / c.Infra.Git.DIR).exists()

    @staticmethod
    def _submodule_names(workspace_root: Path) -> set[str]:
        """Retrieve submodule names from .gitmodules."""
        gitmodules = workspace_root / c.Infra.Files.GITMODULES
        if not gitmodules.exists():
            return set()
        try:
            content = gitmodules.read_text(encoding=c.Infra.Encoding.DEFAULT)
        except OSError:
            return set()
        return set(re.findall(r"^\s*path\s*=\s*(.+?)\s*$", content, re.MULTILINE))

    @staticmethod
    def discover_projects(
        workspace_root: Path,
    ) -> r[list[m.Infra.ProjectInfo]]:
        try:
            projects: list[m.Infra.ProjectInfo] = []
            submodules = FlextInfraUtilitiesDiscovery._submodule_names(workspace_root)
            for entry in sorted(workspace_root.iterdir(), key=lambda v: v.name):
                if (
                    not entry.is_dir()
                    or entry.name == "cmd"
                    or entry.name.startswith(".")
                ):
                    continue
                if not FlextInfraUtilitiesDiscovery._is_git_project(entry):
                    continue
                if not (entry / c.Infra.Files.MAKEFILE_FILENAME).exists():
                    continue
                has_pyproject = (entry / c.Infra.Files.PYPROJECT_FILENAME).exists()
                has_gomod = (entry / c.Infra.Files.GO_MOD).exists()
                if not has_pyproject and (not has_gomod):
                    continue
                stack = c.Infra.Toml.PYTHON if has_pyproject else c.Infra.Gates.GO
                kind = "submodule" if entry.name in submodules else "external"
                projects.append(
                    m.Infra.ProjectInfo(
                        path=entry,
                        name=entry.name,
                        stack=f"{stack}/{kind}",
                        has_tests=(entry / c.Infra.Directories.TESTS).is_dir(),
                        has_src=(entry / c.Infra.Paths.DEFAULT_SRC_DIR).is_dir(),
                    ),
                )
            return r[list[m.Infra.ProjectInfo]].ok(projects)
        except OSError as exc:
            return r[list[m.Infra.ProjectInfo]].fail(
                f"project discovery failed: {exc}",
            )

    @staticmethod
    def discover_project_roots(
        workspace_root: Path,
        *,
        scan_dirs: frozenset[str] | None = None,
    ) -> list[Path]:
        return FlextInfraUtilitiesIteration.discover_project_roots(
            workspace_root=workspace_root,
            scan_dirs=scan_dirs,
        )

    @staticmethod
    def discover_project_root_from_file(file_path: Path) -> Path | None:
        """Discover the project root directory starting from a file path."""
        resolved = file_path.resolve()
        candidate = resolved.parent if resolved.is_file() else resolved
        lineage = (candidate, *candidate.parents)
        for current in lineage:
            if current.name == "src":
                return current.parent
            src_dir = current / "src"
            if src_dir.is_dir():
                return current
        return None

    @staticmethod
    def discover_package_from_file(file_path: Path) -> str:
        """Discover the package name for a Python file."""
        resolved = file_path.resolve()
        candidate = resolved.parent if resolved.is_file() else resolved
        lineage = (candidate, *candidate.parents)
        for current in lineage:
            if current.name != "src":
                continue
            try:
                relative = resolved.relative_to(current)
            except ValueError:
                continue
            if len(relative.parts) == 0:
                continue
            package_name = relative.parts[0]
            package_dir = current / package_name
            if (package_dir / "__init__.py").is_file():
                return package_name
        project_root = FlextInfraUtilitiesDiscovery.discover_project_root_from_file(
            file_path,
        )
        if project_root is None:
            return ""
        src_dir = project_root / "src"
        if not src_dir.is_dir():
            return ""
        for child in sorted(src_dir.iterdir()):
            if child.is_dir() and (child / "__init__.py").is_file():
                return child.name
        return ""

    @staticmethod
    def discover_workspace_root_from_file(file_path: Path) -> Path:
        """Discover the workspace root (directory containing all projects)."""
        project_root = FlextInfraUtilitiesDiscovery.discover_project_root_from_file(
            file_path,
        )
        return project_root.parent if project_root else file_path.resolve().parent

    @staticmethod
    def discover_workspace_packages(workspace_root: Path) -> frozenset[str]:
        """Discover all project package names in the workspace."""
        packages: set[str] = set()
        if not workspace_root.is_dir():
            return frozenset()
        for entry in workspace_root.iterdir():
            if not entry.is_dir() or entry.name.startswith("."):
                continue
            package_name = FlextInfraUtilitiesDiscovery.discover_package_from_file(
                entry / "src",
            )
            if package_name:
                packages.add(package_name)
        return frozenset(packages)

    @staticmethod
    def discover_core_package(project_root: Path) -> str:
        """Discover the core package name for a project."""
        pyproject_path = project_root / c.Infra.Files.PYPROJECT_FILENAME
        if pyproject_path.is_file():
            content = pyproject_path.read_text(encoding=c.Infra.Encoding.DEFAULT)
            if "flext-core" in content or "flext_core" in content:
                return "flext_core"
        return "flext_core"

    @staticmethod
    def iter_workspace_python_modules(
        workspace_root: Path,
        *,
        exclude_packages: frozenset[str] | None = None,
        include_tests: bool = True,
    ) -> r[list[tuple[Path, Path]]]:
        """Iterate workspace Python files with project root association.

        Returns list of (project_root, python_file) tuples.
        """
        project_roots = FlextInfraUtilitiesDiscovery.discover_project_roots(
            workspace_root,
        )
        files_result = FlextInfraUtilitiesIteration.iter_python_files(
            workspace_root,
            project_roots=project_roots,
            include_tests=include_tests,
        )
        if files_result.is_failure:
            return r[list[tuple[Path, Path]]].fail(files_result.error)

        excluded = exclude_packages or frozenset()
        root_by_name = {root.name: root for root in project_roots}
        modules: list[tuple[Path, Path]] = []
        for file_path in files_result.value:
            if "__pycache__" in file_path.parts:
                continue
            project_name = FlextInfraUtilitiesDiscovery._identify_project_by_roots(
                file_path,
                project_roots,
            )
            if project_name in excluded:
                continue
            project_root = root_by_name.get(project_name)
            if project_root is None:
                continue
            modules.append((project_root, file_path))
        return r[list[tuple[Path, Path]]].ok(modules)

    @staticmethod
    def find_all_pyproject_files(
        workspace_root: Path,
        *,
        skip_dirs: frozenset[str] | None = None,
        project_paths: list[Path] | None = None,
    ) -> r[list[Path]]:
        try:
            if project_paths:
                selected: list[Path] = []
                for proj_path in project_paths:
                    target = (
                        proj_path
                        if proj_path.name == c.Infra.Files.PYPROJECT_FILENAME
                        else proj_path / c.Infra.Files.PYPROJECT_FILENAME
                    )
                    if target.exists() and target.is_file():
                        selected.append(target)
                return r[list[Path]].ok(sorted(set(selected)))
            effective_skip = (
                skip_dirs
                if skip_dirs is not None
                else c.Infra.Excluded.PYPROJECT_SKIP_DIRS
            )
            result = [
                found
                for found in sorted(
                    workspace_root.rglob(c.Infra.Files.PYPROJECT_FILENAME),
                )
                if not any(skip in found.parts for skip in effective_skip)
            ]
            return r[list[Path]].ok(result)
        except OSError as exc:
            return r[list[Path]].fail(f"pyproject file scan failed: {exc}")


__all__ = ["FlextInfraUtilitiesDiscovery"]
