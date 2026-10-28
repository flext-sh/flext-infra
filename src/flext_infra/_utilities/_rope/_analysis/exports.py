"""Rope export-name resolution, scopes, and docstring summaries.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)

import ast
from collections.abc import MutableSequence, Sequence

from flext_infra import c, m, t
from flext_infra._utilities._rope._analysis.asthelpers import (
    FlextInfraUtilitiesRopeAnalysisAstHelpers,
)
from flext_infra._utilities._rope._analysis.sourcescan import (
    FlextInfraUtilitiesRopeAnalysisSourceScan,
)
from flext_infra._utilities._rope.rope_runtime import FlextInfraUtilitiesRopeRuntime


class FlextInfraUtilitiesRopeAnalysisExports:
    """Rope export-name resolution, scopes, and docstring summaries."""

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
    def module_export_names_source(
        source: str,
        *,
        export_options: m.Infra.ExportOptions | None = None,
    ) -> Sequence[str]:
        """Return module-local exports from one parsed source snapshot.

        Returns:
            Module-local exports from one parsed source snapshot.

        """
        resolved_options = export_options or m.Infra.ExportOptions()
        module = ast.parse(source)
        inventory = FlextInfraUtilitiesRopeAnalysisExports._source_binding_inventory(
            module.body,
        )
        assignments = inventory[0]
        definitions = inventory[1]
        explicit_all = inventory[2]
        if not explicit_all:
            explicit_all = (
                FlextInfraUtilitiesRopeAnalysisExports._source_binding_inventory(
                    FlextInfraUtilitiesRopeAnalysisSourceScan.export_declaration_body(
                        module
                    ),
                )[2]
            )
        if explicit_all:
            return tuple(
                dict.fromkeys(
                    FlextInfraUtilitiesRopeAnalysisSourceScan.module_assignment_strings_source(
                        source,
                        c.Infra.DUNDER_ALL,
                    ),
                ),
            )
        if resolved_options.require_explicit_all:
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
        statements: Sequence[ast.stmt],
    ) -> tuple[
        MutableSequence[str],
        MutableSequence[tuple[str, bool]],
        bool,
    ]:
        """Inventory one statement list's assignments, definitions, and ``__all__``.

        Returns:
            The assignment names, the definition name and class-kind pairs,
            and whether ``__all__`` was bound.

        """
        collector = FlextInfraUtilitiesRopeAnalysisExports.BindingInventory()
        collector.collect_statements(statements)
        return (collector.assignments, collector.definitions, collector.explicit_all)

    @staticmethod
    def public_export_names_source(source: str) -> Sequence[str]:
        """Return the explicit public ABI declared by one module source.

        Returns:
            The explicit public ABI declared by one module source.

        """
        return (
            FlextInfraUtilitiesRopeAnalysisSourceScan.module_assignment_strings_source(
                source,
                c.Infra.DUNDER_ALL,
            )
        )

    @staticmethod
    def module_has_docstring_source(source: str) -> bool:
        """Return whether ``source`` starts with a module docstring (rope-parsed).

        Returns:
            Whether ``source`` starts with a module docstring (rope-parsed).

        """
        pymodule = FlextInfraUtilitiesRopeAnalysisAstHelpers.parse_string_module(source)
        return bool(pymodule.get_doc())

    @staticmethod
    def module_docstring_summary_source(source: str) -> str:
        """Return the PEP 257 summary line of the module docstring (rope-parsed).

        Returns:
            The PEP 257 summary line of the module docstring (rope-parsed).

        """
        pymodule = FlextInfraUtilitiesRopeAnalysisAstHelpers.parse_string_module(source)
        doc = pymodule.get_doc() or ""
        summary = next((line for line in doc.splitlines() if line.strip()), "")
        # The summary is rendered verbatim into generated markdown, where runs
        # of spaces are a lint failure nobody can hand-fix in a generated file.
        # Collapsing them here keeps the summary faithful and renderable.
        return " ".join(summary.split())

    @staticmethod
    def symbol_has_docstring_source(source: str, symbol_name: str) -> bool:
        """Check a locally defined symbol; imported docs need module context.

        Returns:
            The resulting ``bool``.

        """
        pymodule = FlextInfraUtilitiesRopeAnalysisAstHelpers.parse_string_module(source)
        pyname = pymodule.get_attributes().get(symbol_name)
        if pyname is None or not FlextInfraUtilitiesRopeRuntime.defined_name(pyname):
            return False
        obj = pyname.get_object()
        get_doc = getattr(obj, "get_doc", None)
        if not callable(get_doc):
            # Plain PyObjects (assignments, imports) carry no docstring.
            return False
        return bool(get_doc())

    @staticmethod
    def assignment_docstrings_source(source: str) -> Sequence[str]:
        """Return assignment names followed by a string literal (rope-parsed).

        Iterates the parsed module's body via ``_fields`` access and pairs each
        ``Assign``/``AnnAssign``/PEP-695 ``TypeAlias`` target with the next
        sibling ``Expr(Constant(str))``.

        Returns:
            Assignment names followed by a string-literal expression (rope-parsed).

        """
        pymodule = FlextInfraUtilitiesRopeAnalysisAstHelpers.parse_string_module(source)
        module_ast = pymodule.get_ast()
        body = getattr(module_ast, "body", []) or []
        names: list[str] = []
        previous_targets: list[str] = []
        for statement in body:
            kind = FlextInfraUtilitiesRopeAnalysisAstHelpers.node_kind(statement)
            if kind in {"Assign", "AnnAssign", "TypeAlias"}:
                previous_targets = (
                    FlextInfraUtilitiesRopeAnalysisAstHelpers.statement_target_names(
                        statement,
                    )
                )
                continue
            if kind == "Expr" and previous_targets:
                value = getattr(statement, "value", None)
                if (
                    value is not None
                    and FlextInfraUtilitiesRopeAnalysisAstHelpers.node_kind(value)
                    == "Constant"
                    and isinstance(getattr(value, "value", None), str)
                ):
                    names.extend(previous_targets)
            previous_targets = []
        return tuple(dict.fromkeys(names))

    @staticmethod
    def module_body_nodes_source(source: str) -> Sequence[t.Infra.RopeAstNode]:
        """Return top-level parsed statements for one source module.

        Returns:
            Top-level parsed statements for one source module.

        """
        del source
        return ()

    @staticmethod
    def module_reachable_nodes_source(source: str) -> Sequence[t.Infra.RopeAstNode]:
        """Return parsed nodes reachable from one source module.

        Returns:
            Parsed nodes reachable from one source module.

        """
        del source
        return ()

    class BindingInventory:
        """Inventory one statement list's exports, definitions, and ``__all__``."""

        def __init__(self) -> None:
            """Initialize the empty inventory."""
            self.assignments: MutableSequence[str] = []
            self.definitions: MutableSequence[tuple[str, bool]] = []
            self.explicit_all = False

        def collect_statements(self, statements: Sequence[ast.stmt]) -> None:
            """Inventory each statement in declaration order.

            Parameters:
                statements: The module or block statements to inventory.

            """
            for statement in statements:
                self._dispatch(statement)

        def _dispatch(self, statement: ast.stmt) -> None:
            """Route one statement to its inventory handler."""
            if isinstance(statement, c.Infra.AST_DEFINITION_TYPES):
                self._define(statement)
            elif isinstance(statement, c.Infra.AST_IMPORT_TYPES):
                return
            elif isinstance(statement, ast.If):
                self._if(statement)
            elif isinstance(statement, (ast.For, ast.AsyncFor, ast.While)):
                self._collect_branches(statement)
            elif isinstance(statement, c.Infra.AST_WITH_TYPES):
                self.collect_statements(statement.body)
            elif isinstance(statement, c.Infra.AST_TRY_TYPES):
                self._try(statement)
            elif isinstance(statement, ast.Match):
                self._match(statement)
            else:
                self._assign(statement)

        def _define(
            self,
            statement: ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef,
        ) -> None:
            """Record one definition and whether it declares a class."""
            self.definitions.append((
                statement.name,
                isinstance(statement, ast.ClassDef),
            ))

        def _assign(self, statement: ast.stmt) -> None:
            """Record one assignment statement's bound names."""
            names = self._bound_statement_names(statement)
            if not names:
                return
            self.explicit_all = self.explicit_all or c.Infra.DUNDER_ALL in names
            self.assignments.extend(
                name for name in names if name != c.Infra.DUNDER_ALL
            )

        def _bound_statement_names(self, statement: ast.stmt) -> Sequence[str]:
            """Return the names one assignment statement binds.

            Returns:
                The resulting ``Sequence[str]``.

            """
            if isinstance(statement, ast.Assign):
                return tuple(
                    name
                    for target in statement.targets
                    for name in self._bound_names(target)
                )
            if isinstance(statement, (ast.AnnAssign, ast.AugAssign)):
                return self._bound_names(statement.target)
            return ()

        def _if(self, statement: ast.If) -> None:
            """Inventory one conditional statement's statically executed branches."""
            if self._main_guard(statement):
                return
            self.collect_statements(statement.body)
            self.collect_statements(statement.orelse)

        def _collect_branches(
            self,
            statement: ast.For | ast.AsyncFor | ast.While,
        ) -> None:
            """Inventory one loop statement's body and else branch."""
            self.collect_statements(statement.body)
            self.collect_statements(statement.orelse)

        def _try(self, statement: ast.Try | ast.TryStar) -> None:
            """Inventory one try statement's handlers, else, and finally blocks."""
            self.collect_statements(statement.body)
            for handler in statement.handlers:
                self.collect_statements(handler.body)
            self.collect_statements(statement.orelse)
            self.collect_statements(statement.finalbody)

        def _match(self, statement: ast.Match) -> None:
            """Inventory one match statement's case bodies."""
            for case in statement.cases:
                self.collect_statements(case.body)

        @staticmethod
        def _main_guard(statement: ast.If) -> bool:
            """Return whether one if statement is the ``__main__`` guard.

            Returns:
                Whether one if statement is the ``__main__`` guard.

            """
            test = statement.test
            sides = (
                (test.left, test.comparators[0])
                if isinstance(test, ast.Compare)
                and len(test.ops) == 1
                and isinstance(test.ops[0], ast.Eq)
                and len(test.comparators) == 1
                else ()
            )
            names_in_test = {side.id for side in sides if isinstance(side, ast.Name)}
            values_in_test = {
                side.value for side in sides if isinstance(side, ast.Constant)
            }
            return names_in_test == {"__name__"} and values_in_test == {"__main__"}

        def _bound_names(self, target: ast.expr) -> Sequence[str]:
            """Return the names one assignment target binds.

            Returns:
                The resulting ``Sequence[str]``.

            """
            if isinstance(target, ast.Name):
                return (target.id,)
            if isinstance(target, c.Infra.AST_SEQUENCE_DISPLAY_TYPES):
                return tuple(
                    name
                    for element in target.elts
                    for name in self._bound_names(element)
                )
            return ()


__all__: list[str] = ["FlextInfraUtilitiesRopeAnalysisExports"]
