"""Shared Rope lifecycle helpers.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Callable, Generator, Sequence
from contextlib import closing, contextmanager
from pathlib import Path

from rope.base.exceptions import RopeError

from flext_infra import c, config, m, p, r, t
from flext_infra._utilities import (
    FlextInfraUtilitiesGit,
    FlextInfraUtilitiesProjectDiscovery,
    FlextInfraUtilitiesProjectManagedArtifacts,
    FlextInfraUtilitiesWorkspaceInventory,
)
from flext_infra._utilities._rope import (
    FlextInfraRopeProject,
    FlextInfraUtilitiesRopeCorePyModule,
    FlextInfraUtilitiesRopeCoreResources,
    FlextInfraUtilitiesRopeRuntime,
)


class FlextInfraUtilitiesRopeCore(
    FlextInfraUtilitiesRopeCoreResources,
    FlextInfraUtilitiesRopeCorePyModule,
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
        project_roots: Sequence[Path],
        consumer_root: Path | None = None,
        fscommands: p.Infra.RopeProjectFiles | None = None,
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
            fscommands=fscommands,
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
    ) -> tuple[Path, ...]:
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
    def binding_projects(
        producer: p.Infra.RopeProject,
        projects: Sequence[p.Infra.RopeProject],
        declaration: Path,
    ) -> tuple[p.Infra.RopeProject, ...]:
        """Elect the repository projects that can bind one native declaration.

        ``src/`` holds a repository's public namespaces; every other child of
        the repository root is an internal tier whose dotted names denote that
        repository's own modules only. Another repository resolves the same
        dotted name inside its own tier, so it never binds this declaration.

        Returns:
            The producer first, followed by every other project when public.

        """
        public = declaration.resolve().is_relative_to(
            Path(producer.root.real_path) / c.Infra.DEFAULT_SRC_DIR
        )
        return (
            producer,
            *(project for project in projects if public and project is not producer),
        )

    @staticmethod
    @contextmanager
    def workspace_overlay_project(
        root: Path,
        project_roots: tuple[Path, ...],
        *,
        declared_files: tuple[p.Infra.CodegenFilePlan, ...] = (),
        additional_source_folders: tuple[str, ...] = (),
    ) -> Generator[p.Infra.RopeProject]:
        """Open the native source engine project that reads planned sources first.

        The live project elects the source folders, extension modules and
        Python path once; the returned project reads the declared plans before
        the live tree through the same native resolver.

        Yields:
            The overlaid native project.

        Raises:
            ValueError: If a declared project root lies outside ``root``.

        """
        root = root.resolve()
        if any(not project.is_relative_to(root) for project in project_roots):
            msg = "Rope declared project root is outside the original authority"
            raise ValueError(msg)
        files = FlextInfraRopeProject.OverlayFiles((), source_roots=(root,))
        with FlextInfraUtilitiesRopeCore.open_project(
            next(path for path in (root, *root.parents) if path.is_dir()),
            project_roots=project_roots or None,
            fscommands=files,
        ) as live:
            election = m.Infra.RopeProjectElection(
                preferred_import_style=live.get_prefs().imports.preferred_import_style,
                ignored_resources=tuple(
                    sorted(config.Infra.codegen.source_scan_ignored)
                ),
                source_folders=tuple(
                    sorted(folder.path for folder in live.get_source_folders())
                ),
                extension_modules=(
                    FlextInfraUtilitiesRopeRuntime.extension_module_names(live)
                ),
                python_path_folders=tuple(
                    folder.real_path
                    for folder in live.get_python_path_folders()
                    if folder.is_folder()
                ),
            )
            with (
                closing(
                    FlextInfraRopeProject.from_atomic_reads(
                        live,
                        election=election,
                        declared_files=declared_files,
                        additional_source_folders=additional_source_folders,
                    )
                ) as project,
                project.frozen_layout(),
            ):
                yield project

    @staticmethod
    @contextmanager
    def open_import_project(source_root: Path) -> Generator[t.Infra.RopeProject]:
        """Open the native project of the repository that owns ``source_root``.

        One native project per repository (ADR-028 Decision 17): the project is
        rooted at the owning repository, and every other repository of the
        declared graph resolves through Rope's native ``python_path`` as a
        provider. A workspace member, a separate workspace and a standalone
        repository are opened the same way. Invalid workspace declarations
        propagate from the declaration reader.

        Yields:
            The owning repository's native project.

        """
        resolved = source_root.resolve()
        roots = FlextInfraUtilitiesRopeCore.import_project_roots(resolved)
        owner = max(
            (
                root.resolve()
                for root in roots
                if resolved.is_relative_to(root.resolve())
            ),
            key=lambda root: len(root.parts),
        )
        with FlextInfraUtilitiesRopeCore.open_project(owner) as project:
            for provider in roots:
                provider_root = provider.resolve()
                if provider_root == owner or owner.is_relative_to(provider_root):
                    continue
                source = provider_root / c.Infra.DEFAULT_SRC_DIR
                project.get_prefs().add(
                    "python_path",
                    str(source if source.is_dir() else provider_root),
                )
            yield project

    @staticmethod
    @contextmanager
    def open_project(
        repository_root: Path,
        *,
        project_roots: Sequence[Path] | None = None,
        consumer_root: Path | None = None,
        fscommands: p.Infra.RopeProjectFiles | None = None,
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
            fscommands=fscommands,
        )
        try:
            yield rope_project
        finally:
            rope_project.close()

    @classmethod
    def apply_reducing_loop(
        cls,
        rope_project: t.Infra.RopeProject,
        steps: Sequence[Callable[[t.Infra.RopeProject], t.Infra.RopeChangeSet]],
        diagnostics: Callable[[], int],
    ) -> p.Result[int]:
        """Aplicar mudanças Rope em laço, mantendo apenas as que reduzem diagnóstico.

        Cada passo recebe o projeto já atualizado pelo passo anterior. O
        diagnóstico é recalculado após a aplicação; quando não reduz, a mudança
        é desfeita pelo próprio Rope antes do próximo passo.

        Args:
            rope_project: O projeto Rope nativo já inicializado.
            steps: Fábricas de ChangeSet avaliadas em ordem.
            diagnostics: Contador de diagnósticos corrente, chamado após cada passo.

        Returns:
            O menor total de diagnósticos alcançado.

        """
        try:
            baseline = cls._apply_reducing_steps(
                rope_project, steps=steps, diagnostics=diagnostics
            )
        except (RopeError, TypeError, RuntimeError, ValueError) as exc:
            return r[int].fail(str(exc), exception=exc)
        return r[int].ok(value=baseline)

    @classmethod
    def _apply_reducing_steps(
        cls,
        rope_project: t.Infra.RopeProject,
        *,
        steps: Sequence[Callable[[t.Infra.RopeProject], t.Infra.RopeChangeSet]],
        diagnostics: Callable[[], int],
    ) -> int:
        """Apply the reducing loop and roll back the active step on failure.

        Returns:
            The smallest diagnostics total reached.

        Raises:
            TypeError: If a step returns something that is not a ChangeSet.

        """
        baseline = diagnostics()
        active: t.Infra.RopeChangeSet | None = None
        try:
            for build in steps:
                changes = build(rope_project)
                if not isinstance(changes, p.Infra.RopeChangeSet):
                    msg = "Rope loop step returned invalid ChangeSet"
                    raise TypeError(msg)
                active = changes
                changes.do()
                current = diagnostics()
                if current >= baseline:
                    changes.undo()
                    active = None
                    continue
                baseline = current
                active = None
        finally:
            if active is not None:
                active.undo()
        return baseline


__all__: list[str] = ["FlextInfraUtilitiesRopeCore"]
