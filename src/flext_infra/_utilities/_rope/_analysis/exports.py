"""Rope export-name resolution, scopes, and documentation declarations.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import MutableSequence, Sequence

from flext_infra import c, m, p, t
from flext_infra._utilities._rope._analysis.sourcescan import (
    FlextInfraUtilitiesRopeAnalysisSourceScan,
)
from flext_infra._utilities._rope.rope_runtime import FlextInfraUtilitiesRopeRuntime


class FlextInfraUtilitiesRopeAnalysisExports:
    """Rope export-name resolution, scopes, and documentation declarations."""

    @staticmethod
    def scope_definitions(
        pymodule: t.Infra.RopePyModule,
    ) -> Sequence[m.Infra.ScopeDefinition]:
        """Return every def/class scope in a module via rope's semantic tree.

        Uses ``PyModule.get_scope()`` and recursive ``PyScope.get_scopes()`` —
        never ``get_ast``/``ast.walk``. Each entry carries the scope kind
        (Function/Class/Comprehension), its 1-based start line, and whether it
        is a direct child of the module (global) scope.

        Returns:
            Every def/class scope in a module via rope's semantic tree.

        """
        root_scope = pymodule.get_scope()
        definitions: MutableSequence[m.Infra.ScopeDefinition] = []
        FlextInfraUtilitiesRopeAnalysisExports._collect_scope_definitions(
            scope=root_scope,
            is_module_level=True,
            definitions=definitions,
        )
        return tuple(definitions)

    @staticmethod
    def _collect_scope_definitions(
        *,
        scope: t.Infra.RopeScope,
        is_module_level: bool,
        definitions: MutableSequence[m.Infra.ScopeDefinition],
    ) -> None:
        """Recurse the rope scope tree, appending one entry per child scope."""
        for child in scope.get_scopes():
            start = child.get_start()
            # RopeScope.get_start() is
            # declared int in p.Infra; the old isinstance guard was dead code.
            definitions.append(
                m.Infra.ScopeDefinition(
                    name=FlextInfraUtilitiesRopeAnalysisExports._scope_name(child),
                    kind=FlextInfraUtilitiesRopeAnalysisExports._scope_kind(child),
                    line=start if start > 0 else 1,
                    is_module_level=is_module_level,
                ),
            )
            FlextInfraUtilitiesRopeAnalysisExports._collect_scope_definitions(
                scope=child,
                is_module_level=False,
                definitions=definitions,
            )

    @staticmethod
    def _scope_kind(scope: t.Infra.RopeScope) -> c.Infra.RopeScopeKind:
        """Map rope's ``get_kind()`` to the typed enum.

        Rope documents ``None`` for comprehension scopes, which maps to
        ``UNKNOWN``; any other undeclared kind raises its ``ValueError``.

        Returns:
            The resulting ``c.Infra.RopeScopeKind``.

        """
        raw_kind = scope.get_kind()
        if raw_kind is None:
            return c.Infra.RopeScopeKind.UNKNOWN
        return c.Infra.RopeScopeKind(raw_kind)

    @staticmethod
    def _scope_name(scope: t.Infra.RopeScope) -> str:
        """Return the def/class name backing one rope scope.

        Returns:
            The def/class name backing one rope scope.

        """
        name: str = scope.pyobject.get_name()
        return name

    @staticmethod
    @FlextInfraUtilitiesRopeRuntime.semantic_matching_context()
    def module_export_names_source(
        source_module: p.Infra.RopeSourceModule,
        *,
        export_options: m.Infra.ExportOptions | None = None,
    ) -> Sequence[str]:
        """Return module-local exports from one parsed source snapshot.

        Returns:
            Module-local exports from one parsed source snapshot.

        """
        resolved_options = export_options or m.Infra.ExportOptions()
        declared = source_module.get_source_binding_index().assignment_string_sequence(
            c.Infra.DUNDER_ALL, class_metadata=True
        )
        if declared is not None:
            return tuple(dict.fromkeys(declared))
        if resolved_options.require_explicit_all:
            return ()
        assignments, definitions, conditional_all = (
            FlextInfraUtilitiesRopeAnalysisExports._source_binding_inventory(
                source_module
            )
        )
        if conditional_all:
            return ()
        if resolved_options.include_dunder:
            return tuple(
                dict.fromkeys(
                    name
                    for name in assignments
                    if name.startswith("__") and name.endswith("__")
                ),
            )
        implicit_names: MutableSequence[str] = [
            name
            for name, is_class in definitions
            if is_class
            or resolved_options.allow_functions
            or (resolved_options.allow_main and name == "main")
        ]
        if resolved_options.allow_assignments:
            implicit_names.extend(assignments)
        return tuple(dict.fromkeys(implicit_names))

    @staticmethod
    def _source_binding_inventory(
        source_module: p.Infra.RopeSourceModule,
    ) -> tuple[
        MutableSequence[str],
        MutableSequence[tuple[str, bool]],
        bool,
    ]:
        """Inventory native global bindings outside the main-guard declarations.

        Returns:
            The assignment names, the definition name and class-kind pairs,
            and whether ``__all__`` was bound.

        """
        module_scope = source_module.get_scope()
        index = source_module.get_source_binding_index()
        guards = FlextInfraUtilitiesRopeAnalysisExports._native_main_guards(
            source_module
        )
        definitions: MutableSequence[tuple[str, bool]] = []
        for scope in module_scope.get_scopes():
            if scope.get_kind() not in {"Class", "Function"}:
                continue
            offset = source_module.lines.get_line_start(scope.get_start())
            if any(begin <= offset < end for begin, end in guards):
                continue
            definitions.append((scope.pyobject.get_name(), scope.get_kind() == "Class"))
        assignments: MutableSequence[str] = []
        explicit_all = False
        for fragment in index.fragments:
            if (
                fragment.depth < 1
                or fragment.context.structural_scope.pyobject
                is not module_scope.pyobject
                or any(begin <= fragment.start < end for begin, end in guards)
            ):
                continue
            for (
                name
            ) in FlextInfraUtilitiesRopeAnalysisSourceScan.statement_declaration_names(
                source_module, (fragment.start, fragment.end), include_augmented=True
            ):
                if name == c.Infra.DUNDER_ALL:
                    explicit_all = True
                else:
                    assignments.append(name)
        return assignments, definitions, explicit_all

    @staticmethod
    def _native_main_guards(
        module: p.Infra.RopeSourceModule,
    ) -> tuple[tuple[int, int], ...]:
        """Bind native guard tests to their immediately enclosing if statement.

        Returns:
            The resulting ``tuple[tuple[int, int], ...]``.

        Raises:
            TypeError: If Native main-guard query requires the word finder contract.

        """
        runtime = FlextInfraUtilitiesRopeRuntime
        index = module.get_source_binding_index()
        module_scope = module.get_scope()
        word = runtime.runtime_callable("rope.base.worder", "Worder")(
            module.source_code
        )
        if not isinstance(word, p.Infra.RopeWorder):
            msg = "Native main-guard query requires the word finder contract"
            raise TypeError(msg)
        guards: list[tuple[int, int]] = []
        conditions = frozenset(
            region
            for pattern in ("__name__ == '__main__'", "'__main__' == __name__")
            for region in runtime.semantic_regions(module, pattern, arguments={})
        )
        for fragment in index.fragments:
            if (
                fragment.context.structural_scope.pyobject is not module_scope.pyobject
                or word.get_word_at(fragment.start) not in {"if", "elif"}
            ):
                continue
            children = tuple(
                child
                for child in index.fragments
                if child.depth == fragment.depth + 1
                and fragment.start <= child.start < child.end <= fragment.end
            )
            if (
                children
                and (
                    min(children, key=lambda child: child.start).start,
                    min(children, key=lambda child: child.start).end,
                )
                in conditions
            ):
                guards.append((fragment.start, fragment.end))
        return tuple(guards)

    @staticmethod
    def public_export_names_source(
        source_module: p.Infra.RopeSourceModule,
    ) -> Sequence[str]:
        """Return the explicit public ABI through the bound native module's DSL.

        Returns:
            The explicit public ABI declared by one module source.

        """
        return (
            FlextInfraUtilitiesRopeAnalysisSourceScan.module_assignment_strings_source(
                source_module,
                c.Infra.DUNDER_ALL,
            )
        )

    @staticmethod
    @FlextInfraUtilitiesRopeRuntime.semantic_matching_context()
    def assignment_docstrings_source(
        source_module: p.Infra.RopeSourceModule,
    ) -> Sequence[str]:
        """Pair native direct assignment declarations with their following strings.

        Returns:
            Assignment names followed by a string-literal expression (rope-parsed).

        """
        names: list[str] = []
        previous_targets: tuple[str, ...] = ()
        for statement in source_module.get_source_binding_index().fragments:
            if statement.depth != 1:
                continue
            region = (statement.start, statement.end)
            if previous_targets and (
                FlextInfraUtilitiesRopeAnalysisSourceScan.literal_string_region(
                    source_module, region
                )
                is not None
            ):
                names.extend(previous_targets)
            previous_targets = (
                FlextInfraUtilitiesRopeAnalysisSourceScan.statement_declaration_names(
                    source_module, region, unpack_targets=False
                )
            )
        return tuple(dict.fromkeys(names))


__all__: list[str] = ["FlextInfraUtilitiesRopeAnalysisExports"]
