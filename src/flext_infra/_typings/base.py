"""Base typings for flext-infra project.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, MutableMapping, MutableSequence, Sequence
from pathlib import Path as _Path

from flext_core import FlextTypes
from pydantic import BaseModel


class FlextInfraTypesBase:
    """Base typings for flext-infra project."""

    type Pair[LeftT, RightT] = tuple[LeftT, RightT]
    "Generic pair alias for two ordered values."
    type Triple[FirstT, SecondT, ThirdT] = tuple[FirstT, SecondT, ThirdT]
    "Generic triple alias for three ordered values."
    type Quad[FirstT, SecondT, ThirdT, FourthT] = tuple[
        FirstT,
        SecondT,
        ThirdT,
        FourthT,
    ]
    "Generic 4-item tuple alias."
    type Quint[FirstT, SecondT, ThirdT, FourthT, FifthT] = tuple[
        FirstT,
        SecondT,
        ThirdT,
        FourthT,
        FifthT,
    ]
    "Generic 5-item tuple alias."
    type VariadicTuple[ItemT] = tuple[ItemT, ...]
    "Generic variadic tuple alias for homogeneous tuples."

    type InfraValue = (
        str
        | int
        | float
        | bool
        | Mapping[str, FlextInfraTypesBase.InfraValue]
        | Sequence[FlextInfraTypesBase.InfraValue]
        | None
    )
    "Recursive infrastructure value: primitive, nested dict/list, or null."
    type ContainerDict = Mapping[str, InfraValue]
    "Dict with string keys and infra values (project reports, etc.)."
    type FacadeFamily = str
    "Facade family identifier for MRO chain resolution."
    type ExpectedBase = type | str
    "Expected MRO base: a class or its qualified name."
    type PolicyContext = Mapping[str, ContainerDict]
    "Class-nesting policy matrix keyed by module family."
    type MetricValue = FlextTypes.Scalar | _Path | None
    "Output metric value: scalar (str/int/float/bool/datetime), path, or null."
    type MetricRecord = BaseModel | Mapping[str, MetricValue]
    "A single metric record: a Pydantic model or a string-keyed mapping of metric values."
    type ChangeCallback = Callable[[str], None] | None
    "Optional callback invoked on transformer changes."
    type StrIndex = Mapping[str, int]
    "String-keyed integer index (counters, metrics)."
    type MutableStrIndex = MutableMapping[str, int]
    "Mutable string-keyed integer index."
    type StrPair = tuple[str, str]
    "Ordered pair of strings."
    type StrIntPair = tuple[str, int]
    "Ordered pair of (str, int)."
    type IntPair = tuple[int, int]
    "Ordered pair of (int, int)."
    type StrPairSequence = Sequence[StrPair]
    "Read-only sequence of string pairs."
    type LazyImportMap = Mapping[str, StrPair]
    "Lazy import table: export -> (module, attr)."
    type MutableLazyImportMap = MutableMapping[str, StrPair]
    "Mutable lazy import table."
    type LazyInitProcessResult = tuple[int | None, LazyImportMap]
    "Result for per-directory lazy init processing."
    type LazyInitWriteResult = tuple[int, LazyImportMap]
    "Result for writing generated __init__.py."
    type VersionExportsResult = tuple[FlextTypes.StrMapping, LazyImportMap]
    "Result for __version__.py export extraction (inline constants, eager import map)."
    type StrSet = set[str]
    "Mutable string set (supports .update/.intersection/etc)."
    type PathSet = set[_Path]
    "Mutable path set."
    type IntSet = set[int]
    "Mutable integer set."
    type StrPairSet = set[StrPair]
    "Mutable set of (str, str) tuples."
    type IntPairSet = set[StrIntPair]
    "Mutable set of (str, int) tuples."
    type TomlData = dict[str, InfraValue]
    "Unwrapped TOML table data — nested dicts of primitives from tomlkit unwrap()."

    type InfraMapping = Mapping[str, InfraValue]
    "Read-only string-keyed infra value mapping."
    type MutableInfraMapping = MutableMapping[str, InfraValue]
    "Mutable string-keyed infra value mapping."
    type InfraSequence = Sequence[InfraValue]
    "Read-only infra value sequence."
    type MutableInfraSequence = MutableSequence[InfraValue]
    "Mutable infra value sequence."
