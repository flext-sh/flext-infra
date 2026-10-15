"""Rope refactor and occurrence boundary methods.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from collections.abc import Sequence
from typing import cast

from flext_cli import u

from flext_infra import m, p, r, t
from flext_infra._utilities import FlextInfraUtilitiesRopeRuntimeBase

_NATIVE_REGION_SPAN = 2


class FlextInfraUtilitiesRopeRuntimeRefactors(FlextInfraUtilitiesRopeRuntimeBase):
    """Load Rope refactor helpers behind protocols."""

    @classmethod
    def reindent_source(cls, source: str, amount: int) -> str:
        """Move source indentation while retaining every multiline literal value.

        Returns:
            The resulting ``str``.

        Raises:
            ValueError: If source indentation is smaller than its native move.

        """
        literals = tuple(
            (begin, end)
            for begin, end, _metadata in cls.ignored_regions(source)
            if source[begin] != "#"
        )
        result = []
        offset = 0
        for line in source.splitlines(keepends=True):
            inside_literal = any(begin < offset < end for begin, end in literals)
            if not inside_literal and line.strip():
                if amount >= 0:
                    changed = " " * amount + line
                else:
                    removable = len(line) - len(line.lstrip(" \t"))
                    if removable < -amount:
                        msg = "source indentation is smaller than its native move"
                        raise ValueError(msg)
                    changed = line[-amount:]
            else:
                changed = line
            result.append(changed)
            offset += len(line)
        return "".join(result)

    @staticmethod
    def compiled_constant(source: str) -> p.Result[p.AttributeProbe]:
        """Read a primitive compiler constant without executing authored source.

        Returns:
            The resulting ``p.Result[p.AttributeProbe]``.

        """
        code = compile(source, "<native constant>", "eval", dont_inherit=True)
        if code.co_names or code.co_freevars or len(code.co_consts) != 1:
            return r[p.AttributeProbe].fail("expression has no sole native constant")
        value = code.co_consts[0]
        if (
            type(value) not in {str, bytes, int, float, complex, bool, type(None)}
            and value is not Ellipsis
        ):
            return r[p.AttributeProbe].fail(
                "expression has no primitive native constant"
            )
        return r[p.AttributeProbe].ok(value)

    @classmethod
    def literal_constant(cls, source: str) -> bool:
        """Return whether native compilation proves a sole immutable primitive."""
        return cls.compiled_constant(source).success

    @classmethod
    def literal_string(cls, source: str) -> str | None:
        """Decode native string escapes without evaluating source callbacks.

        Returns:
            The resulting ``str | None``.

        """
        observed = cls.compiled_constant(source)
        if observed.failure:
            return None
        value = observed.value
        return value if type(value) is str else None

    @classmethod
    def ignored_regions(
        cls,
        source: str,
    ) -> t.VariadicTuple[t.Triple[int, int, t.MappingKV[str, str | None]]]:
        """Read complete literal and comment ranges from Rope's native lexer.

        Returns:
            The resulting ``t.VariadicTuple[t.Triple[int, int, t.MappingKV[str, str |
                None]]]``.

        """
        adapter: t.ValueAdapter[
            t.SequenceOf[t.Triple[int, int, t.MappingKV[str, str | None]]]
        ] = u.type_adapter(
            Sequence[tuple[int, int, dict[str, str | None]]],
        )
        return tuple(
            adapter.validate_python(
                cls.runtime_callable("rope.base.simplify", "ignored_regions")(source),
                strict=True,
            ),
        )

    @classmethod
    def patched_ast(cls, source: str) -> ast.AST:
        """Parse the real SDK patched AST and validate its native result.

        Returns:
            The SDK AST with source-order information attached.

        Raises:
            TypeError: If the native parser does not return an AST.

        """
        value = cls.runtime_callable(
            "rope.refactor.patchedast",
            "get_patched_ast",
        )(source, sorted_children=True)
        if not isinstance(value, ast.AST):
            msg = "Rope patched AST parser did not return an AST"
            raise TypeError(msg)
        return value

    @classmethod
    def write_patched_ast(cls, tree: ast.AST) -> str:
        """Render the real SDK patched AST without replacing its writer.

        Returns:
            The source emitted by the native patched-AST writer.

        Raises:
            TypeError: If the native writer does not return source text.

        """
        value = cls.runtime_callable(
            "rope.refactor.patchedast",
            "write_ast",
        )(tree)
        if not isinstance(value, str):
            msg = "Rope patched AST writer did not return source text"
            raise TypeError(msg)
        return value

    @staticmethod
    def change_set_members(
        value: p.AttributeProbe,
        invalid_result: str,
    ) -> p.Result[t.SequenceOf[p.Infra.RopeChangeContents]]:
        """Validate a native content-change list once at the Rope SDK boundary.

        Returns:
            Typed content changes, or a failure for malformed lists or members.

        """
        if not isinstance(value, list):
            return r[t.SequenceOf[p.Infra.RopeChangeContents]].fail(invalid_result)
        members = cast("list[p.AttributeProbe]", value)
        validated: list[p.Infra.RopeChangeContents] = []
        for member in members:
            if not isinstance(member, p.Infra.RopeChangeContents):
                return r[t.SequenceOf[p.Infra.RopeChangeContents]].fail(invalid_result)
            validated.append(member)
        return r[t.SequenceOf[p.Infra.RopeChangeContents]].ok(tuple(validated))

    @classmethod
    def unwrap_class_rewrites(
        cls,
        source: str,
        layout: m.Infra.ClassBlockLayout,
    ) -> t.VariadicTuple[m.Infra.SourceRewrite]:
        """Remove one Rope-resolved header without changing literal payloads.

        The body statements own the dedent width and the wrapper docstring, so
        both derive from the logical facts instead of being passed alongside.

        Returns:
            The resulting ``t.VariadicTuple[m.Infra.SourceRewrite]``.

        Raises:
            TypeError: If Rope's source lines do not satisfy their public contract.
            ValueError: If Rope wrapper body has inconsistent indentation.

        """
        lines = cls.runtime_callable("rope.base.codeanalyze", "SourceLinesAdapter")(
            source,
        )
        if not isinstance(lines, p.Infra.RopeSourceLines):
            msg = "Rope SourceLinesAdapter does not satisfy its public contract"
            raise TypeError(msg)
        regions = cls.ignored_regions(source)
        start = lines.get_line_start(layout.header_start)
        end = min(lines.get_line_end(layout.header_end) + 1, len(source))
        comments = "".join(
            source[begin:finish] + "\n"
            for begin, finish, _metadata in regions
            if start <= begin < end and source[begin:finish].startswith("#")
        )
        prefix = lines.get_line(layout.header_start)
        prefix = prefix[: len(prefix) - len(prefix.lstrip())]
        edits = [
            m.Infra.SourceRewrite(
                start=start,
                end=end,
                text="".join(
                    prefix + line for line in comments.splitlines(keepends=True)
                ),
            ),
        ]
        for number in range(layout.header_end + 1, layout.body_end + 1):
            offset = lines.get_line_start(number)
            line = lines.get_line(number)
            if layout.docstring_span is not None and (
                layout.docstring_span[0] <= number <= layout.docstring_span[1]
            ):
                continue
            if not line.strip() or any(
                begin < offset < finish
                for begin, finish, _metadata in regions
                if not source[begin:finish].startswith("#")
            ):
                continue
            if len(line) - len(line.lstrip()) < layout.indentation:
                msg = "Rope wrapper body has inconsistent indentation"
                raise ValueError(msg)
            edits.append(
                m.Infra.SourceRewrite(
                    start=offset,
                    end=offset + layout.indentation,
                    text="",
                ),
            )
        if layout.docstring_span is not None:
            edits.append(
                m.Infra.SourceRewrite(
                    start=lines.get_line_start(layout.docstring_span[0]),
                    end=min(
                        lines.get_line_end(layout.docstring_span[1]) + 1,
                        len(source),
                    ),
                    text="",
                ),
            )
        return tuple(edits)

    @classmethod
    def content_change(
        cls,
        resource: p.Infra.RopeResource,
        source: str,
        rewrites: t.SequenceOf[m.Infra.SourceRewrite],
    ) -> p.Infra.RopeChangeContents:
        """Preview checked, disjoint edits through Rope's change machinery.

        Returns:
            The resulting ``p.Infra.RopeChangeContents``.

        Raises:
            TypeError: If Rope ChangeCollector has an invalid contract; or if Rope
                ChangeCollector returned a non-source result; or if Rope ChangeContents
                returned an invalid content plan.
            ValueError: If Rope source edits overlap or escape their snapshot.

        """
        collector = cls.runtime_callable("rope.base.codeanalyze", "ChangeCollector")(
            source,
        )
        add = getattr(collector, "add_change", None)
        changed = getattr(collector, "get_changed", None)
        if not callable(add) or not callable(changed):
            msg = "Rope ChangeCollector has an invalid contract"
            raise TypeError(msg)
        end = 0
        for rewrite in sorted(rewrites, key=lambda item: (item.start, item.end)):
            if rewrite.start < end or not 0 <= rewrite.start <= rewrite.end <= len(
                source,
            ):
                msg = "Rope source edits overlap or escape their snapshot"
                raise ValueError(msg)
            add(rewrite.start, rewrite.end, rewrite.text)
            end = rewrite.end
        updated = changed()
        if updated is None:
            updated = source
        if not isinstance(updated, str):
            msg = "Rope ChangeCollector returned a non-source result"
            raise TypeError(msg)
        change = cls.runtime_callable("rope.base.change", "ChangeContents")(
            resource,
            updated,
        )
        if not isinstance(change, p.Infra.RopeChangeContents):
            msg = "Rope ChangeContents returned an invalid content plan"
            raise TypeError(msg)
        return change

    @classmethod
    def restructure_changes(
        cls,
        rope_project: p.Infra.RopeProject,
        request: m.Infra.RopeRestructureRequest,
    ) -> p.Infra.RopeChangeSet:
        """Plan Rope 1.14 semantic changes without invoking Project.do.

        Returns:
            The resulting ``p.Infra.RopeChangeSet``.

        Raises:
            TypeError: If rope Restructure does not satisfy its public planning
                contract.

        """
        factory = cls.runtime_callable(
            "flext_infra._utilities._rope.restructure", "FlextInfraRopeRestructure"
        )
        restructuring = factory(
            rope_project,
            request,
        )
        if not isinstance(restructuring, p.Infra.RopeRestructure):
            msg = "rope Restructure does not satisfy its public planning contract"
            raise TypeError(msg)
        changes = restructuring.get_changes(resources=list(request.resources))
        u.Cli.info(
            "Rope restructuring "
            f"matched={restructuring.matched_count} "
            f"admitted={restructuring.admitted_count} pattern={request.pattern}"
        )
        return changes

    @classmethod
    def semantic_regions(
        cls,
        module: p.Infra.RopePyModule,
        pattern: str,
        *,
        arguments: t.MappingKV[str, str],
        start: int = 0,
        end: int | None = None,
    ) -> t.VariadicTuple[t.Pair[int, int]]:
        """Resolve source regions through Rope's identity-aware pattern matcher.

        Returns:
            Matched character ranges from the module's immutable source snapshot.

        """
        finder = cls.semantic_finder(module)
        return tuple(finder.get_match_regions(pattern, arguments, start=start, end=end))

    @classmethod
    def semantic_finder(
        cls,
        module: p.Infra.RopePyModule,
    ) -> p.Infra.RopeSimilarFinder:
        """Reuse one native matcher across an immutable module's semantic queries.

        Rope caches matches by pattern text. A reused pattern must retain its
        identity arguments; distinct bindings require distinct wildcard names.

        Returns:
            Rope's identity-aware matcher for the supplied module.

        Raises:
            TypeError: If Rope does not expose its semantic region contract.

        """
        finder = cls.runtime_callable("rope.refactor.similarfinder", "SimilarFinder")(
            module,
        )
        if not isinstance(finder, p.Infra.RopeSimilarFinder):
            message = "Rope SimilarFinder does not expose semantic match regions"
            raise TypeError(message)
        return finder

    @classmethod
    def semantic_capture_region(
        cls,
        match: p.Infra.RopeContractMatch,
        variable: str,
    ) -> t.Pair[int, int]:
        """Read a captured region through Rope's native match boundary.

        Returns:
            The resulting ``t.Pair[int, int]``.

        Raises:
            TypeError: If Rope capture does not expose its native character region; or
                if Rope capture region contains non-integer coordinates.
            ValueError: If Rope match has no captured variable.

        """
        captured = match.get_ast(variable)
        if captured is None:
            message = f"Rope match has no captured variable: {variable}"
            raise ValueError(message)
        region = cls.runtime_callable(
            "rope.refactor.patchedast",
            "node_region",
        )(captured)
        if not isinstance(region, tuple) or len(region) != _NATIVE_REGION_SPAN:
            message = "Rope capture does not expose its native character region"
            raise TypeError(message)
        begin, end = region
        if not isinstance(begin, int) or not isinstance(end, int):
            message = "Rope capture region contains non-integer coordinates"
            raise TypeError(message)
        return begin, end

    @classmethod
    def create_move(
        cls,
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
        offset: int | None,
    ) -> t.Infra.RopeMoveGlobal:
        create = cls.runtime_callable("rope.refactor.move", "create_move")
        mover = create(rope_project, resource, offset)
        if not isinstance(mover, p.Infra.RopeMoveGlobal):
            msg = "rope create_move did not return MoveGlobal-compatible object"
            raise TypeError(msg)
        return mover

    @classmethod
    def rename_changes(
        cls,
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
        offset: int,
        new_name: str,
        *,
        options: m.Infra.RopeRenameOptions,
    ) -> t.Infra.RopeChangeSet:
        renamer_factory = cls.runtime_callable("rope.refactor.rename", "Rename")
        renamer = renamer_factory(rope_project, resource, offset)
        get_changes = getattr(renamer, "get_changes", None)
        if not callable(get_changes):
            msg = "rope Rename does not expose callable get_changes"
            raise TypeError(msg)
        changes = get_changes(
            new_name,
            resources=list(options.resources),
            in_hierarchy=options.in_hierarchy,
        )
        if not isinstance(changes, p.Infra.RopeChangeSet):
            msg = "rope Rename returned invalid ChangeSet"
            raise TypeError(msg)
        return changes

    @classmethod
    def create_occurrence_finder(
        cls,
        rope_project: t.Infra.RopeProject,
        name: str,
        pyname: t.Infra.RopePyName,
        *,
        imports: bool,
        in_hierarchy: bool,
    ) -> t.Infra.RopeOccurrenceFinder:
        create_finder = cls.runtime_callable(
            "rope.refactor.occurrences",
            "create_finder",
        )
        finder = create_finder(
            rope_project,
            name,
            pyname,
            imports=imports,
            in_hierarchy=in_hierarchy,
        )
        if not isinstance(finder, p.Infra.RopeOccurrenceFinder):
            msg = "rope occurrence finder does not satisfy p.Infra.RopeOccurrenceFinder"
            raise TypeError(msg)
        return finder

    @classmethod
    def lexical_occurrence_finder(
        cls, project: p.Infra.RopeProject, name: str
    ) -> p.Infra.RopeOccurrenceFinder:
        """Find native lexical occurrences without last-binding inference.

        Returns:
            The resulting ``p.Infra.RopeOccurrenceFinder``.

        Raises:
            TypeError: If Rope lexical finder does not satisfy its native contract.

        """
        finder = cls.runtime_callable("rope.refactor.occurrences", "Finder")(
            project, name
        )
        if not isinstance(finder, p.Infra.RopeOccurrenceFinder):
            message = "Rope lexical finder does not satisfy its native contract"
            raise TypeError(message)
        return finder

    @classmethod
    def word_primary_range(cls, source: str, offset: int) -> t.Pair[int, int]:
        word_finder = cls._word_finder(source)
        primary_range = getattr(word_finder, "get_primary_range", None)
        if not callable(primary_range):
            msg = "rope Worder does not expose callable get_primary_range"
            raise TypeError(msg)
        value = primary_range(offset)
        match value:
            case tuple([int() as start, int() as end]):
                return start, end
            case _:
                msg = "rope Worder returned invalid primary range"
                raise TypeError(msg)

    @classmethod
    def word_call_regions(
        cls, source: str, region: t.Pair[int, int]
    ) -> t.SequenceOf[t.Pair[int, int]]:
        """Collect native call facts using one Rope word finder for the region.

        Returns:
            Distinct called-word regions, with strings and comments ignored.

        Raises:
            TypeError: When Rope cannot provide its declared word facts.

        """
        finder = cls._word_finder(source)
        if not isinstance(finder, p.Infra.RopeWorder):
            message = "Rope word finder does not satisfy its source fact contract"
            raise TypeError(message)
        regions: set[t.Pair[int, int]] = set()
        offset, limit = region
        while offset < limit:
            start, end = finder.get_word_range(offset)
            if start < end <= limit and finder.is_a_function_being_called(start):
                regions.add((start, end))
            offset = max(offset + 1, end)
        return tuple(sorted(regions))

    @classmethod
    def word_is_function_call(cls, source: str, offset: int) -> bool:
        """Return Rope's syntactic call fact for the primary at ``offset``.

        Returns:
            Rope's syntactic call fact for the primary at ``offset``.

        Raises:
            TypeError: If rope Worder does not expose callable
                is_a_function_being_called; or if rope Worder returned a non-boolean
                function-call fact.

        """
        word_finder = cls._word_finder(source)
        is_called = getattr(word_finder, "is_a_function_being_called", None)
        if not callable(is_called):
            msg = "rope Worder does not expose callable is_a_function_being_called"
            raise TypeError(msg)
        value = is_called(offset)
        if not isinstance(value, bool):
            msg = "rope Worder returned a non-boolean function-call fact"
            raise TypeError(msg)
        return value

    @classmethod
    def _word_finder(cls, source: str) -> p.AttributeProbe:
        worder_module = cls._module("rope.base.worder")
        worder_factory = getattr(worder_module, "Worder", None)
        if not callable(worder_factory):
            msg = "rope Worder factory is not callable"
            raise TypeError(msg)
        finder: p.AttributeProbe = worder_factory(source, handle_ignores=True)
        return finder


__all__: list[str] = ["FlextInfraUtilitiesRopeRuntimeRefactors"]
