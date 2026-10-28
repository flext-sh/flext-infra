"""Docs project discovery and canonical descriptor construction.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import operator
from collections.abc import MutableMapping, Sequence
from pathlib import Path

from flext_infra import c, m, p, r
from flext_infra._utilities import (
    FlextInfraUtilitiesGit,
    FlextInfraUtilitiesProjectDiscovery,
)
from flext_infra._utilities._docs import FlextInfraUtilitiesDocsScopePolicy


class FlextInfraUtilitiesDocsScopeProjects(
    FlextInfraUtilitiesDocsScopePolicy,
):
    """Discover governed projects from the authenticated workspace topology."""

    @staticmethod
    def resolve_projects(
        repository_root: Path,
        names: Sequence[str],
    ) -> p.Result[Sequence[m.Infra.ProjectInfo]]:
        """Resolve project names through repository-local topology only.

        Returns:
            The resulting ``p.Result[Sequence[m.Infra.ProjectInfo]]``.

        """
        owner = FlextInfraUtilitiesDocsScopeProjects
        discovered = owner.discover_projects(repository_root)
        if discovered.failure:
            return r[Sequence[m.Infra.ProjectInfo]].from_failure(discovered)
        projects = list(discovered.value)
        root = owner.absolute_lexical(repository_root)
        if all(project.path != root for project in projects):
            root_project = owner.project_info_for_entry(
                root,
                workspace_declared_repositories=owner.workspace_declared_repository_path_set(
                    root,
                ),
            )
            if root_project is not None:
                projects.append(root_project)
        if not names:
            return r[Sequence[m.Infra.ProjectInfo]].ok(
                sorted(projects, key=operator.attrgetter("name")),
            )
        by_name: MutableMapping[str, m.Infra.ProjectInfo] = {}
        for project in projects:
            by_name.setdefault(project.name, project)
            by_name.setdefault(project.path.name, project)
            if project.path == root:
                by_name.setdefault(".", project)
            elif project.path.is_relative_to(root):
                by_name.setdefault(project.path.relative_to(root).as_posix(), project)
        missing = [name for name in names if name not in by_name]
        if missing:
            return r[Sequence[m.Infra.ProjectInfo]].fail(
                f"unknown projects: {', '.join(sorted(missing))}",
            )
        return r[Sequence[m.Infra.ProjectInfo]].ok(
            sorted((by_name[name] for name in names), key=operator.attrgetter("name")),
        )

    @staticmethod
    def workspace_declared_repository_path_set(
        repository_root: Path,
        *,
        source_project: p.Infra.RopeProject | None = None,
    ) -> frozenset[Path]:
        """Return lexical subprojects freshly read from this root's manifest.

        Returns:
            Lexical subprojects freshly read from this root's manifest.

        Raises:
            ValueError: If ``declared.failure``.

        """
        root = FlextInfraUtilitiesDocsScopeProjects.absolute_lexical(
            repository_root,
        )
        declared = FlextInfraUtilitiesGit.git_submodule_declarations(
            root, source_project=source_project
        )
        if declared.failure:
            raise ValueError(declared.error or f"invalid workspace: {root}")
        return frozenset(root / item.path for item in declared.value)

    @staticmethod
    def project_info_for_entry(
        entry: Path,
        *,
        workspace_declared_repositories: frozenset[Path],
        source_project: p.Infra.RopeProject | None = None,
    ) -> m.Infra.ProjectInfo | None:
        """Build one canonical project descriptor for one discovered project root.

        Returns:
            The resulting ``m.Infra.ProjectInfo | None``.

        """
        entry = FlextInfraUtilitiesDocsScopeProjects.absolute_lexical(entry)
        project_state = FlextInfraUtilitiesDocsScopeProjects.project_state(
            entry, source_project=source_project
        )
        project_section = project_state.payload.get("project")
        project_name = (
            project_section.get("name") if isinstance(project_section, dict) else None
        )
        if (
            not isinstance(project_section, dict)
            or not isinstance(project_name, str)
            or not project_name.strip()
        ):
            return None
        is_workspace_declared_repository = entry in workspace_declared_repositories
        if not FlextInfraUtilitiesDocsScopeProjects.docs_scope_enabled(
            project_state.docs_meta,
        ):
            return None
        has_src = (
            FlextInfraUtilitiesDocsScopeProjects.physical_directory_exists(
                entry / c.Infra.DEFAULT_SRC_DIR,
            )
            if source_project is None
            else source_project.source_query(entry / c.Infra.DEFAULT_SRC_DIR, "isdir")
        )
        has_tests = (
            FlextInfraUtilitiesDocsScopeProjects.physical_directory_exists(
                entry / c.Infra.DIR_TESTS,
            )
            if source_project is None
            else source_project.source_query(entry / c.Infra.DIR_TESTS, "isdir")
        )
        has_deps = bool(project_section.get("dependencies"))
        if (
            not is_workspace_declared_repository
            and not has_src
            and not has_tests
            and not has_deps
        ):
            return None
        if source_project is None:
            has_manifest = FlextInfraUtilitiesDocsScopeProjects._physical_file_exists(
                entry / c.Infra.GITMODULES,
            )
        else:
            source_project.source_state(entry / c.Infra.GITMODULES, required=False)
            has_manifest = source_project.source_query(
                entry / c.Infra.GITMODULES, "isfile"
            )
        make_profile = (
            c.Infra.MakeProfile.WORKSPACE
            if has_manifest
            else c.Infra.MakeProfile.STANDALONE
        )
        return m.Infra.ProjectInfo(
            path=entry,
            name=project_state.project_name,
            stack="python/flext",
            has_tests=has_tests,
            has_src=has_src,
            project_class=(
                FlextInfraUtilitiesDocsScopeProjects.classify_project_from_meta(
                    project_state.project_name,
                    project_state.docs_meta,
                )
            ),
            package_name=project_state.package_name,
            make_profile=make_profile,
            declared_subproject=is_workspace_declared_repository,
        )

    @staticmethod
    def discover_projects(
        repository_root: Path,
        *,
        source_project: p.Infra.RopeProject | None = None,
    ) -> p.Result[Sequence[m.Infra.ProjectInfo]]:
        """Discover the root or projects declared by its own ``.gitmodules``.

        Returns:
            The resulting ``p.Result[Sequence[m.Infra.ProjectInfo]]``.

        """
        owner = FlextInfraUtilitiesDocsScopeProjects
        if source_project is None:
            roots = owner.docs_repository_roots(repository_root)
            if roots.failure:
                return r[Sequence[m.Infra.ProjectInfo]].from_failure(roots)
            repository_root = roots.value[0]
        else:
            repository_root = owner.absolute_lexical(repository_root)
            if not source_project.source_query(repository_root, "isdir"):
                return r[Sequence[m.Infra.ProjectInfo]].fail(
                    f"docs repository root is missing from source view: {repository_root}"
                )
        excluded = owner.excluded_roots(repository_root, source_project=source_project)
        workspace_declared_repositories = owner.workspace_declared_repository_path_set(
            repository_root,
            source_project=source_project,
        )
        project_roots = FlextInfraUtilitiesProjectDiscovery.discover_project_candidates(
            repository_root,
            source_project=source_project,
        )
        root_project: m.Infra.ProjectInfo | None = None
        projects: list[m.Infra.ProjectInfo] = []
        for project_root in project_roots:
            if project_root.name == "cmd" or project_root.name in excluded:
                continue
            has_root_src = (
                owner.physical_directory_exists(project_root / c.Infra.DEFAULT_SRC_DIR)
                if source_project is None
                else source_project.source_query(
                    project_root / c.Infra.DEFAULT_SRC_DIR, "isdir"
                )
            )
            if project_root == repository_root and not has_root_src:
                continue
            project_info = owner.project_info_for_entry(
                project_root,
                workspace_declared_repositories=workspace_declared_repositories,
                source_project=source_project,
            )
            if project_info is None:
                continue
            if project_root == repository_root:
                root_project = project_info
                continue
            projects.append(project_info)
        if not projects and root_project is not None:
            return r[Sequence[m.Infra.ProjectInfo]].ok([root_project])
        return r[Sequence[m.Infra.ProjectInfo]].ok(projects)


__all__: list[str] = ["FlextInfraUtilitiesDocsScopeProjects"]
