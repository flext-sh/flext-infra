"""Atomic, fail-fast Rope declaration relocation for ``u.Infra``.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from pathlib import Path

from flext_cli import u

from flext_infra import c, m, p, t
from flext_infra._utilities import (
    FlextInfraUtilitiesCodegenNamespace,
    FlextInfraUtilitiesCodemodProject,
    FlextInfraUtilitiesRopeCorePyModuleMixin,
    FlextInfraUtilitiesRopeImports,
    FlextInfraUtilitiesRopeRuntime,
    FlextInfraUtilitiesRopeRuntimeModules,
)


class FlextInfraUtilitiesRopeClassMove:
    """Own identity-preserving class and module relocation through Rope."""

    @classmethod
    def plan_module_move(
        cls,
        rope_project: p.Infra.RopeProject,
        source_file: Path,
        destination_directory: Path,
        *,
        sources: t.MappingKV[Path, str],
        source_states: tuple[m.Cli.AtomicFileState, ...],
    ) -> tuple[m.Infra.CodegenFilePlan, ...]:
        """Plan a class-only module relocation without creating its destination.

        Native class relocation supplies reference edits. Complete module metadata
        remains in the virtual destination; concrete create/delete effects belong
        to the existing codegen publisher, never to Rope's mutable filesystem.

        Returns:
            Authenticated file plans for the declaration and its consumers.

        Raises:
            ValueError: If input identity or a native relocation proof differs.

        """
        root = Path(rope_project.root.real_path).resolve()
        source = cls._owned_path(root, root / source_file)
        target = cls._owned_path(root, root / destination_directory) / source.name
        if source == target:
            msg = f"module move source and target are identical: {source}"
            raise ValueError(msg)
        before, captured = cls._module_input_epoch(root, source, sources, source_states)
        request, target_plan, proposed, virtual, source_module_name = (
            cls._module_move_preparation(
                rope_project, source, target, sources, captured
            )
        )
        source_states = target_plan.source_states
        return cls._module_file_plans(
            target_plan,
            source,
            before,
            cls._module_completed_changes(
                request, source_module_name, sources, proposed, (captured, virtual)
            ),
            source_states,
        )

    @classmethod
    def _module_move_preparation(
        cls,
        rope_project: p.Infra.RopeProject,
        source: Path,
        target: Path,
        sources: t.MappingKV[Path, str],
        captured: m.Infra.CodemodSourceEpoch,
    ) -> tuple[
        m.Infra.ClassMoveRequest,
        m.Infra.CodegenFilePlan,
        t.DictKV[Path, str],
        t.VariadicTuple[m.Infra.CodegenFilePlan],
        str,
    ]:
        source_states = captured.snapshot.states
        canonical, source_module_name, reexports = cls._canonical_module_metadata(
            rope_project, source, sources, captured
        )
        declaration = cls._module_class_declaration(canonical, source)
        prelude = cls._module_prelude(canonical, source, declaration)
        request = m.Infra.ClassMoveRequest(
            rope_project=rope_project,
            source_file=source,
            target_file=target,
            class_name=declaration.name,
            line=declaration.lineno,
            apply=False,
        )
        target_plan, virtual, source_states = cls._module_virtual_destinations(
            request, prelude, source_states, sources
        )
        proposed = dict(sources)
        proposed[source] = canonical
        proposed[target] = prelude
        for plan in virtual[1:]:
            proposed[plan.path] = ""
        cls._module_reexport_sources(request, proposed, captured, virtual, reexports)
        return (
            request,
            target_plan.model_copy(update={"source_states": source_states}),
            proposed,
            virtual,
            source_module_name,
        )

    @classmethod
    def _module_virtual_destinations(
        cls,
        request: m.Infra.ClassMoveRequest,
        prelude: str,
        source_states: t.VariadicTuple[m.Cli.AtomicFileState],
        sources: t.MappingKV[Path, str],
    ) -> t.Triple[
        m.Infra.CodegenFilePlan,
        t.VariadicTuple[m.Infra.CodegenFilePlan],
        t.VariadicTuple[m.Cli.AtomicFileState],
    ]:
        root = Path(request.rope_project.root.real_path).resolve()
        target = request.target_file
        before = next(
            state
            for state in source_states
            if state.path.resolve() == request.source_file
        )
        if before.mode is None:
            msg = f"module move source is absent: {request.source_file}"
            raise ValueError(msg)
        target_plan = cls._module_destination_plan(
            root, target, prelude, before.mode, source_states
        )
        virtual = [target_plan]
        # Package identity is needed by native Rope before any directory exists.
        # This lookup-only initializer is never returned for semantic publication:
        # the existing lazy-init phase owns the real generated file.
        initializer = target.parent / c.Infra.INIT_PY
        if initializer not in sources:
            initializer_plan = cls._module_destination_plan(
                root,
                initializer,
                "",
                before.mode,
                source_states,
            )
            if isinstance(initializer_plan.before, m.Cli.AtomicFileState):
                source_states = m.Infra.CodemodBindingSnapshot(
                    states=(*source_states, initializer_plan.before),
                ).states
            elif initializer_plan.before != target_plan.before:
                msg = f"module move destination parent snapshots disagree: {target}"
                raise ValueError(msg)
            virtual.append(initializer_plan)
        return target_plan, tuple(virtual), source_states

    @classmethod
    def _module_completed_changes(
        cls,
        request: m.Infra.ClassMoveRequest,
        source_module_name: str,
        sources: t.MappingKV[Path, str],
        proposed: t.MappingKV[Path, str],
        view: t.Pair[
            m.Infra.CodemodSourceEpoch, t.VariadicTuple[m.Infra.CodegenFilePlan]
        ],
    ) -> t.DictKV[Path, str]:
        captured, virtual = view
        changed = cls._module_reference_changes(
            request, sources, proposed, captured, virtual
        )
        candidate = dict(proposed)
        candidate.update(changed)
        metadata_removed = cls._module_metadata_cleanup(
            request, source_module_name, candidate, captured, virtual
        )
        if metadata_removed is not None:
            changed[request.target_file] = metadata_removed
        relocated = cls._module_class_declaration(
            changed[request.target_file], request.target_file
        )
        if relocated.name != request.class_name:
            msg = (
                f"native Rope changed the published declaration: {request.target_file}"
            )
            raise ValueError(msg)
        return changed

    @classmethod
    def _module_input_epoch(
        cls,
        root: Path,
        source: Path,
        sources: t.MappingKV[Path, str],
        source_states: t.VariadicTuple[m.Cli.AtomicFileState],
    ) -> t.Pair[m.Cli.AtomicFileState, m.Infra.CodemodSourceEpoch]:
        states = {
            state.path.resolve(): state
            for state in m.Infra.CodemodBindingSnapshot(states=source_states).states
        }
        if source not in states or source not in sources:
            msg = f"module move source is not authenticated: {source}"
            raise ValueError(msg)
        before = states[source]
        if before.content is None or before.mode is None:
            msg = f"module move source is absent: {source}"
            raise ValueError(msg)
        for path, text in sources.items():
            state = states.get(path.resolve())
            if state is None or state.content is None:
                msg = f"module move input is not authenticated: {path}"
                raise ValueError(msg)
            if state.content.decode(c.DEFAULT_ENCODING) != text:
                msg = f"module move input disagrees with its snapshot: {path}"
                raise ValueError(msg)
        cls._module_class_declaration(sources[source], source)
        captured = FlextInfraUtilitiesCodemodProject.codemod_binding_snapshot(
            root, tuple(states[path.resolve()] for path in sources)
        )
        for state in captured.states:
            path = state.path.resolve()
            if path in states and states[path] != state:
                msg = f"module move dependency snapshot disagrees: {path}"
                raise ValueError(msg)
            states[path] = state
        return before, FlextInfraUtilitiesCodemodProject.codemod_source_epoch(
            m.Infra.CodemodBindingSnapshot(states=tuple(states.values()))
        )

    @classmethod
    def _canonical_module_metadata(
        cls,
        rope_project: p.Infra.RopeProject,
        source: Path,
        sources: t.MappingKV[Path, str],
        captured: m.Infra.CodemodSourceEpoch,
    ) -> t.Triple[str, str, t.VariadicTuple[str]]:
        root = Path(rope_project.root.real_path).resolve()
        original = FlextInfraUtilitiesRopeRuntimeModules.snapshot_project(
            rope_project, sources, captured=captured
        )
        try:
            source_resource = cls._resource(original, root, source)
            source_module = FlextInfraUtilitiesRopeCorePyModuleMixin.resolve_pymodule(
                original, source_resource
            )
            source_module_name = source_module.get_name()
            tools = FlextInfraUtilitiesRopeRuntime.runtime_callable(
                "rope.refactor.importutils", "ImportTools"
            )(original)
            if not isinstance(tools, p.Infra.RopeImportTools):
                msg = "native Rope import tools violate their contract"
                raise TypeError(msg)
            canonical = tools.relatives_to_absolutes(source_module)
            reexports = cls._module_reexport_packages(
                original,
                sources,
                source_resource,
                cls._module_class_declaration(canonical, source).name,
            )
            return canonical, source_module_name, reexports
        finally:
            original.close()

    @staticmethod
    def _module_prelude(canonical: str, source: Path, declaration: ast.ClassDef) -> str:
        lines = canonical.splitlines(keepends=True)
        start = min((
            declaration.lineno,
            *(item.lineno for item in declaration.decorator_list),
        ))
        if declaration.end_lineno is None:
            msg = f"module move declaration has no end: {source}"
            raise ValueError(msg)
        return "".join(lines[: start - 1] + lines[declaration.end_lineno :])

    @classmethod
    def _module_reexport_sources(
        cls,
        request: m.Infra.ClassMoveRequest,
        proposed: t.MutableMappingKV[Path, str],
        captured: m.Infra.CodemodSourceEpoch,
        virtual: t.VariadicTuple[m.Infra.CodegenFilePlan],
        reexports: t.VariadicTuple[str],
    ) -> None:
        root = Path(request.rope_project.root.real_path).resolve()
        virtual_paths = {plan.path for plan in virtual}
        for origin in reexports:
            package_plan = FlextInfraUtilitiesRopeRuntimeModules.snapshot_project(
                request.rope_project,
                proposed,
                captured=captured,
                declared_files=virtual,
            )
            try:
                destination = FlextInfraUtilitiesRopeCorePyModuleMixin.resolve_pymodule(
                    package_plan,
                    cls._resource(
                        package_plan, root, request.target_file.parent / c.Infra.INIT_PY
                    ),
                ).get_name()
                for path in proposed:
                    if (
                        path in virtual_paths
                        or path == request.source_file
                        or captured.sources[path].startswith(c.Infra.AUTOGEN_HEADERS)
                    ):
                        continue
                    updated = FlextInfraUtilitiesRopeImports.plan_from_import_aliases(
                        package_plan,
                        cls._resource(package_plan, root, path),
                        source_module=origin,
                        target_module=destination,
                        aliases=(request.class_name,),
                    )
                    if updated is not None:
                        proposed[path] = updated
            finally:
                package_plan.close()

    @classmethod
    def _module_reference_changes(
        cls,
        request: m.Infra.ClassMoveRequest,
        sources: t.MappingKV[Path, str],
        proposed: t.MappingKV[Path, str],
        captured: m.Infra.CodemodSourceEpoch,
        virtual: t.VariadicTuple[m.Infra.CodegenFilePlan],
    ) -> t.DictKV[Path, str]:
        planned = FlextInfraUtilitiesRopeRuntimeModules.snapshot_project(
            request.rope_project,
            proposed,
            captured=captured,
            declared_files=virtual,
        )
        try:
            edits = cls.plan_class_move(
                request.model_copy(update={"rope_project": planned}),
                sources=proposed,
            )
        finally:
            planned.close()
        changed = {
            path: content
            for path, content in proposed.items()
            if path in sources and content != sources[path]
        }
        changed.update({edit.file_path: edit.updated_source for edit in edits})
        if request.target_file not in changed:
            msg = f"native Rope did not relocate the declaration: {request.source_file}"
            raise ValueError(msg)
        return changed

    @classmethod
    def _module_metadata_cleanup(
        cls,
        request: m.Infra.ClassMoveRequest,
        source_module_name: str,
        candidate: t.MappingKV[Path, str],
        captured: m.Infra.CodemodSourceEpoch,
        virtual: t.VariadicTuple[m.Infra.CodegenFilePlan],
    ) -> str | None:
        root = Path(request.rope_project.root.real_path).resolve()
        metadata_project = FlextInfraUtilitiesRopeRuntimeModules.snapshot_project(
            request.rope_project,
            candidate,
            captured=captured,
            declared_files=tuple(
                plan.model_copy(
                    update={
                        "desired_content": candidate[plan.path].encode(
                            c.DEFAULT_ENCODING
                        )
                    }
                )
                for plan in virtual
            ),
        )
        try:
            return FlextInfraUtilitiesRopeImports.remove_import_names(
                metadata_project,
                cls._resource(metadata_project, root, request.target_file),
                from_module=source_module_name,
                names=(c.Infra.DUNDER_ALL,),
                apply=False,
            )
        finally:
            metadata_project.close()

    @classmethod
    def _module_file_plans(
        cls,
        target_plan: m.Infra.CodegenFilePlan,
        source: Path,
        before: m.Cli.AtomicFileState,
        changed: t.MappingKV[Path, str],
        source_states: t.VariadicTuple[m.Cli.AtomicFileState],
    ) -> t.VariadicTuple[m.Infra.CodegenFilePlan]:
        root, target = target_plan.project, target_plan.path
        states = {state.path.resolve(): state for state in source_states}
        files = [
            target_plan.model_copy(
                update={
                    "desired_content": changed[target].encode(c.DEFAULT_ENCODING),
                    "source_states": source_states,
                }
            ),
            m.Infra.CodegenFilePlan(
                project=root,
                path=source,
                before=before,
                desired_content=None,
                desired_mode=None,
                source_states=source_states,
            ),
        ]
        for path, content in changed.items():
            if path in {source, target}:
                continue
            state = states.get(path)
            if state is None or state.mode is None:
                msg = f"module move consumer is not authenticated: {path}"
                raise ValueError(msg)
            if state.content is not None and state.content.decode(
                c.DEFAULT_ENCODING,
            ).startswith(c.Infra.AUTOGEN_HEADERS):
                if path.name != c.Infra.INIT_PY:
                    msg = f"module move requires joint facade projection: {path}"
                    raise ValueError(
                        msg,
                    )
                continue
            files.append(
                m.Infra.CodegenFilePlan(
                    project=root,
                    path=path,
                    before=state,
                    desired_content=content.encode(c.DEFAULT_ENCODING),
                    desired_mode=state.mode,
                    source_states=source_states,
                ),
            )
        return tuple(files)

    @classmethod
    def _module_reexport_packages(
        cls,
        project: p.Infra.RopeProject,
        sources: t.MappingKV[Path, str],
        source: p.Infra.RopeFile,
        name: str,
    ) -> tuple[str, ...]:
        """Elect package exports by original closed native declaration identity.

        Returns:
            The original packages exposing the declaration's native identity.

        """
        root = Path(project.root.real_path).resolve()
        expected = FlextInfraUtilitiesRopeCorePyModuleMixin.resolve_pymodule(
            project, source
        ).get_attribute(name)
        owners: list[str] = []
        for path in sorted(sources):
            if path.name != c.Infra.INIT_PY:
                continue
            module_name = FlextInfraUtilitiesRopeCorePyModuleMixin.resolve_pymodule(
                project,
                cls._resource(project, root, path),
            ).get_name()
            published = (
                FlextInfraUtilitiesRopeRuntime
                .require_semantic_module(project.get_module(module_name))
                .get_attributes()
                .get(name)
            )
            if published is not None and FlextInfraUtilitiesRopeRuntime.same_name(
                expected,
                published,
            ):
                owners.append(module_name)
        return tuple(owners)

    @staticmethod
    def _module_class_declaration(source: str, path: Path) -> ast.ClassDef:
        """Require one published class and no separate executable module behavior.

        Returns:
            The single declaration published by this module.

        Raises:
            ValueError: If the module carries separate behavior or ambiguous exports.

        """
        tree = ast.parse(source, filename=str(path))
        declarations = [node for node in tree.body if isinstance(node, ast.ClassDef)]
        if len(declarations) != 1:
            msg = f"module move requires one class: {path}"
            raise ValueError(msg)
        exports: list[str] = []
        for node in tree.body:
            if isinstance(node, ast.ClassDef | ast.Import | ast.ImportFrom):
                continue
            if (
                isinstance(node, ast.Expr)
                and isinstance(node.value, ast.Constant)
                and isinstance(node.value.value, str)
            ):
                continue
            if isinstance(node, ast.Assign) and len(node.targets) == 1:
                name = node.targets[0]
                value = node.value
            elif isinstance(node, ast.AnnAssign):
                name = node.target
                value = node.value
            else:
                msg = f"module move has separate executable behavior: {path}"
                raise ValueError(msg)
            if not isinstance(name, ast.Name) or name.id != "__all__" or value is None:
                msg = f"module move has a separate module binding: {path}"
                raise ValueError(msg)
            exports.extend(
                FlextInfraUtilitiesRopeClassMove._module_literal_exports(value, path),
            )
        if exports != [declarations[0].name]:
            msg = f"module move exports are ambiguous: {path}"
            raise ValueError(msg)
        return declarations[0]

    @staticmethod
    def _module_literal_exports(value: ast.expr, path: Path) -> list[str]:
        """Read the original literal export sequence.

        Returns:
            The ordered literal names.

        Raises:
            ValueError: If the exports are not a literal list or tuple of names.

        """
        match value:
            case ast.List(elts=elements) | ast.Tuple(elts=elements):
                pass
            case _:
                msg = f"module move exports are not literal names: {path}"
                raise ValueError(msg)
        names: list[str] = []
        for element in elements:
            match element:
                case ast.Constant(value=str() as name):
                    names.append(name)
                case _:
                    msg = f"module move exports are not literal names: {path}"
                    raise ValueError(msg)
        return names

    @staticmethod
    def _module_destination_plan(
        root: Path,
        target: Path,
        source: str,
        mode: int,
        source_states: tuple[m.Cli.AtomicFileState, ...],
    ) -> m.Infra.CodegenFilePlan:
        """Capture an absent file or absent parent chain without creating either.

        Returns:
            The authenticated plan for the absent destination.

        Raises:
            FileExistsError: If the destination already has file content.

        """
        parents = u.Cli.atomic_plan_directory_chain(target.parent).unwrap()
        before: m.Cli.AtomicDirectoryChainPlan | m.Cli.AtomicFileState
        if parents.directories:
            before = parents
        else:
            before = u.Cli.atomic_read_binary_file_state(
                target, required=False
            ).unwrap()
            if before.content is not None:
                raise FileExistsError(target)
        return m.Infra.CodegenFilePlan(
            project=root,
            path=target,
            before=before,
            desired_content=source.encode(c.DEFAULT_ENCODING),
            desired_mode=mode,
            source_states=source_states,
        )

    @classmethod
    def move_module(
        cls,
        rope_project: p.Infra.RopeProject,
        source_file: Path,
        destination_directory: Path,
    ) -> Path:
        """Move one module through Rope's existing identity-preserving engine.

        Returns:
            The relocated module path.

        Raises:
            FileNotFoundError: If either declared owner is absent.
            FileExistsError: If the destination already contains the module.

        """
        root = Path(rope_project.root.real_path).resolve()
        source = cls._owned_path(root, root / source_file)
        destination = cls._owned_path(root, root / destination_directory)
        if not source.is_file():
            raise FileNotFoundError(source)
        if not destination.is_dir():
            raise FileNotFoundError(destination)
        target = destination / source.name
        if target.exists():
            raise FileExistsError(target)
        rope_project.validate()
        mover = FlextInfraUtilitiesRopeRuntime.create_move(
            rope_project,
            cls._resource(rope_project, root, source),
            None,
        )
        changes = mover.get_changes(
            rope_project.get_resource(destination.relative_to(root).as_posix()),
        )
        rope_project.do(changes)
        return target

    @classmethod
    def move_class(cls, request: m.Infra.ClassMoveRequest) -> Path:
        """Move one top-level class or return its validated preview target.

        Returns:
            The resulting ``Path``.

        """
        target_file, mover = cls._class_mover(request)
        root = Path(request.rope_project.root.real_path).resolve()
        if not request.apply:
            return target_file

        # Only an authorized application establishes a destination family.
        # Source identity and identifier resolution above are observational.
        target_file.parent.mkdir(parents=True, exist_ok=True)
        created_target = not target_file.exists()
        move_completed = False
        if created_target:
            u.Cli.atomic_write_text_file(
                target_file,
                f"{c.Infra.FUTURE_ANNOTATIONS}\n",
            ).unwrap()
        try:
            request.rope_project.validate()
            target_resource = cls._resource(request.rope_project, root, target_file)
            changes = mover.get_changes(target_resource)
            request.rope_project.do(changes)
            move_completed = True
            return target_file
        finally:
            if created_target and not move_completed and target_file.exists():
                target_file.unlink()

    @classmethod
    def plan_class_move(
        cls,
        request: m.Infra.ClassMoveRequest,
        *,
        sources: t.MappingKV[Path, str],
    ) -> t.VariadicTuple[m.Infra.SemanticMigrationEdit]:
        """Preview one identity-preserving move inside a closed source inventory.

        Returns:
            The resulting ``t.VariadicTuple[m.Infra.SemanticMigrationEdit]``.

        Raises:
            TypeError: If class move planning produced a non-content effect.
            ValueError: If immutable class move planning requires apply=False; or if
                class move owners are absent from the governed source inventory; or if
                class move source differs from its planning snapshot; or if class move
                escaped its governed source inventory.

        """
        if request.apply:
            msg = "immutable class move planning requires apply=False"
            raise ValueError(msg)
        target_file, mover = cls._class_mover(request)
        root = Path(request.rope_project.root.real_path).resolve()
        if request.source_file.resolve() not in sources or target_file not in sources:
            msg = "class move owners are absent from the governed source inventory"
            raise ValueError(msg)
        resources = [
            cls._resource(request.rope_project, root, path) for path in sorted(sources)
        ]
        for resource in resources:
            path = Path(resource.real_path).resolve()
            if resource.read() != sources[path]:
                msg = f"class move source differs from its planning snapshot: {path}"
                raise ValueError(msg)
        changes = mover.get_changes(
            cls._resource(request.rope_project, root, target_file),
            resources=resources,
        )
        edits: list[m.Infra.SemanticMigrationEdit] = []
        for change in changes.changes:
            if not isinstance(change, p.Infra.RopeChangeContents):
                msg = "class move planning produced a non-content effect"
                raise TypeError(msg)
            path = Path(change.resource.real_path).resolve()
            if path not in sources:
                msg = f"class move escaped its governed source inventory: {path}"
                raise ValueError(msg)
            if change.new_contents != sources[path]:
                edits.append(
                    m.Infra.SemanticMigrationEdit(
                        file_path=path,
                        original_source=sources[path],
                        updated_source=change.new_contents,
                        changes=(f"Rope moved {request.class_name} to {target_file}",),
                    ),
                )
        return tuple(edits)

    @classmethod
    def _class_mover(
        cls,
        request: m.Infra.ClassMoveRequest,
    ) -> t.Pair[Path, p.Infra.RopeMoveGlobal]:
        """Resolve both execution and planning from the exact original declaration.

        Returns:
            The resulting ``t.Pair[Path, p.Infra.RopeMoveGlobal]``.

        Raises:
            FileNotFoundError: If ``not source_file.is_file()``.
            ValueError: If class move source and target are identical; or if class.

        """
        root = Path(request.rope_project.root.real_path).resolve()
        source_file = cls._owned_path(root, request.source_file)
        target_file = cls._owned_path(root, request.target_file)
        if source_file == target_file:
            msg = f"class move source and target are identical: {source_file}"
            raise ValueError(msg)
        if not source_file.is_file():
            raise FileNotFoundError(source_file)
        source_resource = cls._resource(request.rope_project, root, source_file)
        source = source_resource.read()
        offset = (
            FlextInfraUtilitiesRopeCorePyModuleMixin.find_identifier_offset_in_lines(
                source.splitlines(keepends=True),
                line=request.line,
                symbol=request.class_name,
            )
        )
        if offset is None:
            msg = f"class {request.class_name} was not found at line {request.line}"
            raise ValueError(msg)
        mover = FlextInfraUtilitiesRopeRuntime.create_move(
            request.rope_project,
            source_resource,
            offset,
        )
        return target_file, mover

    @staticmethod
    def class_module_stem(class_name: str) -> str:
        """Derive one module stem from the core CamelCase boundary authority.

        Returns:
            The resulting ``str``.

        """
        return c.CAMEL_TO_SNAKE_RE.sub(r"\1_\2", class_name).lower()

    @classmethod
    def class_target_file(
        cls,
        *,
        package_dir: Path,
        source_file: Path,
        class_name: str,
        family: str,
    ) -> Path:
        """Derive a canonical destination without a project-owned registry.

        Returns:
            The resulting ``Path``.

        """
        module_stem = cls.class_module_stem(class_name)
        if family:
            family_dir = FlextInfraUtilitiesCodegenNamespace.facade_families()[
                family
            ].directory
            return package_dir / family_dir / f"{module_stem}.py"
        return source_file.parent / f"_{source_file.stem}_{module_stem}.py"

    @staticmethod
    def _owned_path(root: Path, candidate: Path) -> Path:
        resolved = candidate.resolve()
        if not resolved.is_relative_to(root):
            msg = f"class move path is outside Rope project {root}: {resolved}"
            raise ValueError(msg)
        return resolved

    @staticmethod
    def _resource(
        rope_project: t.Infra.RopeProject,
        root: Path,
        file_path: Path,
    ) -> t.Infra.RopeFile:

        relative_path = file_path.relative_to(root).as_posix()
        resource = rope_project.get_resource(relative_path)
        if not FlextInfraUtilitiesRopeRuntime.file_resource(resource):
            msg = f"expected a Rope file resource: {file_path}"
            raise TypeError(msg)
        return resource


__all__: list[str] = ["FlextInfraUtilitiesRopeClassMove"]
