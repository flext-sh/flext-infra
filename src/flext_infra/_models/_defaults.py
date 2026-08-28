"""Typed immutable defaults shared by Pydantic model fields."""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType
from typing import Any, Never


def immutable_empty_mapping() -> Mapping[Any, Never]:
    """Return a fresh immutable empty mapping."""
    empty: dict[Any, Never] = {}
    return MappingProxyType(empty)


# Internal owner: direct module imports are intentional; no facade ABI is published.
__all__: tuple[str, ...] = ()
