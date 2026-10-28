"""Quoted type references resolved in the original Rope lexical scope.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import operator
from bisect import bisect_left, bisect_right
from collections.abc import Callable, Iterator

from flext_infra import c, m, p, t
from flext_infra._utilities._rope.rope_core import FlextInfraUtilitiesRopeCore
from flext_infra._utilities._rope.rope_runtime_modules import (
    FlextInfraUtilitiesRopeRuntimeModules,
)
from flext_infra._utilities._rope.rope_runtime_refactors import (
    FlextInfraUtilitiesRopeRuntimeRefactors,
)
from flext_infra._utilities._rope.rope_runtime_types import (
    FlextInfraUtilitiesTypesRopeRuntime,
)
from flext_infra._utilities._rope.rope_structure import FlextInfraUtilitiesRopeStructure


class FlextInfraUtilitiesSemanticFamilyTypeReferences:
    """Select type positions structurally and bind every edit to Rope identity."""

    _MIN_DECLARATION_SEGMENTS = 2

    @classmethod
    def rewrite_type_source(
        cls,
        source: str,
        project: p.Infra.RopeProject,
        scope: p.Infra.RopeScope,
        replacement: Callable[[p.Infra.RopeScope, str], str | None],
    ) -> str:
        """Rewrite bound type references once, preserving metadata and literal data.

        Returns:
            The resulting ``str``.

        """
        protected = cls.expression_payload_ranges(source, project, scope)
        edits: list[tuple[int, int, str]] = []
        for begin, end in cls.reference_regions(source):
            if any(first <= begin and end <= last for first, last in protected):
                continue
            expression = source[begin:end]
            changed = replacement(scope, expression)
            if changed is not None and changed != expression:
                edits.append((begin, end, changed))
        for (
            begin,
            end,
            _metadata,
        ) in FlextInfraUtilitiesRopeRuntimeRefactors.ignored_regions(source):
            if source[begin] == "#" or any(
                first <= begin and end <= last for first, last in protected
            ):
                continue
            literal = cls.string_constant(source[begin:end])
            if literal is None:
                continue
            changed = cls.rewrite_type_source(literal, project, scope, replacement)
            if changed != literal:
                edits.append((begin, end, repr(changed)))
        return cls._apply_type_rewrites(source, edits)

    @staticmethod
    def _apply_type_rewrites(
        source: str,
        edits: t.SequenceOf[tuple[int, int, str]],
    ) -> str:
        """Apply the outermost nonoverlapping type edits in reverse source order.

        Returns:
            The source with the admitted edits applied once.

        """
        selected: list[tuple[int, int, str]] = []
        previous = -1
        for begin, end, changed in sorted(edits, key=lambda item: (item[0], -item[1])):
            if begin >= previous:
                selected.append((begin, end, changed))
                previous = end
        for begin, end, changed in reversed(selected):
            source = source[:begin] + changed + source[end:]
        return source

    @classmethod
    def annotation_regions(
        cls,
        source: str,
        module: p.Infra.RopePyModule,
    ) -> tuple[tuple[int, int, int | None], ...]:
        """Return annotation coordinates from native match and declaration regions.

        The native Worder and declaration header contracts fail the scan when a
        runtime product is foreign or a header has no named region.

        Returns:
            Sorted ``(begin, end, declaration line)`` annotation regions.

        """
        regions = cls._semantic_annotation_regions(module)
        words = cls._require_worder(
            source,
            "annotation regions require Rope Worder",
        )
        for statement in FlextInfraUtilitiesRopeStructure.logical_statements(source):
            regions.update(cls._statement_regions(source, words, statement))
        return tuple(sorted(regions, key=operator.itemgetter(0, 1)))

    @classmethod
    def _require_worder(cls, source: str, requirement: str) -> p.Infra.RopeWorder:
        """Build the native Rope Worder or fail the structural contract.

        Args:
            source: The native source text the Worder indexes.
            requirement: The contract message raised on a foreign Worder.

        Returns:
            The validated native Rope Worder for ``source``.

        Raises:
            TypeError: If the runtime Worder product is not the native contract.

        """
        words = FlextInfraUtilitiesRopeRuntimeRefactors.runtime_callable(
            "rope.base.worder",
            "Worder",
        )(source)
        if not isinstance(words, p.Infra.RopeWorder):
            raise TypeError(requirement)
        return words

    @staticmethod
    def _semantic_annotation_regions(
        module: p.Infra.RopePyModule,
    ) -> set[tuple[int, int, int | None]]:
        """Collect native semantic capture regions for declared annotations.

        Returns:
            The semantic annotation capture regions keyed by native offsets.

        """
        refactors = FlextInfraUtilitiesRopeRuntimeRefactors
        finder = refactors.semantic_finder(module)
        regions: set[tuple[int, int, int | None]] = set()
        for pattern in (
            "${declared}: ${annotation}",
            "${declared}: ${annotation} = ${value}",
        ):
            for match in finder.get_matches(pattern):
                begin, end = refactors.semantic_capture_region(match, "annotation")
                regions.add((begin, end, None))
        return regions

    @classmethod
    def _statement_regions(
        cls,
        source: str,
        words: p.Infra.RopeWorder,
        statement: m.Infra.LogicalStatement,
    ) -> set[tuple[int, int, int | None]]:
        """Resolve the annotation regions owned by one logical statement.

        Returns:
            The annotation regions owned by the statement's native category.

        """
        if statement.category == c.Infra.StatementCategory.TYPE_ALIAS:
            return cls._type_alias_regions(source, statement)
        if statement.category in {
            c.Infra.StatementCategory.FUNC_DEF,
            c.Infra.StatementCategory.CLASS_DEF,
        }:
            return cls._declaration_regions(source, words, statement)
        return set()

    @classmethod
    def _type_alias_regions(
        cls,
        source: str,
        statement: m.Infra.LogicalStatement,
    ) -> set[tuple[int, int, int | None]]:
        """Return the annotation region of one native ``type`` alias statement."""
        start = statement.start_offset + statement.indent
        end = statement.end_offset
        parts = cls.expression_segments(source, start, end, "=")
        if len(parts) < cls._MIN_DECLARATION_SEGMENTS:
            return set()
        return {(parts[1][0], end, None)}

    @classmethod
    def _declaration_regions(
        cls,
        source: str,
        words: p.Infra.RopeWorder,
        statement: m.Infra.LogicalStatement,
    ) -> set[tuple[int, int, int | None]]:
        """Return annotation regions of one native ``def``/``class`` declaration.

        Returns:
            The declaration's base, parameter, and return annotation regions.

        Raises:
            ValueError: If the native declaration header has no named region.

        """
        start = statement.start_offset + statement.indent
        end = statement.end_offset
        name = FlextInfraUtilitiesRopeStructure.header_name(statement.text)
        prefix = source.find(name, start, end)
        if prefix < 0:
            msg = "native declaration header has no named region"
            raise ValueError(msg)
        after = prefix + len(name)
        regions: set[tuple[int, int, int | None]] = set()
        if source[after : after + 1] == "[":
            generic_start, generic_end = words.code_finder.get_word_parens_range(
                after - 1,
                "[",
                "]",
            )
            regions.update(
                cls._parameter_annotation_regions(
                    source,
                    generic_start + 1,
                    generic_end - 1,
                    statement,
                    include_defaults=True,
                ),
            )
            after = generic_end
        opening = source.find("(", after, end)
        if opening < 0:
            return regions
        first, last = words.code_finder.get_word_parens_range(opening - 1)
        if statement.category == c.Infra.StatementCategory.CLASS_DEF:
            regions.add((first + 1, last - 1, statement.line))
            return regions
        regions.update(
            cls._parameter_annotation_regions(
                source, first + 1, last - 1, statement, include_defaults=False
            ),
        )
        tail = source[last:end]
        arrow = tail.find("->")
        if arrow >= 0:
            regions.add((last + arrow + 2, end - 1, statement.line))
        return regions

    @classmethod
    def _parameter_annotation_regions(
        cls,
        source: str,
        begin: int,
        end: int,
        statement: m.Infra.LogicalStatement,
        *,
        include_defaults: bool,
    ) -> set[tuple[int, int, int | None]]:
        """Read parameter annotations, including generic bounds and defaults.

        Returns:
            Source regions for the selected parameter type expressions.

        """
        regions: set[tuple[int, int, int | None]] = set()
        for parameter_start, parameter_end in cls.expression_segments(
            source,
            begin,
            end,
            ",",
        ):
            parts = cls.expression_segments(
                source,
                parameter_start,
                parameter_end,
                ":=",
            )
            if include_defaults:
                selected = parts[1:]
            elif (
                len(parts) >= cls._MIN_DECLARATION_SEGMENTS
                and ":" in source[parts[0][1] : parts[1][0]]
            ):
                selected = parts[1:2]
            else:
                continue
            regions.update((*region, statement.line) for region in selected)
        return regions

    @classmethod
    def quoted_type_regions(
        cls,
        source: str,
        _project: p.Infra.RopeProject,
        module: p.Infra.RopePyModule,
    ) -> tuple[tuple[int, int, str, p.Infra.RopeScope], ...]:
        """Return only string constants occupying native annotation type positions."""
        del _project
        protected: frozenset[tuple[int, int]] | None = None
        literals = FlextInfraUtilitiesRopeRuntimeRefactors.ignored_regions(source)
        starts = [start for start, _stop, _metadata in literals]
        selected: list[tuple[int, int, str, p.Infra.RopeScope]] = []
        for begin, end, line in cls.annotation_regions(source, module):
            # Literals are ordered and disjoint: scan only those starting inside.
            for start, stop, _metadata in literals[
                bisect_left(starts, begin) : bisect_left(starts, end)
            ]:
                if not start < stop <= end or source[start] == "#":
                    continue
                if protected is None:
                    protected = cls.type_payload_ranges(source, module)
                if any(first <= start and stop <= last for first, last in protected):
                    continue
                literal = cls.string_constant(source[start:stop])
                if literal is not None:
                    selected.append((
                        start,
                        stop,
                        literal,
                        FlextInfraUtilitiesRopeRuntimeModules.scope_at(
                            module, begin, declaration_line=line
                        ),
                    ))
        return tuple({(item[0], item[1]): item for item in selected}.values())

    @staticmethod
    def string_constant(literal: str) -> str | None:
        """Decode one literal through CPython compilation without executing code.

        Returns:
            The decoded string constant, or ``None`` for non-string literals.

        """
        return FlextInfraUtilitiesRopeRuntimeRefactors.literal_string(literal)

    @classmethod
    def reference_regions(
        cls,
        source: str,
    ) -> tuple[tuple[int, int], ...]:
        """Return maximal identifier primaries through native Rope word boundaries.

        A foreign runtime Worder product fails the scan.

        Returns:
            Sorted maximal identifier primary regions.

        Raises:
            ValueError: If a native reference region does not advance the scan.

        """
        refactors = FlextInfraUtilitiesRopeRuntimeRefactors
        opaque = sorted(
            (start, end) for start, end, _metadata in refactors.ignored_regions(source)
        )
        words = cls._require_worder(
            source,
            "reference regions require Rope Worder",
        )
        imports = sorted(
            (row.start_offset, row.end_offset)
            for row in FlextInfraUtilitiesRopeStructure.logical_statements(source)
            if row.category
            in {c.Infra.StatementCategory.IMPORT, c.Infra.StatementCategory.FROM_IMPORT}
        )
        regions: set[tuple[int, int]] = set()
        cursor = 0
        while cursor < len(source):
            # Each region kind is disjoint: only the last one starting at or
            # before the cursor can hold it.
            ignored = next(
                (
                    spans[index - 1][1]
                    for spans in (opaque, imports)
                    for index in (bisect_right(spans, (cursor, len(source))),)
                    if index and cursor < spans[index - 1][1]
                ),
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
            # The native primary of a head word excludes its own ``.member``
            # chain; extend it forward so every emitted region is maximal and
            # no wrapper-alias prefix is ever split mid-path.
            end = cls._primary_chain_end(source, words, end)
            if all(part.isidentifier() for part in source[begin:end].split(".")):
                regions.add((begin, end))
            cursor = last
        return tuple(sorted(regions))

    @staticmethod
    def _primary_chain_end(source: str, words: p.Infra.RopeWorder, end: int) -> int:
        """Extend an identifier primary over the following native member chain.

        Returns:
            The end offset of the maximal advancing identifier chain.

        """
        while source[end : end + 1] == ".":
            following = end + 1
            while following < len(source) and source[following].isspace():
                following += 1
            if following >= len(source) or not source[following].isidentifier():
                break
            _member_first, member_last = words.get_word_range(following)
            if member_last <= following:
                break
            end = member_last
        return end

    @classmethod
    def scoped_quoted_type_references(
        cls,
        source: str,
        project: p.Infra.RopeProject,
        module: p.Infra.RopePyModule,
    ) -> Iterator[tuple[str, p.Infra.RopeScope, int]]:
        """Yield native type primaries in quoted annotations, with original scope."""
        for begin, _end, literal, scope in cls.quoted_type_regions(
            source, project, module
        ):
            line = module.lines.get_line_number(begin)
            selected: list[str] = []

            def collect(
                _scope: p.Infra.RopeScope,
                expression: str,
                *,
                _selected: list[str] = selected,
            ) -> None:
                del _scope
                _selected.append(expression)

            cls.rewrite_type_source(literal, project, scope, collect)
            yield from ((expression, scope, line) for expression in selected)

    @classmethod
    def type_payload_ranges(
        cls,
        source: str,
        module: p.Infra.RopePyModule,
    ) -> frozenset[tuple[int, int]]:
        """Protect Literal values and Annotated metadata in every alias form.

        Selection uses the same resolved typing identities as quoted rewrites;
        an ordinary runtime assignment is not implicitly a type declaration.

        Returns:
            The resulting ``frozenset[t.Pair[int, int]]``.

        """
        protected: set[tuple[int, int]] = set()
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

    @classmethod
    def expression_segments(
        cls,
        source: str,
        begin: int,
        end: int,
        separators: str,
    ) -> tuple[tuple[int, int], ...]:
        """Split a native region using Rope-owned literal and delimiter ranges.

        A foreign runtime Worder product fails the split.

        Returns:
            Whitespace-trimmed sub-region pairs for every separator-delimited part.

        Raises:
            ValueError: If a Rope delimiter differs from the native region.

        """
        refactors = FlextInfraUtilitiesRopeRuntimeRefactors
        cls._require_worder(source, "type references require native Rope word regions")
        opaque = {
            start: stop for start, stop, _metadata in refactors.ignored_regions(source)
        }
        pairs = {"(": ")", "[": "]", "{": "}"}
        closers = {closing: opening for opening, closing in pairs.items()}
        regions: list[tuple[int, int]] = []
        opens: list[int] = []
        cursor = part = begin
        while cursor < end:
            ignored_end = opaque.get(cursor)
            if ignored_end is not None:
                cursor = ignored_end
                continue
            character = source[cursor]
            if character in pairs:
                opens.append(cursor)
            elif character in closers:
                if not opens or source[opens[-1]] != closers[character]:
                    msg = "type reference delimiter differs from native region"
                    raise ValueError(msg)
                opens.pop()
            elif character in separators and not opens:
                regions.append((part, cursor))
                part = cursor + 1
            cursor += 1
        if opens:
            msg = "type reference delimiter differs from native region"
            raise ValueError(msg)
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
    ) -> frozenset[tuple[int, int]]:
        """Protect typing payloads inside a quoted expression in its original scope.

        A foreign runtime Worder product fails the protection scan.

        Returns:
            The protected ``frozenset[t.Pair[int, int]]`` payload regions.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        words = cls._require_worder(
            source,
            "quoted types require native Rope delimiters",
        )
        typing = FlextInfraUtilitiesTypesRopeRuntime.require_semantic_module(
            project.get_module("typing")
        )
        protected: set[tuple[int, int]] = set()
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
    ) -> tuple[bool, tuple[m.Infra.SourceRewrite, ...]]:
        module = FlextInfraUtilitiesRopeCore.resolve_pymodule(
            flatten.project,
            FlextInfraUtilitiesTypesRopeRuntime.require_file_resource(
                resource, resource.path
            ),
        )
        edits: list[m.Infra.SourceRewrite] = []
        for begin, end, literal, scope in cls.quoted_type_regions(
            source, flatten.project, module
        ):
            blocked, changed = cls._quoted_type_source(
                literal, resource, scope, flatten=flatten
            )
            if blocked:
                return True, ()
            if changed != literal:
                edits.append(
                    m.Infra.SourceRewrite(start=begin, end=end, text=repr(changed))
                )
        return False, tuple(edits)

    @classmethod
    def _quoted_type_source(
        cls,
        source: str,
        _resource: p.Infra.RopeResource,
        scope: p.Infra.RopeScope,
        *,
        flatten: m.Infra.FamilyWrapperFlatten,
    ) -> tuple[bool, str]:
        del _resource
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        unresolved = False

        def replace(lexical: p.Infra.RopeScope, expression: str) -> str | None:
            nonlocal unresolved
            prefix, separator, name = expression.rpartition(".")
            if separator and runtime.same_name(
                flatten.wrapper, runtime.expression_name(lexical, prefix)
            ):
                if name not in flatten.names:
                    unresolved = True
                    return None
                parent, dotted, _wrapper = prefix.rpartition(".")
                if dotted:
                    return f"{parent}.{flatten.names[name]}"
                return (
                    f"{flatten.owner_name}.{flatten.names[name]}"
                    if lexical.get_kind() == c.Infra.RopeScopeKind.FUNCTION
                    and flatten.owner_name
                    else flatten.names[name]
                )
            if expression in flatten.names and runtime.same_name(
                flatten.wrapper.get_object().get_attribute(expression),
                runtime.expression_name(lexical, expression),
            ):
                return flatten.names[expression]
            return None

        changed = cls.rewrite_type_source(source, flatten.project, scope, replace)
        primaries = cls.reference_regions(changed)
        blocked = any(
            runtime.same_name(
                flatten.wrapper, runtime.expression_name(scope, changed[begin:end])
            )
            for begin, end in primaries
            if not any(
                other_begin <= begin and end < other_end
                for other_begin, other_end in primaries
            )
        )
        return unresolved or blocked, changed


__all__: list[str] = ["FlextInfraUtilitiesSemanticFamilyTypeReferences"]
