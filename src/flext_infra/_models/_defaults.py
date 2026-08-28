"""Typed immutable defaults shared by Pydantic model fields."""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType


def immutable_empty_mapping[K, V]() -> Mapping[K, V]:
    """Return a fresh, fully typed immutable empty mapping."""
    empty: dict[K, V] = {}
    return MappingProxyType(empty)


# Internal owner: direct module imports are intentional; no facade ABI is published.
__all__: tuple[str, ...] = ()
