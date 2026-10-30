"""Per-run workspace snapshot owner for ``u.Infra``.

One run (generation, modification) opens one source engine project over the
workspace; that project is the in-memory model and lists, parses and caches
modules lazily. Every other fact is derived on first query, once, and kept on
the snapshot, so every stage and member reuses it instead of rebuilding its
own inventory, parse, graph or project.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
import hashlib
from collections.abc import Generator, Mapping, MutableMapping, Sequence
from contextlib import ExitStack, contextmanager
from pathlib import Path

from flext_cli import u

from flext_infra import c, config, m, p, t
from flext_infra._utilities import (
    FlextInfraUtilitiesIterationDirectory,
    FlextInfraUtilitiesProjectDiscovery,
)
from flext_infra._utilities._rope._analysis.sourcescan import (
    FlextInfraUtilitiesRopeAnalysisSourceScan,
)
from flext_infra._utilities._rope.core import FlextInfraUtilitiesRopeCore
from flext_infra._utilities._rope.project import FlextInfraRopeProject
from flext_infra._utilities._rope.runtime import FlextInfraUtilitiesRopeRuntime
from flext_infra._utilities._rope.source_bases_runtime import (
    FlextInfraUtilitiesRopeSourceBasesRuntime,
)


class FlextInfraUtilitiesWorkspaceSnapshot:
    """Build the one snapshot of a workspace run and answer its queries."""

    @staticmethod
    def facade_original_sources(
        root: Path,
        states: tuple[m.Cli.AtomicFileState, ...],
    ) -> Mapping[Path, str]:
        """Select owned Python observations without another read or discovery.

        Returns:
            Captured Python text keyed by its authenticated source path.

        """
        return {
            state.path: state.content.decode(c.DEFAULT_ENCODING)
            for state in states
            if state.content is not None
            and state.path.is_relative_to(root)
            and state.path.suffix in c.Infra.PYTHON_SOURCE_SUFFIXES
            and not FlextInfraUtilitiesIterationDirectory.source_scan_ignored_path(
                root, state.path
            )
        }

    @classmethod
    def candidate_python_sources(
        cls,
        candidate: m.Infra.StageSourcePlan,
        states: tuple[m.Cli.AtomicFileState, ...],
    ) -> MutableMapping[Path, str]:
        """Project source observations over the candidate's declared scopes.

        Returns:
            Python observations retained by reference until their decode boundary.

        """
        return {
            path: source
            for scope in candidate.workspaces or (candidate.workspace,)
            for path, source in cls.facade_original_sources(scope, states).items()
        }

    @classmethod
    @contextmanager
    @staticmethod
    def project_captured_sources(
        project: p.Infra.RopeProject,
    ) -> dict[str, tuple[Path, str]]:
        """Capture the live candidate view as module-name to source entries.

        Ownership and identity elections resolve through the same captured
        view the run stages; an empty source set would blind their resolver
        to staged move destinations.

        Returns:
            The qualified module name to path and source text.

        """
        sources: dict[str, tuple[Path, str]] = {}
        root = Path(project.root.real_path)
        for resource in project.get_python_files():
            path = Path(resource.real_path).resolve()
            name = FlextInfraUtilitiesProjectDiscovery.module_name_for_file(
                path,
                project_root=root,
                source_project=project,
            )
            if name:
                sources[name] = (path, project.source_text(path))
        return sources

    @classmethod
    @contextmanager
    def facade_source_project(
        cls,
        root: Path,
        *,
        declared_files: tuple[m.Infra.CodegenFilePlan, ...] = (),
        planned_sources: Mapping[Path, str | None] | None = None,
        project_roots: tuple[Path, ...] = (),
        source_project: p.Infra.RopeProject | None = None,
    ) -> Generator[tuple[p.Infra.RopeProject, MutableMapping[Path, str]]]:
        """Bind authenticated planned overrides to the elected native project.

        A supplied invocation-owned project evolves only for this binding and
        restores its entry view on exit. Independent callers acquire a project
        through the same existing overlay owner.

        Yields:
            The native project and its elected captured Python sources.

        Raises:
            ValueError: If a project root escapes its authority.

        """
        root = root.resolve()
        project_roots = tuple(sorted({project.resolve() for project in project_roots}))
        if any(not project.is_relative_to(root) for project in project_roots):
            msg = "Rope declared project root is outside the original authority"
            raise ValueError(msg)
        original_root = next(path for path in (root, *root.parents) if path.is_dir())
        if (
            source_project is not None
            and Path(source_project.root.real_path) != original_root
        ):
            msg = "shared source project differs from the declared physical root"
            raise ValueError(msg)
        with ExitStack() as bindings:
            if source_project is not None:
                bindings.enter_context(
                    source_project.source_view(
                        declared_files=None, additional_source_folders=None
                    )
                )
            if planned_sources is not None:
                declared_files = cls.workspace_declared_sources(
                    root,
                    declared_files,
                    planned_sources,
                    source_project=source_project,
                )
            folders = cls._workspace_planned_folders(
                root, project_roots, declared_files, original_root=original_root
            )
            project_context = (
                cls.workspace_overlay_project(
                    root,
                    project_roots,
                    declared_files=declared_files,
                    additional_source_folders=folders,
                )
                if source_project is None
                else source_project.source_view(
                    declared_files=declared_files,
                    additional_source_folders=folders,
                )
            )
            project = bindings.enter_context(project_context)
            yield (
                project,
                {
                    path: project.source_text(path)
                    for scope in project_roots or (root,)
                    for path in (
                        FlextInfraUtilitiesProjectDiscovery.discover_python_files(
                            scope,
                            workspace_excluded_top_dirs=frozenset(),
                            source_project=project,
                        )
                    )
                },
            )

    @staticmethod
    def _workspace_planned_folders(
        root: Path,
        project_roots: tuple[Path, ...],
        declared_files: tuple[m.Infra.CodegenFilePlan, ...],
        *,
        original_root: Path,
    ) -> tuple[str, ...]:
        """Elect live and proposed source folders from the same native authority.

        Returns:
            The elected relative source folders.

        """
        proposed = tuple(
            plan.path for plan in declared_files if plan.desired_content is not None
        )
        return tuple(
            sorted({
                ""
                if folder == original_root
                else folder.relative_to(original_root).as_posix()
                for folder in (
                    root,
                    *project_roots,
                    *(
                        project / name
                        for project in (root, *project_roots)
                        for name in config.Infra.source_scan.roots
                    ),
                )
                if folder.is_dir()
                or any(path.is_relative_to(folder) for path in proposed)
            }),
        )

    @staticmethod
    def workspace_declared_sources(
        root: Path,
        declared_files: tuple[m.Infra.CodegenFilePlan, ...],
        planned_sources: Mapping[Path, str | None],
        *,
        source_project: p.Infra.RopeProject | None = None,
    ) -> tuple[m.Infra.CodegenFilePlan, ...]:
        """Bind planned overrides to their original physical witnesses.

        Returns:
            Declared plans including authenticated source overrides.

        Raises:
            ValueError: If planned bytes conflict with a declared plan.

        """
        inherited = (
            {plan.path: plan for plan in source_project.source_plans}
            if source_project is not None
            else {}
        )
        declarations: dict[Path, m.Infra.CodegenFilePlan] = {}
        for plan in declared_files:
            previous = declarations.get(plan.path)
            if previous is not None and previous != plan:
                message = f"Rope source has competing declarations: {plan.path}"
                raise ValueError(message)
            declarations[plan.path] = plan
        for supplied_path, source in planned_sources.items():
            path = supplied_path.resolve()
            content = source.encode(c.DEFAULT_ENCODING) if source is not None else None
            declared = declarations.get(path)
            if declared is not None:
                if declared.desired_content != content:
                    message = f"Rope planned source has competing declarations: {path}"
                    raise ValueError(message)
                continue
            prior = inherited.get(path)
            before = (
                prior.before
                if prior is not None
                else source_project.source_state(path, required=False)
                if source_project is not None
                else u.Cli.atomic_read_binary_file_state(path).unwrap()
            )
            mode = (
                prior.desired_mode
                if prior is not None and prior.desired_mode is not None
                else before.mode
            )
            if mode is None:
                mode = config.Infra.codegen.modes.file_default
            declarations[path] = m.Infra.CodegenFilePlan(
                project=prior.project if prior is not None else root,
                path=path,
                before=before,
                desired_content=content,
                desired_mode=None if content is None else mode,
            )
        return tuple((inherited | declarations).values())

    @staticmethod
    @contextmanager
    def workspace_overlay_project(
        root: Path,
        project_roots: tuple[Path, ...],
        *,
        declared_files: tuple[m.Infra.CodegenFilePlan, ...] = (),
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
            TypeError: If the native project lacks the required capabilities.

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
            project = FlextInfraRopeProject.from_atomic_reads(
                live,
                election=election,
                declared_files=declared_files,
                additional_source_folders=additional_source_folders,
            )
            with project.frozen_layout():
                yield project

    @classmethod
    @contextmanager
    def workspace_snapshot(
        cls,
        root: Path,
        members: Sequence[Path],
    ) -> Generator[p.Infra.WorkspaceSnapshot]:
        """Open one repository engine with explicit nested inventory ownership.

        ``members`` separates nested checkout inventories. Only ``root`` elects
        the native project's source roots, so sibling internal packages cannot
        replace this repository's bindings.

        Yields:
            The snapshot every stage of the run reads.

        """
        root = root.resolve()
        member_roots = tuple(dict.fromkeys(member.resolve() for member in members))
        with cls.workspace_overlay_project(root, (root,)) as project:
            yield m.Infra.WorkspaceSnapshot(
                workspace_root=root,
                members=member_roots,
                engine=project,
                python_files={},
                directory_facts={},
                python_module_facts={},
                sources={},
                packages={},
                import_edges={},
                bootstrap_dependencies={},
                absolute_import_roots={},
                import_namespaces={},
                class_ancestors={},
                exports={},
                bindings={},
                initializer_aliases={},
                receiver_bindings={},
                facade_paths={},
                pyproject_texts={},
                codemod_renderings={},
            )

    @staticmethod
    def workspace_python_files(
        snapshot: p.Infra.WorkspaceSnapshot,
        member: Path,
        *,
        project: p.Infra.RopeProject | None = None,
    ) -> tuple[Path, ...]:
        """Return one member's Python sources, listed through one project view.

        The snapshot's engine lists once per member; a planned view project
        (with proposed additions and retirements) lists through itself.
        Sources of a member nested inside this one belong to that member.

        Returns:
            The member's Python source and stub paths in path order.

        """
        member = member.resolve()
        view = snapshot.engine if project is None else project
        listed = snapshot.python_files.get(member) if project is None else None
        if listed is None:
            nested = tuple(
                other
                for other in snapshot.members
                if other != member and other.is_relative_to(member)
            )
            listed = tuple(
                path
                for path in FlextInfraUtilitiesProjectDiscovery.discover_python_files(
                    member,
                    workspace_excluded_top_dirs=frozenset(),
                    source_project=view,
                )
                if not any(path.is_relative_to(other) for other in nested)
            )
            if project is None:
                snapshot.python_files[member] = listed
        return listed

    @classmethod
    def workspace_resolve(
        cls,
        snapshot: p.Infra.WorkspaceSnapshot,
        identity: str,
    ) -> str:
        """Resolve a qualified name to the identity of the object it binds.

        Re-exports and imports are followed by the engine to the defining
        object.

        Returns:
            The defining object's qualified identity.

        """
        return cls._object_identity(cls._engine_object(snapshot, identity))

    @classmethod
    def workspace_class_ancestors(
        cls,
        snapshot: p.Infra.WorkspaceSnapshot,
        identity: str,
    ) -> t.StrTuple:
        """Return a class and its ancestors in C3 method order.

        Returns:
            The qualified identities from the class to its last ancestor.

        Raises:
            TypeError: If the identity does not name a class.

        """
        value = cls._engine_object(snapshot, identity)
        if not isinstance(value, p.Infra.RopeClassObject):
            msg = f"identity does not name a class: {identity}"
            raise TypeError(msg)
        return cls._linearized(snapshot, value)

    @classmethod
    def _linearized(
        cls,
        snapshot: p.Infra.WorkspaceSnapshot,
        value: p.Infra.RopeClassObject,
    ) -> t.StrTuple:
        """Return one engine class's C3 order, memoized per identity.

        Returns:
            The qualified identities in method order.

        """
        identity = cls._object_identity(value)
        ordered = snapshot.class_ancestors.get(identity)
        if ordered is None:
            parents = tuple(
                parent
                for parent in value.get_superclasses()
                if isinstance(parent, p.Infra.RopeClassObject)
            )
            ordered = (
                identity,
                *FlextInfraUtilitiesRopeSourceBasesRuntime.merge_class_lineages(
                    (
                        *(cls._linearized(snapshot, parent) for parent in parents),
                        tuple(cls._object_identity(parent) for parent in parents),
                    ),
                    message=f"inconsistent C3 order for {identity}",
                ),
            )
            snapshot.class_ancestors[identity] = ordered
        return ordered

    @staticmethod
    def _engine_object(
        snapshot: p.Infra.WorkspaceSnapshot,
        identity: str,
    ) -> p.Infra.RopePyObject:
        """Return the engine object a qualified name binds.

        Returns:
            The bound engine object.

        Raises:
            ValueError: If the identity has no module part.

        """
        module, separator, name = identity.rpartition(".")
        if not separator:
            msg = f"identity has no module part: {identity}"
            raise ValueError(msg)
        return snapshot.engine.get_module(module).get_attribute(name).get_object()

    @staticmethod
    def _object_identity(value: p.Infra.RopePyObject) -> str:
        """Return the qualified identity of an engine object.

        A module-level object is its defining module plus its name; an object
        without a source resource (a builtin) belongs to ``builtins``.

        Returns:
            The qualified identity.

        Raises:
            TypeError: If the object carries no name.

        """
        if not isinstance(value, p.Infra.RopeNamedObject):
            msg = "engine object carries no name"
            raise TypeError(msg)
        module = value.get_module()
        resource = None if module is None else module.get_resource()
        if resource is None:
            return f"builtins.{value.get_name()}"
        name = FlextInfraUtilitiesRopeRuntime.runtime_callable(
            "rope.base.libutils", "modname"
        )(resource)
        if not isinstance(name, str):
            msg = "engine module name is not text"
            raise TypeError(msg)
        return f"{name}.{value.get_name()}"

    @classmethod
    def workspace_source(
        cls,
        snapshot: p.Infra.WorkspaceSnapshot,
        path: Path,
    ) -> p.Infra.WorkspaceSnapshotSource:
        """Return one workspace file, read once through the authenticated owner.

        Returns:
            The file's snapshot entry.

        Raises:
            ValueError: If the file lies outside every member.

        """
        source = snapshot.sources.get(path)
        if source is not None:
            return source
        member = max(
            (root for root in snapshot.members if path.is_relative_to(root)),
            key=lambda root: len(root.parts),
            default=None,
        )
        if member is None:
            msg = f"workspace file lies outside every member: {path}"
            raise ValueError(msg)
        state = snapshot.engine.source_state(path, required=True)
        raw = snapshot.engine.source_bytes(path)
        source = m.Infra.WorkspaceSnapshotSource(
            path=path,
            state=state,
            digest=hashlib.sha256(raw).hexdigest(),
            module=cls._module_name(snapshot, path, member),
            member=member,
            text=raw.decode(c.DEFAULT_ENCODING),
        )
        snapshot.sources[path] = source
        return source

    @classmethod
    def workspace_sources(
        cls,
        snapshot: p.Infra.WorkspaceSnapshot,
    ) -> Mapping[Path, p.Infra.WorkspaceSnapshotSource]:
        """Read every member Python source once and return them all.

        Returns:
            Every member source keyed by path.

        """
        for member in snapshot.members:
            for path in cls.workspace_python_files(snapshot, member):
                cls.workspace_source(snapshot, path)
        return snapshot.sources

    @staticmethod
    def workspace_public_exports(
        snapshot: p.Infra.WorkspaceSnapshot,
        path: Path,
    ) -> Sequence[str]:
        """Read a module's public exports once from its authenticated native tree.

        Returns:
            The names declared by the source module's literal ``__all__``.

        """
        owner = FlextInfraUtilitiesWorkspaceSnapshot
        if path not in snapshot.exports:
            owner.workspace_source(snapshot, path)
            snapshot.exports[path] = (
                FlextInfraUtilitiesRopeAnalysisSourceScan.module_assignment_strings_source(
                    FlextInfraUtilitiesRopeCore.resolve_pymodule(
                        snapshot.engine,
                        FlextInfraUtilitiesRopeRuntime.file_resource_at(
                            snapshot.engine, path
                        ),
                    ),
                    c.Infra.DUNDER_ALL,
                )
            )
        return snapshot.exports[path]

    @staticmethod
    def workspace_module_tree(
        snapshot: p.Infra.WorkspaceSnapshot,
        path: Path,
    ) -> t.Infra.AstModule:
        """Return the engine's cached syntax tree of one workspace module.

        Returns:
            The module tree, parsed once by the engine.

        Raises:
            TypeError: If the engine's tree is not a module tree.

        """
        engine = snapshot.engine
        tree = engine.get_pymodule(
            engine.get_resource(
                path.relative_to(Path(engine.root.real_path)).as_posix()
            )
        ).get_ast()
        if not isinstance(tree, ast.Module):
            msg = f"source engine tree is not a module: {path}"
            raise TypeError(msg)
        return tree

    @classmethod
    def workspace_module_imports(
        cls,
        snapshot: p.Infra.WorkspaceSnapshot,
        path: Path,
    ) -> tuple[frozenset[str], frozenset[str]]:
        """Return the modules one source imports at runtime and only for typing.

        An import under ``if TYPE_CHECKING:`` is a typing edge; every other
        import, function-local ones included, is a runtime edge. ``from X
        import Y`` imports ``X`` and ``X.Y``; relative imports resolve against
        the importing package. Only statement nodes can hold an import.

        Returns:
            The runtime and the typing-only imported module names.

        """
        edges = snapshot.import_edges.get(path)
        if edges is not None:
            return edges
        module = cls.workspace_source(snapshot, path).module
        base = module if path.name == c.Infra.INIT_PY else module.rpartition(".")[0]
        runtime: set[str] = set()
        typing: set[str] = set()
        pending: list[tuple[ast.AST, bool]] = [
            (statement, False)
            for statement in cls.workspace_module_tree(snapshot, path).body
        ]
        while pending:
            node, typing_only = pending.pop()
            if isinstance(node, ast.Import | ast.ImportFrom):
                (typing if typing_only else runtime).update(
                    cls._import_targets(node, base)
                )
                continue
            if isinstance(node, ast.If) and cls._typing_guard(node.test):
                pending.extend((child, True) for child in node.body)
                pending.extend((child, typing_only) for child in node.orelse)
                continue
            pending.extend(
                (child, typing_only)
                for child in ast.iter_child_nodes(node)
                if isinstance(child, ast.stmt | ast.excepthandler | ast.match_case)
            )
        edges = (frozenset(runtime), frozenset(typing - runtime))
        snapshot.import_edges[path] = edges
        return edges

    @classmethod
    def workspace_module_closure(
        cls,
        snapshot: p.Infra.WorkspaceSnapshot,
        modules: frozenset[str],
        *,
        reverse: bool,
        typing: bool,
    ) -> p.Result[frozenset[str]]:
        """Return the modules with everything they reach through workspace imports.

        ``reverse`` follows importers instead of imports; ``typing`` adds the
        typing-only edges to the runtime ones. The graph covers every member
        source, derived once from the engine's trees.

        Returns:
            The closure, or the failure naming modules outside the graph.

        """
        sources = cls.workspace_sources(snapshot)
        paths = {
            source.module: path for path, source in sources.items() if source.module
        }
        edges: dict[str, frozenset[str]] = {}
        for module, path in paths.items():
            if path.suffix != c.Infra.EXT_PYTHON:
                continue
            runtime, typed = cls.workspace_module_imports(snapshot, path)
            edges[module] = frozenset(
                name for name in (*runtime, *(typed if typing else ())) if name in paths
            )
        if reverse:
            reversed_edges: dict[str, set[str]] = {name: set() for name in edges}
            for name, targets in edges.items():
                for target in targets:
                    reversed_edges.setdefault(target, set()).add(name)
            edges = {name: frozenset(found) for name, found in reversed_edges.items()}
        return u.Cli.dag_closure(edges, modules)

    @classmethod
    def workspace_snapshot_rebase(
        cls,
        snapshot: p.Infra.WorkspaceSnapshot,
        paths: Sequence[Path],
    ) -> None:
        """Refresh this run's recorded states for paths the run itself wrote.

        Later planning surfaces of one process must verify against the bytes
        their own run published, not the process-start capture; external
        mutations still fail the unchanged-file proof.

        """
        for path in paths:
            if path in snapshot.sources:
                del snapshot.sources[path]
                cls.workspace_source(snapshot, path)

    @staticmethod
    def workspace_snapshot_verify(
        snapshot: p.Infra.WorkspaceSnapshot,
        paths: Sequence[Path],
    ) -> p.Result[bool]:
        """Prove the given read files still carry the states the snapshot read.

        Returns:
            True when every file is unchanged, or the failure naming the first
            file that changed during the run.

        """
        return u.Cli.atomic_verify_binary_file_states(
            tuple(snapshot.sources[path].state for path in paths),
        ).map(lambda _verified: True)

    @staticmethod
    def _module_name(
        snapshot: p.Infra.WorkspaceSnapshot,
        path: Path,
        member: Path,
    ) -> str:
        """Return the dotted module name of a member source.

        Returns:
            The module name, or an empty string outside a package.

        """
        package = snapshot.packages.get(path.parent)
        if package is None:
            package = FlextInfraUtilitiesProjectDiscovery.package_name_for_dir(
                path.parent, project_root=member, source_project=snapshot.engine
            )
            snapshot.packages[path.parent] = package
        if path.name == c.Infra.INIT_PY or not package:
            return package
        return f"{package}.{path.stem}"

    @staticmethod
    def _typing_guard(test: ast.expr) -> bool:
        """Report whether an ``if`` test is the typing-only guard.

        Returns:
            True for ``TYPE_CHECKING`` and ``typing.TYPE_CHECKING``.

        """
        return (
            isinstance(test, ast.Name) and test.id == c.Infra.TYPING_GUARD_NAME
        ) or (
            isinstance(test, ast.Attribute) and test.attr == c.Infra.TYPING_GUARD_NAME
        )

    @staticmethod
    def _import_targets(node: ast.Import | ast.ImportFrom, base: str) -> Sequence[str]:
        """Return every module name one import statement can bind from.

        Returns:
            The candidate module names.

        """
        if isinstance(node, ast.Import):
            return tuple(alias.name for alias in node.names)
        parts = base.split(".") if base else []
        anchor = ".".join(parts[: len(parts) - node.level + 1]) if node.level else ""
        source = ".".join(part for part in (anchor, node.module or "") if part)
        return (source, *(f"{source}.{alias.name}" for alias in node.names))


__all__: list[str] = ["FlextInfraUtilitiesWorkspaceSnapshot"]
