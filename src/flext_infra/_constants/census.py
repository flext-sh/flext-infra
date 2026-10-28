"""Constants for the unified census pipeline — accessed via c.Infra.*.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)

import builtins
from enum import StrEnum, unique
from typing import ClassVar


class FlextInfraConstantsCensus:
    """Census pipeline constants for object detection and classification."""

    DUPLICATE_BUILTIN_NAMES: ClassVar[frozenset[str]] = frozenset(dir(builtins))
    "Native builtin bindings available to pure duplicate definitions."
    DUPLICATE_PURE_CONSTRUCTORS: ClassVar[frozenset[str]] = frozenset({
        "bool",
        "bytes",
        "complex",
        "dict",
        "float",
        "frozenset",
        "int",
        "list",
        "range",
        "set",
        "str",
        "tuple",
    })
    "Builtin constructors admitted by the duplicate purity grammar."
    DUPLICATE_TRIVIAL_KINDS: ClassVar[frozenset[str]] = frozenset({
        "assignment",
        "class",
        "constant",
        "function",
    })
    "Census object kinds supporting identity-proven cure planning."
    DUPLICATE_DELETE_ACTION: ClassVar[str] = "delete-copy"
    "Removal action recorded by the public duplicate cure receipt."
    DUPLICATE_REBIND_ACTION: ClassVar[str] = "rebind-import"
    "Consumer import migration action."
    DUPLICATE_BIND_ACTION: ClassVar[str] = "bind-owner"
    "Binding of the elected duplicate owner."
    DUPLICATE_KEEP_ACTION: ClassVar[str] = "keep-owner"
    "Preservation of the elected duplicate owner."

    @unique
    class CensusRule(StrEnum):
        """Stable analysis identifiers shared by census and semantic planning."""

        DUPLICATE = "duplicate"
        UNUSED = "unused"
        WRONG_TIER = "wrong_tier"
        CONSTANT_CONSUMERS = "constant-consumers"

    CENSUS_UNSUPPORTED_SIMPLE_REMOVAL_CODE: ClassVar[str] = (
        "CENSUS_UNSUPPORTED_SIMPLE_REMOVAL"
    )
    "Error code marking a candidate outside the simple-removal contract."


__all__: list[str] = ["FlextInfraConstantsCensus"]
