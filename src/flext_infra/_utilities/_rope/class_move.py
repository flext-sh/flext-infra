"""Atomic, fail-fast Rope declaration relocation for ``u.Infra``.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
import hashlib
import keyword
import re
from collections.abc import Mapping, MutableMapping
from pathlib import Path
from types import MappingProxyType
from typing import Final

from flext_cli import u

from flext_infra import c, m, p, r, t
from flext_infra._utilities import (
    FlextInfraUtilitiesCodegenFilePlan,
    FlextInfraUtilitiesCodegenNamespace,
    FlextInfraUtilitiesProjectDiscovery,
    FlextInfraUtilitiesProtectedEditLinting,
    FlextInfraUtilitiesWorkspaceSnapshot,
)
from flext_infra._utilities._rope import (
    FlextInfraUtilitiesRopeAnalysis,
    FlextInfraUtilitiesRopeCorePyModule,
    FlextInfraUtilitiesRopeImports,
    FlextInfraUtilitiesRopeModulePatch,
    FlextInfraUtilitiesRopeMovePublication,
    FlextInfraUtilitiesRopeRuntime,
    FlextInfraUtilitiesRopeRuntimeModules,
)
from flext_infra._utilities._semantic_cutover import (
    FlextInfraUtilitiesTypesSemanticNesting,
)


class FlextInfraUtilitiesRopeClassMove(FlextInfraUtilitiesRopeMovePublication):
    """Own identity-preserving class and module relocation through Rope."""

    class NativeSourceView:
        """Authenticate native candidate text against original publication witnesses.

        The same view owns source admission and output-plan construction, retaining
        unpublished candidate modes without replacing their physical before states.
        """

        def __init__(
            self,
            sources: Mapping[Path, str],
            states: tuple[p.Cli.AtomicFileState, ...],
            *,
            declared_files: tuple[p.Infra.CodegenFilePlan, ...] = (),
        ) -> None:
            self.sources: Final = sources
            self.states: Final = MappingProxyType({
                state.path.resolve(): state for state in states
            })
            self.declared: Final = MappingProxyType({
                plan.path: plan for plan in declared_files
            })

        def authenticate(self, source: Path) -> Mapping[Path, p.Cli.AtomicFileState]:
            """Require candidate text and witnesses to describe the same source view.

            Returns:
                The original physical witnesses, never candidate replacement states.

            Raises:
                ValueError: A source, candidate or observed witness disagrees.

            """
            before = self.states.get(source)
            if before is None or source not in self.sources:
                resolved = source.resolve()
                mismatched = sum(
                    1 for path in self.sources if path.resolve() not in self.states
                )
                msg = f"module move source is not among its inputs: {source}"
                raise ValueError(
                    msg,
                    {
                        "sources": len(self.sources),
                        "states": len(self.states),
                        "declared": len(self.declared),
                        "resolved": str(resolved),
                        "resolved_in_sources": resolved in self.sources,
                        "resolved_in_states": resolved in self.states,
                        "sources_outside_states": mismatched,
                    },
                ) from None
            if source not in self.declared and (
                before.content is None or before.mode is None
            ):
                msg = f"module move source is absent: {source}"
                raise ValueError(msg)
            for path, text in self.sources.items():
                state = self.states.get(path.resolve())
                if state is None:
                    msg = f"module move input has no observed state: {path}"
                    raise ValueError(msg)
                candidate = self.declared.get(path)
                if candidate is not None and candidate.before != state:
                    msg = (
                        "module move candidate has a conflicting source witness: "
                        f"{path}"
                    )
                    raise ValueError(msg)
                content = (
                    candidate.desired_content
                    if candidate is not None
                    else state.content
                )
                if content is None or content.decode(c.DEFAULT_ENCODING) != text:
                    msg = f"module move input disagrees with its observed state: {path}"
                    raise ValueError(msg)
            return self.states

        def file_plans(
            self,
            target_plan: p.Infra.CodegenFilePlan,
            source: Path,
            changed: Mapping[Path, str],
            *,
            resource_move: bool = False,
        ) -> tuple[p.Infra.CodegenFilePlan, ...]:
            """Build create/retire/consumer effects from the authenticated witnesses.

            Returns:
                File plans retaining original before states and candidate modes.

            Raises:
                ValueError: A consumer lacks a witness or requires joint generation.

            """
            root, target = target_plan.project, target_plan.path
            declared_source = self.declared.get(source)
            origin = (
                declared_source.move_source
                if declared_source is not None
                and declared_source.move_source is not None
                else source
            )
            original = (
                self.declared[origin].before
                if origin in self.declared
                else self.states[origin]
            )
            files = [
                m.Infra.CodegenFilePlan(
                    project=root,
                    path=target,
                    before=target_plan.before,
                    desired_content=changed[target].encode(c.DEFAULT_ENCODING),
                    desired_mode=target_plan.desired_mode,
                    move_source=origin if original.content is not None else None,
                    inputs=(original,),
                ),
                m.Infra.CodegenFilePlan(
                    project=root,
                    path=source,
                    before=self.states[source],
                    desired_content=None,
                    desired_mode=None,
                ),
            ]
            for path, content in changed.items():
                if path in {source, target}:
                    continue
                state = self.states.get(path)
                candidate = self.declared.get(path)
                mode = (
                    candidate.desired_mode
                    if candidate is not None
                    else (state.mode if state is not None else None)
                )
                if state is None or mode is None:
                    msg = f"module move consumer has no observed state: {path}"
                    raise ValueError(msg)
                if (
                    not resource_move
                    and state.content is not None
                    and state.content.decode(c.DEFAULT_ENCODING).startswith(
                        c.Infra.AUTOGEN_HEADER
                    )
                ):
                    if path.name != c.Infra.INIT_PY:
                        msg = f"module move requires joint facade projection: {path}"
                        raise ValueError(msg)
                    continue
                files.append(
                    m.Infra.CodegenFilePlan(
                        project=root,
                        path=path,
                        before=state,
                        desired_content=content.encode(c.DEFAULT_ENCODING),
                        desired_mode=mode,
                    )
                )
            return tuple(files)

    @classmethod
    def plan_module_move(
        cls,
        rope_project: p.Infra.RopeProject,
        source_file: Path,
        destination_directory: Path | None = None,
        *,
        inputs: NativeSourceView
        | tuple[Mapping[Path, str], tuple[p.Cli.AtomicFileState, ...]],
        destination_file: Path | None = None,
    ) -> p.Result[tuple[p.Infra.CodegenFilePlan, ...]]:
        """Plan a module relocation without creating its destination.

        Native class relocation supplies reference edits. Complete module metadata
        remains in the virtual destination; concrete create/delete effects belong
        to the existing codegen publisher, never to Rope's mutable filesystem.
        A directory retains the existing class-only contract. An explicit
        ``destination_file`` relocates the complete module, including functions,
        constants and type aliases, with native resource Rename and Move changes.
        A ``NativeSourceView`` authenticates an existing candidate cohort against
        original physical witnesses, including unpublished new consumers.

        Returns:
            Authenticated file plans, or the original typed admission refusal.

        """
        view = (
            inputs
            if isinstance(inputs, cls.NativeSourceView)
            else cls.NativeSourceView(*inputs)
        )
        if destination_file is not None:
            if destination_directory is not None:
                return r[tuple[p.Infra.CodegenFilePlan, ...]].fail(
                    "module move requires exactly one destination"
                )
            return cls._plan_module_resource_move(
                rope_project,
                source_file,
                destination_file,
                view,
            )
        if view.declared:
            return r[tuple[p.Infra.CodegenFilePlan, ...]].fail(
                "candidate sources require an exact module resource move"
            )
        if destination_directory is None:
            return r[tuple[p.Infra.CodegenFilePlan, ...]].fail(
                "module move requires a destination"
            )
        return cls._plan_module_class_move(
            rope_project, source_file, destination_directory, view
        )

    @classmethod
    def _plan_module_class_move(
        cls,
        rope_project: p.Infra.RopeProject,
        source_file: Path,
        destination_directory: Path,
        view: NativeSourceView,
    ) -> p.Result[tuple[p.Infra.CodegenFilePlan, ...]]:
        """Plan the class-only module relocation into a destination directory.

        Returns:
            Authenticated file plans, or the original typed admission refusal.

        """
        sources = view.sources
        root = Path(rope_project.root.real_path).resolve()
        source = cls._owned_path(root, root / source_file)
        target = cls._owned_path(root, root / destination_directory) / source.name
        if source == target:
            return r[tuple[p.Infra.CodegenFilePlan, ...]].fail(
                f"module move source and target are identical: {source}"
            )
        states = view.authenticate(source)
        cls._module_class_declaration(sources[source], source)
        prepared = cls._module_move_preparation(
            rope_project, source, target, sources, states
        )
        if prepared.failure:
            return r[tuple[p.Infra.CodegenFilePlan, ...]].from_failure(prepared)
        request, target_plan, proposed, virtual, source_module_name = prepared.value
        return r[tuple[p.Infra.CodegenFilePlan, ...]].ok(
            view.file_plans(
                target_plan,
                source,
                cls._module_completed_changes(
                    request, source_module_name, sources, proposed, virtual
                ),
            )
        )

    @classmethod
    def _plan_module_resource_move(
        cls,
        project: p.Infra.RopeProject,
        source_file: Path,
        destination_file: Path,
        view: NativeSourceView,
    ) -> p.Result[tuple[p.Infra.CodegenFilePlan, ...]]:
        """Compose native resource rename and move in lookup-only source views.

        Returns:
            Authenticated create, retire and reference file plans.

        """
        root = Path(project.root.real_path).resolve()
        source = cls._owned_path(root, root / source_file)
        target = cls._owned_path(root, root / destination_file)
        if source == target:
            return r[tuple[p.Infra.CodegenFilePlan, ...]].fail(
                f"module move source and target are identical: {source}"
            )
        validation = cls._validate_module_resource_paths(root, source, target)
        if validation.failure:
            return r[tuple[p.Infra.CodegenFilePlan, ...]].from_failure(validation)
        return cls._module_resource_move_plans(project, root, (source, target), view)

    @staticmethod
    def _validate_module_resource_paths(
        root: Path, source: Path, target: Path
    ) -> p.Result[bool]:
        """Reject invalid module identifiers and occupied package parents.

        Returns:
            Successful admission or the invalid path/occupied-parent refusal.

        """
        for path in (source, target):
            if path.suffix != ".py" or path.name == c.Infra.INIT_PY:
                return r[bool].fail(
                    f"module resource move requires a Python file module: {path}"
                )
            names = (*path.parent.relative_to(root).parts, path.stem)
            if any(
                not name.isidentifier() or keyword.iskeyword(name) for name in names
            ):
                return r[bool].fail(
                    f"module resource move requires Python identifiers: {path}"
                )
        for directory in target.parents:
            if directory == root:
                break
            module_file = directory.with_suffix(".py")
            if module_file.exists():
                return r[bool].fail(f"module parent is occupied: {module_file}")
        return r[bool].ok(value=True)

    @classmethod
    def _module_resource_move_plans(
        cls,
        project: p.Infra.RopeProject,
        root: Path,
        paths: tuple[Path, Path],
        view: NativeSourceView,
    ) -> p.Result[tuple[p.Infra.CodegenFilePlan, ...]]:
        """Compose native resource changes and publication plans.

        Returns:
            File plans for the destination, the retired source and consumers.

        """
        source, target = paths
        sources = view.sources
        inventory = {
            Path(item.real_path).resolve() for item in project.get_python_files()
        }
        if not inventory.issubset(sources):
            return r[tuple[p.Infra.CodegenFilePlan, ...]].fail(
                "module resource move requires the complete source inventory"
            )
        declared = view.declared
        states = view.authenticate(source)
        mode = (
            declared[source].desired_mode if source in declared else states[source].mode
        )
        if mode is None:
            return r[tuple[p.Infra.CodegenFilePlan, ...]].fail(
                f"module source has no observed mode: {source}"
            )
        target_plan = cls._module_destination_plan(root, target, "", mode)
        if target.with_suffix("").exists():
            return r[tuple[p.Infra.CodegenFilePlan, ...]].fail(
                f"module destination is occupied: {target.with_suffix('')}"
            )
        candidate = dict(sources)
        virtual = [target_plan]
        initializer = target.parent / c.Infra.INIT_PY
        if initializer not in candidate:
            virtual.append(cls._module_destination_plan(root, initializer, "", mode))
        published = cls._module_published_exports(project, root, source)
        intermediate = cls._module_resource_relocation(
            project, paths, candidate, virtual, mode
        )
        if intermediate.failure:
            return r[tuple[p.Infra.CodegenFilePlan, ...]].from_failure(intermediate)
        rewired = cls._module_barrel_consumers(
            project, (source, target), candidate, published
        )
        if rewired.failure:
            return r[tuple[p.Infra.CodegenFilePlan, ...]].from_failure(rewired)
        changed = {
            path: text
            for path, text in candidate.items()
            if path == target or (path in sources and text != sources[path])
        }
        changed.pop(
            intermediate.value if intermediate.value != target else source, None
        )
        return r[tuple[p.Infra.CodegenFilePlan, ...]].ok(
            view.file_plans(
                target_plan,
                source,
                changed,
                resource_move=True,
            )
        )

    @classmethod
    def _module_published_exports(
        cls, project: p.Infra.RopeProject, root: Path, source: Path
    ) -> tuple[str, frozenset[str]]:
        """Read the moved module's identity and public exports before the move.

        Returns:
            The moved module name and the names it publishes.

        """
        moved = cls._elected_move_module(project, root, source, role="source")
        return (
            moved.get_name(),
            frozenset(
                FlextInfraUtilitiesRopeAnalysis.public_export_names_source(moved)
            ),
        )

    @classmethod
    def _module_barrel_consumers(
        cls,
        project: p.Infra.RopeProject,
        paths: tuple[Path, Path],
        candidate: MutableMapping[Path, str],
        published: tuple[str, frozenset[str]],
    ) -> p.Result[bool]:
        """Rewire consumers that import a moved class through a package barrel.

        Every ``from barrel import Name`` of a moved export is retargeted to the
        nearest package that publishes it: the destination package, whose
        initializer the same ``make mod`` candidate regenerates (the semantic
        publication joins the planned lazy inits). Importing the package, never
        its leaf module, keeps a layer-zero consumer on a lazy barrel. A
        consumer importing the barrel module itself cannot be proved and
        refuses the move. Initializers are owned by the publication rewrite and
        their regeneration.

        Returns:
            True, or the first consumer whose barrel route cannot be rewired.

        """
        source, target = paths
        module_name, exports = published
        parts = module_name.split(".")
        root = Path(project.root.real_path).resolve()
        destination_package = FlextInfraUtilitiesProjectDiscovery.package_name_for_dir(
            target.parent, project_root=root, source_project=project
        )
        # Every package in the chain from the top-level package down to the
        # moved module may republish its exports; none of them is regenerated
        # yet in this candidate, so each barrel route is retargeted.
        barrels = frozenset(".".join(parts[:index]) for index in range(1, len(parts)))
        if not exports or not barrels:
            return r[bool].ok(value=True)
        if not destination_package:
            return r[bool].fail(
                f"module move destination has no import package: {target}"
            )
        # The destination package is the nearest owner that publishes the
        # moved exports once this candidate's initializers are regenerated.
        route = destination_package
        for path, text in tuple(candidate.items()):
            if (
                path in {source, target}
                or not any(name in text for name in exports)
                or not any(barrel in text for barrel in barrels)
            ):
                continue
            if path.name == c.Infra.INIT_PY:
                # Initializer publications are rewritten by
                # ``_rewritten_init_publications`` and regenerated from children.
                continue
            rewritten = cls._barrel_consumer_text(
                project, (root, path), text, (barrels, exports, route)
            )
            if rewritten.failure:
                return r[bool].from_failure(rewritten)
            candidate[path] = rewritten.value
        return r[bool].ok(value=True)

    @classmethod
    def _barrel_consumer_text(
        cls,
        project: p.Infra.RopeProject,
        location: tuple[Path, Path],
        text: str,
        route: tuple[frozenset[str], frozenset[str], str],
    ) -> p.Result[str]:
        """Retarget one consumer's barrel imports of moved exports.

        Returns:
            The consumer text, retargeted when it imported a moved export from
            a barrel, or the barrel attribute route the move cannot prove.

        """
        root, path = location
        barrels, exports, destination_package = route
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        imports = runtime.module_imports_for_pymodule(
            project,
            runtime.build_string_module(
                project, text, resource=cls._resource(project, root, path)
            ),
        )
        retargeted: list[tuple[str, str | None]] = []
        for statement in imports.imports:
            info = statement.import_info
            if isinstance(info, p.Infra.RopeNormalImport) and any(
                name in barrels for name, _alias in info.names_and_aliases
            ):
                return r[str].fail(
                    f"module move cannot prove a barrel attribute consumer: {path}"
                )
            if not (
                isinstance(info, p.Infra.RopeFromImport)
                and info.level == 0
                and info.module_name in barrels
            ):
                continue
            moved = [item for item in info.names_and_aliases if item[0] in exports]
            if moved:
                retargeted.extend(moved)
                statement.import_info = runtime.from_import(
                    info.module_name,
                    0,
                    tuple(
                        item
                        for item in info.names_and_aliases
                        if item[0] not in exports
                    ),
                )
        if not retargeted:
            return r[str].ok(text)
        imports.add_import(
            runtime.from_import(destination_package, 0, tuple(retargeted))
        )
        return r[str].ok(imports.get_changed_source())

    @classmethod
    def _module_resource_relocation(
        cls,
        project: p.Infra.RopeProject,
        paths: tuple[Path, Path],
        candidate: MutableMapping[Path, str],
        virtual: list[p.Infra.CodegenFilePlan],
        mode: int,
    ) -> p.Result[Path]:
        """Compose lookup-only native Rename followed by native Move.

        Returns:
            The intermediate path, or an admission/publication refusal.

        """
        root = Path(project.root.real_path).resolve()
        source, target = paths
        intermediate = source.with_name(target.name)
        if intermediate != source:
            if intermediate.with_suffix("").exists():
                return r[Path].fail(
                    f"module intermediate is occupied: {intermediate.with_suffix('')}"
                )
            declaration = cls._module_destination_plan(root, intermediate, "", mode)
            if intermediate != target:
                virtual.append(declaration)
            native = FlextInfraUtilitiesRopeRuntimeModules.snapshot_project(
                project, candidate, declared_files=tuple(virtual)
            )
            try:
                cls._validate_module_rename_capture(
                    native, root, (source, intermediate), candidate
                )
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
                quoted = cls._module_quoted_sources(
                    native,
                    candidate,
                    source,
                    intermediate,
                    declared_files=tuple(virtual),
                )
                if quoted.failure:
                    return r[Path].from_failure(quoted)
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
                    native.get_folder(target.parent.relative_to(root).as_posix()),
                    resources=tuple(
                        cls._resource(native, root, path) for path in candidate
                    ),
                )
                cls._module_resource_changes(changes, candidate, intermediate, target)
                quoted = cls._module_quoted_sources(
                    native,
                    candidate,
                    intermediate,
                    target,
                    declared_files=tuple(virtual),
                )
                if quoted.failure:
                    return r[Path].from_failure(quoted)
            finally:
                native.close()
        return r[Path].ok(intermediate)

    @classmethod
    def _validate_module_rename_capture(
        cls,
        project: p.Infra.RopeProject,
        root: Path,
        paths: tuple[Path, Path],
        consumers: Mapping[Path, str],
    ) -> None:
        """Reject a module rename whose new stem a consumer already binds.

        Consumer scopes are read in the pre-rename basis that elects the moved
        module: once the rename is applied the old stem binding is gone, so
        only this basis proves that the new stem would capture another object.
        A consumer without the old stem holds no binding of the module.

        Raises:
            ValueError: If a consumer scope binding the module also binds the
                new stem to another object.

        """
        source, target = paths
        expected = id(cls._elected_move_module(project, root, source, role="source"))
        for path, text in consumers.items():
            if path == source or not cls._binds_name(text, source.stem):
                continue
            module = FlextInfraUtilitiesRopeCorePyModule.resolve_pymodule(
                project, cls._resource(project, root, path)
            )
            for scope in cls._module_scopes(module).values():
                previous = scope.lookup(source.stem)
                occupied = scope.lookup(target.stem)
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

    @staticmethod
    def _rewritten_init_publications(
        composed: p.Infra.RopeProject,
        root: Path,
        path: Path,
        *,
        route: tuple[
            p.Infra.RopeSemanticModule,
            str,
            Path,
            MutableMapping[Path, str],
        ],
    ) -> p.Result[str]:
        """Keep initializer publications in the same native move candidate.

        Args:
            composed: The staged candidate project being planned.
            root: Absolute repository root of the staged view.
            path: Consumer ``__init__`` path inside the staged view.
            route: Expected source module, destination identity, destination
                file path and the staged candidate text map.

        Returns:
            The rewritten initializer text.

        """
        expected, destination, target, candidate = route
        consumer = FlextInfraUtilitiesRopeCorePyModule.resolve_pymodule(
            composed,
            FlextInfraUtilitiesRopeClassMove._resource(composed, root, path),
        )
        destination_module = FlextInfraUtilitiesRopeCorePyModule.resolve_pymodule(
            composed,
            FlextInfraUtilitiesRopeClassMove._resource(composed, root, target),
        )
        package = consumer.get_name().removesuffix(".__init__")
        return FlextInfraUtilitiesRopeClassMove.rewrite_module_move_publications(
            consumer,
            package=package,
            moves={expected.get_name(): destination},
            exports={
                destination: frozenset(
                    FlextInfraUtilitiesRopeAnalysis.public_export_names_source(
                        destination_module
                    )
                )
            }
            if target in candidate
            else {},
        )

    @staticmethod
    def _elected_move_module(
        project: p.Infra.RopeProject,
        root: Path,
        path: Path,
        *,
        role: str,
    ) -> p.Infra.RopeSourceModule:
        """Elect one move endpoint through its native module identity.

        Returns:
            The elected source module at ``path``.

        Raises:
            ValueError: The native module identity does not select the endpoint.

        """
        elected = FlextInfraUtilitiesRopeCorePyModule.resolve_pymodule(
            project, FlextInfraUtilitiesRopeClassMove._resource(project, root, path)
        )
        resolved = project.find_module(elected.get_name())
        if resolved is None or Path(resolved.real_path).resolve() != path:
            msg = f"native module identity does not select its {role} file: {path}"
            raise ValueError(msg)
        return elected

    @classmethod
    def _module_quoted_sources(
        cls,
        project: p.Infra.RopeProject,
        candidate: MutableMapping[Path, str],
        source: Path,
        target: Path,
        *,
        declared_files: tuple[p.Infra.CodegenFilePlan, ...],
    ) -> p.Result[bool]:
        """Rewire quoted type prefixes through the class-bound native move owner.

        Initializer publication changes become the input of quoted-reference
        changes, so neither effect overwrites the other. Only explicit candidate
        retirements omit a consumer; an unexpectedly missing source retains the
        native resource exception.

        Args:
            project: The Rope project instance.
            candidate: A mapping of file paths to their current content.
            source: The path of the source file being moved.
            target: The path of the target file being moved to.
            declared_files: A tuple of codegen file plans that have been declared.

        Returns:
            Successful admission once every quoted consumer is verified.

        """
        root = Path(project.root.real_path).resolve()
        expected = cls._elected_move_module(project, root, source, role="source")
        destination = cls._elected_move_module(
            project, root, target, role="destination"
        ).get_name()
        runtime = FlextInfraUtilitiesRopeRuntimeModules

        checks: dict[Path, dict[tuple[t.StrTuple, str], int]] = {}
        composed = runtime.snapshot_project(
            project, candidate, declared_files=declared_files
        )
        try:
            destination_module = FlextInfraUtilitiesRopeCorePyModule.resolve_pymodule(
                composed, cls._resource(composed, root, target)
            )
            retired = frozenset(
                plan.path
                for plan in composed.source_plans
                if plan.desired_content is None
            )

            for path, epoch_text in tuple(candidate.items()):
                # A sibling staged plan may have advanced this consumer after
                # the candidate epoch was captured; the composed project's
                # current bytes are the authoritative pre-move text, and the
                # stale copy would mis-describe the scope baseline.
                # Only a manifested retirement removes a consumer from this
                # candidate. Other missing resources retain their native error.
                if path in retired:
                    continue
                # The overlay's bytes are the staged text; parsing every module
                # only to read them back would build each consumer's AST.
                staged_text = composed.source_text(path)
                authoritative = staged_text if staged_text != epoch_text else epoch_text
                consumer_text = cls._divergence_diagnostic(project, path, authoritative)
                if path.name == c.Infra.INIT_PY and path != source:
                    publication = cls._rewritten_init_publications(
                        composed,
                        root,
                        path,
                        route=(expected, destination, target, candidate),
                    )
                    if publication.failure:
                        return r[bool].from_failure(publication)
                    consumer_text = publication.value
                    candidate[path] = consumer_text
                # A quoted prefix resolves to the moved module object only through
                # a binding that names it (an import, a package attribute or an
                # export), and every such binding spells the module's stem; a
                # source without the stem inside a literal holds no quoted type
                # or export to rewrite or check.
                if path == source or not cls._quoted_stem_reference(
                    consumer_text, source.stem
                ):
                    continue
                # Module and PyObject protocols expose the same native identities.
                rewritten, required = cls._module_quoted_consumer(
                    (project, composed),
                    (source, target, path),
                    consumer_text,
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
            relocated = FlextInfraUtilitiesRopeCorePyModule.resolve_pymodule(
                verified, cls._resource(verified, root, target)
            )

            for path, required in checks.items():
                cls._validate_module_quoted_consumer(
                    verified, path, candidate[path], required, id(relocated)
                )
        finally:
            verified.close()
        return r[bool].ok(value=True)

    @staticmethod
    def _binds_name(text: str, name: str) -> bool:
        """Whether a consumer declares any binding site for one name.

        A scope lookup can only return a binding the source declares: an
        unaliased import of the name, a star import, an assignment, loop,
        ``with``, ``except`` or ``match`` target, a parameter, or a function or
        class of that name. A consumer without such a site cannot bind the module.

        Returns:
            Whether any binding site of the name exists in the source.

        """
        return name in text and any(
            not FlextInfraUtilitiesRopeClassMove._node_bound_names(node).isdisjoint({
                name,
                "*",
            })
            for node in ast.walk(ast.parse(text))
        )

    @staticmethod
    def _node_bound_names(node: ast.AST) -> frozenset[str]:
        """Name every binding one syntax node declares.

        Returns:
            The bound names, with ``*`` for a star import.

        """
        match node:
            case ast.Import(names=aliases) | ast.ImportFrom(names=aliases):
                names = frozenset(
                    alias.asname or alias.name.partition(".")[0] for alias in aliases
                )
            case ast.Name(id=identifier, ctx=ast.Store()) | ast.arg(arg=identifier):
                names = frozenset({identifier})
            case (
                ast.FunctionDef(name=identifier)
                | ast.AsyncFunctionDef(name=identifier)
                | ast.ClassDef(name=identifier)
            ):
                names = frozenset({identifier})
            case (
                ast.ExceptHandler(name=str() as identifier)
                | ast.MatchAs(name=str() as identifier)
                | ast.MatchStar(name=str() as identifier)
                | ast.MatchMapping(rest=str() as identifier)
            ):
                names = frozenset({identifier})
            case _:
                names = frozenset()
        return names

    @staticmethod
    def _quoted_stem_reference(text: str, stem: str) -> bool:
        """Whether a source can hold a quoted type or export of the moved module.

        The quoted rewrite edits only string constants in annotation positions
        (``quoted_type_regions``) and ``__all__`` exports. A quoted type reaches
        the module through an attribute read (``stem.Name``, or an import alias
        of the module such as ``rt.Name``); an export spells the stem as a
        whole literal, which Rope's native lexer delimits. Prose literals and
        non-annotation strings can never be rewritten.

        Returns:
            Whether an annotation string or an export literal names the module.

        """
        if stem not in text:
            return False
        stem_word = re.escape(stem)
        names = "|".join(
            re.escape(name)
            for name in (
                stem,
                *re.findall(rf"(?<![A-Za-z0-9_]){stem_word}\s+as\s+(\w+)", text),
            )
        )
        quoted = re.compile(rf"(?<![A-Za-z0-9_])(?:{names})\.[A-Za-z_]")
        exported = re.compile(rf"^[rRbBuU]?(['\"]){stem_word}\1$")
        lexer = FlextInfraUtilitiesRopeRuntime.ignored_regions
        return (
            re.search(rf"['\"]{stem_word}['\"]", text) is not None
            and any(
                text[first] != "#" and exported.search(text[first:last]) is not None
                for first, last, _metadata in lexer(text)
            )
        ) or (
            quoted.search(text) is not None
            and any(
                isinstance(node, ast.Constant)
                and isinstance(node.value, str)
                and quoted.search(node.value) is not None
                for annotation in FlextInfraUtilitiesRopeClassMove._annotation_nodes(
                    ast.parse(text)
                )
                for node in ast.walk(annotation)
            )
        )

    @staticmethod
    def _annotation_nodes(tree: ast.Module) -> tuple[ast.expr, ...]:
        """Collect the annotation-position expressions of one module.

        Mirrors the native annotation regions: variable and parameter
        annotations, return annotations, class bases and keywords, ``type``
        alias values, and type-parameter bounds and defaults.

        Returns:
            Every annotation-position expression in the module.

        """
        found: list[ast.expr | None] = []
        for node in ast.walk(tree):
            match node:
                case (
                    ast.AnnAssign(annotation=annotation)
                    | ast.arg(annotation=annotation)
                ):
                    found.append(annotation)
                case (
                    ast.FunctionDef(returns=returns)
                    | ast.AsyncFunctionDef(returns=returns)
                ):
                    found.append(returns)
                case ast.ClassDef(bases=bases, keywords=keywords):
                    found.extend(bases)
                    found.extend(keyword.value for keyword in keywords)
                case ast.TypeAlias(value=value):
                    found.append(value)
                case ast.TypeVar(bound=bound, default_value=default):
                    found.extend((bound, default))
                case (
                    ast.ParamSpec(default_value=default)
                    | ast.TypeVarTuple(default_value=default)
                ):
                    found.append(default)
                case _:
                    continue
        return tuple(item for item in found if item is not None)

    @staticmethod
    def _module_scopes(
        module: p.Infra.RopeParsedModule,
    ) -> dict[t.StrTuple, p.Infra.RopeScope]:
        """Map native lexical declarations independently of synthetic scope caches.

        Returns:
            Native scopes keyed by declaration ancestry and sibling identity.

        """
        scopes: dict[t.StrTuple, p.Infra.RopeScope] = {(): module.get_scope()}
        pending: list[t.StrTuple] = [()]
        index = 0
        while index < len(pending):
            parent = pending[index]
            occurrences: dict[str, int] = {}
            for scope in scopes[parent].get_scopes():
                node = scope.pyobject.get_ast()
                # Rope caches expression comprehensions alongside declarations.
                if isinstance(
                    node, ast.ListComp | ast.SetComp | ast.DictComp | ast.GeneratorExp
                ):
                    continue
                declaration = (
                    f"{scope.get_kind()}:{type(node).__name__}:"
                    f"{scope.pyobject.get_name()}"
                )
                occurrence = occurrences.get(declaration, 0)
                occurrences[declaration] = occurrence + 1
                identity = (*parent, f"{declaration}:{occurrence}")
                scopes[identity] = scope
                pending.append(identity)
            index += 1
        return scopes

    @staticmethod
    def _divergence_diagnostic(
        project: p.Infra.RopeProject, path: Path, candidate_text: str
    ) -> str:
        """Report candidate-versus-physical drift before rewriting one consumer.

        Returns:
            The candidate text, unchanged; the diagnostic is observational only.

        """
        if project.source_text(path) == candidate_text:
            return candidate_text
        u.Cli.info(
            "quoted-move candidate digest divergence "
            f"path={path} "
            f"candidate={hashlib.sha256(candidate_text.encode()).hexdigest()[:12]} "
            f"physical="
            f"{hashlib.sha256(project.source_text(path).encode()).hexdigest()[:12]}"
        )
        return candidate_text

    @classmethod
    def _module_quoted_consumer(
        cls,
        projects: tuple[p.Infra.RopeProject, p.Infra.RopeProject],
        paths: tuple[Path, Path, Path],
        text: str,
        identities: tuple[int, int],
        destination: str,
    ) -> tuple[str, dict[tuple[t.StrTuple, str], int]]:
        """Rewrite one consumer with callback state owned by this invocation.

        Returns:
            Rewritten text and the native identity checks it requires.

        """
        project, composed = projects
        source, target, path = paths
        root = Path(project.root.real_path).resolve()
        resource = cls._resource(composed, root, path)
        original = FlextInfraUtilitiesRopeCorePyModule.resolve_pymodule(
            project, cls._resource(project, root, source if path == target else path)
        )
        module = FlextInfraUtilitiesRopeCorePyModule.resolve_pymodule(
            composed, resource
        )
        rewritten, required = cls._module_quoted_rewrite(
            composed, (original, module), text, paths, (identities, destination)
        )
        return cls._module_quoted_exports(
            original, rewritten, paths, identities[0]
        ), required

    @classmethod
    def _module_quoted_rewrite(
        cls,
        composed: p.Infra.RopeProject,
        modules: tuple[p.Infra.RopeParsedModule, p.Infra.RopeParsedModule],
        text: str,
        paths: tuple[Path, Path, Path],
        destination_info: tuple[tuple[int, int], str],
    ) -> tuple[str, dict[tuple[t.StrTuple, str], int]]:
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
        # The before state is the consumer's pre-move text parsed in the same
        # composed basis as the after state: staged sibling plans (for example a
        # sanctioned class rename from another pipeline stage) are present on
        # both sides, so this comparison isolates only this move's own effects.
        before_module = FlextInfraUtilitiesRopeRuntimeModules.build_string_module(
            composed, text, resource=resource
        )
        before_scopes = cls._module_scopes(before_module)
        current_scopes = cls._module_scopes(module)
        cls._validate_module_quoted_scopes(before_scopes, current_scopes, paths)
        positions = cls._module_quoted_positions(composed, before_module, text)
        required: dict[tuple[t.StrTuple, str], int] = {}
        binding: str | None = None

        def replacement(scope: p.Infra.RopeScope, expression: str) -> str | None:
            nonlocal binding
            identity = positions[id(scope)]
            selected, elected, count = cls._module_quoted_reference(
                composed,
                module,
                (scope, current_scopes[identity]),
                expression,
                ((paths[0], paths[1]), identities, destination),
            )
            if count:
                required[identity, selected if selected is not None else expression] = (
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
        rewritten = FlextInfraUtilitiesTypesSemanticNesting.rewrite_quoted_types(
            (composed, resource), text, replacement, module=before_module
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
        before: Mapping[t.StrTuple, p.Infra.RopeScope],
        current: Mapping[t.StrTuple, p.Infra.RopeScope],
        paths: tuple[Path, Path, Path],
    ) -> None:
        """Require the relocation to keep the consumer's lexical declarations.

        Raises:
            ValueError: If the native annotation scopes change.

        """
        source, target, path = paths
        old_declarations = tuple(before)
        declarations = tuple(current)
        if old_declarations != declarations:
            msg = (
                f"module relocation changed native annotation scopes: {path}; "
                f"native scope counts: original={len(old_declarations)}, "
                f"current={len(declarations)}; source={source}; target={target}"
            )
            for index in range(max(len(old_declarations), len(declarations))):
                original = (
                    old_declarations[index] if index < len(old_declarations) else None
                )
                relocated = declarations[index] if index < len(declarations) else None
                if original != relocated:
                    msg += (
                        f"; first differing native scope: index={index}; "
                        f"original={str(original)[:160]!r}; "
                        f"current={str(relocated)[:160]!r}"
                    )
                    break
            raise ValueError(msg)

    @classmethod
    def _module_quoted_reference(
        cls,
        project: p.Infra.RopeProject,
        module: p.Infra.RopeParsedModule,
        scopes: tuple[p.Infra.RopeScope, p.Infra.RopeScope],
        expression: str,
        destination_info: tuple[
            tuple[Path, Path],
            tuple[int, int],
            str,
        ],
    ) -> tuple[str | None, str | None, int]:
        """Resolve a quoted prefix by original and destination native identity.

        Returns:
            Replacement, required import binding and verified prefix length.

        """
        paths, identities, destination = destination_info
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        types = FlextInfraUtilitiesTypesSemanticNesting
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

    @classmethod
    def _module_quoted_positions(
        cls,
        project: p.Infra.RopeProject,
        module: p.Infra.RopeParsedModule,
        source: str,
    ) -> dict[int, t.StrTuple]:
        """Pair native annotation environments with their structural declarations.

        Returns:
            Annotation identities keyed to authenticated lexical positions.

        """
        native = FlextInfraUtilitiesRopeRuntime.require_source_module(module)
        declarations = {
            id(scope): key for key, scope in cls._module_scopes(native).items()
        }
        bindings = native.get_source_binding_index()
        return {
            id(environment): declarations[
                id(bindings.context_at(begin).structural_scope)
            ]
            for begin, _end, _literal, environment in (
                FlextInfraUtilitiesTypesSemanticNesting.quoted_type_regions(
                    source, project, native
                )
            )
        }

    @staticmethod
    def _module_quoted_exports(
        original: p.Infra.RopeParsedModule,
        rewritten: str,
        paths: tuple[Path, Path, Path],
        expected: int,
    ) -> str:
        """Preserve explicit exports of the relocated native module.

        Returns:
            The text with an authenticated exported module name updated.

        Raises:
            TypeError: If Quoted module exports require their original native source
                module.

        """
        source, target, _path = paths
        if not FlextInfraUtilitiesRopeRuntime.source_module(original):
            msg = "Quoted module exports require their original native source module"
            raise TypeError(msg)
        exports = FlextInfraUtilitiesRopeAnalysis.public_export_names_source(original)
        published = original.get_scope().lookup(source.stem)
        if (
            source.stem != target.stem
            and source.stem in exports
            and published is not None
            and id(published.get_object()) == expected
        ):
            with FlextInfraUtilitiesRopeModulePatch.candidate_module(
                original, rewritten
            ) as candidate:
                return FlextInfraUtilitiesRopeModulePatch.rewrite_all_declaration(
                    candidate,
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
        required: dict[tuple[t.StrTuple, str], int],
        relocated: int,
    ) -> None:
        """Verify every original quoted position in a single consumer invocation.

        Raises:
            ValueError: If any required quoted position or native identity is lost.

        """
        root = Path(project.root.real_path).resolve()
        resource = cls._resource(project, root, path)
        module = FlextInfraUtilitiesRopeCorePyModule.resolve_pymodule(project, resource)
        positions = cls._module_quoted_positions(project, module, text)
        seen: set[tuple[t.StrTuple, str]] = set()

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

        FlextInfraUtilitiesTypesSemanticNesting.quoted_type_edits(
            (project, resource), text, validate, module=module
        )
        if seen != set(required):
            msg = f"module relocation lost original quoted type positions: {path}"
            raise ValueError(msg)

    @staticmethod
    def _module_resource_changes(
        changes: p.Infra.RopeChangeSet,
        candidate: MutableMapping[Path, str],
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
                    msg = (
                        "native module move disagrees with its exact destination: "
                        f"source={change.resource.real_path} "
                        f"expected_source={source}; "
                        f"target={change.new_resource.real_path} "
                        f"expected_target={target}; "
                        f"folder={change.resource.is_folder()} duplicate={moved}"
                    )
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
        sources: Mapping[Path, str],
        states: Mapping[Path, p.Cli.AtomicFileState],
    ) -> p.Result[
        tuple[
            p.Infra.ClassMoveRequest,
            p.Infra.CodegenFilePlan,
            dict[Path, str],
            tuple[p.Infra.CodegenFilePlan, ...],
            str,
        ]
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
        publication = cls._module_reexport_sources(
            request, proposed, sources, virtual, reexports
        )
        return publication.map(
            lambda _: (
                request,
                target_plan,
                proposed,
                virtual,
                source_module_name,
            )
        )

    @classmethod
    def _module_completed_changes(
        cls,
        request: p.Infra.ClassMoveRequest,
        source_module_name: str,
        sources: Mapping[Path, str],
        proposed: Mapping[Path, str],
        virtual: tuple[p.Infra.CodegenFilePlan, ...],
    ) -> dict[Path, str]:
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
    def _canonical_module_metadata(
        cls,
        rope_project: p.Infra.RopeProject,
        source: Path,
        sources: Mapping[Path, str],
    ) -> tuple[str, str, tuple[str, ...]]:
        root = Path(rope_project.root.real_path).resolve()
        original = FlextInfraUtilitiesRopeRuntimeModules.snapshot_project(
            rope_project, sources
        )
        try:
            source_resource = cls._resource(original, root, source)
            source_module = FlextInfraUtilitiesRopeCorePyModule.resolve_pymodule(
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
        request: p.Infra.ClassMoveRequest,
        proposed: MutableMapping[Path, str],
        sources: Mapping[Path, str],
        virtual: tuple[p.Infra.CodegenFilePlan, ...],
        reexports: tuple[str, ...],
    ) -> p.Result[bool]:
        root = Path(request.rope_project.root.real_path).resolve()
        virtual_paths = {plan.path for plan in virtual}
        for origin in reexports:
            package_plan = FlextInfraUtilitiesRopeRuntimeModules.snapshot_project(
                request.rope_project,
                proposed,
                declared_files=virtual,
            )
            try:
                destination = FlextInfraUtilitiesRopeCorePyModule.resolve_pymodule(
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
                    if updated.failure:
                        return r[bool].from_failure(updated)
                    proposed[path] = updated.value
            finally:
                package_plan.close()
        return r[bool].ok(value=True)

    @classmethod
    def _module_reference_changes(
        cls,
        request: p.Infra.ClassMoveRequest,
        sources: Mapping[Path, str],
        proposed: Mapping[Path, str],
        virtual: tuple[p.Infra.CodegenFilePlan, ...],
    ) -> dict[Path, str]:
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
        request: p.Infra.ClassMoveRequest,
        source_module_name: str,
        candidate: Mapping[Path, str],
        virtual: tuple[p.Infra.CodegenFilePlan, ...],
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
    def _module_reexport_packages(
        cls,
        project: p.Infra.RopeProject,
        sources: Mapping[Path, str],
        source: p.Infra.RopeFile,
        name: str,
    ) -> tuple[str, ...]:
        """Elect package exports by original closed native declaration identity.

        Returns:
            The original packages exposing the declaration's native identity.

        """
        root = Path(project.root.real_path).resolve()
        expected = FlextInfraUtilitiesRopeCorePyModule.resolve_pymodule(
            project, source
        ).get_attribute(name)
        owners: list[str] = []
        for path in sorted(sources):
            if path.name != c.Infra.INIT_PY:
                continue
            module_name = FlextInfraUtilitiesRopeCorePyModule.resolve_pymodule(
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

    @classmethod
    def _module_class_declaration(cls, source: str, path: Path) -> ast.ClassDef:
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
            exports.extend(cls._module_literal_exports(value, path))
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
    ) -> p.Infra.CodegenFilePlan:
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
        with FlextInfraUtilitiesWorkspaceSnapshot.facade_source_project(
            root,
            source_project=rope_project,
            declared_files=rope_project.source_plans,
        ) as (project, sources):
            view = cls.NativeSourceView(
                sources,
                tuple(project.source_state(path, required=False) for path in sources),
                declared_files=project.source_plans,
            )
            plans = cls.plan_module_move(
                project, source, destination_file=target, inputs=view
            ).unwrap()
        FlextInfraUtilitiesProtectedEditLinting.publish_codegen_plans(
            root, plans
        ).unwrap()
        return target

    @classmethod
    def move_class(cls, request: p.Infra.ClassMoveRequest) -> Path:
        """Move one top-level class or return its validated preview target.

        Returns:
            The resulting ``Path``.

        """
        if not request.apply:
            return cls._class_mover(request)[0]
        project = request.rope_project
        root = Path(project.root.real_path).resolve()
        target_file = cls._owned_path(root, request.target_file)
        snapshot = FlextInfraUtilitiesWorkspaceSnapshot
        declared = snapshot.workspace_declared_sources(
            root,
            (),
            {
                target_file: (
                    project.source_text(target_file)
                    if project.source_query(target_file, "isfile")
                    else f"{c.Infra.FUTURE_ANNOTATIONS}\n"
                )
            },
            source_project=project,
        )
        with snapshot.facade_source_project(
            root, source_project=project, declared_files=declared
        ) as (candidate, sources):
            edits = cls.plan_class_move(
                request.model_copy(update={"apply": False}), sources=sources
            )
            declarations = {plan.path: plan for plan in declared}
            plans = tuple(
                FlextInfraUtilitiesCodegenFilePlan.source_file_plan_from_edit(
                    root,
                    edit,
                    source_project=candidate,
                    declared_files=declarations,
                )
                for edit in edits
            )
        FlextInfraUtilitiesProtectedEditLinting.publish_codegen_plans(
            root, plans
        ).unwrap()
        return target_file

    @classmethod
    def plan_class_move(
        cls,
        request: p.Infra.ClassMoveRequest,
        *,
        sources: Mapping[Path, str],
    ) -> tuple[p.Infra.SemanticMigrationEdit, ...]:
        """Preview one identity-preserving move inside a closed source inventory.

        Returns:
            The resulting ``tuple[p.Infra.SemanticMigrationEdit, ...]``.

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
        edits: list[p.Infra.SemanticMigrationEdit] = []
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
        request: p.Infra.ClassMoveRequest,
    ) -> tuple[Path, p.Infra.RopeMoveGlobal]:
        """Resolve both execution and planning from the exact original declaration.

        Returns:
            The resulting ``tuple[Path, p.Infra.RopeMoveGlobal]``.

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
        offset = FlextInfraUtilitiesRopeCorePyModule.find_identifier_offset_in_lines(
            source.splitlines(keepends=True),
            line=request.line,
            symbol=request.class_name,
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
    def family_declaration_target_file(
        *,
        project_root: Path,
        source_file: Path,
        family: str,
    ) -> Path:
        """Derive the family module that carries the declaring module's domain.

        ADR-028 Decisions 3-4: every declaration lives in the family that owns
        its kind, one nested class per module. The destination is the module of
        ``family`` named after the declaring module (``_models/matchers.py``
        relocates a typing to ``_typings/matchers.py``), inside the namespace
        root that hosts the family directories: ``src/<package>`` for public
        sources, the tier directory (``tests``, ``examples``, ``scripts``) for
        every other tier. Both the directory and the family come from the
        facade-family census, never from a list.

        Returns:
            The family domain module path, existing or to be scaffolded.

        """
        parts = source_file.relative_to(project_root).parts
        source_package = parts[:2]
        if parts[0] == c.Infra.DEFAULT_SRC_DIR and len(parts) > len(source_package):
            namespace_root = project_root.joinpath(*source_package)
        elif len(parts) > 1:
            namespace_root = project_root / parts[0]
        else:
            namespace_root = project_root
        directory = FlextInfraUtilitiesCodegenNamespace.facade_families()[
            family
        ].directory
        stem = source_file.stem.strip("_")
        if stem.startswith(c.Infra.NAMESPACE_PYTEST_MODULE_PREFIX):
            stem = stem.removeprefix(c.Infra.NAMESPACE_PYTEST_MODULE_PREFIX)
        return namespace_root / directory / f"{stem}.py"

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
