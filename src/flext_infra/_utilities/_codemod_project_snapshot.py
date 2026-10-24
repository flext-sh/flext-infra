"""Immutable binding snapshots and source epochs for codemod admission.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Generator
from contextlib import closing, contextmanager
from pathlib import Path
from types import MappingProxyType

from flext_cli import u

from flext_infra import c, m, p, t
from flext_infra._utilities import (
    FlextInfraUtilitiesRopeCore,
    FlextInfraUtilitiesRopeImports,
    FlextInfraUtilitiesRopeRuntimeModules,
)


class FlextInfraUtilitiesCodemodProjectSnapshotMixin:
    """Capture each selected project's import closure once per admission pass."""

    @staticmethod
    def codemod_source_epoch(
        snapshot: m.Infra.CodemodBindingSnapshot,
    ) -> m.Infra.CodemodSourceEpoch:
        """Decode each captured source once for the complete selected-project pass.

        Args:
            snapshot: The binding snapshot whose captured states are decoded.

        Returns:
            The immutable capture epoch shared by the complete pass.

        """
        contents = {
            state.path: state.content
            for state in snapshot.states
            if state.content is not None
        }
        return m.Infra.CodemodSourceEpoch(
            snapshot=snapshot,
            sources=MappingProxyType({
                path: content.decode("utf-8") for path, content in contents.items()
            }),
            contents=MappingProxyType(contents),
        )

    @classmethod
    def identity_source_epoch(
        cls,
        root: Path,
        source_paths: t.SequenceOf[Path],
        identities: t.StrSequence,
    ) -> m.Infra.CodemodSourceEpoch:
        """Capture sources plus every module a resolved identity needs, once.

        A semantic planning snapshot is a closed inventory: an identity such as
        ``pydantic.BaseModel`` resolves only when its module closure was
        captured before planning. Every dotted prefix of each identity is
        offered; a prefix that is not a module resolves to nothing and captures
        nothing. The sources' own import closure is captured with them.

        Returns:
            The immutable epoch every snapshot of one planning pass shares.

        """
        modules = tuple(
            dict.fromkeys(
                ".".join(parts[:end])
                for parts in (identity.split(".") for identity in identities)
                for end in range(1, len(parts) + 1)
            )
        )
        return cls.codemod_source_epoch(
            cls.codemod_binding_snapshot(
                root,
                projects=(
                    m.Infra.CodemodBindingProject(
                        root=root, source_paths=tuple(source_paths), modules=modules
                    ),
                ),
            )
        )

    @staticmethod
    @contextmanager
    def codemod_binding_project(
        root: Path,
        epoch: m.Infra.CodemodSourceEpoch,
    ) -> Generator[t.Pair[p.Infra.RopeProject, t.MappingKV[Path, str]]]:
        """Own one immutable binding graph for the complete admission pass.

        Yields:
            The frozen Rope graph and its complete authenticated source closure.

        """
        sources = epoch.sources
        with (
            FlextInfraUtilitiesRopeCore.open_project(root) as live,
            closing(
                FlextInfraUtilitiesRopeRuntimeModules.snapshot_project(
                    live, sources, captured=epoch
                )
            ) as project,
            project.frozen_layout(),
        ):
            yield project, sources

    @classmethod
    def codemod_binding_snapshot(
        cls,
        root: Path,
        source_states: tuple[m.Cli.AtomicFileState, ...] = (),
        modules: t.StrSequence = (),
        *,
        projects: t.SequenceOf[m.Infra.CodemodBindingProject] | None = None,
    ) -> m.Infra.CodemodBindingSnapshot:
        """Capture every selected project's owners once before inference.

        Args:
            root: The root path of the project to capture.
            source_states: A tuple of atomic file states representing the source files.
            modules: A sequence of module names to include in the snapshot.
            projects: An optional sequence of codemod binding projects to consider.

        Returns:
            The resulting ``m.Infra.CodemodBindingSnapshot``..

        """
        states: t.MutableMappingKV[Path, m.Cli.AtomicFileState] = {
            state.path.resolve(): state
            for state in m.Infra.CodemodBindingSnapshot(states=source_states).states
        }
        selections = (
            projects
            if projects is not None
            else (
                m.Infra.CodemodBindingProject(
                    root=root, source_paths=tuple(states), modules=modules
                ),
            )
        )
        imports: t.MutableMappingKV[
            Path, t.VariadicTuple[p.Infra.RopeImportStatement]
        ] = {}
        python_modules: t.MutableMappingKV[
            t.Pair[str, str], t.Infra.RopeResource | None
        ] = {}
        for selection in selections:
            with (
                FlextInfraUtilitiesRopeCore.open_project(selection.root) as project,
                project.frozen_layout(),
            ):
                lookup = m.Infra.CodemodImportResources(
                    modules={},
                    source_folders=tuple(
                        folder
                        for folder in project.get_source_folders()
                        if isinstance(folder, p.Infra.RopeRoot)
                    ),
                    python_folders=tuple(
                        folder
                        for folder in project.get_python_path_folders()
                        if isinstance(folder, p.Infra.RopeRoot)
                    ),
                    python_modules=python_modules,
                )
                for name in dict.fromkeys(selection.modules):
                    cls._snapshot_imported_resource(
                        project,
                        project.root,
                        name,
                        level=0,
                        lookup=lookup,
                    )
                pending = [
                    project.get_resource(
                        path.relative_to(selection.root.resolve()).as_posix()
                    )
                    for path in selection.source_paths
                ]
                pending.extend(
                    resource
                    for resource in lookup.modules.values()
                    if resource is not None
                )
                scheduled = {resource.real_path for resource in pending}
                visited: set[Path] = set()
                while pending:
                    fetched = cls._snapshot_module_imports(
                        project, states, imports, visited, pending.pop()
                    )
                    if fetched is None:
                        continue
                    path, resource, statements = fetched
                    visited.add(path)
                    for imported in cls._snapshot_import_resources(
                        project, resource, statements, lookup
                    ):
                        if imported.real_path not in scheduled:
                            scheduled.add(imported.real_path)
                            pending.append(imported)
                python_modules = lookup.python_modules
        return m.Infra.CodemodBindingSnapshot(states=tuple(states.values()))

    @staticmethod
    def _snapshot_module_imports(
        project: p.Infra.RopeProject,
        states: t.MutableMappingKV[Path, m.Cli.AtomicFileState],
        imports: t.MutableMappingKV[Path, t.VariadicTuple[p.Infra.RopeImportStatement]],
        visited: set[Path],
        resource: t.Infra.RopeResource,
    ) -> (
        t.Triple[
            Path, t.Infra.RopeResource, t.VariadicTuple[p.Infra.RopeImportStatement]
        ]
        | None
    ):
        """Authenticate one module and retain only its static import statements.

        Returns:
            The resolved path, live resource, and native imports, or ``None``
            when the resource carries no governable Python source.

        Raises:
            TypeError: If binding package has no source resource contract.
            ValueError: If binding source is absent.

        """
        path = Path(resource.real_path).resolve()
        if path.is_dir():
            if not isinstance(resource, p.Infra.RopeRoot):
                msg = f"binding package has no source resource contract: {path}"
                raise TypeError(msg)
            # A package binds through its initializer; a compiled
            # extension's PEP 561 stub package binds through its
            # ``__init__.pyi``. Only a PEP 420 namespace portion, which
            # has neither, carries no module source to read.
            initializer = next(
                (
                    name
                    for name in (c.Infra.INIT_PY, c.Infra.INIT_PYI)
                    if resource.has_child(name)
                ),
                None,
            )
            if initializer is None:
                return None
            resource = resource.get_child(initializer)
            path = Path(resource.real_path).resolve()
        if (
            path in visited
            or not path.is_file()
            or path.suffix not in {c.Infra.EXT_PYTHON, c.Infra.EXT_PYTHON_STUB}
        ):
            return None
        state = states.get(path)
        if state is None:
            u.Cli.info(
                f"mod: binding capture sources={len(states)} path={path}",
            )
            state = u.Cli.atomic_read_binary_file_state(path, required=True).unwrap()
            states[path] = state
        if state.content is None:
            msg = f"binding source is absent: {path}"
            raise ValueError(msg)
        if path not in imports:
            imports[path] = FlextInfraUtilitiesRopeImports.source_import_statements(
                project,
                state.content.decode("utf-8"),
            )
        return path, resource, imports[path]

    @classmethod
    def _snapshot_import_resources(
        cls,
        project: p.Infra.RopeProject,
        resource: t.Infra.RopeResource,
        imports: t.SequenceOf[p.Infra.RopeImportStatement],
        lookup: m.Infra.CodemodImportResources,
    ) -> list[t.Infra.RopeResource]:
        """Resolve native import targets through the shared resource cache.

        Returns:
            The pending resources named by the module's import statements.

        """
        found: list[t.Infra.RopeResource] = []
        for node in imports:
            declared = FlextInfraUtilitiesRopeImports.import_statement_module_name(node)
            names = FlextInfraUtilitiesRopeImports.import_statement_names_and_aliases(
                node
            )
            level = (
                len(declared) - len(declared.lstrip(".")) if declared is not None else 0
            )
            module_name = declared[level:] if declared is not None else ""
            targets = (
                (
                    module_name,
                    *(
                        f"{module_name}.{name}" if module_name else name
                        for name, _alias in names
                        if name != "*"
                    ),
                )
                if declared is not None
                else tuple(name for name, _alias in names)
            )
            for name in targets:
                imported = cls._snapshot_imported_resource(
                    project, resource, name, level=level, lookup=lookup
                )
                if imported is not None:
                    found.append(imported)
        return found

    @staticmethod
    def _snapshot_imported_resource(
        project: p.Infra.RopeProject,
        resource: t.Infra.RopeResource,
        name: str,
        *,
        level: int,
        lookup: m.Infra.CodemodImportResources,
    ) -> t.Infra.RopeResource | None:
        """Resolve one imported module name relative to the importing package.

        Returns:
            The imported module resource, or ``None`` when Rope cannot find it.

        """
        key = (name, resource.parent.real_path, level)
        if key not in lookup.modules:
            lookup.modules[key] = (
                project.find_relative_module(name, resource.parent, level)
                if level
                else project.find_module(name, resource.parent)
            )
        return lookup.modules[key]


__all__: list[str] = ["FlextInfraUtilitiesCodemodProjectSnapshotMixin"]
