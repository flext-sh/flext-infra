"""Plan own-method and import changes through the bound native Rope DSL.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from contextlib import AbstractContextManager
from pathlib import Path

from flext_infra import c, m, p, t
from flext_infra._utilities._rope.rope_runtime import FlextInfraUtilitiesRopeRuntime


class FlextInfraUtilitiesSemanticCutoverOwnMro:
    """Preserve native bindings without a second parser or source visitor."""

    @classmethod
    def rewrite_own_family_members(
        cls,
        source: str,
        routes: Mapping[t.StrTuple, tuple[str, str, str]],
        imports: Mapping[str, str],
        *,
        source_project: p.Infra.RopeProject,
        file_path: Path,
    ) -> str:
        """Plan member and import changes without moving an import's suite.

        Returns:
            The native candidate with exact lexical owner bindings.

        """
        module = cls._module(source_project, file_path, source)
        declarations = cls._family_declarations(module, source_project, imports, routes)
        updated = source
        for path, (_provider, owner, suffix) in routes.items():
            root = path[0]

            def admit(
                native: t.Infra.RopeNativeSourceModule,
                match: p.Infra.RopeContractMatch,
            ) -> bool:
                scope = (
                    native
                    .get_source_binding_index()
                    .context_at(match.get_region()[0])
                    .environment
                )
                binding = scope.lookup(root)
                if not isinstance(binding, p.Infra.RopeImportedName):
                    return False
                if (
                    binding.imported_module.module_name != imports[root]
                    or binding.imported_module.level
                ):
                    return False
                if scope.lookup(owner) is not None:
                    msg = "Own-family repair would capture a binding"
                    raise ValueError(msg)
                return True

            updated = cls._restructure(
                source_project,
                file_path,
                updated,
                ".".join(path),
                f"{owner}.{suffix}",
                admit,
            )
        for pattern, goal in declarations:
            updated = cls._restructure(
                source_project, file_path, updated, pattern, goal, None
            )
        with cls._candidate(source_project, file_path, updated):
            module = cls._module(source_project, file_path, updated)
            for scope in cls._scopes(module.get_scope()):
                for name, provider in imports.items():
                    binding = scope.get_defined_names().get(name)
                    if (
                        isinstance(binding, p.Infra.RopeImportedName)
                        and binding.imported_module.module_name == provider
                        and not binding.imported_module.level
                    ):
                        msg = (
                            "Rope does not expose the complete scoped import "
                            f"declaration required for {file_path}:{name}"
                        )
                        raise ValueError(msg)
        return updated

    @classmethod
    def rewrite_own_method_mro_calls(
        cls,
        source: str,
        *,
        source_project: p.Infra.RopeProject,
        file_path: Path,
    ) -> tuple[str, tuple[str, ...]]:
        """Bind source-proven own helpers through their enclosing receiver.

        Returns:
            The native candidate and actual methods whose dispatch changed.

        """
        runtime = FlextInfraUtilitiesRopeRuntime
        module = cls._module(source_project, file_path, source)
        targets = tuple(
            (cls._scope_path(scope), scope.pyobject.get_name(), name)
            for scope in cls._scopes(module.get_scope())
            if scope.get_kind() == "Class"
            for name, binding in scope.get_defined_names().items()
            if runtime.py_function(binding.get_object())
        )
        method_order = {
            cls._scope_path(scope): scope.get_region()[1]
            for scope in cls._scopes(module.get_scope())
            if scope.get_kind() == "Function"
            and scope.parent is not None
            and scope.parent.get_kind() == "Class"
        }
        updated = source
        changed: dict[t.StrTuple, str] = {}
        for owner_path, owner_name, target_name in targets:
            with cls._candidate(source_project, file_path, updated):
                owner_scope = cls._scope(
                    cls._module(source_project, file_path, updated), owner_path
                )
                receivers: set[str] = set()
                for method in owner_scope.get_scopes():
                    function = method.pyobject
                    if runtime.py_function(function):
                        parameters = tuple(function.get_param_names(special_args=True))
                        receivers.add(
                            "cls"
                            if function.get_kind() == "function" or not parameters
                            else parameters[0]
                        )
            for receiver in sorted(receivers):
                promotions: set[t.StrTuple] = set()

                def admit(
                    native: t.Infra.RopeNativeSourceModule,
                    match: p.Infra.RopeContractMatch,
                ) -> bool:
                    current_owner = cls._scope(native, owner_path)
                    context = native.get_source_binding_index().context_at(
                        match.get_region()[0]
                    )
                    if context.role not in {
                        "function-body",
                        "lambda-body",
                        "comprehension-inner",
                    }:
                        return False
                    binding = context.environment.lookup(owner_name)
                    if (
                        binding is None
                        or binding.get_object() is not current_owner.pyobject
                    ):
                        return False
                    method = cls._enclosing_method(context.structural_scope, owner_path)
                    if method is None:
                        return False
                    target = current_owner.get_defined_names()[target_name].get_object()
                    function = method.pyobject
                    if not runtime.py_function(target) or not runtime.py_function(
                        function
                    ):
                        msg = "Own MRO requires native source functions"
                        raise TypeError(msg)
                    if target.get_kind() == "method":
                        msg = (
                            "Own instance method retains an unbound reference: "
                            f"{owner_name}.{target_name}"
                        )
                        raise ValueError(msg)
                    parameters = tuple(function.get_param_names(special_args=True))
                    if function.get_kind() == "function":
                        if (
                            "cls" in parameters
                            or context.environment.lookup("cls") is not None
                        ):
                            msg = (
                                "Own MRO receiver would capture a parameter: "
                                f"{owner_name}.{function.get_name()}"
                            )
                            raise ValueError(msg)
                        selected = "cls"
                    elif parameters:
                        selected = parameters[0]
                    else:
                        msg = "Own MRO method has no receiver"
                        raise ValueError(msg)
                    if selected != receiver:
                        return False
                    if function.get_kind() != "function":
                        expected = method.get_defined_names().get(receiver)
                        actual = context.environment.lookup(receiver)
                        same = runtime.runtime_callable(
                            "rope.refactor.occurrences", "same_pyname"
                        )
                        if (
                            expected is None
                            or actual is None
                            or not same(expected, actual)
                        ):
                            msg = "Own MRO receiver would capture a binding"
                            raise ValueError(msg)
                    path = cls._scope_path(method)
                    changed[path] = f"own-method-mro:{owner_name}.{function.get_name()}"
                    if function.get_kind() == "function":
                        promotions.add(path)
                    return True

                updated = cls._restructure(
                    source_project,
                    file_path,
                    updated,
                    f"{owner_name}.{target_name}",
                    f"{receiver}.{target_name}",
                    admit,
                )
                if promotions:
                    updated = cls._promote(
                        source_project, file_path, updated, promotions
                    )
        return updated, tuple(
            changed[path] for path in sorted(changed, key=method_order.__getitem__)
        )

    @staticmethod
    def _module(
        project: p.Infra.RopeProject, path: Path, source: str
    ) -> p.Infra.RopeSourceModule:
        """Require the exact active source before native change planning."""
        runtime = FlextInfraUtilitiesRopeRuntime
        if project.source_text(path) != source:
            msg = f"Own MRO source differs from its bound view: {path}"
            raise ValueError(msg)
        module = project.get_pymodule(
            runtime.file_resource_at(project, path), force_errors=True
        )
        if not runtime.source_module(module):
            msg = "Own MRO requires a native source module"
            raise TypeError(msg)
        return module

    @staticmethod
    def _candidate(
        project: p.Infra.RopeProject, path: Path, source: str
    ) -> AbstractContextManager[p.Infra.RopeProject]:
        """Retain the complete provider cohort while binding one changed file."""
        plans = {plan.path: plan for plan in project.source_plans}
        existing = plans.get(path)
        if existing is None:
            before = project.source_state(path)
            plans[path] = m.Infra.CodegenFilePlan(
                project=Path(project.root.real_path),
                path=path,
                before=before,
                desired_content=source.encode(c.DEFAULT_ENCODING),
                desired_mode=before.mode,
            )
        else:
            plans[path] = existing.model_copy(
                update={"desired_content": source.encode(c.DEFAULT_ENCODING)}
            )
        return project.source_view(
            declared_files=tuple(plans.values()),
            additional_source_folders=tuple(
                folder.path for folder in project.get_source_folders()
            ),
        )

    @classmethod
    def _restructure(
        cls,
        project: p.Infra.RopeProject,
        path: Path,
        source: str,
        pattern: str,
        goal: str,
        admission: t.Infra.RopeMatchFilter | None,
    ) -> str:
        """Delegate matching, admission and source emission to native Restructure."""
        runtime = FlextInfraUtilitiesRopeRuntime
        with cls._candidate(project, path, source):
            changes = runtime.restructure_changes(
                project,
                m.Infra.RopeRestructureRequest(
                    pattern=pattern,
                    goal=goal,
                    arguments={},
                    resources=(runtime.file_resource_at(project, path),),
                    match_filter=admission,
                ),
            )
            updated = source
            for change in runtime.change_set_members(changes):
                if not isinstance(change, p.Infra.RopeChangeContents):
                    msg = "Own MRO received a non-content native effect"
                    raise TypeError(msg)
                if Path(change.resource.real_path) != path:
                    msg = "Own MRO native change escaped its source"
                    raise ValueError(msg)
                updated = change.new_contents
            return updated

    @classmethod
    def _scopes(cls, scope: p.Infra.RopeScope) -> Iterator[p.Infra.RopeScope]:
        """Read the lexical hierarchy already indexed by Rope."""
        yield scope
        for child in scope.get_scopes():
            yield from cls._scopes(child)

    @staticmethod
    def _scope_path(scope: p.Infra.RopeScope) -> t.StrTuple:
        """Project native scope identities into a stable lexical path."""
        names: list[str] = []
        while scope.get_kind() != "Module":
            names.append(scope.pyobject.get_name())
            if scope.parent is None:
                msg = "Native lexical scope has no module owner"
                raise ValueError(msg)
            scope = scope.parent
        return tuple(reversed(names))

    @classmethod
    def _scope(
        cls, module: p.Infra.RopeSourceModule, path: t.StrTuple
    ) -> p.Infra.RopeScope:
        """Resolve exactly one declared native scope for a lexical path."""
        scope = module.get_scope()
        for name in path:
            matches = tuple(
                child
                for child in scope.get_scopes()
                if child.pyobject.get_name() == name
            )
            if len(matches) != 1:
                msg = f"Own MRO scope is not uniquely declared: {path}"
                raise ValueError(msg)
            scope = matches[0]
        return scope

    @classmethod
    def _enclosing_method(
        cls, scope: p.Infra.RopeScope, owner: t.StrTuple
    ) -> p.Infra.RopeScope | None:
        """Find the enclosing method through native scope parents."""
        while scope.parent is not None:
            if (
                scope.get_kind() == "Function"
                and cls._scope_path(scope.parent) == owner
            ):
                return scope
            scope = scope.parent
        return None

    @classmethod
    def _promote(
        cls,
        project: p.Infra.RopeProject,
        path: Path,
        source: str,
        methods: set[t.StrTuple],
    ) -> str:
        """Preserve signatures using native header coordinates and writer."""
        runtime = FlextInfraUtilitiesRopeRuntime
        with cls._candidate(project, path, source):
            module = cls._module(project, path, source)
            finder = runtime.runtime_callable("rope.base.worder", "Worder")(source)
            if not isinstance(finder, p.Infra.RopeWorder):
                msg = "Native word finder lacks its public contract"
                raise TypeError(msg)
            edits: list[m.Infra.SourceRewrite] = []
            for method in sorted(methods):
                scope = cls._scope(module, method)
                function = scope.pyobject
                if not runtime.py_function(function):
                    msg = "Own MRO promotion requires a native function"
                    raise TypeError(msg)
                name_offset = finder.find_function_offset(
                    module.lines.get_line_start(scope.get_start())
                )
                start, _end = finder.get_word_parens_range(name_offset)
                context = module.get_source_binding_index().context_at(start)
                if context.role == "type-parameter-expression":
                    _left, right = finder.code_finder.get_word_parens_range(
                        name_offset, opening="[", closing="]"
                    )
                    start, _end = finder.get_word_parens_range(right - 1)
                edits.append(
                    m.Infra.SourceRewrite(
                        start=start + 1,
                        end=start + 1,
                        text="cls, "
                        if function.get_param_names(special_args=True)
                        else "cls",
                    )
                )
                decorators = runtime.semantic_regions(
                    module,
                    "staticmethod",
                    arguments={},
                    start=scope.get_region()[0],
                    end=module.lines.get_line_start(scope.get_start()),
                )
                indexed = tuple(
                    (fragment.depth, region)
                    for region in decorators
                    for fragment in module.get_source_binding_index().fragments
                    if (fragment.start, fragment.end) == region
                )
                shallowest = min((depth for depth, _region in indexed), default=None)
                direct = frozenset(
                    region for depth, region in indexed if depth == shallowest
                )
                if len(direct) != 1:
                    msg = "Own MRO static decorator is not uniquely bound"
                    raise ValueError(msg)
                decorator = next(iter(direct))
                edits.append(
                    m.Infra.SourceRewrite(
                        start=decorator[0],
                        end=decorator[1],
                        text="classmethod",
                    )
                )
            return runtime.content_change(
                runtime.file_resource_at(project, path), source, edits
            ).new_contents

    @classmethod
    def _family_declarations(
        cls,
        module: p.Infra.RopeSourceModule,
        project: p.Infra.RopeProject,
        imports: Mapping[str, str],
        routes: Mapping[t.StrTuple, tuple[str, str, str]],
    ) -> tuple[tuple[str, str], ...]:
        """Read scoped declarations from the native source binding index."""
        runtime = FlextInfraUtilitiesRopeRuntime
        finder = runtime.runtime_callable("rope.base.worder", "Worder")(
            module.source_code
        )
        if not isinstance(finder, p.Infra.RopeWorder):
            msg = "Native word finder lacks its public contract"
            raise TypeError(msg)
        fragments = module.get_source_binding_index().fragments
        replacements: dict[tuple[int, int], tuple[str, str]] = {}
        for name, provider in imports.items():
            binding = module.get_scope().lookup(name)
            if not isinstance(binding, p.Infra.RopeImportedName):
                msg = f"Own-family import lacks its native binding: {name}"
                raise ValueError(msg)
            if (
                binding.imported_module.module_name != provider
                or binding.imported_module.level
            ):
                msg = f"Own-family import differs from its declared provider: {name}"
                raise ValueError(msg)
            occurrences = runtime.create_occurrence_finder(
                project, name, binding, imports=True, in_hierarchy=False
            ).find_occurrences(pymodule=module)
            for occurrence in occurrences:
                if not finder.is_a_name_after_from_import(occurrence.offset):
                    continue
                enclosing = tuple(
                    fragment
                    for fragment in fragments
                    if fragment.start <= occurrence.offset < fragment.end
                    and finder.get_word_at(fragment.start) == "from"
                )
                if not enclosing:
                    msg = (
                        "Rope has no scoped import declaration for the elected binding"
                    )
                    raise ValueError(msg)
                statement = min(enclosing, key=lambda item: item.end - item.start)
                region = (statement.start, statement.end)
                if region in replacements:
                    continue
                declared = {
                    (fragment.start, fragment.end): fragment
                    for fragment in fragments
                    if statement.start <= fragment.start < fragment.end <= statement.end
                    and finder.is_a_name_after_from_import(fragment.start)
                }
                aliases: list[tuple[str, str | None]] = []
                for position, _stop in sorted(declared):
                    imported = finder.get_word_at(position)
                    alias = (
                        finder.get_from_aliased(position)
                        if finder.is_from_aliased(position)
                        else None
                    )
                    aliases.append((imported, alias))
                if not aliases:
                    msg = "Rope has no alias declarations for the elected import"
                    raise ValueError(msg)
                expected = runtime.from_import(
                    provider, 0, aliases
                ).get_import_statement()
                if not runtime.semantic_regions(
                    module,
                    expected,
                    arguments={},
                    start=statement.start,
                    end=statement.end,
                ):
                    msg = "Native import aliases do not prove the whole declaration"
                    raise ValueError(msg)
                elected = {
                    alias or imported
                    for imported, alias in aliases
                    if imports.get(alias or imported) == provider
                }
                retained = tuple(
                    (imported, alias)
                    for imported, alias in aliases
                    if (alias or imported) not in elected
                )
                goals = (
                    *(
                        (
                            runtime.from_import(
                                provider, 0, retained
                            ).get_import_statement(),
                        )
                        if retained
                        else ()
                    ),
                    *(
                        runtime.from_import(
                            target, 0, ((owner, None),)
                        ).get_import_statement()
                        for target, owner in sorted({
                            (target, owner)
                            for path, (target, owner, _) in routes.items()
                            if path[0] in elected
                        })
                    ),
                )
                line = module.lines.get_line_number(statement.start)
                indentation = runtime.runtime_callable(
                    "rope.refactor.sourceutils", "get_indents"
                )(module.lines, line)
                if not isinstance(indentation, int):
                    msg = "Rope indentation query returned a non-integer"
                    raise TypeError(msg)
                inline = (
                    statement.start - module.lines.get_line_start(line) > indentation
                )
                # Read only the region already owned by the native index. Rope
                # parses the DSL pattern and emits the actual replacement.
                pattern = module.source_code[statement.start : statement.end]
                replacements[region] = (pattern, ("; " if inline else "\n").join(goals))
        return tuple(replacements.values())


__all__: list[str] = ["FlextInfraUtilitiesSemanticCutoverOwnMro"]
