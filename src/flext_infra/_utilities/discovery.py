"""Project discovery utilities for package and workspace resolution."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path

from flext_infra import c, r, t
from flext_infra._utilities.docs_scope import FlextInfraUtilitiesDocsScope
from flext_infra._utilities.rope_analysis import FlextInfraUtilitiesRopeAnalysis
from flext_infra._utilities.rope_core import FlextInfraUtilitiesRopeCore


class FlextInfraUtilitiesDiscovery:
    """Canonical discovery helpers for path, package, and Rope-backed scans."""

    @staticmethod
    def discover_project_root_from_file(file_path: Path) -> Path | None:
        """Discover the enclosing project root for one file or directory path."""
        resolved = file_path.resolve()
        candidate = (
            resolved.parent
            if resolved.suffix == c.Infra.Extensions.PYTHON
            else resolved
        )
        wrapper_root: Path | None = None
        for current in (candidate, *candidate.parents):
            if current.name == c.Infra.Paths.DEFAULT_SRC_DIR:
                wrapper_root = current.parent
                continue
            if current.name in c.Infra.ROOT_WRAPPER_SEGMENTS:
                wrapper_root = current.parent
                continue
            if (current / c.Infra.Paths.DEFAULT_SRC_DIR).is_dir():
                return current
        return wrapper_root

    @staticmethod
    def discover_package_from_file(file_path: Path) -> str:
        """Discover the module or package path for one Python file or package directory."""
        resolved = file_path.resolve()
        relative_parts: tuple[str, ...] = ()
        project_root = FlextInfraUtilitiesDiscovery.discover_project_root_from_file(
            file_path,
        )
        if project_root is not None:
            try:
                relative_parts = resolved.relative_to(project_root).parts
            except ValueError:
                relative_parts = ()
        normalized_parts = (
            relative_parts[:-1]
            if relative_parts and relative_parts[-1] == c.Infra.Files.INIT_PY
            else relative_parts[:-1] + (resolved.stem,)
            if resolved.suffix == c.Infra.Extensions.PYTHON and relative_parts
            else relative_parts
        )
        if normalized_parts:
            root_name = normalized_parts[0]
            if root_name in c.Infra.ROOT_WRAPPER_SEGMENTS:
                package_parts = (
                    normalized_parts[1:]
                    if root_name == c.Infra.Paths.DEFAULT_SRC_DIR
                    else normalized_parts
                )
                return ".".join(package_parts)
        absolute_parts = (
            resolved.parts[:-1]
            if resolved.name == c.Infra.Files.INIT_PY
            else resolved.parts[:-1] + (resolved.stem,)
            if resolved.suffix == c.Infra.Extensions.PYTHON
            else resolved.parts
        )
        for index, part in enumerate(absolute_parts):
            if part not in c.Infra.ROOT_WRAPPER_SEGMENTS:
                continue
            package_parts = (
                absolute_parts[index + 1 :]
                if part == c.Infra.Paths.DEFAULT_SRC_DIR
                else absolute_parts[index:]
            )
            return ".".join(package_parts)
        if resolved.name == c.Infra.Files.INIT_PY:
            top_level_parts = tuple(
                part for part in absolute_parts if part and part != resolved.anchor
            )
            match top_level_parts:
                case (_, package_name):
                    return package_name
        return (
            FlextInfraUtilitiesDocsScope.package_name(project_root)
            if project_root is not None
            else ""
        )

    @staticmethod
    def discover_python_dirs(
        project_dir: Path,
        *,
        skip_dirs: frozenset[str] | None = None,
    ) -> t.StrSequence:
        """Return top-level directories that contain at least one Python file."""
        if not project_dir.is_dir():
            return []
        effective_skip = skip_dirs if skip_dirs is not None else c.Infra.SKIP_DIRS
        return [
            subdir.name
            for subdir in sorted(project_dir.iterdir())
            if subdir.is_dir()
            and not subdir.name.startswith(".")
            and subdir.name not in effective_skip
            and any(subdir.rglob(c.Infra.Extensions.PYTHON_GLOB))
        ]

    @staticmethod
    def discover_src_package_dir(
        project_root: Path,
    ) -> t.Pair[str, Path] | None:
        """Find the primary package directory inside ``src/``."""
        package_name = FlextInfraUtilitiesDocsScope.package_name(project_root)
        if not package_name:
            return None
        package_dir = project_root / c.Infra.Paths.DEFAULT_SRC_DIR / Path(
            *package_name.split("."),
        )
        return (
            (package_name, package_dir)
            if (package_dir / c.Infra.Files.INIT_PY).is_file()
            else None
        )

    @staticmethod
    def find_all_pyproject_files(
        workspace_root: Path,
        *,
        skip_dirs: frozenset[str] | None = None,
        project_paths: Sequence[Path] | None = None,
    ) -> r[Sequence[Path]]:
        """Find all ``pyproject.toml`` files under one workspace root."""
        if not workspace_root.exists():
            return r[Sequence[Path]].ok([])
        effective_skip = skip_dirs if skip_dirs is not None else c.Infra.SKIP_DIRS
        try:
            all_files = [
                path
                for path in workspace_root.rglob(c.Infra.Files.PYPROJECT_FILENAME)
                if not any(
                    part in effective_skip
                    for part in path.relative_to(workspace_root).parts[:-1]
                )
            ]
        except OSError as exc:
            return r[Sequence[Path]].fail(f"pyproject file scan failed: {exc}")
        if project_paths is not None:
            all_files = [
                path
                for path in all_files
                if any(path.is_relative_to(project_path) for project_path in project_paths)
            ]
        return r[Sequence[Path]].ok(all_files)

    @staticmethod
    def resolve_parent_constants_mro(
        pkg_dir_or_file: Path,
        *,
        return_module: bool = False,
    ) -> tuple[str, ...]:
        """Resolve imported parent constants through Rope-backed class MRO."""
        constants_file = (
            pkg_dir_or_file
            if pkg_dir_or_file.name == c.Infra.Files.CONSTANTS_PY
            else pkg_dir_or_file / c.Infra.Files.CONSTANTS_PY
        )
        if not constants_file.is_file():
            return ()
        project_root = FlextInfraUtilitiesDiscovery.discover_project_root_from_file(
            constants_file,
        )
        if project_root is None:
            return ()
        current_module = FlextInfraUtilitiesDiscovery.discover_package_from_file(
            constants_file,
        )
        with FlextInfraUtilitiesRopeCore.open_project(project_root.parent) as rope_proj:
            resource = FlextInfraUtilitiesRopeCore.get_resource_from_path(
                rope_proj,
                constants_file,
            )
            if resource is None:
                return ()
            class_infos = FlextInfraUtilitiesRopeAnalysis.get_class_info(
                rope_proj,
                resource,
            )
            imported = FlextInfraUtilitiesRopeAnalysis.get_semantic_module_imports(
                rope_proj,
                resource,
            )
        current_root = (
            current_module.split(".", maxsplit=1)[0] if current_module else ""
        )
        resolved: list[str] = []
        for class_info in class_infos:
            if "Constants" not in class_info.name:
                continue
            for base_name in class_info.bases:
                for local_name, semantic_target in imported.items():
                    imported_name = semantic_target.rsplit(".", maxsplit=1)[-1]
                    if base_name not in {local_name, imported_name}:
                        continue
                    package_root = semantic_target.split(".", maxsplit=1)[0]
                    if package_root == current_root:
                        continue
                    target = package_root if return_module else imported_name
                    if target and target not in resolved:
                        resolved.append(target)
        return tuple(resolved)

    @staticmethod
    def contextual_runtime_alias_sources(
        *,
        project_root: Path,
        file_path: Path,
    ) -> Mapping[str, frozenset[str]]:
        """Return allowed foreign-package runtime alias sources for one file."""
        package_info = FlextInfraUtilitiesDiscovery.discover_src_package_dir(
            project_root,
        )
        if package_info is None:
            return {}
        _package_name, package_dir = package_info
        parent_packages = FlextInfraUtilitiesDiscovery.resolve_parent_constants_mro(
            package_dir,
            return_module=True,
        )
        if not parent_packages:
            return {}
        allowed_sources = frozenset(
            package.split(".", maxsplit=1)[0] for package in parent_packages
        )
        for family_dir in c.Infra.FAMILY_DIRECTORIES.values():
            if file_path.is_relative_to(package_dir / family_dir):
                return dict.fromkeys(c.Infra.MRO_FAMILIES, allowed_sources)
        return {}


__all__ = ["FlextInfraUtilitiesDiscovery"]
