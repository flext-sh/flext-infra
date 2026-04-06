"""Project discovery utilities for workspace scanning."""

from __future__ import annotations

import re
from collections.abc import Sequence
from pathlib import Path

from flext_core import r
from flext_infra import (
    FlextInfraUtilitiesDiscoveryScanning,
    FlextInfraUtilitiesDocsScope,
    c,
    m,
    t,
)


class FlextInfraUtilitiesDiscovery(FlextInfraUtilitiesDiscoveryScanning):
    """Static project discovery utilities."""

    @staticmethod
    def discover_projects(
        workspace_root: Path,
    ) -> r[Sequence[m.Infra.ProjectInfo]]:
        """Find valid projects in the workspace."""
        if not workspace_root.exists() or not workspace_root.is_dir():
            return r[Sequence[m.Infra.ProjectInfo]].fail(
                f"discovery failed: invalid workspace root {workspace_root}",
            )
        excluded = FlextInfraUtilitiesDocsScope.excluded_roots(workspace_root)
        projects: list[m.Infra.ProjectInfo] = []
        try:
            for entry in sorted(workspace_root.iterdir(), key=lambda item: item.name):
                if (
                    not entry.is_dir()
                    or entry.name.startswith(".")
                    or entry.name == "cmd"
                    or entry.name in excluded
                ):
                    continue
                pyproject = entry / c.Infra.Files.PYPROJECT_FILENAME
                if not pyproject.is_file():
                    continue
                if not (entry / c.Infra.Files.MAKEFILE_FILENAME).is_file():
                    continue
                payload = FlextInfraUtilitiesDocsScope.pyproject_payload(entry)
                docs_meta = FlextInfraUtilitiesDocsScope.docs_meta_from_payload(payload)
                enabled = docs_meta.get("enabled", True)
                if isinstance(enabled, bool) and not enabled:
                    continue
                projects.append(
                    m.Infra.ProjectInfo.model_construct(
                        path=entry,
                        name=entry.name,
                        stack="python/flext",
                        has_tests=(entry / c.Infra.Directories.TESTS).is_dir(),
                        has_src=(entry / c.Infra.Paths.DEFAULT_SRC_DIR).is_dir(),
                        project_class=(
                            FlextInfraUtilitiesDocsScope.classify_project_from_meta(
                                entry.name,
                                docs_meta,
                            )
                        ),
                        package_name=(
                            FlextInfraUtilitiesDocsScope.package_name_from_payload(
                                entry,
                                payload,
                                docs_meta,
                            )
                        ),
                    )
                )
        except OSError as exc:
            return r[Sequence[m.Infra.ProjectInfo]].fail(
                f"discovery failed: {exc}",
            )
        return r[Sequence[m.Infra.ProjectInfo]].ok(projects)

    @staticmethod
    def _submodule_names(workspace_root: Path) -> t.Infra.StrSet:
        gitmodules = workspace_root / ".gitmodules"
        if not gitmodules.exists():
            return set()
        try:
            content = gitmodules.read_text(encoding=c.Infra.Encoding.DEFAULT)
        except OSError:
            return set()
        return set(re.findall(r"^\s*path\s*=\s*(.+?)\s*$", content, re.MULTILINE))

    @staticmethod
    def discover_project_root_from_file(file_path: Path) -> Path | None:
        """Discover the project root directory starting from a file path."""
        resolved = file_path.resolve()
        candidate = resolved.parent if resolved.is_file() else resolved
        lineage = (candidate, *candidate.parents)
        for current in lineage:
            if current.name == c.Infra.Paths.DEFAULT_SRC_DIR:
                return current.parent
            if (current / c.Infra.Paths.DEFAULT_SRC_DIR).is_dir():
                return current
        return None

    @staticmethod
    def discover_package_from_file(file_path: Path) -> str:
        """Discover the package name for a Python file."""
        resolved = file_path.resolve()
        probe_path = FlextInfraUtilitiesDiscovery._package_probe_path(resolved)
        module_path = FlextInfraUtilitiesDiscovery.discover_module_path(probe_path)
        if module_path:
            return module_path
        via_src = FlextInfraUtilitiesDiscovery._discover_package_via_src_lineage(
            resolved,
        )
        if via_src:
            return via_src
        return FlextInfraUtilitiesDiscovery._discover_package_via_project_root(
            file_path,
        )

    @staticmethod
    def _package_probe_path(path: Path) -> Path:
        """Return a synthetic __init__.py path for package-path discovery."""
        if path.suffix == c.Infra.Extensions.PYTHON:
            if path.name == c.Infra.Files.INIT_PY:
                return path
            return path.parent / c.Infra.Files.INIT_PY
        return path / c.Infra.Files.INIT_PY

    @staticmethod
    def _discover_package_via_src_lineage(resolved: Path) -> str:
        """Walk parent directories looking for a src/ boundary with a package."""
        candidate = (
            resolved.parent
            if resolved.suffix == c.Infra.Extensions.PYTHON
            else resolved
        )
        lineage = (candidate, *candidate.parents)
        for current in lineage:
            if current.name != c.Infra.Paths.DEFAULT_SRC_DIR:
                continue
            try:
                relative = resolved.relative_to(current)
                relative_parts = relative.parts
                if relative_parts and relative_parts[-1] == c.Infra.Files.INIT_PY:
                    relative_parts = relative_parts[:-1]
                if not relative_parts:
                    continue
                package_name = ".".join(relative_parts)
                if package_name:
                    return package_name
            except ValueError:
                continue
        return ""

    @staticmethod
    def _discover_package_via_project_root(file_path: Path) -> str:
        """Fallback: find project root and return its first src/ package."""
        project_root = FlextInfraUtilitiesDiscovery.discover_project_root_from_file(
            file_path,
        )
        if project_root is None:
            return ""
        src_dir = project_root / c.Infra.Paths.DEFAULT_SRC_DIR
        if not src_dir.is_dir():
            return ""
        for child in sorted(src_dir.iterdir()):
            if child.is_dir() and (child / c.Infra.Files.INIT_PY).is_file():
                return child.name
        return ""

    @staticmethod
    def discover_module_path(path: Path) -> str:
        """Discover the fully qualified module path for a Python file."""
        root_markers = {
            c.Infra.Directories.DOCS,
            c.Infra.Directories.EXAMPLES,
            c.Infra.Directories.SCRIPTS,
            c.Infra.Paths.DEFAULT_SRC_DIR,
            c.Infra.Directories.TESTS,
        }
        abs_parts = path.absolute().parts
        for index, part in enumerate(abs_parts):
            if part not in root_markers:
                continue
            pkg_parts = abs_parts[index + 1 : -1]
            if part == c.Infra.Paths.DEFAULT_SRC_DIR:
                return ".".join(pkg_parts)
            return ".".join([part, *pkg_parts]) if pkg_parts else part
        return ""

    @staticmethod
    def discover_workspace_root_from_file(file_path: Path) -> Path:
        """Discover the workspace root."""
        root = FlextInfraUtilitiesDiscovery.discover_project_root_from_file(file_path)
        return root.parent if root else file_path.resolve().parent

    @staticmethod
    def package_context(file_path: Path) -> t.Infra.Pair[Path, str]:
        """Return (package_dir, package_name) for any project type."""
        parts = file_path.resolve().parts
        # 1. Standard FLEXT structure: .../src/<package_name>/...
        if c.Infra.Paths.DEFAULT_SRC_DIR in parts:
            src_idx = parts.index(c.Infra.Paths.DEFAULT_SRC_DIR)
            # Package name is always the directory immediately after 'src'
            if src_idx + 1 < len(parts):
                package_name = parts[src_idx + 1]
                package_dir = Path(*parts[: src_idx + 2])
                return package_dir, package_name

        # 2. Alternative structure: find highest-level directory with __init__.py
        current = file_path.resolve().parent
        best_dir, best_name = current, ""
        while current.parent != current:
            if (current / c.Infra.Files.INIT_PY).is_file():
                best_dir, best_name = current, current.name
            elif best_name:  # Stop once we've crossed out of the package
                break
            current = current.parent
        return best_dir, best_name

    @staticmethod
    def discover_core_package(_project_root: Path) -> str:
        """Discover the core package name for a project."""
        return c.Infra.Packages.CORE_UNDERSCORE


__all__ = ["FlextInfraUtilitiesDiscovery"]
