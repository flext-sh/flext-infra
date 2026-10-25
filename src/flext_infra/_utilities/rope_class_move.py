"""Atomic, fail-fast Rope declaration relocation for ``u.Infra``.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
import keyword
from pathlib import Path

from flext_cli import u

from flext_infra import c, m, p, t
from flext_infra._utilities import (
    FlextInfraUtilitiesCodegenNamespace,
    FlextInfraUtilitiesRopeAnalysis,
    FlextInfraUtilitiesRopeCorePyModuleMixin,
    FlextInfraUtilitiesRopeImports,
    FlextInfraUtilitiesRopeModulePatch,
    FlextInfraUtilitiesRopeRuntime,
    FlextInfraUtilitiesRopeRuntimeModules,
)
from flext_infra._utilities._semantic_cutover import (
    FlextInfraUtilitiesSemanticNestingTypes,
)


class FlextInfraUtilitiesRopeClassMove:
    """Own identity-preserving class and module relocation through Rope."""

    @classmethod
    def plan_module_move(
        cls,
        rope_project: p.Infra.RopeProject,
        source_file: Path,
        destination_directory: Path | None = None,
        *,
        inputs: t.Pair[t.MappingKV[Path, str], tuple[m.Cli.AtomicFileState, ...]],
        destination_file: Path | None = None,
    ) -> tuple[m.Infra.CodegenFilePlan, ...]:
        """Plan a module relocation without creating its destination.

        Native class relocation supplies reference edits. Complete module metadata
        remains in the virtual destination; concrete create/delete effects belong
        to the existing codegen publisher, never to Rope's mutable filesystem.
        A directory retains the existing class-only contract. An explicit
        ``destination_file`` relocates the complete module, including functions,
        constants and type aliases, with native resource Rename and Move changes.

        Returns:
            Authenticated file plans for the declaration and its consumers.

        Raises:
            ValueError: If input identity or a native relocation proof differs.

        """
        sources = inputs[0]
        if destination_file is not None:
            if destination_directory is not None:
                msg = "module move requires exactly one destination"
                raise ValueError(msg)
            return cls._plan_module_resource_move(
                rope_project, source_file, destination_file, inputs
            )
        if destination_directory is None:
            msg = "module move requires a destination"
            raise ValueError(msg)
        root = Path(rope_project.root.real_path).resolve()
        source = cls._owned_path(root, root / source_file)
        target = cls._owned_path(root, root / destination_directory) / source.name
        if source == target:
            msg = f"module move source and target are identical: {source}"
            raise ValueError(msg)
        states = cls._module_input_states(source, inputs)
        request, target_plan, proposed, virtual, source_module_name = (
            cls._module_move_preparation(rope_project, source, target, sources, states)
        )
        return cls._module_file_plans(
            target_plan,
            source,
            cls._module_completed_changes(
                request, source_module_name, sources, proposed, virtual
            ),
            states,
        )

    @classmethod
    def _plan_module_resource_move(
        cls,
        project: p.Infra.RopeProject,
        source_file: Path,
        destination_file: Path,
        inputs: t.Pair[t.MappingKV[Path, str], tuple[m.Cli.AtomicFileState, ...]],
    ) -> tuple[m.Infra.CodegenFilePlan, ...]:
        """Compose native resource rename and move in lookup-only source views.

        Returns:
            Authenticated create, retire and reference file plans.

        Raises:
            ValueError: If paths or source identities are invalid or incomplete.

        """
        root = Path(project.root.real_path).resolve()
        source = cls._owned_path(root, root / source_file)
        target = cls._owned_path(root, root / destination_file)
        if source == target:
            msg = f"module move source and target are identical: {source}"
            raise ValueError(msg)
        cls._validate_module_resource_paths(root, source, target)
        return cls._module_resource_move_plans(project, root, (source, target), inputs)

    @staticmethod
    def _validate_module_resource_paths(root: Path, source: Path, target: Path) -> None:
        """Reject invalid module identifiers and occupied package parents.

        Raises:
            ValueError: If a path cannot identify a Python module.
            FileExistsError: If a parent is already a file module.

        """
        for path in (source, target):
            if path.suffix != ".py" or path.name == c.Infra.INIT_PY:
                msg = f"module resource move requires a Python file module: {path}"
                raise ValueError(msg)
            names = (*path.parent.relative_to(root).parts, path.stem)
            if any(
                not name.isidentifier() or keyword.iskeyword(name) for name in names
            ):
                msg = f"module resource move requires Python identifiers: {path}"
                raise ValueError(msg)
        for directory in target.parents:
            if directory == root:
                break
            module_file = directory.with_suffix(".py")
            if module_file.exists():
                raise FileExistsError(module_file)

    @classmethod
    def _module_resource_move_plans(
        cls,
        project: p.Infra.RopeProject,
        root: Path,
        paths: t.Pair[Path, Path],
        inputs: t.Pair[t.MappingKV[Path, str], tuple[m.Cli.AtomicFileState, ...]],
    ) -> tuple[m.Infra.CodegenFilePlan, ...]:
        """Compose native resource changes and publication plans.

        Returns:
            File plans for the destination, the retired source and consumers.

        Raises:
            ValueError: If the source inventory is incomplete.
            FileNotFoundError: If the source has no observed mode.
            FileExistsError: If an intermediate module is occupied.

        """
        source, target = paths
        sources = inputs[0]
        inventory = {
            Path(item.real_path).resolve() for item in project.get_python_files()
        }
        if not inventory.issubset(sources):
            msg = "module resource move requires the complete source inventory"
            raise ValueError(msg)
        states = cls._module_input_states(source, inputs, class_only=False)
        mode = states[source].mode
        if mode is None:
            raise FileNotFoundError(source)
        target_plan = cls._module_destination_plan(root, target, "", mode)
        if target.with_suffix("").exists():
            raise FileExistsError(target.with_suffix(""))
        candidate = dict(sources)
        virtual = [target_plan]
        initializer = target.parent / c.Infra.INIT_PY
        if initializer not in candidate:
            virtual.append(cls._module_destination_plan(root, initializer, "", mode))
        intermediate = cls._module_resource_relocation(
            project, paths, candidate, virtual, mode
        )
        changed = {
            path: text
            for path, text in candidate.items()
            if path == target or (path in sources and text != sources[path])
        }
        changed.pop(intermediate if intermediate != target else source, None)
        return cls._module_file_plans(target_plan, source, changed, states)

    @classmethod
    def _module_resource_relocation(
        cls,
        project: p.Infra.RopeProject,
        paths: t.Pair[Path, Path],
        candidate: t.MutableMappingKV[Path, str],
        virtual: list[m.Infra.CodegenFilePlan],
        mode: int,
    ) -> Path:
        """Compose lookup-only native Rename followed by native Move.

        Returns:
            The intermediate path.

        Raises:
            FileExistsError: If the intermediate name is occupied.

        """
        root = Path(project.root.real_path).resolve()
        source, target = paths
        intermediate = source.with_name(target.name)
        if intermediate != source:
            if intermediate.with_suffix("").exists():
                raise FileExistsError(intermediate.with_suffix(""))
            declaration = cls._module_destination_plan(root, intermediate, "", mode)
            if intermediate != target:
                virtual.append(declaration)
            native = FlextInfraUtilitiesRopeRuntimeModules.snapshot_project(
                project, candidate, declared_files=tuple(virtual)
            )
            try:
                changes = FlextInfraUtilitiesRopeRuntime.rename_changes(
                    native,
                    cls._resource(native, root, source),
                    None,
                    target.stem,
                    options=m.Infra.RopeRenameOptions(
                        resources=tuple(
                            cls._resource(native, root, path) for path in candidate
                        ),
                    ),
                )
                cls._module_resource_changes(changes, candidate, source, intermediate)
                cls._module_quoted_sources(
                    native,
                    candidate,
                    source,
                    intermediate,
                    declared_files=tuple(virtual),
                )
            finally:
                native.close()
        if intermediate.parent != target.parent:
            native = FlextInfraUtilitiesRopeRuntimeModules.snapshot_project(
                project, candidate, declared_files=tuple(virtual)
            )
            try:
                mover = FlextInfraUtilitiesRopeRuntime.create_move(
                    native, cls._resource(native, root, intermediate), None
                )
                changes = mover.get_changes(
                    native.get_resource(target.parent.relative_to(root).as_posix()),
                    resources=tuple(
                        cls._resource(native, root, path) for path in candidate
                    ),
                )
                cls._module_resource_changes(changes, candidate, intermediate, target)
                cls._module_quoted_sources(
                    native,
                    candidate,
                    intermediate,
                    target,
                    declared_files=tuple(virtual),
                )
            finally:
                native.close()
        return intermediate

    @classmethod
    def _module_quoted_sources(
        cls,
        project: p.Infra.RopeProject,
        candidate: t.MutableMappingKV[Path, str],
        source: Path,
        target: Path,
        *,
        declared_files: tuple[m.Infra.CodegenFilePlan, ...],
    ) -> None:
        """Rewire only quoted type prefixes with the native source module identity.

        Raises:
            ValueError: If native module election or a consumer binding conflicts.

        """
        root = Path(project.root.real_path).resolve()
        expected = FlextInfraUtilitiesRopeCorePyModuleMixin.resolve_pymodule(
            project, cls._resource(project, root, source)
        )
        resolved = project.find_module(expected.get_name())
        if resolved is None or Path(resolved.real_path).resolve() != source:
            msg = f"native module identity does not select its source file: {source}"
            raise ValueError(msg)
        destination = FlextInfraUtilitiesRopeCorePyModuleMixin.resolve_pymodule(
            project, cls._resource(project, root, target)
        ).get_name()
        resolved = project.find_module(destination)
        if resolved is None or Path(resolved.real_path).resolve() != target:
            msg = f"native module identity does not select its destination: {target}"
            raise ValueError(msg)
        runtime = FlextInfraUtilitiesRopeRuntimeModules

        checks: t.DictKV[Path, t.DictKV[tuple[int, str], int]] = {}
        composed = runtime.snapshot_project(
            project, candidate, declared_files=declared_files
        )
        try:
            destination_module = (
                FlextInfraUtilitiesRopeCorePyModuleMixin.resolve_pymodule(
                    composed, cls._resource(composed, root, target)
                )
            )

            for path, text in tuple(candidate.items()):
                # A quoted prefix resolves to the moved module object only through
                # a binding that names it (an import, a package attribute or an
                # export), and every such binding spells the module's stem; a
                # source without the stem holds no reference to rewrite or check.
                if path == source or source.stem not in text:
                    continue
                # Module and PyObject protocols expose the same native identities.
                rewritten, required = cls._module_quoted_consumer(
                    (project, composed),
                    (source, target, path),
                    text,
                    (id(expected), id(destination_module)),
                    destination,
                )
                candidate[path] = rewritten
                if required:
                    checks[path] = required
        finally:
            composed.close()
        verified = runtime.snapshot_project(
            project, candidate, declared_files=declared_files
        )
        try:
            relocated = FlextInfraUtilitiesRopeCorePyModuleMixin.resolve_pymodule(
                verified, cls._resource(verified, root, target)
            )

            for path, required in checks.items():
                cls._validate_module_quoted_consumer(
                    verified, path, candidate[path], required, id(relocated)
                )
        finally:
            verified.close()

    @staticmethod
    def _module_scopes(module: p.Infra.RopeParsedModule) -> list[p.Infra.RopeScope]:
        """Return native lexical scopes in stable breadth-first order.

        Returns:
            The module scope followed by its lexical children.

        """
        ordered: list[p.Infra.RopeScope] = [module.get_scope()]
        index = 0
        while index < len(ordered):
            ordered.extend(ordered[index].get_scopes())
            index += 1
        return ordered

    @classmethod
    def _module_quoted_consumer(
        cls,
        projects: t.Pair[p.Infra.RopeProject, p.Infra.RopeProject],
        paths: t.Triple[Path, Path, Path],
        text: str,
        identities: t.Pair[int, int],
        destination: str,
    ) -> t.Pair[str, t.DictKV[tuple[int, str], int]]:
        """Rewrite one consumer with callback state owned by this invocation.

        Returns:
            Rewritten text and the native identity checks it requires.

        """
        project, composed = projects
        source, target, path = paths
        root = Path(project.root.real_path).resolve()
        resource = cls._resource(composed, root, path)
        original = FlextInfraUtilitiesRopeCorePyModuleMixin.resolve_pymodule(
            project, cls._resource(project, root, source if path == target else path)
        )
        module = FlextInfraUtilitiesRopeCorePyModuleMixin.resolve_pymodule(
            composed, resource
        )
        cls._validate_module_quoted_scopes(
            cls._module_scopes(original),
            cls._module_scopes(module),
            paths,
            identities[0],
        )
        rewritten, required = cls._module_quoted_rewrite(
            composed, (original, module), text, paths, (identities, destination)
        )
        return cls._module_quoted_exports(
            original, text, rewritten, paths, identities[0]
        ), required

    @classmethod
    def _module_quoted_rewrite(
        cls,
        composed: p.Infra.RopeProject,
        modules: t.Pair[p.Infra.RopeParsedModule, p.Infra.RopeParsedModule],
        text: str,
        paths: t.Triple[Path, Path, Path],
        destination_info: t.Pair[t.Pair[int, int], str],
    ) -> t.Pair[str, t.DictKV[tuple[int, str], int]]:
        """Apply one consumer's quoted edits with invocation-local callback state.

        Returns:
            Rewritten source and native prefix checks.

        Raises:
            ValueError: If native import election changes during rewriting.

        """
        module = modules[1]
        identities, destination = destination_info
        resource = cls._resource(
            composed, Path(composed.root.real_path).resolve(), paths[2]
        )
        before_scopes = cls._module_scopes(modules[0])
        positions = {
            id(scope): index for index, scope in enumerate(cls._module_scopes(module))
        }
        required: t.DictKV[tuple[int, str], int] = {}
        binding: str | None = None

        def replacement(scope: p.Infra.RopeScope, expression: str) -> str | None:
            nonlocal binding
            index = positions[id(scope)]
            selected, elected, count = cls._module_quoted_reference(
                composed,
                module,
                (before_scopes[index], scope),
                expression,
                ((paths[0], paths[1]), identities, destination),
            )
            if count:
                required[index, selected if selected is not None else expression] = (
                    count
                )
            if elected is not None:
                if binding is not None and binding != elected:
                    msg = (
                        "quoted module move changed its native import binding: "
                        f"{paths[2]}"
                    )
                    raise ValueError(msg)
                binding = elected
            return selected

        runtime = FlextInfraUtilitiesRopeRuntimeModules
        rewritten = FlextInfraUtilitiesSemanticNestingTypes.rewrite_quoted_types(
            composed, resource, text, replacement
        )
        if binding is not None:
            rewritten, elected = runtime.import_binding(
                composed,
                runtime.build_string_module(composed, rewritten, resource=resource),
                destination,
                None,
            )
            if elected != binding:
                msg = (
                    f"quoted module move changed its native import binding: {paths[2]}"
                )
                raise ValueError(msg)
        return rewritten, required

    @staticmethod
    def _validate_module_quoted_scopes(
        before: t.SequenceOf[p.Infra.RopeScope],
        current: t.SequenceOf[p.Infra.RopeScope],
        paths: t.Triple[Path, Path, Path],
        expected: int,
    ) -> None:
        """Require unchanged lexical declarations and reject name capture.

        Raises:
            ValueError: If declarations change or the destination shadows a binding.

        """
        source, target, path = paths
        old_declarations = [
            (scope.get_kind(), scope.pyobject.get_name() if index else "")
            for index, scope in enumerate(before)
        ]
        declarations = [
            (scope.get_kind(), scope.pyobject.get_name() if index else "")
            for index, scope in enumerate(current)
        ]
        if old_declarations != declarations:
            msg = f"module relocation changed native annotation scopes: {path}"
            raise ValueError(msg)
        if source.stem == target.stem:
            return
        for scope in before:
            previous, occupied = scope.lookup(source.stem), scope.lookup(target.stem)
            if (
                previous is not None
                and id(previous.get_object()) == expected
                and occupied is not None
                and id(occupied.get_object()) != expected
            ):
                msg = (
                    f"module rename would capture a consumer binding: {path}:"
                    f"{target.stem}"
                )
                raise ValueError(msg)

    @classmethod
    def _module_quoted_reference(
        cls,
        project: p.Infra.RopeProject,
        module: p.Infra.RopeParsedModule,
        scopes: t.Pair[p.Infra.RopeScope, p.Infra.RopeScope],
        expression: str,
        destination_info: t.Triple[
            t.Pair[Path, Path],
            t.Pair[int, int],
            str,
        ],
    ) -> t.Triple[str | None, str | None, int]:
        """Resolve a quoted prefix by original and destination native identity.

        Returns:
            Replacement, required import binding and verified prefix length.

        """
        paths, identities, destination = destination_info
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        types = FlextInfraUtilitiesSemanticNestingTypes
        parts = expression.split(".")
        for count in range(1, len(parts) + 1):
            prefix = ".".join(parts[:count])
            old = runtime.expression_name(scopes[0], prefix)
            if old is None or id(old.get_object()) != identities[0]:
                continue
            current = runtime.expression_name(scopes[1], prefix)
            if current is not None and id(current.get_object()) == identities[1]:
                return None, None, count
            renamed = runtime.expression_name(scopes[1], paths[1].stem)
            if (
                count == 1
                and prefix == paths[0].stem
                and renamed is not None
                and id(renamed.get_object()) == identities[1]
            ):
                return (
                    types.checked_type_reference(
                        scopes[1], ".".join((paths[1].stem, *parts[count:]))
                    ),
                    None,
                    1,
                )
            elected = cls._module_quoted_import(
                project, module, destination, identities[1]
            )
            selected = types.checked_type_reference(
                scopes[1], ".".join((elected, *parts[count:]))
            )
            return selected, elected, len(elected.split("."))
        return None, None, 0

    @staticmethod
    def _module_quoted_import(
        project: p.Infra.RopeProject,
        module: p.Infra.RopeParsedModule,
        destination: str,
        destination_module: int,
    ) -> str:
        """Elect an import only when its native module and root stay unambiguous.

        Returns:
            The native import binding.

        Raises:
            ValueError: If the elected import would capture an occupied binding.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        imported, elected = runtime.import_binding(project, module, destination, None)
        resource = module.get_resource()
        imported_module = runtime.build_string_module(
            project, imported, resource=resource
        )
        root_name = elected.partition(".")[0]
        previous_root = runtime.expression_name(module.get_scope(), root_name)
        elected_root = runtime.expression_name(imported_module.get_scope(), root_name)
        elected_module = runtime.expression_name(imported_module.get_scope(), elected)
        if (
            elected_module is None
            or id(elected_module.get_object()) != destination_module
            or (
                previous_root is not None
                and not runtime.same_name(previous_root, elected_root)
            )
        ):
            path = resource.real_path if resource is not None else module.get_name()
            msg = f"occupied native quoted module destination: {path}:{elected}"
            raise ValueError(msg)
        return elected

    @staticmethod
    def _module_quoted_exports(
        original: p.Infra.RopeParsedModule,
        text: str,
        rewritten: str,
        paths: t.Triple[Path, Path, Path],
        expected: int,
    ) -> str:
        """Preserve explicit exports of the relocated native module.

        Returns:
            The text with an authenticated exported module name updated.

        """
        source, target, _path = paths
        exports = FlextInfraUtilitiesRopeAnalysis.public_export_names_source(text)
        published = original.get_scope().lookup(source.stem)
        if (
            source.stem != target.stem
            and source.stem in exports
            and published is not None
            and id(published.get_object()) == expected
        ):
            return FlextInfraUtilitiesRopeModulePatch.rewrite_all_declaration(
                rewritten,
                names=[
                    target.stem if name == source.stem else name for name in exports
                ],
            )
        return rewritten

    @classmethod
    def _validate_module_quoted_consumer(
        cls,
        project: p.Infra.RopeProject,
        path: Path,
        text: str,
        required: t.DictKV[tuple[int, str], int],
        relocated: int,
    ) -> None:
        """Verify every original quoted position in a single consumer invocation.

        Raises:
            ValueError: If any required quoted position or native identity is lost.

        """
        root = Path(project.root.real_path).resolve()
        resource = cls._resource(project, root, path)
        module = FlextInfraUtilitiesRopeCorePyModuleMixin.resolve_pymodule(
            project, resource
        )
        positions = {
            id(scope): index for index, scope in enumerate(cls._module_scopes(module))
        }
        seen: set[tuple[int, str]] = set()

        def validate(scope: p.Infra.RopeScope, expression: str) -> None:
            key = positions[id(scope)], expression
            count = required.get(key)
            if count is None:
                return
            actual = FlextInfraUtilitiesRopeRuntimeModules.expression_name(
                scope, ".".join(expression.split(".")[:count])
            )
            if actual is None or id(actual.get_object()) != relocated:
                msg = (
                    f"quoted module reference lost its native identity: {path}:"
                    f"{expression}"
                )
                raise ValueError(msg)
            seen.add(key)

        FlextInfraUtilitiesSemanticNestingTypes.quoted_type_edits(
            project, resource, text, validate
        )
        if seen != set(required):
            msg = f"module relocation lost original quoted type positions: {path}"
            raise ValueError(msg)

    @staticmethod
    def _module_resource_changes(
        changes: p.Infra.RopeChangeSet,
        candidate: t.MutableMappingKV[Path, str],
        source: Path,
        target: Path,
    ) -> None:
        """Require the native file effect and retain complete module contents.

        Raises:
            ValueError: If native effects disagree with the authenticated owners.
            TypeError: If Rope returns an unsupported effect.

        """
        moved = False
        for change in changes.changes:
            if isinstance(change, p.Infra.RopeChangeContents):
                path = Path(change.resource.real_path).resolve()
                if path not in candidate:
                    msg = f"module move escaped its source inventory: {path}"
                    raise ValueError(msg)
                candidate[path] = change.new_contents
            elif isinstance(change, p.Infra.RopeMoveResource):
                if (
                    moved
                    or change.resource.is_folder()
                    or Path(change.resource.real_path).resolve() != source
                    or Path(change.new_resource.real_path).resolve() != target
                ):
                    msg = "native module move disagrees with its exact destination"
                    raise ValueError(msg)
                moved = True
            else:
                msg = "module move produced an unsupported native effect"
                raise TypeError(msg)
        if not moved:
            msg = f"native Rope did not relocate the module: {source}"
            raise ValueError(msg)
        candidate[target] = candidate[source]
        candidate[source] = ""

    @classmethod
    def _module_move_preparation(
        cls,
        rope_project: p.Infra.RopeProject,
        source: Path,
        target: Path,
        sources: t.MappingKV[Path, str],
        states: t.MappingKV[Path, m.Cli.AtomicFileState],
    ) -> tuple[
        m.Infra.ClassMoveRequest,
        m.Infra.CodegenFilePlan,
        t.DictKV[Path, str],
        t.VariadicTuple[m.Infra.CodegenFilePlan],
        str,
    ]:
        canonical, source_module_name, reexports = cls._canonical_module_metadata(
            rope_project, source, sources
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
        mode = states[source].mode
        if mode is None:
            msg = f"module move source is absent: {source}"
            raise ValueError(msg)
        root = Path(rope_project.root.real_path).resolve()
        target_plan = cls._module_destination_plan(root, target, prelude, mode)
        # Package identity is needed by native Rope before any directory exists.
        # This lookup-only initializer is never returned for semantic publication:
        # the existing lazy-init phase owns the real generated file.
        initializer = target.parent / c.Infra.INIT_PY
        virtual = (
            (target_plan,)
            if initializer in sources
            else (
                target_plan,
                cls._module_destination_plan(root, initializer, "", mode),
            )
        )
        proposed = dict(sources)
        proposed[source] = canonical
        proposed[target] = prelude
        for plan in virtual[1:]:
            proposed[plan.path] = ""
        cls._module_reexport_sources(request, proposed, sources, virtual, reexports)
        return (
            request,
            target_plan,
            proposed,
            virtual,
            source_module_name,
        )

    @classmethod
    def _module_completed_changes(
        cls,
        request: m.Infra.ClassMoveRequest,
        source_module_name: str,
        sources: t.MappingKV[Path, str],
        proposed: t.MappingKV[Path, str],
        virtual: t.VariadicTuple[m.Infra.CodegenFilePlan],
    ) -> t.DictKV[Path, str]:
        changed = cls._module_reference_changes(request, sources, proposed, virtual)
        candidate = dict(proposed)
        candidate.update(changed)
        metadata_removed = cls._module_metadata_cleanup(
            request, source_module_name, candidate, virtual
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
    def _module_input_states(
        cls,
        source: Path,
        inputs: t.Pair[t.MappingKV[Path, str], tuple[m.Cli.AtomicFileState, ...]],
        *,
        class_only: bool = True,
    ) -> t.MappingKV[Path, m.Cli.AtomicFileState]:
        sources, source_states = inputs
        states = {state.path.resolve(): state for state in source_states}
        before = states.get(source)
        if before is None or source not in sources:
            msg = f"module move source is not among its inputs: {source}"
            raise ValueError(msg)
        if before.content is None or before.mode is None:
            msg = f"module move source is absent: {source}"
            raise ValueError(msg)
        for path, text in sources.items():
            state = states.get(path.resolve())
            if state is None or state.content is None:
                msg = f"module move input has no observed state: {path}"
                raise ValueError(msg)
            if state.content.decode(c.DEFAULT_ENCODING) != text:
                msg = f"module move input disagrees with its observed state: {path}"
                raise ValueError(msg)
        if class_only:
            cls._module_class_declaration(sources[source], source)
        return states

    @classmethod
    def _canonical_module_metadata(
        cls,
        rope_project: p.Infra.RopeProject,
        source: Path,
        sources: t.MappingKV[Path, str],
    ) -> t.Triple[str, str, t.VariadicTuple[str]]:
        root = Path(rope_project.root.real_path).resolve()
        original = FlextInfraUtilitiesRopeRuntimeModules.snapshot_project(
            rope_project, sources
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
        sources: t.MappingKV[Path, str],
        virtual: t.VariadicTuple[m.Infra.CodegenFilePlan],
        reexports: t.VariadicTuple[str],
    ) -> None:
        root = Path(request.rope_project.root.real_path).resolve()
        virtual_paths = {plan.path for plan in virtual}
        for origin in reexports:
            package_plan = FlextInfraUtilitiesRopeRuntimeModules.snapshot_project(
                request.rope_project,
                proposed,
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
                        or sources[path].startswith(c.Infra.AUTOGEN_HEADER)
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
        virtual: t.VariadicTuple[m.Infra.CodegenFilePlan],
    ) -> t.DictKV[Path, str]:
        planned = FlextInfraUtilitiesRopeRuntimeModules.snapshot_project(
            request.rope_project,
            proposed,
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
        virtual: t.VariadicTuple[m.Infra.CodegenFilePlan],
    ) -> str | None:
        root = Path(request.rope_project.root.real_path).resolve()
        metadata_project = FlextInfraUtilitiesRopeRuntimeModules.snapshot_project(
            request.rope_project,
            candidate,
            declared_files=virtual,
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
        changed: t.MappingKV[Path, str],
        states: t.MappingKV[Path, m.Cli.AtomicFileState],
    ) -> t.VariadicTuple[m.Infra.CodegenFilePlan]:
        root, target = target_plan.project, target_plan.path
        files = [
            m.Infra.CodegenFilePlan(
                project=root,
                path=target,
                before=target_plan.before,
                desired_content=changed[target].encode(c.DEFAULT_ENCODING),
                desired_mode=target_plan.desired_mode,
            ),
            m.Infra.CodegenFilePlan(
                project=root,
                path=source,
                before=states[source],
                desired_content=None,
                desired_mode=None,
            ),
        ]
        for path, content in changed.items():
            if path in {source, target}:
                continue
            state = states.get(path)
            if state is None or state.mode is None:
                msg = f"module move consumer has no observed state: {path}"
                raise ValueError(msg)
            if state.content is not None and state.content.decode(
                c.DEFAULT_ENCODING,
            ).startswith(c.Infra.AUTOGEN_HEADER):
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
            if isinstance(node, c.Infra.AST_IMPORT_OR_CLASS_TYPES):
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
    ) -> m.Infra.CodegenFilePlan:
        """Plan an absent destination file; publication creates its parents.

        Returns:
            The plan for the absent destination.

        Raises:
            FileExistsError: If the destination already has file content.

        """
        before = u.Cli.atomic_read_binary_file_state(target, required=False).unwrap()
        if before.content is not None:
            raise FileExistsError(target)
        return m.Infra.CodegenFilePlan(
            project=root,
            path=target,
            before=before,
            desired_content=source.encode(c.DEFAULT_ENCODING),
            desired_mode=mode,
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
        module_stem = cls.class_module_stem(class_name).lstrip("_")
        if family:
            family_dir = FlextInfraUtilitiesCodegenNamespace.facade_families()[
                family
            ].directory
            return package_dir / family_dir / f"{module_stem}.py"
        return source_file.parent / f"{source_file.stem}_{module_stem}.py".lstrip("_")

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
