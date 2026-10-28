"""Plan own-method and import changes through the bound native Rope DSL.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Generator, Iterator, Mapping
from contextlib import contextmanager
from pathlib import Path

from flext_infra import m, p, t
from flext_infra._utilities import FlextInfraUtilitiesWorkspaceSnapshot
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

        Raises:
            ValueError: A source binding is captured or an import is incomplete.

        """
        module = cls._module(source_project, file_path, source)
        declarations = cls._family_declarations(module, source_project, imports, routes)
        updated = source
        for path, (_provider, owner, suffix) in routes.items():
            updated = cls._restructure(
                source_project,
                file_path,
                updated,
                ".".join(path),
                f"{owner}.{suffix}",
                admission=cls._family_admission(path[0], owner, imports[path[0]]),
            )
        for pattern, goal in declarations:
            updated = cls._restructure(
                source_project, file_path, updated, pattern, goal, admission=None
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
            if runtime.py_function(function := binding.get_object())
            and function.get_scope().parent is not None
            and function.get_scope().parent.pyobject is scope.pyobject
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
                receivers = cls._receivers(owner_scope)
            for receiver in receivers:
                promotions: set[t.StrTuple] = set()
                updated = cls._restructure(
                    source_project,
                    file_path,
                    updated,
                    f"{owner_name}.{target_name}",
                    f"{receiver}.{target_name}",
                    admission=cls._method_admission(
                        (owner_path, owner_name, target_name, receiver),
                        (changed, promotions),
                    ),
                )
                if promotions:
                    updated = cls._promote(
                        source_project, file_path, updated, promotions
                    )
        return updated, tuple(
            changed[path] for path in sorted(changed, key=method_order.__getitem__)
        )

    @staticmethod
    def _family_admission(
        root: str, owner: str, provider: str
    ) -> t.Infra.RopeMatchFilter:
        """Bind a family route once for native lexical admission.

        Returns:
            The matcher whose route cannot change during planning.

        """

        def admit(
            native: p.Infra.RopePyModule, match: p.Infra.RopeContractMatch
        ) -> bool:
            if not FlextInfraUtilitiesRopeRuntime.source_module(native):
                msg = "Own-family matching requires native source"
                raise TypeError(msg)
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
                binding.imported_module.module_name != provider
                or binding.imported_module.level
            ):
                return False
            if scope.lookup(owner) is not None:
                msg = "Own-family repair would capture a binding"
                raise ValueError(msg)
            return True

        return admit

    @staticmethod
    def _receivers(owner: p.Infra.RopeScope) -> t.StrTuple:
        """Collect native receiver spellings without re-reading source.

        Returns:
            Ordered distinct receiver names for this owner.

        """
        receivers: set[str] = set()
        for method in owner.get_scopes():
            function = method.pyobject
            if FlextInfraUtilitiesRopeRuntime.py_function(function):
                parameters = tuple(function.get_param_names(special_args=True))
                receivers.add(
                    "cls"
                    if function.get_kind() == "staticmethod" or not parameters
                    else parameters[0]
                )
        return tuple(sorted(receivers))

    @classmethod
    def _method_admission(
        cls,
        route: tuple[t.StrTuple, str, str, str],
        effects: tuple[dict[t.StrTuple, str], set[t.StrTuple]],
    ) -> t.Infra.RopeMatchFilter:
        """Bind one own-method route and its planned effects.

        Returns:
            The identity-authenticated native match filter.

        """
        owner_path, owner_name, target_name, receiver = route
        changed, promotions = effects
        runtime = FlextInfraUtilitiesRopeRuntime

        def admit(
            native: p.Infra.RopePyModule, match: p.Infra.RopeContractMatch
        ) -> bool:
            if not runtime.source_module(native):
                msg = "Own MRO matching requires native source"
                raise TypeError(msg)
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
            if binding is None or binding.get_object() is not current_owner.pyobject:
                return False
            method = cls._enclosing_method(context.structural_scope, owner_path)
            if method is None:
                return False
            target = current_owner.get_defined_names()[target_name].get_object()
            function = method.pyobject
            if not runtime.py_function(target) or not runtime.py_function(function):
                msg = "Own MRO requires native source functions"
                raise TypeError(msg)
            target_parent = target.get_scope().parent
            if (
                target_parent is None
                or target_parent.pyobject is not current_owner.pyobject
            ):
                return False
            if target.get_kind() == "method":
                msg = (
                    "Own instance method retains an unbound reference: "
                    f"{owner_name}.{target_name}"
                )
                raise ValueError(msg)
            if cls._receiver(function, context, owner_name) != receiver:
                return False
            path = cls._scope_path(method)
            changed[path] = f"own-method-mro:{owner_name}.{function.get_name()}"
            if function.get_kind() == "staticmethod":
                promotions.add(path)
            return True

        return admit

    @staticmethod
    def _receiver(
        function: p.Infra.RopeSourceFunction,
        context: p.Infra.RopeSourceBindingContext,
        owner_name: str,
    ) -> str:
        """Prove that the selected receiver retains its parameter identity.

        Returns:
            The existing receiver or the new class receiver.

        Raises:
            ValueError: A receiver is missing or would capture a binding.

        """
        parameters = tuple(function.get_param_names(special_args=True))
        if function.get_kind() == "staticmethod":
            if "cls" in parameters or context.environment.lookup("cls") is not None:
                msg = (
                    "Own MRO receiver would capture a parameter: "
                    f"{owner_name}.{function.get_name()}"
                )
                raise ValueError(msg)
            return "cls"
        if not parameters:
            msg = "Own MRO method has no receiver"
            raise ValueError(msg)
        receiver = parameters[0]
        expected = function.get_parameters().get(receiver)
        actual = context.environment.lookup(receiver)
        same = FlextInfraUtilitiesRopeRuntime.runtime_callable(
            "rope.refactor.occurrences", "same_pyname"
        )
        if expected is None or actual is None or not same(expected, actual):
            msg = "Own MRO receiver would capture a binding"
            raise ValueError(msg)
        return receiver

    @staticmethod
    def _module(
        project: p.Infra.RopeProject, path: Path, source: str
    ) -> p.Infra.RopeSourceModule:
        """Require the exact active source before native change planning.

        Returns:
            The resulting ``p.Infra.RopeSourceModule``.

        Raises:
            TypeError: If Own MRO requires a native source module.
            ValueError: If Own MRO source differs from its bound view.

        """
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
    @contextmanager
    def _candidate(
        project: p.Infra.RopeProject, path: Path, source: str
    ) -> Generator[p.Infra.RopeProject]:
        """Retain the complete provider cohort while binding one changed file.

        Yields:
            Each ``p.Infra.RopeProject``.

        """
        with FlextInfraUtilitiesWorkspaceSnapshot.facade_source_project(
            Path(project.root.real_path),
            planned_sources={path: source},
            source_project=project,
        ) as binding:
            yield binding[0]

    @classmethod
    def _restructure(
        cls,
        project: p.Infra.RopeProject,
        path: Path,
        source: str,
        pattern: str,
        goal: str,
        *,
        admission: t.Infra.RopeMatchFilter | None,
    ) -> str:
        """Delegate matching, admission and source emission to native Restructure.

        Returns:
            The resulting ``str``.

        Raises:
            TypeError: If Own MRO received a non-content native effect.
            ValueError: If Own MRO native change escaped its source.

        """
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
            for change in runtime.change_set_members(
                changes.changes, "Own MRO received a non-content native effect"
            ).unwrap():
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
        """Read the lexical hierarchy already indexed by Rope.

        Yields:
            Each ``p.Infra.RopeScope``.

        """
        yield scope
        for child in scope.get_scopes():
            yield from cls._scopes(child)

    @staticmethod
    def _scope_path(scope: p.Infra.RopeScope) -> t.StrTuple:
        """Project native scope identities into a stable lexical path.

        Returns:
            The resulting ``t.StrTuple``.

        Raises:
            ValueError: If Native lexical scope has no module owner.

        """
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
        """Resolve Rope's elected declaration, including overload implementations.

        Returns:
            The resulting ``p.Infra.RopeScope``.

        Raises:
            TypeError: If Own MRO binding has no source scope.
            ValueError: If Own MRO scope has no declared binding; or if Own MRO binding
                belongs to another declaration.

        """
        scope = module.get_scope()
        for name in path:
            names = (
                scope.get_names()
                if scope.get_kind() == "Function"
                else scope.get_defined_names()
            )
            binding = names.get(name)
            if binding is None:
                msg = f"Own MRO scope has no declared binding: {path}"
                raise ValueError(msg)
            definition = binding.get_object()
            runtime = FlextInfraUtilitiesRopeRuntime
            if not runtime.py_function(definition) and not runtime.py_class(definition):
                msg = f"Own MRO binding has no source scope: {path}"
                raise TypeError(msg)
            child = definition.get_scope()
            if child.parent is None or child.parent.pyobject is not scope.pyobject:
                msg = f"Own MRO binding belongs to another declaration: {path}"
                raise ValueError(msg)
            scope = child
        return scope

    @classmethod
    def _enclosing_method(
        cls, scope: p.Infra.RopeScope, owner: t.StrTuple
    ) -> p.Infra.RopeScope | None:
        """Find the enclosing method through native scope parents.

        Returns:
            The resulting ``p.Infra.RopeScope | None``.

        """
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
        """Preserve signatures using native header coordinates and writer.

        Returns:
            The resulting ``str``.

        Raises:
            TypeError: If Native word finder lacks its public contract; or if Own MRO
                promotion requires a native function.
            ValueError: If Own MRO static decorator is not uniquely bound.

        """
        runtime = FlextInfraUtilitiesRopeRuntime
        with cls._candidate(project, path, source):
            module = cls._module(project, path, source)
            finder = runtime.runtime_callable("rope.base.worder", "Worder")(source)
            if not isinstance(finder, p.Infra.RopeWorder):
                msg = "Native word finder lacks its public contract"
                raise TypeError(msg)
            edits: list[m.Infra.SourceRewrite] = []
            scopes = tuple(
                declaration
                for method in sorted(methods)
                for declaration in cls._promotion_scopes(module, method)
            )
            for scope in scopes:
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
                    "${own_staticmethod}",
                    arguments={"own_staticmethod": "name=__builtin__.staticmethod"},
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
    def _promotion_scopes(
        cls, module: p.Infra.RopeSourceModule, method: t.StrTuple
    ) -> tuple[p.Infra.RopeScope, ...]:
        """Include only native overload declarations of the elected method.

        Returns:
            The resulting ``tuple[p.Infra.RopeScope, ...]``.

        Raises:
            ValueError: If Own MRO promotion has no declaring owner; or if Own MRO
                overload differs from its static implementation.

        """
        implementation = cls._scope(module, method)
        owner = implementation.parent
        if owner is None:
            msg = "Own MRO promotion has no declaring owner"
            raise ValueError(msg)
        runtime = FlextInfraUtilitiesRopeRuntime
        index = module.get_source_binding_index()
        declarations: list[p.Infra.RopeScope] = []
        siblings = sorted(
            (
                candidate
                for candidate in owner.get_scopes()
                if candidate.pyobject.get_name() == method[-1]
                and candidate.get_start() < implementation.get_start()
            ),
            key=lambda candidate: candidate.get_start(),
            reverse=True,
        )
        for candidate in siblings:
            function = candidate.pyobject
            if not runtime.py_function(function):
                break
            start = candidate.get_region()[0]
            end = module.lines.get_line_start(candidate.get_start())
            decorators = runtime.semantic_regions(
                module,
                "${own_overload}",
                arguments={"own_overload": "name=typing.overload"},
                start=start,
                end=end,
            )
            fragments = tuple(
                fragment
                for fragment in index.fragments
                if start <= fragment.start < fragment.end <= end
                and index.context_at(fragment.start).role == "decorator"
            )
            shallowest = min((fragment.depth for fragment in fragments), default=None)
            if not any(
                (fragment.start, fragment.end) in decorators
                and fragment.depth == shallowest
                for fragment in fragments
            ):
                break
            if function.get_kind() != "staticmethod":
                msg = "Own MRO overload differs from its static implementation"
                raise ValueError(msg)
            declarations.append(candidate)
        declarations.append(implementation)
        return tuple(declarations)

    @classmethod
    def _family_declarations(
        cls,
        module: p.Infra.RopeSourceModule,
        project: p.Infra.RopeProject,
        imports: Mapping[str, str],
        routes: Mapping[t.StrTuple, tuple[str, str, str]],
    ) -> tuple[tuple[str, str], ...]:
        """Read scoped declarations from the native source binding index.

        Returns:
            The resulting ``tuple[tuple[str, str], ...]``.

        Raises:
            TypeError: If Native word finder lacks its public contract; or if Rope
                indentation query returned a non-integer.
            ValueError: If Own-family import lacks its native binding; or if Own-family
                import differs from its declared provider; or if Rope has no scoped
                import declaration for the elected binding; or if Rope has no alias
                declarations for the elected import; or if Native import aliases do not
                prove the whole declaration.

        """
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
