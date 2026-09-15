"""Source-slice parsing and export-name analysis."""

from __future__ import annotations

import ast
from collections.abc import MutableMapping
from typing import TYPE_CHECKING

from flext_infra.constants import c
from flext_infra.models import m
from flext_infra.typings import t

from ..rope_core import FlextInfraUtilitiesRopeCore
from ..rope_runtime import FlextInfraUtilitiesRopeRuntime

if TYPE_CHECKING:
    from collections.abc import Iterator

    from flext_infra.protocols import p

from .base import FlextInfraUtilitiesRopeAnalysisBase
from .imports import FlextInfraUtilitiesRopeAnalysisImports
from .nodes import FlextInfraUtilitiesRopeAnalysisNodes
from .scope import FlextInfraUtilitiesRopeAnalysisScope


class FlextInfraUtilitiesRopeAnalysisSource(FlextInfraUtilitiesRopeAnalysisScope):
    """Source-slice parsing and export-name analysis."""

    @staticmethod
    def get_module_export_names(
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
        *,
        export_options: m.Infra.ExportOptions | None = None,
    ) -> t.StrSequence:
        """Return module-local export names from Rope metadata."""
        resolved_export_options = export_options or m.Infra.ExportOptions()
        cache_key = (
            *FlextInfraUtilitiesRopeAnalysisImports._resource_cache_key(
                rope_project, resource
            ),
            resolved_export_options.include_dunder,
            resolved_export_options.allow_main,
            resolved_export_options.allow_assignments,
            resolved_export_options.allow_functions,
            resolved_export_options.require_explicit_all,
        )
        cached = FlextInfraUtilitiesRopeAnalysisBase._EXPORT_NAMES_CACHE.get(cache_key)
        export_names: t.StrSequence
        if cached is not None:
            export_names = cached
        else:
            pymodule = FlextInfraUtilitiesRopeCore.get_pymodule(rope_project, resource)
            export_names = FlextInfraUtilitiesRopeAnalysisSource._module_export_names(
                export_options=resolved_export_options,
                pymodule=pymodule,
                resource=resource,
            )
            FlextInfraUtilitiesRopeAnalysisBase._EXPORT_NAMES_CACHE[cache_key] = (
                export_names
            )
        return export_names

    @staticmethod
    def module_export_names_source(
        source: str, *, export_options: m.Infra.ExportOptions | None = None
    ) -> t.StrSequence:
        """Return module-local exports from one parsed source snapshot."""
        resolved_options = export_options or m.Infra.ExportOptions()
        module = ast.parse(source)
        assignments: t.MutableSequenceOf[str] = []
        definitions: t.MutableSequenceOf[t.Pair[str, bool]] = []
        explicit_all = False

        def bound_names(target: ast.expr) -> t.StrSequence:
            if isinstance(target, ast.Name):
                return (target.id,)
            if isinstance(target, (ast.List, ast.Tuple)):
                return tuple(
                    name for element in target.elts for name in bound_names(element)
                )
            return ()

        def collect(statements: t.SequenceOf[ast.stmt]) -> None:
            nonlocal explicit_all
            for statement in statements:
                if isinstance(
                    statement, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
                ):
                    definitions.append((
                        statement.name,
                        isinstance(statement, ast.ClassDef),
                    ))
                    continue
                if isinstance(statement, ast.Assign):
                    names = tuple(
                        name
                        for target in statement.targets
                        for name in bound_names(target)
                    )
                elif isinstance(statement, (ast.AnnAssign, ast.AugAssign)):
                    names = bound_names(statement.target)
                else:
                    names = ()
                if names:
                    explicit_all = explicit_all or c.Infra.DUNDER_ALL in names
                    assignments.extend(
                        name for name in names if name != c.Infra.DUNDER_ALL
                    )
                    continue
                if isinstance(statement, (ast.Import, ast.ImportFrom)):
                    continue
                if isinstance(statement, ast.If):
                    sides = (
                        (statement.test.left, statement.test.comparators[0])
                        if isinstance(statement.test, ast.Compare)
                        and len(statement.test.ops) == 1
                        and isinstance(statement.test.ops[0], ast.Eq)
                        and len(statement.test.comparators) == 1
                        else ()
                    )
                    names_in_test = {
                        side.id for side in sides if isinstance(side, ast.Name)
                    }
                    values_in_test = {
                        side.value for side in sides if isinstance(side, ast.Constant)
                    }
                    if names_in_test == {"__name__"} and values_in_test == {"__main__"}:
                        continue
                    collect(statement.body)
                    collect(statement.orelse)
                    continue
                if isinstance(statement, (ast.For, ast.AsyncFor, ast.While)):
                    collect(statement.body)
                    collect(statement.orelse)
                    continue
                if isinstance(statement, (ast.With, ast.AsyncWith)):
                    collect(statement.body)
                    continue
                if isinstance(statement, (ast.Try, ast.TryStar)):
                    collect(statement.body)
                    for handler in statement.handlers:
                        collect(handler.body)
                    collect(statement.orelse)
                    collect(statement.finalbody)
                    continue
                if isinstance(statement, ast.Match):
                    for case in statement.cases:
                        collect(case.body)

        collect(module.body)
        if resolved_options.include_dunder:
            return tuple(
                dict.fromkeys(
                    name
                    for name in assignments
                    if name.startswith("__") and name.endswith("__")
                )
            )
        if explicit_all:
            return tuple(
                dict.fromkeys(
                    FlextInfraUtilitiesRopeAnalysisSource.module_assignment_strings_source(
                        source, c.Infra.DUNDER_ALL
                    )
                )
            )
        if resolved_options.require_explicit_all:
            return ()
        implicit_names: t.MutableSequenceOf[str] = [
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
    def _module_export_names(
        *,
        export_options: m.Infra.ExportOptions,
        pymodule: t.Infra.RopePyModule,
        resource: t.Infra.RopeResource,
    ) -> t.StrSequence:
        """Return export names for one resolved Rope module."""
        attributes = pymodule.get_attributes()
        if export_options.include_dunder:
            return FlextInfraUtilitiesRopeAnalysisSource._dunder_export_names(
                attributes=attributes, resource=resource
            )
        explicit_all = FlextInfraUtilitiesRopeAnalysisSource._explicit_export_names(
            attributes=attributes, pymodule=pymodule, resource=resource
        )
        if explicit_all is not None:
            return tuple(dict.fromkeys(explicit_all))
        if export_options.require_explicit_all:
            return ()
        return FlextInfraUtilitiesRopeAnalysisSource._implicit_export_names(
            attributes=attributes,
            export_options=export_options,
            resource=resource,
            pymodule=pymodule,
        )

    @staticmethod
    def _dunder_export_names(
        *,
        attributes: t.MappingKV[str, t.Infra.RopePyName],
        resource: t.Infra.RopeResource,
    ) -> t.StrSequence:
        """Return locally assigned dunder export names."""
        return tuple(
            dict.fromkeys(
                name
                for name, pyname in attributes.items()
                if name != c.Infra.DUNDER_ALL
                and name.startswith("__")
                and name.endswith("__")
                and FlextInfraUtilitiesRopeRuntime.is_assigned_name(pyname)
                and FlextInfraUtilitiesRopeAnalysisImports._is_local_name(
                    pyname, resource
                )
            )
        )

    @staticmethod
    def _explicit_export_names(
        *,
        attributes: t.MappingKV[str, t.Infra.RopePyName],
        pymodule: t.Infra.RopePyModule,
        resource: t.Infra.RopeResource,
    ) -> t.StrSequence | None:
        """Return explicit ``__all__`` export names when declared locally."""
        explicit_all_name = attributes.get(c.Infra.DUNDER_ALL)
        if (
            explicit_all_name is None
            or not FlextInfraUtilitiesRopeRuntime.is_assigned_name(explicit_all_name)
        ):
            return None
        assigned_all: t.Infra.RopeAssignedName = explicit_all_name
        if not FlextInfraUtilitiesRopeAnalysisImports._is_local_name(
            assigned_all, resource
        ):
            return None
        return FlextInfraUtilitiesRopeAnalysisSource._explicit_all_names(
            assigned_all, pymodule
        )

    @staticmethod
    def _implicit_export_names(
        *,
        attributes: t.MappingKV[str, t.Infra.RopePyName],
        export_options: m.Infra.ExportOptions,
        resource: t.Infra.RopeResource,
        pymodule: t.Infra.RopePyModule,
    ) -> t.StrSequence:
        """Return implicit export names accepted by the export options."""
        guard_spans = FlextInfraUtilitiesRopeAnalysisSource._script_guard_spans(
            pymodule
        )
        names: t.MutableSequenceOf[str] = []
        for name, pyname in attributes.items():
            if name == c.Infra.DUNDER_ALL:
                continue
            if not FlextInfraUtilitiesRopeAnalysisImports._is_local_name(
                pyname, resource
            ):
                continue
            if FlextInfraUtilitiesRopeAnalysisSource._is_export_name(
                export_options=export_options,
                name=name,
                pyname=pyname,
                guard_spans=guard_spans,
            ):
                names.append(name)
        return tuple(dict.fromkeys(names))

    @staticmethod
    def _script_guard_spans(
        pymodule: t.Infra.RopePyModule,
    ) -> t.SequenceOf[t.Pair[int, int]]:
        """Return the line spans of top-level ``if __name__ == "__main__":`` blocks.

        Names bound there exist only when the module runs as a script; a
        package facade that re-exported them (flext-core's examples exported
        ``result`` and ``msg``) failed every importer.
        """
        module_ast = pymodule.get_ast()
        body = getattr(module_ast, "body", ())
        spans: t.MutableSequenceOf[t.Pair[int, int]] = []
        for node in body:
            if not isinstance(node, ast.If):
                continue
            test = node.test
            if not (
                isinstance(test, ast.Compare)
                and len(test.ops) == 1
                and isinstance(test.ops[0], ast.Eq)
                and len(test.comparators) == 1
            ):
                continue
            sides = (test.left, test.comparators[0])
            names = {side.id for side in sides if isinstance(side, ast.Name)}
            values = {side.value for side in sides if isinstance(side, ast.Constant)}
            if names == {"__name__"} and values == {"__main__"}:
                spans.append((node.lineno, node.end_lineno or node.lineno))
        return tuple(spans)

    @staticmethod
    def _is_export_name(
        *,
        export_options: m.Infra.ExportOptions,
        name: str,
        pyname: t.Infra.RopePyName,
        guard_spans: t.SequenceOf[t.Pair[int, int]] = (),
    ) -> bool:
        """Return whether one Rope name is exportable under the options."""
        if FlextInfraUtilitiesRopeRuntime.is_imported_name(pyname):
            return False
        if FlextInfraUtilitiesRopeRuntime.is_assigned_name(pyname):
            allow_assignments: bool = export_options.allow_assignments
            if not allow_assignments:
                return False
            lines = tuple(
                line
                for assignment in pyname.assignments
                if (line := getattr(assignment.ast_node, "lineno", None)) is not None
            )
            return not lines or not all(
                any(start <= line <= end for start, end in guard_spans)
                for line in lines
            )
        if not FlextInfraUtilitiesRopeRuntime.is_defined_name(pyname):
            return False
        obj = pyname.get_object()
        if FlextInfraUtilitiesRopeRuntime.is_abstract_class(obj):
            return True
        if not FlextInfraUtilitiesRopeRuntime.is_py_function(obj):
            return False
        allow_main: bool = export_options.allow_main
        allow_functions: bool = export_options.allow_functions
        return (allow_main and name == "main") or allow_functions

    @staticmethod
    def _explicit_all_names(
        pyname: t.Infra.RopeAssignedName, pymodule: t.Infra.RopePyModule
    ) -> t.StrSequence | None:
        """Return literal ``__all__`` names from a Rope-cached source slice.

        Reads the assignment's source range via the module's ``source_code``
        and extracts string literals with ``c.Infra.STRING_LITERAL_RE`` —
        avoiding ``ast`` walking entirely.
        """
        for assignment in pyname.assignments:
            node = assignment.ast_node
            start = getattr(node, "lineno", None)
            end = getattr(node, "end_lineno", None) or start
            if start is None:
                continue
            lines = pymodule.source_code.splitlines()
            slice_text = "\n".join(lines[start - 1 : end])
            return tuple(dict.fromkeys(c.Infra.STRING_LITERAL_RE.findall(slice_text)))
        return None

    @staticmethod
    def public_export_names_source(source: str) -> t.StrSequence:
        """Return the explicit public ABI declared by one module source."""
        return FlextInfraUtilitiesRopeAnalysisSource.module_assignment_strings_source(
            source, c.Infra.DUNDER_ALL
        )

    @staticmethod
    def module_has_docstring_source(source: str) -> bool:
        """Return whether ``source`` starts with a module docstring (rope-parsed)."""
        pymodule = FlextInfraUtilitiesRopeAnalysisBase.parse_string_module(source)
        return bool(pymodule.get_doc())

    @staticmethod
    def module_docstring_summary_source(source: str) -> str:
        """Return the PEP 257 summary line of the module docstring (rope-parsed)."""
        pymodule = FlextInfraUtilitiesRopeAnalysisBase.parse_string_module(source)
        doc = pymodule.get_doc() or ""
        summary = next((line for line in doc.splitlines() if line.strip()), "")
        # The summary is rendered verbatim into generated markdown, where runs
        # of spaces are a lint failure nobody can hand-fix in a generated file.
        # Collapsing them here keeps the summary faithful and renderable.
        return " ".join(summary.split())

    @staticmethod
    def symbol_has_docstring_source(source: str, symbol_name: str) -> bool:
        """Check a locally defined symbol; imported docs need module context."""
        pymodule = FlextInfraUtilitiesRopeAnalysisBase.parse_string_module(source)
        pyname = pymodule.get_attributes().get(symbol_name)
        if pyname is None or not FlextInfraUtilitiesRopeRuntime.is_defined_name(pyname):
            return False
        obj = pyname.get_object()
        get_doc = getattr(obj, "get_doc", None)
        if not callable(get_doc):
            # Plain PyObjects (assignments, imports) carry no docstring.
            return False
        return bool(get_doc())

    @staticmethod
    def assignment_docstrings_source(source: str) -> t.StrSequence:
        """Return assignment names followed by a string-literal expression (rope-parsed).

        Iterates the parsed module's body via ``_fields`` access and pairs each
        ``Assign``/``AnnAssign``/PEP-695 ``TypeAlias`` target with the next
        sibling ``Expr(Constant(str))``.
        """
        pymodule = FlextInfraUtilitiesRopeAnalysisBase.parse_string_module(source)
        module_ast = pymodule.get_ast()
        body = getattr(module_ast, "body", []) or []
        names: list[str] = []
        previous_targets: list[str] = []
        for statement in body:
            kind = FlextInfraUtilitiesRopeAnalysisNodes.node_kind(statement)
            if kind in {"Assign", "AnnAssign", "TypeAlias"}:
                previous_targets = (
                    FlextInfraUtilitiesRopeAnalysisSource._statement_target_names(
                        statement
                    )
                )
                continue
            if kind == "Expr" and previous_targets:
                value = getattr(statement, "value", None)
                if (
                    value is not None
                    and FlextInfraUtilitiesRopeAnalysisNodes.node_kind(value)
                    == "Constant"
                    and isinstance(getattr(value, "value", None), str)
                ):
                    names.extend(previous_targets)
            previous_targets = []
        return tuple(dict.fromkeys(names))

    @staticmethod
    def literal_string_sequence(node: p.AttributeProbe | None) -> t.StrSequence:
        """Return string entries from a parsed literal sequence node."""
        if node is None:
            return ()
        if FlextInfraUtilitiesRopeAnalysisNodes.node_kind(node) not in {
            "List",
            "Tuple",
            "Set",
        }:
            return ()
        values: list[str] = []
        for element in getattr(node, "elts", ()) or ():
            element_kind = FlextInfraUtilitiesRopeAnalysisNodes.node_kind(element)
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
    def _sequence_constructor_ref_source(source: str) -> str:
        """Return the name wrapped by ``tuple``/``list``/``set`` or a bare name."""
        text = source.strip()
        if not text:
            return ""
        if text.isidentifier():
            return text
        for constructor in ("tuple", "list", "frozenset", "set"):
            prefix = f"{constructor}("
            if not text.startswith(prefix) or not text.endswith(")"):
                continue
            inner = text[len(prefix) : -1].strip()
            if inner.isidentifier():
                return inner
        return ""

    @staticmethod
    def module_assignment_strings_source(source: str, name: str) -> t.StrSequence:
        """Collect strings from a literal module-level assignment."""
        value_source = FlextInfraUtilitiesRopeAnalysisSource._assignment_value_source(
            source, name
        )
        values = FlextInfraUtilitiesRopeAnalysisSource._literal_string_sequence_source(
            value_source
        )
        if values:
            return values
        # Generated roots use ``__all__ = tuple(_PUBLIC_EXPORTS)``; follow the
        # bound name so docs validate matches the live lazy-init ABI.
        nested_name = (
            FlextInfraUtilitiesRopeAnalysisSource._sequence_constructor_ref_source(
                value_source
            )
        )
        if not nested_name or nested_name == name:
            return ()
        return FlextInfraUtilitiesRopeAnalysisSource.module_assignment_strings_source(
            source, nested_name
        )

    @staticmethod
    def module_mapping_assignment_source(
        source: str, name: str
    ) -> t.Pair[t.VariadicTuple[t.Pair[str, t.StrSequence]], t.StrSequence]:
        """Collect mapping entries and referenced names from an assignment."""
        value_source = FlextInfraUtilitiesRopeAnalysisSource._assignment_value_source(
            source, name
        )
        return FlextInfraUtilitiesRopeAnalysisSource._mapping_entries_refs_source(
            value_source
        )

    @staticmethod
    def mapping_entries_refs(
        node: p.AttributeProbe | None,
    ) -> t.Pair[t.VariadicTuple[t.Pair[str, t.StrSequence]], t.StrSequence]:
        """Return literal mapping entries plus variable references."""
        if node is None:
            return ((), ())
        kind = FlextInfraUtilitiesRopeAnalysisNodes.node_kind(node)
        if kind == "Name":
            node_name = FlextInfraUtilitiesRopeAnalysisNodes.name_of(node)
            return ((), (node_name,) if node_name else ())
        if kind == "Dict":
            return FlextInfraUtilitiesRopeAnalysisSource._dict_entries_refs(node)
        if kind != "Call":
            return ((), ())
        function_name = FlextInfraUtilitiesRopeAnalysisNodes.name_of(
            getattr(node, "func", None)
        )
        args = getattr(node, "args", ()) or ()
        if function_name in {"MappingProxyType", "build_lazy_import_map"} and args:
            return FlextInfraUtilitiesRopeAnalysisSource.mapping_entries_refs(args[0])
        if function_name != "merge_lazy_imports":
            return ((), ())
        entries: list[tuple[str, t.StrSequence]] = []
        refs: list[str] = []
        for argument in args:
            next_entries, next_refs = (
                FlextInfraUtilitiesRopeAnalysisSource.mapping_entries_refs(argument)
            )
            entries.extend(next_entries)
            refs.extend(next_refs)
        return (tuple(entries), tuple(dict.fromkeys(refs)))

    @staticmethod
    def _dict_entries_refs(
        node: p.AttributeProbe,
    ) -> t.Pair[t.VariadicTuple[t.Pair[str, t.StrSequence]], t.StrSequence]:
        """Return string-sequence dict entries and unpack references."""
        keys = getattr(node, "keys", ()) or ()
        values = getattr(node, "values", ()) or ()
        entries: list[tuple[str, t.StrSequence]] = []
        refs: list[str] = []
        for key_node, value_node in zip(keys, values, strict=False):
            if key_node is None:
                ref_name = FlextInfraUtilitiesRopeAnalysisNodes.name_of(value_node)
                if ref_name:
                    refs.append(ref_name)
                continue
            key_value = getattr(key_node, "value", None)
            if not isinstance(key_value, str):
                continue
            value_strings = (
                FlextInfraUtilitiesRopeAnalysisSource.literal_string_sequence(
                    value_node
                )
            )
            if value_strings:
                entries.append((key_value, value_strings))
        return (tuple(entries), tuple(dict.fromkeys(refs)))

    @staticmethod
    def imported_symbol_binding_source(
        source: str, *, current_module: str, symbol_name: str, package_module: bool
    ) -> t.Pair[str, str]:
        """Return ``(module, original_name)`` for one imported symbol binding."""
        for (
            module_source,
            level,
            original_name,
            bound_name,
        ) in FlextInfraUtilitiesRopeAnalysisSource._from_import_bindings_source(source):
            if bound_name != symbol_name:
                continue
            module_name = (
                FlextInfraUtilitiesRopeAnalysisImports.relative_import_module_name(
                    current_module=current_module,
                    imported_module=module_source,
                    level=level,
                    package_module=package_module,
                )
            )
            return (module_name, original_name or symbol_name)
        return ("", "")

    @staticmethod
    def class_bases_source(source: str, class_name: str) -> t.StrSequence:
        """Return declared base names for one class in source."""
        class_source = FlextInfraUtilitiesRopeAnalysisSource._class_header_source(
            source, class_name
        )
        if not class_source:
            return ()
        open_index = class_source.find("(")
        close_index = class_source.rfind(")")
        if open_index < 0 or close_index <= open_index:
            return ()
        bases_source = class_source[open_index + 1 : close_index]
        return tuple(
            base_name
            for base_name in (
                FlextInfraUtilitiesRopeAnalysisSource._symbol_name_source(item)
                for item in FlextInfraUtilitiesRopeAnalysisSource._split_top_level_commas(
                    bases_source
                )
            )
            if base_name
        )

    @staticmethod
    def class_declared_source(source: str, class_name: str) -> bool:
        """Return whether one class is declared in source."""
        return bool(
            FlextInfraUtilitiesRopeAnalysisSource._class_header_source(
                source, class_name
            )
        )

    @staticmethod
    def lazy_public_exports_source(source: str) -> t.Pair[t.StrSequence, str]:
        """Return lazy-loader public exports or the local symbol holding them."""
        call_args = FlextInfraUtilitiesRopeAnalysisSource._call_args_source(
            source, "install_lazy_exports"
        )
        public_exports = FlextInfraUtilitiesRopeAnalysisSource._keyword_value_source(
            call_args, "public_exports"
        )
        if public_exports:
            values = (
                FlextInfraUtilitiesRopeAnalysisSource._literal_string_sequence_source(
                    public_exports
                )
            )
            if values:
                return (values, "")
            return (
                (),
                FlextInfraUtilitiesRopeAnalysisSource._symbol_name_source(
                    public_exports
                ),
            )
        return ((), "")

    @staticmethod
    def lazy_imports_name_source(source: str) -> str:
        """Return the local symbol passed as the lazy import map."""
        call_args = FlextInfraUtilitiesRopeAnalysisSource._call_args_source(
            source, "install_lazy_exports"
        )
        if (
            len(call_args)
            > FlextInfraUtilitiesRopeAnalysisBase._INSTALL_LAZY_IMPORTS_ARG_INDEX
        ):
            return FlextInfraUtilitiesRopeAnalysisSource._symbol_name_source(
                call_args[
                    FlextInfraUtilitiesRopeAnalysisBase._INSTALL_LAZY_IMPORTS_ARG_INDEX
                ]
            )
        keyword_value = FlextInfraUtilitiesRopeAnalysisSource._keyword_value_source(
            call_args, "lazy_imports"
        )
        if keyword_value:
            return FlextInfraUtilitiesRopeAnalysisSource._symbol_name_source(
                keyword_value
            )
        return ""

    @staticmethod
    def _assignment_value_source(source: str, name: str) -> str:
        """Return the source value assigned to one top-level symbol."""
        lines = source.splitlines()
        for index, line in enumerate(lines):
            if line[: len(line) - len(line.lstrip())]:
                continue
            stripped = line.strip()
            if not stripped.startswith(name):
                continue
            tail = stripped[len(name) :].lstrip()
            if not tail or tail[0] not in {":", "="}:
                continue
            statement = FlextInfraUtilitiesRopeAnalysisSource._collect_statement(
                lines, index
            )
            _head, separator, value = statement.partition("=")
            if not separator:
                return ""
            return value.strip()
        return ""

    @staticmethod
    def _collect_statement(lines: t.StrSequence, start_index: int) -> str:
        """Collect a balanced Python statement starting at ``start_index``."""
        collected: list[str] = []
        depth = 0
        for line in lines[start_index:]:
            collected.append(line)
            depth += FlextInfraUtilitiesRopeAnalysisSource._bracket_depth_delta(line)
            if depth <= 0:
                break
        return "\n".join(collected)

    @staticmethod
    def _unquoted_characters(source: str, start: int = 0) -> Iterator[t.Pair[int, str]]:
        """Yield ``(index, character)`` for every character outside a string literal.

        Single owner of the quote/escape state machine every top-level source
        scanner in this module needs; each caller keeps only its own bracket
        depth bookkeeping.
        """
        quote = ""
        escaped = False
        for index in range(start, len(source)):
            char = source[index]
            if quote:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == quote:
                    quote = ""
                continue
            if char in {"'", '"'}:
                quote = char
                continue
            yield index, char

    @staticmethod
    def _bracket_depth_delta(source: str) -> int:
        """Return bracket nesting delta for one source line."""
        depth = 0
        for _index, char in FlextInfraUtilitiesRopeAnalysisSource._unquoted_characters(
            source
        ):
            if char == "#":
                break
            if char in "([{":
                depth += 1
            elif char in ")]}":
                depth -= 1
        return depth

    @staticmethod
    def _split_top_level_commas(source: str) -> t.StrSequence:
        """Split one source fragment on commas outside nested delimiters."""
        parts: list[str] = []
        start = 0
        depth = 0
        for index, char in FlextInfraUtilitiesRopeAnalysisSource._unquoted_characters(
            source
        ):
            if char in "([{":
                depth += 1
            elif char in ")]}":
                depth -= 1
            elif char == "," and depth == 0:
                item = source[start:index].strip()
                if item:
                    parts.append(item)
                start = index + 1
        tail = source[start:].strip()
        if tail:
            parts.append(tail)
        return tuple(parts)

    @staticmethod
    def _top_level_partition(source: str, separator: str) -> t.Triple[str, str, str]:
        """Partition one source fragment at a top-level separator."""
        depth = 0
        for index, char in FlextInfraUtilitiesRopeAnalysisSource._unquoted_characters(
            source
        ):
            if char in "([{":
                depth += 1
            elif char in ")]}":
                depth -= 1
            elif char == separator and depth == 0:
                return (source[:index], separator, source[index + 1 :])
        return (source, "", "")

    @staticmethod
    def _literal_string_source(source: str) -> str:
        """Return the value of a simple string literal source fragment."""
        text = source.strip()
        while text and text[0].isalpha() and len(text) > 1 and text[1] in {"'", '"'}:
            text = text[1:]
        if len(
            text
        ) < FlextInfraUtilitiesRopeAnalysisBase._STRING_LITERAL_MIN_LENGTH or text[
            0
        ] not in {"'", '"'}:
            return ""
        quote = text[0]
        triple_quote = quote * FlextInfraUtilitiesRopeAnalysisBase._TRIPLE_QUOTE_LENGTH
        if text.startswith(triple_quote):
            end = text.find(
                triple_quote, FlextInfraUtilitiesRopeAnalysisBase._TRIPLE_QUOTE_LENGTH
            )
            return (
                text[FlextInfraUtilitiesRopeAnalysisBase._TRIPLE_QUOTE_LENGTH : end]
                if end >= FlextInfraUtilitiesRopeAnalysisBase._TRIPLE_QUOTE_LENGTH
                else ""
            )
        end = 1
        escaped = False
        while end < len(text):
            char = text[end]
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                break
            end += 1
        return text[1:end]

    @staticmethod
    def _literal_string_sequence_source(source: str) -> t.StrSequence:
        """Return string entries from a literal sequence source fragment."""
        text = source.strip()
        if not text or text[0] not in "[{(":
            return ()
        close = {"[": "]", "{": "}", "(": ")"}[text[0]]
        if not text.endswith(close):
            return ()
        inner = text[1:-1]
        values: list[str] = []
        for item in FlextInfraUtilitiesRopeAnalysisSource._split_top_level_commas(
            inner
        ):
            value = FlextInfraUtilitiesRopeAnalysisSource._literal_string_source(item)
            if not value:
                return ()
            values.append(value)
        return tuple(values)

    @staticmethod
    def _call_args_source(source: str, function_name: str) -> t.StrSequence:
        """Return top-level argument sources for the first matching call."""
        search_from = 0
        while True:
            name_index = source.find(function_name, search_from)
            if name_index < 0:
                return ()
            open_index = source.find("(", name_index + len(function_name))
            if open_index < 0:
                return ()
            between = source[name_index + len(function_name) : open_index].strip()
            if between:
                search_from = name_index + len(function_name)
                continue
            close_index = FlextInfraUtilitiesRopeAnalysisSource._matching_close_index(
                source, open_index
            )
            if close_index < 0:
                return ()
            return FlextInfraUtilitiesRopeAnalysisSource._split_top_level_commas(
                source[open_index + 1 : close_index]
            )

    @staticmethod
    def _matching_close_index(source: str, open_index: int) -> int:
        """Return the index of the closing delimiter matching ``open_index``."""
        open_char = source[open_index]
        close_char = {"(": ")", "[": "]", "{": "}"}[open_char]
        depth = 0
        for index, char in FlextInfraUtilitiesRopeAnalysisSource._unquoted_characters(
            source, open_index
        ):
            if char == open_char:
                depth += 1
            elif char == close_char:
                depth -= 1
                if depth == 0:
                    return index
        return -1

    @staticmethod
    def _keyword_value_source(args: t.StrSequence, keyword: str) -> str:
        """Return a keyword argument value source from split call args."""
        prefix = f"{keyword}="
        # NOTE (multi-agent, flext-f8vk / kimi): args is t.StrSequence
        # (SequenceOf[str]); the old isinstance guard was dead code.
        for arg in args:
            text = arg.strip()
            if text.startswith(prefix):
                value: str = t.Infra.STR_ADAPTER.validate_python(
                    text[len(prefix) :].strip()
                )
                return value
        return ""

    @staticmethod
    def _mapping_entries_refs_source(
        source: str,
    ) -> t.Pair[t.VariadicTuple[t.Pair[str, t.StrSequence]], t.StrSequence]:
        """Return lazy-map entries and referenced mapping symbols from source."""
        text = source.strip()
        if not text:
            return ((), ())
        if FlextInfraUtilitiesRopeAnalysisSource._is_symbol_source(text):
            return ((), (text,))
        call_name = FlextInfraUtilitiesRopeAnalysisSource._call_name_source(text)
        if call_name in {"MappingProxyType", "build_lazy_import_map"}:
            args = FlextInfraUtilitiesRopeAnalysisSource._call_args_source(
                text, call_name
            )
            return (
                FlextInfraUtilitiesRopeAnalysisSource._mapping_entries_refs_source(
                    args[0]
                )
                if args
                else ((), ())
            )
        if call_name == "merge_lazy_imports":
            entries: list[tuple[str, t.StrSequence]] = []
            refs: list[str] = []
            for arg in FlextInfraUtilitiesRopeAnalysisSource._call_args_source(
                text, call_name
            ):
                next_entries, next_refs = (
                    FlextInfraUtilitiesRopeAnalysisSource._mapping_entries_refs_source(
                        arg
                    )
                )
                entries.extend(next_entries)
                refs.extend(next_refs)
            return (tuple(entries), tuple(dict.fromkeys(refs)))
        if not text.startswith("{") or not text.endswith("}"):
            return ((), ())
        entries = []
        refs = []
        for item in FlextInfraUtilitiesRopeAnalysisSource._split_top_level_commas(
            text[1:-1]
        ):
            stripped = item.strip()
            if stripped.startswith("**"):
                ref_name = FlextInfraUtilitiesRopeAnalysisSource._symbol_name_source(
                    stripped[2:]
                )
                if ref_name:
                    refs.append(ref_name)
                continue
            key_source, separator, value_source = (
                FlextInfraUtilitiesRopeAnalysisSource._top_level_partition(
                    stripped, ":"
                )
            )
            if not separator:
                continue
            key = FlextInfraUtilitiesRopeAnalysisSource._literal_string_source(
                key_source
            )
            values = (
                FlextInfraUtilitiesRopeAnalysisSource._literal_string_sequence_source(
                    value_source
                )
            )
            if key and values:
                entries.append((key, values))
        return (tuple(entries), tuple(dict.fromkeys(refs)))

    @staticmethod
    def _call_name_source(source: str) -> str:
        """Return the final symbol name for a call source fragment."""
        text = source.strip()
        open_index = text.find("(")
        if open_index < 0:
            return ""
        return FlextInfraUtilitiesRopeAnalysisSource._symbol_name_source(
            text[:open_index]
        )

    @staticmethod
    def _is_symbol_source(source: str) -> bool:
        """Return whether source is a simple dotted or underscored symbol."""
        text = source.strip()
        return bool(text) and all(char.isalnum() or char in {"_", "."} for char in text)

    @staticmethod
    def _symbol_name_source(source: str) -> str:
        """Return the final identifier from one symbol source fragment."""
        text = source.strip()
        if not FlextInfraUtilitiesRopeAnalysisSource._is_symbol_source(text):
            return ""
        return text.rsplit(".", maxsplit=1)[-1]

    @staticmethod
    def _class_header_source(source: str, class_name: str) -> str:
        """Return the collected class header source for one top-level class."""
        lines = source.splitlines()
        prefix = f"class {class_name}"
        for index, line in enumerate(lines):
            if line[: len(line) - len(line.lstrip())]:
                continue
            stripped = line.strip()
            if not stripped.startswith(prefix):
                continue
            tail = stripped[len(prefix) :]
            if tail and tail[0] not in {"(", ":"}:
                continue
            statement = FlextInfraUtilitiesRopeAnalysisSource._collect_statement(
                lines, index
            )
            return statement.rsplit(":", maxsplit=1)[0]
        return ""

    @staticmethod
    def _statement_target_names(statement: object) -> list[str]:
        """Extract target names from an Assign/AnnAssign/PEP-695 TypeAlias."""
        kind = FlextInfraUtilitiesRopeAnalysisNodes.node_kind(statement)
        if kind == "AnnAssign":
            target = getattr(statement, "target", None)
            name = getattr(target, "id", "") if target is not None else ""
            return [name] if name else []
        if kind == "TypeAlias":
            name_node = getattr(statement, "name", None)
            name = getattr(name_node, "id", "")
            return [name] if isinstance(name, str) and name else []
        targets = getattr(statement, "targets", []) or []
        names: list[str] = []
        for target in targets:
            name = getattr(target, "id", "")
            if isinstance(name, str) and name:
                names.append(name)
        return names

    @staticmethod
    def _from_import_bindings_source(
        source: str,
    ) -> t.VariadicTuple[t.Quad[str, int, str, str]]:
        """Return ``(module, level, original, bound)`` for ``from`` imports."""
        lines = source.splitlines()
        bindings: list[tuple[str, int, str, str]] = []
        for index, line in enumerate(lines):
            stripped = line.strip()
            if not stripped.startswith("from ") or " import " not in stripped:
                continue
            statement = FlextInfraUtilitiesRopeAnalysisSource._collect_statement(
                lines, index
            ).strip()
            import_index = statement.find(" import ")
            module_source = statement[5:import_index].strip()
            level = len(module_source) - len(module_source.lstrip("."))
            module_name = module_source[level:]
            aliases_source = statement[import_index + len(" import ") :].strip()
            if aliases_source.startswith("(") and aliases_source.endswith(")"):
                aliases_source = aliases_source[1:-1]
            for (
                alias_source
            ) in FlextInfraUtilitiesRopeAnalysisSource._split_top_level_commas(
                aliases_source
            ):
                original, bound = (
                    FlextInfraUtilitiesRopeAnalysisSource._import_alias_names(
                        alias_source
                    )
                )
                if original and bound:
                    bindings.append((module_name, level, original, bound))
        return tuple(bindings)

    @staticmethod
    def _import_alias_names(source: str) -> t.Pair[str, str]:
        """Return ``(original, bound)`` names for one import alias source."""
        parts = source.strip().split()
        if (
            len(parts) == FlextInfraUtilitiesRopeAnalysisBase._IMPORT_ALIAS_AS_PARTS
            and parts[1] == "as"
        ):
            return (parts[0], parts[2])
        if len(parts) == 1:
            return (parts[0], parts[0])
        return ("", "")

    @staticmethod
    def export_target_modules_source(
        source: str, package_name: str, exports: t.StrSequence
    ) -> MutableMapping[str, str]:
        """Map exports → defining module via rope's parsed-source import table."""
        export_names = {name for name in exports if name}
        target_map: MutableMapping[str, str] = dict.fromkeys(export_names, package_name)
        pymodule = FlextInfraUtilitiesRopeAnalysisBase.parse_string_module(source)
        module_ast = pymodule.get_ast()
        for node in FlextInfraUtilitiesRopeAnalysisNodes.walk_ast_nodes(module_ast):
            kind = FlextInfraUtilitiesRopeAnalysisNodes.node_kind(node)
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
