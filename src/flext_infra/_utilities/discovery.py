"""Project discovery utilities for package and workspace resolution.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import MutableMapping
from importlib.machinery import PathFinder
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

from flext_infra import c, config, r, t
from flext_infra._utilities import (
    FlextInfraUtilitiesNamespaceConfig,
    FlextInfraUtilitiesProjectDiscovery,
    FlextInfraUtilitiesPyproject,
    FlextInfraUtilitiesRopeAnalysis,
)

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraUtilitiesDiscovery(
    FlextInfraUtilitiesNamespaceConfig,
    FlextInfraUtilitiesProjectDiscovery,
    FlextInfraUtilitiesPyproject,
    FlextInfraUtilitiesRopeAnalysis,
):
    """Canonical discovery helpers for path, package, and Rope-backed scans."""

    _PARENT_CONSTANTS_FLEXT_CACHE: ClassVar[
        MutableMapping[t.Pair[str, bool], t.StrSequence]
    ] = {}

    @staticmethod
    def _discover_project_root_from_path(
        file_path: str,
        *,
        source_project: p.Infra.RopeProject | None = None,
    ) -> str:
        """Discover the enclosing project root through the current authority.

        Returns:
            The resulting ``str``.

        """
        resolved = Path(file_path).resolve()
        candidate = (
            resolved.parent
            if resolved.suffix in {c.Infra.EXT_PYTHON, c.Infra.EXT_PYTHON_STUB}
            # A project manifest belongs to the root it declares, never to a
            # parent discovered by walking above it.
            or resolved.name == c.PYPROJECT_FILENAME
            else resolved
        )
        wrapper_root: Path | None = None
        for current in (candidate, *candidate.parents):
            if current.name == c.Infra.DEFAULT_SRC_DIR:
                wrapper_root = current.parent
                continue
            if current.name in c.Infra.ROOT_WRAPPER_SEGMENTS:
                wrapper_root = current.parent
                continue
            if (
                (current / c.Infra.DEFAULT_SRC_DIR).is_dir()
                if source_project is None
                else source_project.source_query(
                    current / c.Infra.DEFAULT_SRC_DIR, "isdir"
                )
            ):
                relative = candidate.relative_to(current)
                if (
                    not relative.parts
                    or relative.parts[0] in c.Infra.ROOT_WRAPPER_SEGMENTS
                ):
                    return str(current)
        return str(wrapper_root) if wrapper_root is not None else ""

    @staticmethod
    def _relative_path_parts(resolved: Path, project_root: Path | None) -> t.StrTuple:
        """Return path parts relative to project root when possible.

        Returns:
            Path parts relative to project root when possible.

        """
        if project_root is None or not resolved.is_relative_to(project_root):
            return ()
        return resolved.relative_to(project_root).parts

    @staticmethod
    def _normalized_python_parts(resolved: Path, path_parts: t.StrTuple) -> t.StrTuple:
        """Normalize filesystem parts into package/module parts.

        Returns:
            The resulting ``t.StrTuple``.

        """
        if path_parts and path_parts[-1] == c.Infra.INIT_PY:
            return path_parts[:-1]
        if resolved.suffix == c.Infra.EXT_PYTHON and path_parts:
            return (*path_parts[:-1], resolved.stem)
        return path_parts

    @staticmethod
    def _package_name_from_wrapper_parts(path_parts: t.StrSequence) -> str:
        """Return package name when path parts start with a known wrapper.

        Returns:
            Package name when path parts start with a known wrapper.

        """
        if not path_parts:
            return ""
        root_name = path_parts[0]
        if root_name not in c.Infra.ROOT_WRAPPER_SEGMENTS:
            return ""
        package_parts = (
            path_parts[1:] if root_name == c.Infra.DEFAULT_SRC_DIR else path_parts
        )
        return ".".join(package_parts)

    @staticmethod
    def _package_name_from_src_dir(resolved: Path) -> str:
        """Return the package name when the path is a project root with src/<pkg>.

        Returns:
            The package name when the path is a project root with src/<pkg>.

        """
        src_dir = resolved / c.Infra.DEFAULT_SRC_DIR
        if not src_dir.is_dir():
            return ""
        for child in sorted(src_dir.iterdir()):
            if child.is_dir() and (child / c.Infra.INIT_PY).is_file():
                child_path: Path = child
                return child_path.name
        return ""

    @staticmethod
    def pytest_test_module(file_path: Path) -> bool:
        """Return whether a file is a pytest test module, not a production module.

        Returns:
            Whether a file is a pytest test module, not a production module.

        """
        if c.Infra.DIR_TESTS not in file_path.parts:
            return False
        file_name = file_path.name
        return file_name.startswith(
            c.Infra.NAMESPACE_PYTEST_MODULE_PREFIX,
        ) or file_name.endswith(tuple(c.Infra.NAMESPACE_PYTEST_MODULE_SUFFIXES))

    @staticmethod
    def project_root(
        file_path: Path,
        *,
        source_project: p.Infra.RopeProject | None = None,
    ) -> Path | None:
        """Discover the enclosing project root for one file or directory path.

        Returns:
            The resulting ``Path | None``.

        """
        project_root = FlextInfraUtilitiesDiscovery._discover_project_root_from_path(
            str(file_path),
            source_project=source_project,
        )
        return Path(project_root) if project_root else None

    @classmethod
    def _discover_package_from_path(cls, file_path: str) -> str:
        """Discover the package path cached by file path.

        Returns:
            The resulting ``str``.

        """
        resolved = Path(file_path).resolve()
        project_root_value = cls._discover_project_root_from_path(file_path)
        project_root = Path(project_root_value) if project_root_value else None
        normalized_parts = cls._normalized_python_parts(
            resolved,
            cls._relative_path_parts(resolved, project_root),
        )
        package_name = cls._package_name_from_wrapper_parts(normalized_parts)
        if package_name:
            return package_name
        package_name = cls._package_name_from_src_dir(resolved)
        if package_name:
            return package_name
        absolute_parts = cls._normalized_python_parts(resolved, resolved.parts)
        for index, part in enumerate(absolute_parts):
            package_name = cls._package_name_from_wrapper_parts(absolute_parts[index:])
            if package_name and part in c.Infra.ROOT_WRAPPER_SEGMENTS:
                return package_name
        if resolved.name == c.Infra.INIT_PY:
            top_level_parts = tuple(
                part for part in absolute_parts if part and part != resolved.anchor
            )
            match top_level_parts:
                case (_, package_name):
                    resolved_package: str = package_name
                    return resolved_package
                case _:
                    pass
        if project_root is None:
            return ""

        return cls.project_package_name(project_root)

    @classmethod
    def package_name(cls, file_path: Path) -> str:
        """Discover the module or package path for one Python file or package directory.

        Returns:
            The resulting ``str``.

        """
        return cls._discover_package_from_path(str(file_path))

    @staticmethod
    def declared_package_dir(
        package_name: str,
        *,
        search_paths: t.StrSequence | None = None,
    ) -> Path | None:
        """Elect the physical import path without trusting cached module origins.

        Returns:
            The unique package directory, or None for an absent name/plain module.

        Raises:
            ValueError: If the declared package has ambiguous physical origins.

        """
        locations = search_paths
        components = package_name.split(".")
        for index in range(len(components)):
            spec = PathFinder.find_spec(".".join(components[: index + 1]), locations)
            if spec is None or not spec.submodule_search_locations:
                return None
            locations = spec.submodule_search_locations
        if locations is None or len(locations) != 1:
            msg = f"declared package has ambiguous physical origins: {package_name}"
            raise ValueError(msg)
        return Path(locations[0])

    @classmethod
    def rope_repository_root(cls, repository_root: Path) -> Path:
        """Resolve a local project without expanding it to an ancestor workspace.

        Returns:
            The resulting ``Path``.

        """
        resolved_root = repository_root.resolve()
        execution_dir = (
            resolved_root if resolved_root.is_dir() else resolved_root.parent
        )
        discovered_root = cls.project_root(resolved_root)
        project_root = discovered_root
        if (
            resolved_root.is_dir()
            and not (execution_dir / c.PYPROJECT_FILENAME).is_file()
        ):
            relative_parts = (
                resolved_root.relative_to(discovered_root).parts
                if discovered_root is not None
                and resolved_root.is_relative_to(discovered_root)
                else ()
            )
            if (
                not relative_parts
                or relative_parts[0] not in c.Infra.ROOT_WRAPPER_SEGMENTS
            ):
                project_root = resolved_root
        if project_root is not None and (
            (project_root / c.PYPROJECT_FILENAME).is_file()
            or (project_root / c.Infra.GIT_DIR).exists()
        ):
            return project_root
        return resolved_root

    @classmethod
    def find_all_pyproject_files(
        cls,
        repository_root: Path,
        *,
        skip_dirs: frozenset[str] | None = None,
        project_paths: t.SequenceOf[Path] | None = None,
    ) -> p.Result[t.SequenceOf[Path]]:
        """Find all managed ``pyproject.toml`` files for one workspace root.

        Returns:
            The resulting ``p.Result[t.SequenceOf[Path]]``.

        """
        if not repository_root.exists() or not repository_root.is_dir():
            return r[t.SequenceOf[Path]].ok([])
        effective_skip = (
            skip_dirs
            if skip_dirs is not None
            else frozenset(config.Infra.codegen.deps_discovery_excluded_dirs)
        )
        # Explicit project paths are a hard write-scope boundary. Without one,
        # discovery is strictly local to the repository supplied by the caller.
        scan_roots = (
            sorted({project_path.resolve() for project_path in project_paths})
            if project_paths is not None
            else [repository_root.resolve()]
        )
        all_files: list[Path] = []
        for scan_root in scan_roots:
            if scan_root.is_file():
                if scan_root.name != c.PYPROJECT_FILENAME:
                    return r[t.SequenceOf[Path]].fail(
                        f"explicit project file must be "
                        f"{c.PYPROJECT_FILENAME}: {scan_root}",
                    )
                all_files.append(scan_root)
                continue
            if not scan_root.is_dir():
                return r[t.SequenceOf[Path]].fail(
                    f"explicit project path is not accessible: {scan_root}",
                )
            try:
                all_files.extend(
                    sorted(
                        path
                        for path in scan_root.rglob(c.PYPROJECT_FILENAME)
                        if not any(
                            part.startswith(".") or part in effective_skip
                            for part in path.relative_to(scan_root).parts[:-1]
                        )
                    ),
                )
            except OSError as exc:
                return r[t.SequenceOf[Path]].fail_op("pyproject file scan", exc)
        if project_paths is not None:
            all_files = [
                path
                for path in all_files
                if any(
                    path.is_relative_to(project_path) for project_path in project_paths
                )
            ]
        return r[t.SequenceOf[Path]].ok(all_files)


__all__: list[str] = ["FlextInfraUtilitiesDiscovery"]
