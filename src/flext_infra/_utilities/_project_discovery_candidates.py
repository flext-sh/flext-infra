"""Project candidate discovery for flext-infra utilities.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from os.path import abspath
from pathlib import Path

from flext_infra import c, m, p, t
from flext_infra._utilities import (
    FlextInfraUtilitiesGit,
    FlextInfraUtilitiesProjectDiscoveryShapeMixin,
)


class FlextInfraUtilitiesProjectDiscoveryCandidatesMixin(
    FlextInfraUtilitiesProjectDiscoveryShapeMixin,
):
    """Private candidate enumeration for workspace project discovery."""

    @classmethod
    def discover_project_candidates(
        cls,
        repository_root: Path,
        *,
        scan_dirs: frozenset[str] | None = None,
        declarations: t.VariadicTuple[m.Infra.GitSubmoduleDeclaration] | None = None,
        source_project: p.Infra.RopeProject | None = None,
    ) -> t.SequenceOf[Path]:
        """Elect candidates and exclusions from one current Git declaration read.

        Returns:
            The root and participating projects declared by its own ``.gitmodules``.

        Raises:
            ValueError: If ``declared_paths.failure``.

        """
        roots: t.MutableSequenceOf[Path] = []
        effective_scan_dirs = scan_dirs or frozenset()
        if declarations is None:
            declared = FlextInfraUtilitiesGit.git_submodule_declarations(
                repository_root,
                source_project=source_project,
            )
            if declared.failure:
                raise ValueError(declared.error or "invalid .gitmodules")
            declarations = declared.value
        nonparticipants = cls.repository_nonparticipant_paths(
            repository_root,
            declarations=declarations,
        )
        configured_projects = tuple(item.path.as_posix() for item in declarations)
        configured_project_set = frozenset(configured_projects)
        resolved_repository_root = repository_root.resolve()
        configured_entries: set[Path] = set()
        for project in configured_projects:
            entry = (
                (resolved_repository_root / project).resolve() if source_project is None
                else Path(abspath(resolved_repository_root / project))
            )
            if (
                entry.is_dir()
                if source_project is None
                else source_project.source_query(entry, "isdir")
            ) and entry.is_relative_to(resolved_repository_root):
                configured_entries.add(entry)
        if cls._looks_like_project(
            resolved_repository_root,
            effective_scan_dirs=effective_scan_dirs,
            configured_project_set=configured_project_set,
            source_project=source_project,
        ):
            roots.append(resolved_repository_root)
        if configured_projects:
            candidate_entries: t.SequenceOf[Path] = sorted(
                configured_entries,
                key=Path.as_posix,
            )
            roots.extend([
                entry.resolve()
                for entry in candidate_entries
                if (
                    entry.is_dir()
                    if source_project is None
                    else source_project.source_query(entry, "isdir")
                )
                and not entry.name.startswith(".")
                and cls._looks_like_project(
                    entry.resolve(),
                    effective_scan_dirs=effective_scan_dirs,
                    configured_project_set=configured_project_set,
                    source_project=source_project,
                )
            ])
        if not roots and (
            (resolved_repository_root / c.Infra.DEFAULT_SRC_DIR).is_dir()
            if source_project is None
            else source_project.source_query(
                resolved_repository_root / c.Infra.DEFAULT_SRC_DIR, "isdir"
            )
        ):
            roots.append(resolved_repository_root)
        if not nonparticipants:
            return roots
        return tuple(
            root
            for root in roots
            if not cls._is_nonparticipant(
                root, resolved_repository_root, nonparticipants
            )
        )

    @classmethod
    def repository_nonparticipant_paths(
        cls,
        repository_root: Path,
        *,
        declarations: t.VariadicTuple[m.Infra.GitSubmoduleDeclaration] | None = None,
        source_project: p.Infra.RopeProject | None = None,
    ) -> frozenset[str]:
        """Derive exclusions from this invocation's Git declarations, never a cache.

        Returns:
            Every explicitly unmanaged Git submodule path.

        """
        if declarations is None:
            declarations = FlextInfraUtilitiesGit.git_submodule_declarations(
                repository_root,
                source_project=source_project,
            ).unwrap()
        return frozenset(
            declaration.path.as_posix()
            for declaration in declarations
            if declaration.managed is False
        )


__all__: list[str] = ["FlextInfraUtilitiesProjectDiscoveryCandidatesMixin"]
