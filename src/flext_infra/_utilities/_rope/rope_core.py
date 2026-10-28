"""Shared Rope lifecycle helpers.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

from flext_infra import c, config, t
from flext_infra._utilities import (
    FlextInfraUtilitiesGit,
    FlextInfraUtilitiesProjectDiscovery,
    FlextInfraUtilitiesProjectManagedArtifacts,
    FlextInfraUtilitiesWorkspaceInventory,
)
from flext_infra._utilities._rope.pymodule import (
    FlextInfraUtilitiesRopeCorePyModuleMixin,
)
from flext_infra._utilities._rope.rope_core_resources import (
    FlextInfraUtilitiesRopeCoreResourcesMixin,
)
from flext_infra._utilities._rope.rope_runtime import FlextInfraUtilitiesRopeRuntime


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
        consumer_root: Path | None = None,
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
                if consumer_root is None or project_root == consumer_root
                if (scan_path := project_root / dir_name).is_dir()
                and scan_path.resolve().is_relative_to(resolved_root)
            }
            | {
                ""
                if project_root == resolved_root
                else str(project_root.relative_to(resolved_root))
                for project_root in project_roots
                if consumer_root is None or project_root == consumer_root
                if project_root.is_dir()
                and project_root.resolve().is_relative_to(resolved_root)
            },
        )
        project = FlextInfraUtilitiesRopeRuntime.new_project(
            str(resolved_root),
            ropefolder="",
            save_objectdb=False,
            filter_lists=(
                sorted({
                    *config.Infra.codegen.source_scan_ignored,
                    *(
                        owner.relative_to(resolved_root).as_posix()
                        for owner in project_roots
                        if consumer_root is not None
                        and owner != consumer_root
                        and owner.is_relative_to(consumer_root)
                    ),
                }),
                source_folders,
            ),
        )
        for owner in project_roots:
            if consumer_root is not None and owner != consumer_root:
                source = owner / c.Infra.DEFAULT_SRC_DIR
                project.get_prefs().add(
                    "python_path",
                    str(source if source.is_dir() else owner),
                )
        return project

    @staticmethod
    def import_project_roots(
        source_root: Path,
        *,
        include_consumers: bool = False,
    ) -> t.VariadicTuple[Path]:
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
                roots = (parent, *members)
                break
        else:
            standalone = FlextInfraUtilitiesProjectDiscovery.nearest_project_root(
                Path(resolved.anchor), resolved
            )
            roots = (standalone if standalone is not None else resolved,)
        if not include_consumers:
            return roots
        inputs = FlextInfraUtilitiesProjectManagedArtifacts.load_codegen_inputs(
            roots[0]
        ).unwrap()
        consumers = FlextInfraUtilitiesWorkspaceInventory.discover_external_consumers(
            roots[0],
            inputs,
        ).unwrap()
        discovery = FlextInfraUtilitiesProjectDiscovery
        return tuple(
            dict.fromkeys(
                project
                for root in (*roots, *(consumer.root for consumer in consumers))
                for project in discovery.discover_rope_project_roots(root)
            )
        )

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
        consumer_root: Path | None = None,
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
            consumer_root=consumer_root,
        )
        try:
            yield rope_project
        finally:
            rope_project.close()


__all__: list[str] = ["FlextInfraUtilitiesRopeCore"]
