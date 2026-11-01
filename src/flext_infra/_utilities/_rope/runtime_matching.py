"""Native Rope semantic pattern-matching boundary.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import logging
from collections.abc import Generator, Mapping, MutableMapping, Sequence
from contextlib import contextmanager
from contextvars import ContextVar
from typing import ClassVar

from flext_infra import p
from flext_infra._utilities._rope import FlextInfraUtilitiesRopeRuntimeBase

_LOGGER = logging.getLogger(__name__)


class FlextInfraUtilitiesRopeRuntimeMatching(FlextInfraUtilitiesRopeRuntimeBase):
    """Delegate semantic matching and capture queries to Rope's native SDK."""

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

        Matches whose node shapes Rope cannot map to a source region (bare
        constants) are skipped with a logged note; policy detection stays
        authoritative and the rule simply does not rewrite that node.

        Returns:
            Matched character ranges from the module's immutable source snapshot.

        """
        finder = cls.semantic_finder(module, arguments=arguments)
        regions: list[tuple[int, int]] = []

        def region_of(match: p.Infra.RopeMatch) -> tuple[int, int]:
            """Map one match to its source region, skipping unmappable shapes.

            Returns:
                The matched character range.

            """
            try:
                return match.get_region()
            except AttributeError as error:
                resource = module.get_resource()
                error.add_note(
                    f"Rope semantic match skipped resource="
                    f"{resource.path if resource else None!r} "
                    f"pattern={pattern!r} arguments={arguments!r} "
                    f"region={(start, end)!r}",
                )
                _LOGGER.warning("rope semantic match skipped: %s", error)
                return (-1, -1)

        try:
            mapped = (
                region_of(match)
                for match in finder.get_matches(
                    pattern, arguments, start=start, end=end
                )
            )
            regions.extend(region for region in mapped if region != (-1, -1))
        except AttributeError as error:
            # the native matcher is itself a lazy generator: it may hit the
            # same unmappable node while iterating; regions resolved so far
            # are kept and the skip stays visible
            resource = module.get_resource()
            error.add_note(
                f"Rope semantic match stream skipped resource="
                f"{resource.path if resource else None!r} "
                f"pattern={pattern!r} arguments={arguments!r} "
                f"region={(start, end)!r}",
            )
            _LOGGER.warning("rope semantic match stream skipped: %s", error)
        return tuple(regions)

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


__all__: list[str] = ["FlextInfraUtilitiesRopeRuntimeMatching"]
