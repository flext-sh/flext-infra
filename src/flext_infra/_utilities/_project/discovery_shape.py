"""Project shape helpers for flext-infra discovery utilities.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from contextlib import closing, nullcontext
from pathlib import Path

from flext_infra import c, config, m, p
from flext_infra._utilities import FlextInfraUtilitiesDependencies
from flext_infra._utilities._git import (
    FlextInfraUtilitiesGitSemanticIdentity,
    FlextInfraUtilitiesGitWorktreeDiscovery,
    FlextInfraUtilitiesGitWorktreeRoots,
)
from flext_infra._utilities._pyproject import FlextInfraUtilitiesPyprojectConform
from flext_infra._utilities._rope import FlextInfraUtilitiesRopeRuntime


class FlextInfraUtilitiesProjectDiscoveryShape:
    """Project-shape predicates and manifest-owner lookup for project discovery."""

    @classmethod
    def detected_project_kind(
        cls,
        repository_root: Path,
        *,
        source_project: p.Infra.RopeProject | None = None,
    ) -> c.Infra.ProjectKind:
        """Derive governance from native dependencies and managed composition.

        Returns:
            FLEXT governance for a consuming project or composed workspace;
            ordinary internal governance when neither fact is present.

        """
        payload = FlextInfraUtilitiesPyprojectConform.pyproject_payload(
            repository_root / c.PYPROJECT_FILENAME, source_project=source_project
        )
        dependency_owner = FlextInfraUtilitiesDependencies
        dependencies = dependency_owner.declared_dependency_names_from_payload(payload)
        if any(name.startswith(c.Infra.PKG_PREFIX_HYPHEN) for name in dependencies):
            return c.Infra.ProjectKind.INTERNAL_FLEXT
        declarations = FlextInfraUtilitiesGitWorktreeRoots.git_submodule_declarations(
            repository_root, source_project=source_project
        ).unwrap()
        if any(
            declaration.managed is True
            or (
                declaration.managed is not False
                and (
                    (repository_root / declaration.path).is_dir()
                    if source_project is None
                    else source_project.source_query(
                        repository_root / declaration.path, "isdir"
                    )
                )
                and cls.detected_project_kind(
                    repository_root / declaration.path, source_project=source_project
                )
                is c.Infra.ProjectKind.INTERNAL_FLEXT
            )
            for declaration in declarations
        ) or cls._uses_flext_imports(repository_root, source_project):
            return c.Infra.ProjectKind.INTERNAL_FLEXT
        if (repository_root / c.GIT_DIR_NAME).exists():
            identity = FlextInfraUtilitiesGitSemanticIdentity.git_identity(
                m.Infra.GitRepoRequest(repo_root=repository_root)
            ).unwrap()
            if identity.upstream_remote and (
                FlextInfraUtilitiesGitWorktreeDiscovery.git_remote_identity(
                    identity.upstream_remote
                )
                != FlextInfraUtilitiesGitWorktreeDiscovery.git_remote_identity(
                    identity.origin_remote or ""
                )
            ):
                return c.Infra.ProjectKind.THIRD_PARTY_FORK
        return c.Infra.ProjectKind.INTERNAL

    @staticmethod
    def _uses_flext_imports(
        root: Path, source_project: p.Infra.RopeProject | None
    ) -> bool:
        """Read imports from the native source project's own inventory.

        Returns:
            Whether a source module imports a FLEXT package.

        """
        native = FlextInfraUtilitiesRopeRuntime
        context = (
            nullcontext(source_project)
            if source_project is not None
            else closing(
                native.new_project(
                    str(root),
                    ropefolder="",
                    save_objectdb=False,
                    filter_lists=(config.Infra.codegen.source_scan_ignored, ("",)),
                )
            )
        )
        with context as project:
            for resource in project.get_python_files():
                if not Path(resource.real_path).is_relative_to(root):
                    continue
                parsed = native.require_parsed_module(project.get_pymodule(resource))
                imports = native.module_imports_for_pymodule(project, parsed)
                for statement in imports.imports:
                    info = statement.import_info
                    names = (
                        (info.module_name,)
                        if isinstance(info, p.Infra.RopeFromImport)
                        else tuple(name for name, _alias in info.names_and_aliases)
                    )
                    if any(
                        name.startswith(c.Infra.PKG_PREFIX_UNDERSCORE) for name in names
                    ):
                        return True
        return False

    @classmethod
    def _is_nonparticipant(
        cls,
        candidate: Path,
        repository_root: Path,
        nonparticipants: frozenset[str],
    ) -> bool:
        """Return whether one candidate lies under a declared non-participant.

        Returns:
            Whether the candidate is excluded by the current declaration.

        """
        resolved = (
            candidate.absolute() if candidate.suffix == ".pyi" else candidate.resolve()
        )
        root = repository_root.resolve()
        if not resolved.is_relative_to(root):
            return False
        posix = resolved.relative_to(root).as_posix()
        if posix in {".", ""}:
            return False
        return any(
            posix == declared or posix.startswith(f"{declared}/")
            for declared in nonparticipants
        )

    @staticmethod
    def _looks_like_project(
        path: Path,
        *,
        effective_scan_dirs: frozenset[str],
        configured_project_set: frozenset[str],
        source_project: p.Infra.RopeProject | None = None,
    ) -> bool:
        """Return whether one path matches the canonical governed project shape.

        Returns:
            Whether one path matches the canonical governed project shape.

        """
        if not (
            path.is_dir()
            if source_project is None
            else source_project.source_query(path, "isdir")
        ):
            return False
        pyproject_path = path / c.PYPROJECT_FILENAME
        if (
            pyproject_path.exists()
            if source_project is None
            else source_project.source_query(pyproject_path, "exists")
        ) and (
            path.name in configured_project_set
            or (
                (path / c.Infra.MAKEFILE_FILENAME).exists()
                if source_project is None
                else source_project.source_query(
                    path / c.Infra.MAKEFILE_FILENAME, "exists"
                )
            )
        ):
            return True
        payload = FlextInfraUtilitiesPyprojectConform.pyproject_payload(
            pyproject_path, source_project=source_project
        )
        if not payload:
            return False
        dependency_names: set[str] = set(
            FlextInfraUtilitiesDependencies.declared_dependency_names_from_payload(
                payload,
            ),
        )
        if c.Infra.PKG_CORE in dependency_names:
            return True
        if effective_scan_dirs:
            return any(
                (path / name).is_dir()
                if source_project is None
                else source_project.source_query(path / name, "isdir")
                for name in effective_scan_dirs
            )
        return True

    @staticmethod
    def nearest_project_root(
        repository_root: Path,
        path: Path,
        *,
        source_project: p.Infra.RopeProject | None = None,
    ) -> Path | None:
        """Find the nearest manifest owner inside one governed repository.

        Returns:
            The resulting ``Path | None``.

        """
        boundary = repository_root.resolve()
        candidate = path.resolve()
        if source_project is not None and source_project.source_query(
            candidate, "isfile"
        ):
            candidate = candidate.parent
        if not candidate.is_relative_to(boundary):
            return None
        for parent in (candidate, *candidate.parents):
            is_directory = (
                parent.is_dir()
                if source_project is None
                else source_project.source_query(parent, "isdir")
            )
            if is_directory and (
                (parent / c.PYPROJECT_FILENAME).is_file()
                if source_project is None
                else source_project.source_query(
                    parent / c.PYPROJECT_FILENAME, "isfile"
                )
            ):
                return parent
            if parent == boundary:
                return None
        return None


__all__: list[str] = ["FlextInfraUtilitiesProjectDiscoveryShape"]
