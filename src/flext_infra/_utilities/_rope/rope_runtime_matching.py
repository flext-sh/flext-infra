"""Native Rope semantic pattern-matching boundary.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager
from contextvars import ContextVar
from typing import ClassVar

from flext_infra import p, t
from flext_infra._utilities._rope.rope_runtime_base import (
    FlextInfraUtilitiesRopeRuntimeBase,
)


class FlextInfraUtilitiesRopeRuntimeMatching(FlextInfraUtilitiesRopeRuntimeBase):
    """Delegate semantic matching and capture queries to Rope's native SDK."""

    _semantic_finders: ClassVar[
        ContextVar[
            t.MutableMappingKV[
                t.Pair[p.Infra.RopePyModule, t.VariadicTuple[t.Pair[str, str]]],
                p.Infra.RopeSimilarFinder,
            ]
            | None
        ]
    ] = ContextVar("rope_semantic_finders", default=None)

    @classmethod
    @contextmanager
    def semantic_matching_context(cls) -> Generator[None]:
        """Retain native matchers only within one immutable semantic pass.

        Yields:
            A context whose native matcher caches cannot escape to another epoch.

        """
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
        arguments: t.MappingKV[str, str],
        start: int = 0,
        end: int | None = None,
    ) -> t.VariadicTuple[t.Pair[int, int]]:
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
        arguments: t.MappingKV[str, str] | None = None,
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
        constraints: str | t.StrSequence,
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
    def semantic_capture_region(
        cls,
        match: p.Infra.RopeContractMatch,
        variable: str,
    ) -> t.Pair[int, int]:
        """Read a captured region through Rope's native match boundary.

        Args:
            match: The Rope match object containing captured variables.
            variable: The name of the captured variable to retrieve the region for.

        Returns:
            The start and end character positions of the captured region.

        Raises:
            ValueError: If the specified variable is not captured in the match.
            TypeError: If the captured region does not conform to the expected format.

        """
        captured = match.get_ast(variable)
        if captured is None:
            message = f"Rope match has no captured variable: {variable}"
            raise ValueError(message)
        region = cls.runtime_callable(
            "rope.refactor.patchedast",
            "node_region",
        )(captured)
        match region:
            case tuple((int(begin), int(end))):
                return begin, end
            case _:
                message = "Rope capture does not expose its native character region"
                raise TypeError(message)


__all__: list[str] = ["FlextInfraUtilitiesRopeRuntimeMatching"]
