"""Rope refactor and occurrence boundary methods.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import cast

from flext_cli import u

from flext_infra import m, p, r, t
from flext_infra._utilities import FlextInfraUtilitiesRopeRuntimeBase


class FlextInfraUtilitiesRopeRuntimeRefactors(FlextInfraUtilitiesRopeRuntimeBase):
    """Load Rope refactor helpers behind protocols."""

    @classmethod
    def ignored_regions(
        cls,
        source: str,
    ) -> t.VariadicTuple[t.Triple[int, int, t.MappingKV[str, str | None]]]:
        """Read complete literal and comment ranges from Rope's native lexer.

        Returns:
            Strictly validated native source coordinates and token metadata.
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
        pattern: str,
        goal: str,
        *,
        arguments: t.MappingKV[str, str],
        resources: t.SequenceOf[p.Infra.RopeResource],
        imports: t.StrSequence = (),
        match_filter: Callable[[p.Infra.RopePyModule, p.Infra.RopeContractMatch], bool]
        | None = None,
        import_bindings: t.MappingKV[str, str] | None = None,
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
            pattern,
            goal,
            args=dict(arguments),
            imports=list(imports),
            match_filter=match_filter,
            import_bindings=import_bindings,
        )
        if not isinstance(restructuring, p.Infra.RopeRestructure):
            msg = "rope Restructure does not satisfy its public planning contract"
            raise TypeError(msg)
        changes = restructuring.get_changes(resources=list(resources))
        u.Cli.info(
            "Rope restructuring "
            f"matched={restructuring.matched_count} "
            f"admitted={restructuring.admitted_count} pattern={pattern}"
        )
        return changes

    @classmethod
    def contract_matches(
        cls,
        module: p.Infra.RopePyModule,
        pattern: str,
        arguments: t.MappingKV[str, str],
    ) -> t.VariadicTuple[p.Infra.RopeContractMatch]:
        """Match native Rope patterns with declaration identity constraints.

        Returns:
            Native matches exposing only authenticated source coordinates.

        Raises:
            TypeError: When the SDK does not satisfy the matching contract.
        """
        finder = cls.runtime_callable("rope.refactor.similarfinder", "SimilarFinder")(
            module
        )
        if not isinstance(finder, p.Infra.RopeSimilarFinder):
            message = "Rope SimilarFinder does not satisfy its public contract"
            raise TypeError(message)
        matches = tuple(finder.get_matches(pattern, args=dict(arguments)))
        if not all(isinstance(match, p.Infra.RopeContractMatch) for match in matches):
            message = "Rope SimilarFinder returned an invalid match"
            raise TypeError(message)
        return matches

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
        """Read a captured region through Rope's opaque native match boundary.

        No syntax tree is parsed, inspected or traversed by this adapter.

        Returns:
            Native character coordinates of the named capture.

        Raises:
            ValueError: If the requested variable was not captured.
            TypeError: If Rope returned an invalid region.
        """
        captured = match.get_ast(variable)
        if captured is None:
            message = f"Rope match has no captured variable: {variable}"
            raise ValueError(message)
        region = cls.runtime_callable(
            "rope.refactor.patchedast",
            "node_region",
        )(captured)
        if not isinstance(region, tuple) or len(region) != 2:
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
        """Find native lexical occurrences independently of last-binding inference.

        Returns:
            Rope's unfiltered finder, with strings and comments excluded.

        Raises:
            TypeError: If the finder does not satisfy its native contract.
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
