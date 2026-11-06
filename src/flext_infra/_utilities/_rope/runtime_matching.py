"""Native Rope semantic pattern-matching boundary.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Generator, Mapping, MutableMapping, Sequence
from contextlib import contextmanager
from contextvars import ContextVar
from typing import ClassVar

from flext_infra import p, t
from flext_infra._utilities._rope import FlextInfraUtilitiesRopeRuntimeBase


class FlextInfraUtilitiesRopeRuntimeMatching(FlextInfraUtilitiesRopeRuntimeBase):
    """Delegate semantic matching, capture, occurrence and word queries to Rope."""

    _semantic_finders: ClassVar[
        ContextVar[
            MutableMapping[
                tuple[p.Infra.RopePyModule, tuple[tuple[str, str], ...]],
                p.Infra.RopeSimilarFinder,
            ]
            | None
        ]
    ] = ContextVar("rope_semantic_finders", default=None)

    @classmethod
    def native_call_parameters(
        cls, source: str, primary: tuple[int, int]
    ) -> tuple[Sequence[str], Sequence[tuple[str, str]]] | None:
        """Read an authored call's argument shape through native Rope Worder.

        Returns:
            Native call arguments, or None when the position is not a callee.

        Raises:
            TypeError: The installed Worder lacks the consumed native contract.

        """
        words = cls.runtime_callable("rope.base.worder", "Worder")(source)
        if not isinstance(words, p.Infra.RopeWorder):
            message = "Native Worder does not expose call parameter shapes"
            raise TypeError(message)
        offset, _last = words.get_word_range(primary[1] - 1)
        if not words.is_a_function_being_called(offset):
            return None
        first, last = words.get_word_parens_range(offset)
        return words.get_parameters(first, last - 1)

    @classmethod
    @contextmanager
    def semantic_matching_context(cls) -> Generator[None]:
        """Retain native matchers only within one immutable semantic pass.

        Yields:
            A context whose native matcher caches cannot escape to another epoch.

        """
        if cls._semantic_finders.get() is not None:
            yield
            return
        token = cls._semantic_finders.set({})
        try:
            yield
        finally:
            cls._semantic_finders.reset(token)

    @classmethod
    def semantic_regions(
        cls,
        module: p.Infra.RopePyModule,
        pattern: str,
        *,
        arguments: Mapping[str, str],
        start: int = 0,
        end: int | None = None,
    ) -> tuple[tuple[int, int], ...]:
        """Resolve source regions through Rope's identity-aware pattern matcher.

        Returns:
            Matched character ranges from the module's immutable source snapshot.

        Raises:
            AttributeError: If native matching fails to resolve a semantic attribute.

        """
        finder = cls.semantic_finder(module, arguments=arguments)
        try:
            return tuple(
                match.get_region()
                for match in finder.get_matches(
                    pattern, arguments, start=start, end=end
                )
            )
        except AttributeError as error:
            resource = module.get_resource()
            error.add_note(
                f"Rope semantic match resource={resource.path if resource else None!r} "
                f"pattern={pattern!r} arguments={arguments!r} region={(start, end)!r}",
            )
            raise

    @classmethod
    def semantic_finder(
        cls,
        module: p.Infra.RopePyModule,
        *,
        arguments: Mapping[str, str] | None = None,
    ) -> p.Infra.RopeSimilarFinder:
        """Create a native matcher for one immutable module and binding context.

        Rope caches matches by pattern text. A reused pattern must retain its
        identity arguments; distinct bindings require distinct wildcard names.
        Explicit arguments opt into reuse within the active immutable pass;
        callers that omit them receive a fresh matcher.

        Returns:
            Rope's identity-aware matcher for the supplied module.

        Raises:
            TypeError: If Rope does not expose its semantic region contract.

        """
        cache = None if arguments is None else cls._semantic_finders.get()
        key = (module, tuple(sorted((arguments or {}).items())))
        if cache is not None and (cached := cache.get(key)) is not None:
            return cached
        finder = cls.runtime_callable("rope.refactor.similarfinder", "SimilarFinder")(
            module,
        )
        if not isinstance(finder, p.Infra.RopeSimilarFinder):
            message = "Rope SimilarFinder does not expose semantic match regions"
            raise TypeError(message)
        if cache is not None:
            cache[key] = finder
        return finder

    @classmethod
    def semantic_capture(
        cls,
        project: p.Infra.RopeProject,
        module: p.Infra.RopePyModule,
        captured: p.AttributeProbe | None,
        constraints: str | Sequence[str],
        *,
        name: str,
    ) -> bool:
        """Delegate capture constraints and alternatives to Rope's native matcher.

        Returns:
            Whether any declared alternative admits the original captured node.

        Raises:
            ValueError: The declared capture is absent from the original match.
            TypeError: Rope does not expose its default wildcard contract.

        """
        if captured is None:
            message = f"Rope match has no captured variable: {name}"
            raise ValueError(message)
        wildcard = cls.runtime_callable("rope.refactor.wildcards", "DefaultWildcard")(
            project
        )
        if not isinstance(wildcard, p.Infra.RopeDefaultWildcard):
            message = "Rope DefaultWildcard does not satisfy its native contract"
            raise TypeError(message)
        suspect = cls.runtime_callable("rope.refactor.wildcards", "Suspect")(
            module, captured, name
        )
        choices = (constraints,) if isinstance(constraints, str) else constraints
        return any(wildcard.matches(suspect, choice) for choice in choices)

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

        Args:
            project: The Rope project in which to search for occurrences.
            name: The name of the variable or function to find occurrences for.

        Returns:
            The native finder for occurrences of the specified name.

        Raises:
            TypeError: If the finder violates its native Rope contract.

        """
        finder = cls.runtime_callable("rope.refactor.occurrences", "Finder")(
            project, name
        )
        if not isinstance(finder, p.Infra.RopeOccurrenceFinder):
            message = "Rope lexical finder does not satisfy its native contract"
            raise TypeError(message)
        return finder

    @classmethod
    def word_primary_range(cls, source: str, offset: int) -> tuple[int, int]:
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
        cls, source: str, region: tuple[int, int]
    ) -> Sequence[tuple[int, int]]:
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
        regions: set[tuple[int, int]] = set()
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
        return cls.runtime_callable("rope.base.worder", "Worder")(
            source, handle_ignores=True
        )


__all__: list[str] = ["FlextInfraUtilitiesRopeRuntimeMatching"]
