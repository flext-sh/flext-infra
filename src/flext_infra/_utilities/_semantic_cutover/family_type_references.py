"""Quoted type references resolved in the original Rope lexical scope.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
import operator
import re
from collections.abc import Iterator

from flext_infra import c, m, p, t
from flext_infra._utilities import (
    FlextInfraUtilitiesRopeRuntimeModules,
    FlextInfraUtilitiesRopeRuntimeRefactors,
    FlextInfraUtilitiesRopeStructure,
)


class FlextInfraUtilitiesSemanticFamilyTypeReferences:
    """Select type positions structurally and bind every edit to Rope identity."""

    @classmethod
    def annotation_regions(
        cls,
        source: str,
        module: p.Infra.RopePyModule,
    ) -> t.VariadicTuple[t.Triple[int, int, int | None]]:
        """Return annotation coordinates from native match and declaration regions."""
        refactors = FlextInfraUtilitiesRopeRuntimeRefactors
        finder = refactors.semantic_finder(module)
        regions: set[t.Triple[int, int, int | None]] = set()
        for pattern in (
            "${declared}: ${annotation}",
            "${declared}: ${annotation} = ${value}",
        ):
            for match in finder.get_matches(pattern):
                begin, end = refactors.semantic_capture_region(match, "annotation")
                regions.add((begin, end, None))
        words = refactors.runtime_callable("rope.base.worder", "Worder")(source)
        if not isinstance(words, p.Infra.RopeWorder):
            msg = "annotation regions require Rope Worder"
            raise TypeError(msg)
        statements = FlextInfraUtilitiesRopeStructure.logical_statements(source)
        for statement in statements:
            start = statement.start_offset + statement.indent
            end = statement.end_offset
            category = statement.category
            if category == c.Infra.StatementCategory.TYPE_ALIAS:
                parts = cls.expression_segments(source, start, end, "=")
                if len(parts) >= 2:
                    regions.add((parts[1][0], end, None))
            elif category in {
                c.Infra.StatementCategory.FUNC_DEF,
                c.Infra.StatementCategory.CLASS_DEF,
            }:
                name = FlextInfraUtilitiesRopeStructure._header_name(statement.text)
                prefix = source.find(name, start, end)
                if prefix < 0:
                    msg = "native declaration header has no named region"
                    raise ValueError(msg)
                after = prefix + len(name)
                if source[after : after + 1] == "[":
                    generic_start, generic_end = (
                        words.code_finder.get_word_parens_range(
                            after - 1,
                            "[",
                            "]",
                        )
                    )
                    for parameter_start, parameter_end in cls.expression_segments(
                        source,
                        generic_start + 1,
                        generic_end - 1,
                        ",",
                    ):
                        parts = cls.expression_segments(
                            source,
                            parameter_start,
                            parameter_end,
                            ":=",
                        )
                        regions.update(
                            (begin, stop, statement.line) for begin, stop in parts[1:]
                        )
                    after = generic_end
                opening = source.find("(", after, end)
                if opening < 0:
                    continue
                first, last = words.code_finder.get_word_parens_range(opening - 1)
                if category == c.Infra.StatementCategory.CLASS_DEF:
                    regions.add((first + 1, last - 1, statement.line))
                    continue
                for parameter_start, parameter_end in cls.expression_segments(
                    source,
                    first + 1,
                    last - 1,
                    ",",
                ):
                    parts = cls.expression_segments(
                        source,
                        parameter_start,
                        parameter_end,
                        ":=",
                    )
                    if len(parts) >= 2 and ":" in source[parts[0][1] : parts[1][0]]:
                        regions.add((*parts[1], statement.line))
                tail = source[last:end]
                arrow = tail.find("->")
                if arrow >= 0:
                    begin = last + arrow + 2
                    regions.add((begin, end - 1, statement.line))
        return tuple(sorted(regions, key=operator.itemgetter(0, 1)))

    @classmethod
    def quoted_type_regions(
        cls,
        source: str,
        project: p.Infra.RopeProject,
        module: p.Infra.RopePyModule,
    ) -> t.VariadicTuple[tuple[int, int, str, p.Infra.RopeScope]]:
        """Return only string constants occupying native annotation type positions."""
        protected = cls.type_payload_ranges(source, project, module)
        literals = FlextInfraUtilitiesRopeRuntimeRefactors.ignored_regions(source)
        selected = []
        for begin, end, line in cls.annotation_regions(source, module):
            scope = FlextInfraUtilitiesRopeRuntimeModules.scope_at(
                module,
                begin,
                declaration_line=line,
            )
            for start, stop, _metadata in literals:
                if not begin <= start < stop <= end or source[start] == "#":
                    continue
                if any(first <= start and stop <= last for first, last in protected):
                    continue
                literal = cls.string_constant(source[start:stop])
                if literal is not None:
                    selected.append((start, stop, literal, scope))
        return tuple({(item[0], item[1]): item for item in selected}.values())

    @staticmethod
    def string_constant(literal: str) -> str | None:
        """Decode one literal through CPython compilation without executing code."""
        return FlextInfraUtilitiesRopeRuntimeRefactors.literal_string(literal)

    @staticmethod
    def reference_regions(
        source: str,
    ) -> t.VariadicTuple[t.Pair[int, int]]:
        """Return maximal identifier primaries through native Rope word boundaries."""
        refactors = FlextInfraUtilitiesRopeRuntimeRefactors
        opaque = refactors.ignored_regions(source)
        words = refactors.runtime_callable("rope.base.worder", "Worder")(source)
        if not isinstance(words, p.Infra.RopeWorder):
            msg = "reference regions require Rope Worder"
            raise TypeError(msg)
        regions: set[t.Pair[int, int]] = set()
        cursor = 0
        while cursor < len(source):
            ignored = next(
                (end for start, end, _metadata in opaque if start <= cursor < end),
                None,
            )
            if ignored is not None:
                cursor = ignored
                continue
            character = source[cursor]
            if character != "_" and not character.isalpha():
                cursor += 1
                continue
            _first, last = words.get_word_range(cursor)
            if last <= cursor:
                msg = "native reference region did not advance"
                raise ValueError(msg)
            begin, end = refactors.word_primary_range(source, last - 1)
            if all(part.isidentifier() for part in source[begin:end].split(".")):
                regions.add((begin, end))
            cursor = last
        return tuple(sorted(regions))

    @classmethod
    def scoped_quoted_type_nodes(
        cls,
        source: str,
        project: p.Infra.RopeProject,
        module: p.Infra.RopePyModule,
    ) -> Iterator[t.Triple[ast.expr, p.Infra.RopeScope, int]]:
        """Yield quoted type nodes in their original annotation declaration scope.

        Yields:
            The expression, original Rope scope, and physical annotation line.
            Literal values and Annotated metadata are never type references.
        """
        for annotation, declaration_line in cls._annotation_roots(ast.parse(source)):
            start, _end = cls.expression_range(source, annotation)
            scope = FlextInfraUtilitiesRopeRuntimeModules.scope_at(
                module,
                start,
                declaration_line=declaration_line,
            )
            pending = [annotation]
            while pending:
                expression = pending.pop()
                for node in cls._type_nodes(expression, project, scope):
                    if isinstance(node, ast.Constant) and isinstance(node.value, str):
                        pending.append(ast.parse(node.value, mode="eval").body)
                    elif expression is not annotation:
                        yield (node, scope, annotation.lineno)

    @classmethod
    def typeexpression_ranges(cls, source: str) -> frozenset[t.Pair[int, int]]:
        """Expose the same structural roots to concrete-syntax consumer adapters.

        Returns:
            The resulting ``frozenset[t.Pair[int, int]]``.

        """
        return frozenset(
            cls.expression_range(source, expression)
            for expression, _line in cls._annotation_roots(ast.parse(source))
        )

    @classmethod
    def type_payload_ranges(
        cls,
        source: str,
        project: p.Infra.RopeProject,
        module: p.Infra.RopePyModule,
    ) -> frozenset[t.Pair[int, int]]:
        """Protect Literal values and Annotated metadata in every alias form.

        Selection uses the same resolved typing identities as quoted rewrites;
        an ordinary runtime assignment is not implicitly a type declaration.

        Returns:
            The resulting ``frozenset[t.Pair[int, int]]``.
        """
        protected: set[t.Pair[int, int]] = set()
        refactors = FlextInfraUtilitiesRopeRuntimeRefactors
        finder = refactors.semantic_finder(module)
        for owner in ("Literal", "Annotated"):
            variable = f"payload_{owner}"
            pattern = "${" + variable + "}[${payload_arguments}]"
            for match in finder.get_matches(
                pattern,
                args={variable: f"name=typing.{owner}"},
            ):
                begin, end = refactors.semantic_capture_region(
                    match,
                    "payload_arguments",
                )
                if owner == "Literal":
                    protected.add((begin, end))
                    continue
                arguments = cls.expression_segments(source, begin, end, ",")
                protected.update(arguments[1:])
        return frozenset(protected)

    @staticmethod
    def expression_segments(
        source: str,
        begin: int,
        end: int,
        separators: str,
    ) -> t.VariadicTuple[t.Pair[int, int]]:
        """Split a native region using Rope-owned literal and delimiter ranges."""
        refactors = FlextInfraUtilitiesRopeRuntimeRefactors
        finder = refactors.runtime_callable("rope.base.worder", "Worder")(source)
        if not isinstance(finder, p.Infra.RopeWorder):
            msg = "type references require native Rope word regions"
            raise TypeError(msg)
        opaque = {
            start: stop for start, stop, _metadata in refactors.ignored_regions(source)
        }
        closings = {"(": ")", "[": "]", "{": "}"}
        regions = []
        cursor = part = begin
        while cursor < end:
            ignored_end = opaque.get(cursor)
            if ignored_end is not None:
                cursor = ignored_end
                continue
            character = source[cursor]
            if character in closings:
                opening, closing = finder.code_finder.get_word_parens_range(
                    max(0, cursor - 1),
                    character,
                    closings[character],
                )
                if opening != cursor or closing <= cursor or closing > end:
                    msg = "type reference delimiter differs from native region"
                    raise ValueError(msg)
                cursor = closing
                continue
            if character in separators:
                regions.append((part, cursor))
                part = cursor + 1
            cursor += 1
        regions.append((part, end))
        return tuple(
            (
                start + len(source[start:stop]) - len(source[start:stop].lstrip()),
                stop - len(source[start:stop]) + len(source[start:stop].rstrip()),
            )
            for start, stop in regions
            if source[start:stop].strip()
        )

    @classmethod
    def expression_payload_ranges(
        cls,
        source: str,
        project: p.Infra.RopeProject,
        scope: p.Infra.RopeScope,
    ) -> frozenset[t.Pair[int, int]]:
        """Protect typing payloads inside a quoted expression in its original scope."""
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        refactors = FlextInfraUtilitiesRopeRuntimeRefactors
        words = refactors.runtime_callable("rope.base.worder", "Worder")(source)
        if not isinstance(words, p.Infra.RopeWorder):
            msg = "quoted types require native Rope delimiters"
            raise TypeError(msg)
        typing = project.get_module("typing")
        protected: set[t.Pair[int, int]] = set()
        for begin, end in cls.reference_regions(source):
            cursor = end
            while cursor < len(source) and source[cursor].isspace():
                cursor += 1
            if source[cursor : cursor + 1] != "[":
                continue
            binding = runtime.expression_name(scope, source[begin:end])
            literal = runtime.same_name(typing.get_attribute("Literal"), binding)
            annotated = runtime.same_name(typing.get_attribute("Annotated"), binding)
            if not literal and not annotated:
                continue
            first, last = words.code_finder.get_word_parens_range(cursor - 1, "[", "]")
            if literal:
                protected.add((first + 1, last - 1))
            else:
                protected.update(
                    cls.expression_segments(source, first + 1, last - 1, ",")[1:],
                )
        return frozenset(protected)

    @classmethod
    def _family_quoted_rewrites(
        cls,
        resource: p.Infra.RopeResource,
        source: str,
        *,
        flatten: m.Infra.FamilyWrapperFlatten,
    ) -> t.Pair[bool, t.VariadicTuple[m.Infra.SourceRewrite]]:

        runtime = FlextInfraUtilitiesRopeRuntimeModules
        module = flatten.project.get_pymodule(resource)
        edits: list[m.Infra.SourceRewrite] = []
        for annotation, declaration_line in cls._annotation_roots(ast.parse(source)):
            start, _end = cls.expression_range(source, annotation)
            scope = runtime.scope_at(module, start, declaration_line=declaration_line)
            for node in cls._type_nodes(annotation, flatten.project, scope):
                if not isinstance(node, ast.Constant) or not isinstance(
                    node.value,
                    str,
                ):
                    continue
                blocked, updated = cls._quoted_type_source(
                    node.value,
                    resource,
                    scope,
                    flatten=flatten,
                )
                if blocked:
                    return (True, ())
                if updated != node.value:
                    start, end = cls.expression_range(source, node)
                    edits.append(
                        m.Infra.SourceRewrite(start=start, end=end, text=repr(updated)),
                    )
        return (False, tuple(edits))

    @classmethod
    def _quoted_type_source(
        cls,
        source: str,
        resource: p.Infra.RopeResource,
        scope: p.Infra.RopeScope,
        *,
        flatten: m.Infra.FamilyWrapperFlatten,
    ) -> t.Pair[bool, str]:

        runtime = FlextInfraUtilitiesRopeRuntimeModules
        nodes = tuple(
            cls._type_nodes(
                ast.parse(source, mode="eval").body,
                flatten.project,
                scope,
            ),
        )
        edits: list[m.Infra.SourceRewrite] = []
        for node in nodes:
            blocked, edit = cls._quoted_node_rewrite(
                node,
                source,
                resource,
                scope,
                flatten=flatten,
            )
            if blocked:
                return (True, source)
            if edit is not None:
                edits.append(edit)
        for node in nodes:
            start, end = cls.expression_range(source, node)
            if not any(
                edit.start <= start and end <= edit.end for edit in edits
            ) and runtime.same_name(
                flatten.wrapper,
                runtime.resolve_symbol(scope, node),
            ):
                return (True, source)
        change = FlextInfraUtilitiesRopeRuntimeRefactors.content_change(
            resource,
            source,
            edits,
        )
        return (False, change.new_contents)

    @classmethod
    def _quoted_node_rewrite(
        cls,
        node: ast.expr,
        source: str,
        resource: p.Infra.RopeResource,
        scope: p.Infra.RopeScope,
        *,
        flatten: m.Infra.FamilyWrapperFlatten,
    ) -> t.Pair[bool, m.Infra.SourceRewrite | None]:
        """Resolve one selected node; nested strings retain their original scope.

        Returns:
            The resulting ``t.Pair[bool, m.Infra.SourceRewrite | None]``.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        names = flatten.names
        start, end = cls.expression_range(source, node)
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            blocked, updated = cls._quoted_type_source(
                node.value,
                resource,
                scope,
                flatten=flatten,
            )
            if blocked or updated == node.value:
                return (blocked, None)
            return (
                False,
                m.Infra.SourceRewrite(start=start, end=end, text=repr(updated)),
            )
        if isinstance(node, ast.Attribute) and runtime.same_name(
            flatten.wrapper,
            runtime.resolve_symbol(scope, node.value),
        ):
            if node.attr not in names:
                return (True, None)
            text = cls._promoted_attribute(
                node,
                scope,
                flatten.owner_name,
                names[node.attr],
            )
            return (False, m.Infra.SourceRewrite(start=start, end=end, text=text))
        if (
            isinstance(node, ast.Name)
            and node.id in names
            and runtime.same_name(
                flatten.wrapper.get_object().get_attribute(node.id),
                runtime.resolve_symbol(scope, node),
            )
        ):
            return (
                False,
                m.Infra.SourceRewrite(start=start, end=end, text=names[node.id]),
            )
        return (False, None)

    @staticmethod
    def _promoted_attribute(
        node: ast.Attribute,
        scope: p.Infra.RopeScope,
        owner_name: str,
        name: str,
    ) -> str:
        """Keep an explicit parent or the method's owning class after promotion.

        Returns:
            The resulting ``str``.

        """
        if isinstance(node.value, ast.Attribute):
            return f"{ast.unparse(node.value.value)}.{name}"
        if scope.get_kind() == c.Infra.RopeScopeKind.FUNCTION:
            return f"{owner_name}.{name}" if owner_name else name
        return name

    @classmethod
    def _annotation_roots(
        cls,
        module: ast.Module,
    ) -> Iterator[t.Pair[ast.expr, int | None]]:
        for node in ast.walk(module):
            if isinstance(node, ast.AnnAssign):
                yield (node.annotation, None)
            elif isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                yield from cls._function_annotations(node)
            elif isinstance(node, ast.TypeAlias):
                yield (node.value, None)
            elif isinstance(node, ast.ClassDef):
                for base in node.bases:
                    yield (base, node.lineno)
            elif isinstance(node, ast.TypeVar | ast.ParamSpec | ast.TypeVarTuple):
                yield from cls._type_parameter_annotations(node)

    @staticmethod
    def _type_parameter_annotations(
        node: ast.TypeVar | ast.ParamSpec | ast.TypeVarTuple,
    ) -> Iterator[t.Pair[ast.expr, int | None]]:
        """Yield a type parameter's bound before its optional default.

        Yields:
            Each ``t.Pair[ast.expr, int | None]``.

        """
        if isinstance(node, ast.TypeVar) and node.bound is not None:
            yield (node.bound, None)
        if node.default_value is not None:
            yield (node.default_value, None)

    @staticmethod
    def _function_annotations(
        node: ast.FunctionDef | ast.AsyncFunctionDef,
    ) -> Iterator[t.Pair[ast.expr, int | None]]:
        """Yield each parameter and return annotation in declaration order.

        Yields:
            Each ``t.Pair[ast.expr, int | None]``.

        """
        arguments = (
            *node.args.posonlyargs,
            *node.args.args,
            *node.args.kwonlyargs,
            node.args.vararg,
            node.args.kwarg,
        )
        for argument in arguments:
            if argument is not None and argument.annotation is not None:
                yield (argument.annotation, node.lineno)
        if node.returns is not None:
            yield (node.returns, node.lineno)

    @classmethod
    def _type_nodes(
        cls,
        node: ast.expr,
        project: p.Infra.RopeProject,
        scope: p.Infra.RopeScope,
    ) -> Iterator[ast.expr]:

        yield node
        if isinstance(node, ast.Subscript):
            yield from cls._type_nodes(node.value, project, scope)
            runtime = FlextInfraUtilitiesRopeRuntimeModules
            binding = runtime.resolve_symbol(scope, node.value)
            typing = project.get_module("typing")
            if runtime.same_name(typing.get_attribute("Literal"), binding):
                return
            arguments = (
                node.slice.elts if isinstance(node.slice, ast.Tuple) else [node.slice]
            )
            if runtime.same_name(typing.get_attribute("Annotated"), binding):
                arguments = arguments[:1]
            for argument in arguments:
                yield from cls._type_nodes(argument, project, scope)
        elif isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
            yield from cls._type_nodes(node.left, project, scope)
            yield from cls._type_nodes(node.right, project, scope)
        elif isinstance(node, ast.Tuple | ast.List):
            for element in node.elts:
                yield from cls._type_nodes(element, project, scope)
        elif isinstance(node, ast.Attribute | ast.Starred):
            yield from cls._type_nodes(node.value, project, scope)

    @staticmethod
    def expression_range(source: str, expression: ast.expr) -> t.Pair[int, int]:
        if expression.end_lineno is None or expression.end_col_offset is None:
            msg = "Parsed type expression has no complete source coordinates"
            raise ValueError(msg)
        lines = re.split(r"(?<=\n)|(?<=\r)(?!\n)", source)
        start = sum(map(len, lines[: expression.lineno - 1])) + len(
            lines[expression.lineno - 1]
            .encode("utf-8")[: expression.col_offset]
            .decode("utf-8"),
        )
        end = sum(map(len, lines[: expression.end_lineno - 1])) + len(
            lines[expression.end_lineno - 1]
            .encode("utf-8")[: expression.end_col_offset]
            .decode("utf-8"),
        )
        return (start, end)


__all__: list[str] = ["FlextInfraUtilitiesSemanticFamilyTypeReferences"]
