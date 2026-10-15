"""Shared Rope lifecycle helpers.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

from flext_infra import c, config, t
from flext_infra._utilities import (
    FlextInfraUtilitiesGit,
    FlextInfraUtilitiesProjectDiscovery,
    FlextInfraUtilitiesRopeCorePyModuleMixin,
    FlextInfraUtilitiesRopeCoreResourcesMixin,
    FlextInfraUtilitiesRopeRuntime,
)


class FlextInfraUtilitiesRopeCore(
    FlextInfraUtilitiesRopeCoreResourcesMixin,
    FlextInfraUtilitiesRopeCorePyModuleMixin,
):
    """Core Rope lifecycle helpers."""

    @staticmethod
    def init_rope_project(repository_root: Path) -> t.Infra.RopeProject:
        """Create a project-scoped Rope session with no disk artifacts.

        Returns:
            The resulting ``t.Infra.RopeProject``.

        """
        resolved_root = repository_root.resolve()
        return FlextInfraUtilitiesRopeCore._new_project(
            resolved_root,
            project_roots=(resolved_root,),
        )

    @staticmethod
    def init_rope_workspace(repository_root: Path) -> t.Infra.RopeProject:
        """Create a Rope session spanning every project below a workspace root.

        Returns:
            The resulting ``t.Infra.RopeProject``.

        """
        resolved_root = repository_root.resolve()
        project_roots = tuple(
            project_root
            for project_root in (
                FlextInfraUtilitiesProjectDiscovery.discover_rope_project_roots
            )(
                resolved_root,
            )
            if project_root.resolve().is_relative_to(resolved_root)
        )
        return FlextInfraUtilitiesRopeCore._new_project(
            resolved_root,
            project_roots=project_roots,
        )

    @staticmethod
    def _new_project(
        resolved_root: Path,
        *,
        project_roots: t.SequenceOf[Path],
    ) -> t.Infra.RopeProject:
        """Create one Rope project from validated source roots.

        Returns:
            The resulting ``t.Infra.RopeProject``.

        """
        source_folders = sorted(
            {
                str(scan_path.relative_to(resolved_root))
                for project_root in project_roots
                for dir_name in config.Infra.source_scan.roots
                if (scan_path := project_root / dir_name).is_dir()
                and scan_path.resolve().is_relative_to(resolved_root)
            }
            | {
                ""
                if project_root == resolved_root
                else str(project_root.relative_to(resolved_root))
                for project_root in project_roots
                if project_root.is_dir()
                and project_root.resolve().is_relative_to(resolved_root)
            },
        )
        return FlextInfraUtilitiesRopeRuntime.new_project(
            str(resolved_root),
            ropefolder="",
            save_objectdb=False,
            filter_lists=(
                sorted(config.Infra.codegen.source_scan_ignored),
                source_folders,
                sorted(
                    name
                    for name, module in tuple(sys.modules.items())
                    if name.partition(".")[0] in sys.stdlib_module_names
                    and module.__spec__ is not None
                    and module.__spec__.origin == "frozen"
                ),
            ),
        )

    @staticmethod
    def import_project_roots(source_root: Path) -> t.VariadicTuple[Path]:
        """Resolve the declared source graph containing one import consumer.

        Returns:
            The containing workspace and its members, or the standalone root.

        Raises:
            ValueError: If the containing workspace declaration is invalid.
        """
        resolved = source_root.resolve()
        for parent in (resolved, *resolved.parents):
            if not (parent / c.Infra.GITMODULES).exists():
                continue
            declarations = FlextInfraUtilitiesGit.git_submodule_declarations(parent)
            if declarations.failure:
                raise ValueError(declarations.error or "invalid .gitmodules")
            members = tuple(parent / item.path for item in declarations.value)
            if members and (
                resolved == parent
                or any(resolved.is_relative_to(member.resolve()) for member in members)
            ):
                return (parent, *members)
        standalone = FlextInfraUtilitiesProjectDiscovery.nearest_project_root(
            Path(resolved.anchor), resolved
        )
        return (standalone if standalone is not None else resolved,)

    @staticmethod
    @contextmanager
    def open_import_project(source_root: Path) -> Generator[t.Infra.RopeProject]:
        """Resolve imports against the containing declared workspace, if attached.

        Invalid workspace declarations propagate from the declaration reader.

        Yields:
            A source-scoped project or its declared workspace import graph.
        """
        roots = FlextInfraUtilitiesRopeCore.import_project_roots(source_root)
        with FlextInfraUtilitiesRopeCore.open_project(
            roots[0],
            project_roots=roots,
        ) as project:
            yield project

    @staticmethod
    @contextmanager
    def open_project(
        repository_root: Path,
        *,
        project_roots: t.SequenceOf[Path] | None = None,
    ) -> Generator[t.Infra.RopeProject]:
        """Open one Rope project and always close it through the core boundary.

        Yields:
            Each ``t.Infra.RopeProject``.

        Raises:
            ValueError: If Rope project roots must be nonempty and remain inside the
                declared workspace.

        """
        resolved = repository_root.resolve()
        roots = (
            (resolved,)
            if project_roots is None
            else tuple(path.resolve() for path in project_roots)
        )
        if not roots or any(not path.is_relative_to(resolved) for path in roots):
            msg = (
                "Rope project roots must be nonempty and remain "
                "inside the declared workspace"
            )
            raise ValueError(msg)
        rope_project = FlextInfraUtilitiesRopeCore._new_project(
            resolved,
            project_roots=roots,
        )
        try:
            yield rope_project
        finally:
            rope_project.close()


__all__: list[str] = ["FlextInfraUtilitiesRopeCore"]
