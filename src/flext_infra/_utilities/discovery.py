"""Project discovery utilities for workspace scanning."""

from __future__ import annotations

from pathlib import Path

from flext_infra import (
    FlextInfraUtilitiesDiscoveryScanning,
    c,
)


class FlextInfraUtilitiesDiscovery(FlextInfraUtilitiesDiscoveryScanning):
    """Static project discovery utilities."""

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
            "libs",
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


__all__ = ["FlextInfraUtilitiesDiscovery"]
