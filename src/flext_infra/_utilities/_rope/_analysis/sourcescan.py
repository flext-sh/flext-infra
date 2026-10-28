"""Source-level rope parsing, literal scanning, and reference extraction.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from collections.abc import Generator, MutableMapping, Sequence
from functools import cache
from typing import ClassVar

from flext_infra import c, t
from flext_infra._utilities._rope._analysis.asthelpers import (
    FlextInfraUtilitiesRopeAnalysisAstHelpers,
)


class FlextInfraUtilitiesRopeAnalysisSourceScan:
    """Source-level rope parsing, literal scanning, and reference extraction.

    Every ``*_source`` reader parses the module with :mod:`ast` and reads the
    node it needs; source that does not parse raises its ``SyntaxError``.
    """

    _INSTALL_LAZY_IMPORTS_ARG_INDEX: ClassVar[int] = 2

    @staticmethod
    @cache
    def parsed_module(source: str) -> ast.Module:
        """Parse one module source once per exact content.

        Every reader only inspects the tree, so one parse serves each repeated
        query over the same source; a source that does not parse raises its
        ``SyntaxError`` on every call.

        Returns:
            The parsed module.

        """
        return ast.parse(source)

    @staticmethod
    @cache
    def class_base_names(
        source: str,
    ) -> tuple[tuple[str, frozenset[str]], ...]:
        """Name every class one module source declares with its base spellings.

        Classes are statements, so only statement bodies are traversed;
        nested class, function, conditional and handler bodies included. A
        base is spelled by its last name (``m.Base[T]`` spells ``Base``).

        Returns:
            Each declared class name with the names its bases spell.

        """
        return FlextInfraUtilitiesRopeAnalysisSourceScan.module_class_base_names(
            FlextInfraUtilitiesRopeAnalysisSourceScan.parsed_module(source)
        )

    @staticmethod
    def module_class_base_names(
        module: ast.Module,
    ) -> tuple[tuple[str, frozenset[str]], ...]:
        """Read class names and base spellings from the existing module tree.

        Returns:
            Each class and its syntactic base names, including nested bodies.

        """
        found: list[tuple[str, frozenset[str]]] = []
        pending: list[ast.AST] = [module]
        while pending:
            node = pending.pop()
            for field in ("body", "orelse", "finalbody", "handlers", "cases"):
                for child in getattr(node, field, ()):
                    if isinstance(child, ast.ClassDef):
                        found.append((
                            child.name,
                            frozenset(
                                base.id if isinstance(base, ast.Name) else base.attr
                                for expression in child.bases
                                for base in (
                                    expression.value
                                    if isinstance(expression, ast.Subscript)
                                    else expression,
                                )
                                if isinstance(base, ast.Name | ast.Attribute)
                            ),
                        ))
                    if isinstance(child, ast.stmt | ast.excepthandler | ast.match_case):
                        pending.append(child)
        return tuple(found)

    @staticmethod
    @cache
    def absolute_import_roots(source: str) -> frozenset[str]:
        """Name the top-level packages one module source imports absolutely.

        Imports are statements, so only statement bodies are traversed:
        nested function, class, conditional and handler bodies included,
        expressions never. One traversal serves each exact content.

        Returns:
            The distinct top-level module names, without relative imports.

        """
        return FlextInfraUtilitiesRopeAnalysisSourceScan.module_absolute_import_roots(
            FlextInfraUtilitiesRopeAnalysisSourceScan.parsed_module(source)
        )

    @staticmethod
    def module_absolute_import_roots(module: ast.Module) -> frozenset[str]:
        """Read absolute import roots from an already parsed module.

        Returns:
            Top-level imported packages, including nested statement bodies.

        """
        found: set[str] = set()
        pending: list[ast.AST] = [module]
        while pending:
            node = pending.pop()
            for field in ("body", "orelse", "finalbody", "handlers", "cases"):
                for child in getattr(node, field, ()):
                    if isinstance(child, ast.Import):
                        found.update(
                            alias.name.partition(".")[0] for alias in child.names
                        )
                    elif isinstance(child, ast.ImportFrom):
                        if child.level == 0 and child.module:
                            found.add(child.module.partition(".")[0])
                    elif isinstance(
                        child, ast.stmt | ast.excepthandler | ast.match_case
                    ):
                        pending.append(child)
        return frozenset(found)

    @classmethod
    def single_module_import_binding(cls, tree: ast.Module, name: str) -> bool:
        """Report whether one module-level import is the name's only binding.

        Python then resolves every load of the name to that import, in any
        nested scope.

        Returns:
            True when exactly one import outside every function and class binds
            the name and no star import, assignment, parameter, definition,
            pattern capture, exception alias or scope declaration binds it.

        """
        module_level = sum(
            cls._import_binding_count(statement, name)
            for statement in cls._module_level_statements(tree.body)
        )
        bindings = 0
        for node in ast.walk(tree):
            match node:
                case ast.ImportFrom(names=names) if any(
                    alias.name == "*" for alias in names
                ):
                    return False
                case ast.Global(names=names) | ast.Nonlocal(names=names) if (
                    name in names
                ):
                    return False
                case ast.Import() | ast.ImportFrom():
                    bindings += cls._import_binding_count(node, name)
                case (
                    ast.Name(id=bound, ctx=ast.Store() | ast.Del())
                    | ast.arg(arg=bound)
                    | ast.FunctionDef(name=bound)
                    | ast.AsyncFunctionDef(name=bound)
                    | ast.ClassDef(name=bound)
                    | ast.MatchAs(name=bound)
                    | ast.MatchStar(name=bound)
                    | ast.MatchMapping(rest=bound)
                    | ast.ExceptHandler(name=bound)
                    | ast.TypeVar(name=bound)
                    | ast.ParamSpec(name=bound)
                    | ast.TypeVarTuple(name=bound)
                ) if bound == name:
                    bindings += 1
                case _:
                    pass
        return module_level == 1 and bindings == 1

    @staticmethod
    def _import_binding_count(statement: ast.stmt, name: str) -> int:
        """Count the aliases one import statement binds to ``name``.

        Returns:
            The number of aliases binding the name, zero for other statements.

        """
        if not isinstance(statement, ast.Import | ast.ImportFrom):
            return 0
        return sum(
            1
            for alias in statement.names
            if (alias.asname or alias.name.partition(".")[0]) == name
        )

    @classmethod
    def _module_level_statements(cls, body: Sequence[ast.stmt]) -> Generator[ast.stmt]:
        """Yield statements executed in the module scope, including guarded blocks.

        Yields:
            Each statement outside every function and class body.

        """
        for statement in body:
            yield statement
            match statement:
                case (
                    ast.If(body=inner, orelse=other)
                    | ast.While(body=inner, orelse=other)
                    | ast.For(body=inner, orelse=other)
                    | ast.AsyncFor(body=inner, orelse=other)
                ):
                    yield from cls._module_level_statements((*inner, *other))
                case ast.With(body=inner) | ast.AsyncWith(body=inner):
                    yield from cls._module_level_statements(inner)
                case (
                    ast.Try(
                        body=inner, handlers=handlers, orelse=other, finalbody=final
                    )
                    | ast.TryStar(
                        body=inner, handlers=handlers, orelse=other, finalbody=final
                    )
                ):
                    yield from cls._module_level_statements((
                        *inner,
                        *(item for handler in handlers for item in handler.body),
                        *other,
                        *final,
                    ))
                case ast.Match(cases=cases):
                    yield from cls._module_level_statements(
                        tuple(item for case in cases for item in case.body)
                    )
                case _:
                    pass

    @staticmethod
    def literal_string_sequence(node: t.Infra.RopeAstNode | None) -> Sequence[str]:
        """Return string entries from a parsed literal sequence node.

        Returns:
            String entries from a parsed literal sequence node.

        """
        if node is None:
            return ()
        if FlextInfraUtilitiesRopeAnalysisAstHelpers.node_kind(node) not in {
            "List",
            "Tuple",
            "Set",
        }:
            return ()
        values: list[str] = []
        for element in getattr(node, "elts", ()) or ():
            if not FlextInfraUtilitiesRopeAnalysisAstHelpers.ast_node(element):
                return ()
            element_kind = FlextInfraUtilitiesRopeAnalysisAstHelpers.node_kind(element)
            if element_kind == "Constant":
                value = getattr(element, "value", None)
            elif element_kind == "Str":
                value = getattr(element, "s", None)
            else:
                return ()
            if not isinstance(value, str):
                return ()
            values.append(value)
        return tuple(values)

    @staticmethod
    def export_declaration_body(module: ast.Module) -> Sequence[ast.stmt]:
        """Read metadata from the module or its single class-owned root.

        A module declaration wins over class metadata; unrelated nested classes
        never contribute package exports.

        Returns:
            The statement list owning the explicit export declaration.

        """
        for node in module.body:
            targets = (
                node.targets
                if isinstance(node, ast.Assign)
                else (node.target,)
                if isinstance(node, ast.AnnAssign)
                else ()
            )
            if any(
                isinstance(target, ast.Name) and target.id == "__all__"
                for target in targets
            ):
                return module.body
        roots = [node for node in module.body if isinstance(node, ast.ClassDef)]
        return roots[0].body if len(roots) == 1 else module.body

    @staticmethod
    def _top_level_value(source: str, name: str) -> ast.expr | None:
        """Return a module binding or its single root's export metadata.

        Parsing the module keeps assignments embedded in string literals (for
        example source templates inside tests) from reading as real bindings.

        Returns:
            The value node assigned in the owning declaration scope.

        """
        return FlextInfraUtilitiesRopeAnalysisSourceScan._module_top_level_value(
            FlextInfraUtilitiesRopeAnalysisSourceScan.parsed_module(source), name
        )

    @staticmethod
    def _module_top_level_value(module: ast.Module, name: str) -> ast.expr | None:
        """Read one binding from the supplied module's declaration scope.

        Returns:
            The original assigned expression, or None without a binding.

        """
        body = (
            FlextInfraUtilitiesRopeAnalysisSourceScan.export_declaration_body(module)
            if name == "__all__"
            else module.body
        )
        for node in body:
            if isinstance(node, ast.Assign):
                targets: Sequence[ast.expr] = node.targets
            elif isinstance(node, ast.AnnAssign):
                targets = (node.target,)
            else:
                continue
            if any(
                isinstance(target, ast.Name) and target.id == name for target in targets
            ):
                return node.value
        return None

    @staticmethod
    def _sequence_constructor_ref(value: ast.expr | None) -> str:
        """Return the name a value binds directly or wraps in one sequence constructor.

        Returns:
            The name a value binds directly or wraps in one sequence constructor.

        """
        if isinstance(value, ast.Name):
            return value.id
        if (
            isinstance(value, ast.Call)
            and isinstance(value.func, ast.Name)
            and value.func.id in {"tuple", c.Action.LIST, "frozenset", "set"}
            and len(value.args) == 1
            and not value.keywords
        ):
            wrapped = value.args[0]
            if isinstance(wrapped, ast.Name):
                return wrapped.id
        return ""

    @classmethod
    def module_assignment_strings_source(cls, source: str, name: str) -> Sequence[str]:
        """Collect literal module strings, including class-owned export metadata.

        Returns:
            The resulting ``Sequence[str]``.

        """
        return cls.module_assignment_strings(cls.parsed_module(source), name)

    @classmethod
    def module_assignment_strings(cls, module: ast.Module, name: str) -> Sequence[str]:
        """Read literal and named-sequence strings from an existing parse.

        Returns:
            The declared strings using the source reader's export semantics.

        """
        value = cls._module_top_level_value(module, name)
        values = cls.literal_string_sequence(value)
        if values:
            return values
        # Generated roots use ``__all__ = tuple(_PUBLIC_EXPORTS)``; follow the
        # bound name so docs validate matches the live lazy-init ABI.
        nested_name = cls._sequence_constructor_ref(value)
        if not nested_name or nested_name == name:
            return ()
        return cls.module_assignment_strings(module, nested_name)

    @classmethod
    def module_mapping_assignment_source(
        cls,
        source: str,
        name: str,
    ) -> tuple[tuple[tuple[str, Sequence[str]], ...], Sequence[str]]:
        """Collect mapping entries and referenced names from an assignment.

        Returns:
            The resulting ``tuple[tuple[tuple[str, Sequence[str]], ...],
                Sequence[str]]``.

        """
        return cls.mapping_entries_refs(cls._top_level_value(source, name))

    @staticmethod
    def mapping_entries_refs(
        node: t.Infra.RopeAstNode | None,
    ) -> tuple[tuple[tuple[str, Sequence[str]], ...], Sequence[str]]:
        """Return literal mapping entries plus variable references.

        Returns:
            Literal mapping entries plus variable references.

        """
        if node is None:
            return ((), ())
        kind = FlextInfraUtilitiesRopeAnalysisAstHelpers.node_kind(node)
        if kind == "Name":
            node_name = FlextInfraUtilitiesRopeAnalysisAstHelpers.name_of(node)
            return ((), (node_name,) if node_name else ())
        if kind == "Dict":
            return FlextInfraUtilitiesRopeAnalysisSourceScan._dict_entries_refs(node)
        if kind != "Call":
            return ((), ())
        return FlextInfraUtilitiesRopeAnalysisSourceScan._call_entries_refs(node)

    @classmethod
    def _call_entries_refs(
        cls,
        node: t.Infra.RopeAstNode,
    ) -> tuple[tuple[tuple[str, Sequence[str]], ...], Sequence[str]]:
        """Return entries and references of one mapping-producing call.

        Returns:
            Literal mapping entries plus variable references.

        """
        func = getattr(node, "func", None)
        function_name = (
            FlextInfraUtilitiesRopeAnalysisAstHelpers.name_of(func)
            if func is not None
            and FlextInfraUtilitiesRopeAnalysisAstHelpers.ast_node(func)
            else ""
        )
        args = getattr(node, "args", ()) or ()
        if function_name in {"MappingProxyType", "build_lazy_import_map"} and args:
            first_arg = args[0]
            if FlextInfraUtilitiesRopeAnalysisAstHelpers.ast_node(first_arg):
                return FlextInfraUtilitiesRopeAnalysisSourceScan.mapping_entries_refs(
                    first_arg,
                )
        if function_name != "merge_lazy_imports":
            return ((), ())
        entries: list[tuple[str, Sequence[str]]] = []
        refs: list[str] = []
        for argument in args:
            if not FlextInfraUtilitiesRopeAnalysisAstHelpers.ast_node(argument):
                continue
            next_entries, next_refs = (
                FlextInfraUtilitiesRopeAnalysisSourceScan.mapping_entries_refs(argument)
            )
            entries.extend(next_entries)
            refs.extend(next_refs)
        return (tuple(entries), tuple(dict.fromkeys(refs)))

    @staticmethod
    def _dict_entries_refs(
        node: t.Infra.RopeAstNode,
    ) -> tuple[tuple[tuple[str, Sequence[str]], ...], Sequence[str]]:
        """Return string-sequence dict entries and unpack references.

        Returns:
            String-sequence dict entries and unpack references.

        """
        keys = getattr(node, "keys", ()) or ()
        values = getattr(node, "values", ()) or ()
        entries: list[tuple[str, Sequence[str]]] = []
        refs: list[str] = []
        for key_node, value_node in zip(keys, values, strict=False):
            if key_node is None:
                if FlextInfraUtilitiesRopeAnalysisAstHelpers.ast_node(value_node):
                    ref_name = FlextInfraUtilitiesRopeAnalysisAstHelpers.name_of(
                        value_node,
                    )
                    if ref_name:
                        refs.append(ref_name)
                continue
            if not FlextInfraUtilitiesRopeAnalysisAstHelpers.ast_node(key_node):
                continue
            key_value = getattr(key_node, "value", None)
            if not isinstance(key_value, str):
                continue
            if FlextInfraUtilitiesRopeAnalysisAstHelpers.ast_node(value_node):
                value_strings = (
                    FlextInfraUtilitiesRopeAnalysisSourceScan.literal_string_sequence(
                        value_node,
                    )
                )
            else:
                value_strings = ()
            if value_strings:
                entries.append((key_value, value_strings))
        return (tuple(entries), tuple(dict.fromkeys(refs)))

    @staticmethod
    def relative_import_module_name(
        *,
        current_module: str,
        imported_module: str,
        level: int,
        package_module: bool,
    ) -> str:
        """Resolve a parsed ``from`` import module into an absolute module name.

        Returns:
            The resulting ``str``.

        """
        if level == 0:
            return imported_module
        current_parts = current_module.split(".")
        base_count = len(current_parts) - level + (1 if package_module else 0)
        base = ".".join(current_parts[: max(base_count, 0)])
        return ".".join(part for part in (base, imported_module) if part)

    @classmethod
    def imported_symbol_binding_source(
        cls,
        source: str,
        *,
        current_module: str,
        symbol_name: str,
        package_module: bool,
    ) -> tuple[str, str]:
        """Return ``(module, original_name)`` for one imported symbol binding.

        Returns:
            ``(module, original_name)`` for one imported symbol binding.

        """
        imports = sorted(
            (
                node
                for node in ast.walk(
                    FlextInfraUtilitiesRopeAnalysisSourceScan.parsed_module(source)
                )
                if isinstance(node, ast.ImportFrom)
            ),
            key=lambda node: (node.lineno, node.col_offset),
        )
        for node in imports:
            for alias in node.names:
                if (alias.asname or alias.name) != symbol_name:
                    continue
                relative_module_name = cls.relative_import_module_name
                module_name = relative_module_name(
                    current_module=current_module,
                    imported_module=node.module or "",
                    level=node.level,
                    package_module=package_module,
                )
                return (module_name, alias.name)
        return ("", "")

    @staticmethod
    def _top_level_class(source: str, class_name: str) -> ast.ClassDef | None:
        """Return the top-level class statement named ``class_name``.

        Returns:
            The top-level class statement named ``class_name``.

        """
        for node in FlextInfraUtilitiesRopeAnalysisSourceScan.parsed_module(
            source
        ).body:
            if isinstance(node, ast.ClassDef) and node.name == class_name:
                return node
        return None

    @staticmethod
    def class_bases_source(source: str, class_name: str) -> Sequence[str]:
        """Return declared base names for one class in source.

        Returns:
            Declared base names for one class in source.

        """
        node = FlextInfraUtilitiesRopeAnalysisSourceScan._top_level_class(
            source,
            class_name,
        )
        if node is None:
            return ()
        return tuple(
            base_name
            for base in node.bases
            if (base_name := FlextInfraUtilitiesRopeAnalysisAstHelpers.name_of(base))
        )

    @staticmethod
    def class_declared_source(source: str, class_name: str) -> bool:
        """Return whether one class is declared at the top level of source.

        Returns:
            Whether one class is declared at the top level of source.

        """
        return (
            FlextInfraUtilitiesRopeAnalysisSourceScan._top_level_class(
                source,
                class_name,
            )
            is not None
        )

    @staticmethod
    def _module_mapping_binding(source: str, reference: str) -> ast.Dict | None:
        """Resolve one module-level mapping binding to its literal dict node.

        Members declare the lazy-import map as a named, annotated assignment
        (``_EXPORT_MODULES: MappingProxyType[str, str] = MappingProxyType(
        {...})``) and hand the installer the name. The binding lives in the
        same module body, so the reference resolves statically; only a name
        with no module-level ``MappingProxyType``/dict assignment stays
        unresolved.

        Returns:
            The mapping dict node, or None when the name has no resolvable
            module-level assignment.

        """
        try:
            tree = FlextInfraUtilitiesRopeAnalysisSourceScan.parsed_module(source)
        except SyntaxError:
            return None
        for node in tree.body:
            if isinstance(node, ast.Assign):
                targets: list[ast.expr] = list(node.targets)
                value: ast.expr | None = node.value
            elif isinstance(node, ast.AnnAssign):
                targets = [node.target]
                value = node.value
            else:
                continue
            if not any(
                isinstance(target, ast.Name) and target.id == reference
                for target in targets
            ):
                continue
            if value is None:
                return None
            if (
                isinstance(value, ast.Call)
                and isinstance(value.func, ast.Name)
                and value.func.id == "MappingProxyType"
                and value.args
            ):
                value = value.args[0]
            if (
                isinstance(value, ast.Call)
                and isinstance(value.func, ast.Name)
                and value.func.id == "build_lazy_import_map"
                and value.args
            ):
                inner = value.args[0]
                if (
                    isinstance(inner, ast.Call)
                    and isinstance(inner.func, ast.Name)
                    and inner.func.id == "MappingProxyType"
                    and inner.args
                ):
                    inner = inner.args[0]
                value = (
                    FlextInfraUtilitiesRopeAnalysisSourceScan._expanded_lazy_import_map(
                        inner,
                    )
                )
            return value if isinstance(value, ast.Dict) else None
        return None

    @staticmethod
    def _expanded_lazy_import_map(mapping: ast.expr) -> ast.expr | None:
        """Expand the declared ``module: alias-tuple`` build input.

        ``build_lazy_import_map`` receives the authoring shape — one entry
        per module mapping to its export aliases — while the installer
        consumes the resolved shape, one entry per alias pointing back at
        its module. The scanner reads the authoring shape and expands it
        statically, so a generated module declares exactly what it
        installs and the declared-mapping invariant holds for the idiom
        the base template emits.

        Returns:
            The expanded literal dict node, or None when the input is not
            a static string mapping.

        """
        if not isinstance(mapping, ast.Dict):
            return None
        keys: list[ast.expr | None] = []
        values: list[ast.expr] = []
        for module_key, aliases in zip(mapping.keys, mapping.values, strict=True):
            if not isinstance(module_key, ast.Constant) or not isinstance(
                module_key.value,
                str,
            ):
                return None
            if not isinstance(aliases, c.Infra.AST_SEQUENCE_DISPLAY_TYPES):
                return None
            for alias in aliases.elts:
                if not isinstance(alias, ast.Constant) or not isinstance(
                    alias.value,
                    str,
                ):
                    return None
                keys.append(ast.Constant(value=alias.value))
                values.append(
                    ast.Tuple(
                        elts=[
                            ast.Constant(value=module_key.value),
                            ast.Constant(value=""),
                        ],
                    ),
                )
        return ast.Dict(keys=keys, values=values)

    @staticmethod
    def _first_call(source: str, function_name: str) -> ast.Call | None:
        """Return the first call, in source order, whose callee is ``function_name``.

        Returns:
            The first call, in source order, whose callee is ``function_name``.

        """
        calls = sorted(
            (
                node
                for node in ast.walk(
                    FlextInfraUtilitiesRopeAnalysisSourceScan.parsed_module(source)
                )
                if isinstance(node, ast.Call)
                and FlextInfraUtilitiesRopeAnalysisAstHelpers.name_of(node.func)
                == function_name
            ),
            key=lambda node: (node.lineno, node.col_offset),
        )
        return calls[0] if calls else None

    @staticmethod
    def _keyword_value(call: ast.Call | None, keyword: str) -> ast.expr | None:
        """Return one keyword argument value of a call.

        Returns:
            One keyword argument value of a call.

        """
        if call is None:
            return None
        return next((item.value for item in call.keywords if item.arg == keyword), None)

    @classmethod
    def lazy_public_exports_source(cls, source: str) -> tuple[Sequence[str], str]:
        """Return lazy-loader public exports or the local symbol holding them.

        Returns:
            Lazy-loader public exports or the local symbol holding them.

        """
        public_exports = cls._keyword_value(
            cls._first_call(source, "install_lazy_exports"),
            "public_exports",
        )
        if public_exports is None:
            return ((), "")
        values = cls.literal_string_sequence(public_exports)
        if values:
            return (values, "")
        return ((), FlextInfraUtilitiesRopeAnalysisAstHelpers.name_of(public_exports))

    @classmethod
    @cache
    def lazy_import_mapping_source(
        cls,
        source: str,
    ) -> tuple[tuple[tuple[str, Sequence[str]], ...], Sequence[str]]:
        """Read elected installer targets, including immutable inline mappings.

        Cache parsing by exact source content, not a path or filesystem timestamp.

        Returns:
            Target modules and their export names, plus referenced map symbols.

        """
        call = cls._first_call(source, "install_lazy_exports")
        if call is None:
            return ((), ())
        value = (
            call.args[cls._INSTALL_LAZY_IMPORTS_ARG_INDEX]
            if len(call.args) > cls._INSTALL_LAZY_IMPORTS_ARG_INDEX
            else cls._keyword_value(call, "lazy_imports")
        )
        match value:
            case ast.Name(id=reference):
                value = cls._module_mapping_binding(source, reference)
                if value is None:
                    return ((), (reference,))
            case ast.Call(func=ast.Name(id="MappingProxyType"), args=[mapping]):
                value = mapping
            case _:
                pass
        if not isinstance(value, ast.Dict):
            return cls.mapping_entries_refs(value)
        targets: MutableMapping[str, list[str]] = {}
        for key, target in zip(value.keys, value.values, strict=True):
            match key, target:
                case (
                    ast.Constant(value=str(name)),
                    ast.Constant(value=str(module)),
                ) | (
                    ast.Constant(value=str(name)),
                    ast.Tuple(
                        elts=[
                            ast.Constant(value=str(module)),
                            ast.Constant(value=str()),
                        ],
                    ),
                ):
                    targets.setdefault(module, []).append(name)
                case _:
                    continue
        return (
            tuple((module, tuple(targets[module])) for module in sorted(targets)),
            (),
        )

    @staticmethod
    def export_target_modules_source(
        source: str,
        package_name: str,
        exports: Sequence[str],
    ) -> MutableMapping[str, str]:
        """Map exports → defining module via rope's parsed-source import table.

        Returns:
            The resulting ``MutableMapping[str, str]``.

        """
        export_names = {name for name in exports if name}
        target_map: MutableMapping[str, str] = dict.fromkeys(export_names, package_name)
        pymodule = FlextInfraUtilitiesRopeAnalysisAstHelpers.parse_string_module(source)
        module_ast = pymodule.get_ast()
        for node in FlextInfraUtilitiesRopeAnalysisAstHelpers.walk_ast_nodes(
            module_ast,
        ):
            kind = FlextInfraUtilitiesRopeAnalysisAstHelpers.node_kind(node)
            if kind == "ImportFrom":
                module_name = getattr(node, "module", "") or ""
                names = getattr(node, "names", []) or []
                for alias in names:
                    local = getattr(alias, "asname", None) or getattr(alias, "name", "")
                    if isinstance(local, str) and local in export_names and module_name:
                        target_map[local] = module_name
            elif kind == "Import":
                names = getattr(node, "names", []) or []
                for alias in names:
                    raw_name = getattr(alias, "name", "") or ""
                    local = getattr(alias, "asname", None) or raw_name.partition(".")[0]
                    if isinstance(local, str) and local in export_names and raw_name:
                        module_name = (
                            raw_name.rsplit(".", maxsplit=1)[0]
                            if "." in raw_name
                            else raw_name
                        )
                        target_map[local] = module_name
        return target_map


__all__: list[str] = ["FlextInfraUtilitiesRopeAnalysisSourceScan"]
