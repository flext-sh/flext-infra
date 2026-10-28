"""Centralized TypeAdapter instances for flext-infra.

Copyright (c) 2025 FLEXT Team. All rights reserved.
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

from collections.abc import Mapping, MutableMapping, Sequence
from functools import partial
from operator import attrgetter
from pathlib import Path
from typing import Annotated, ClassVar

from flext_cli import m, t, u
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name


class FlextInfraTypesAdapters:
    """SSOT TypeAdapter singletons for infrastructure validation."""

    # This alias removes the constants-to-typings cycle.
    INFRA_MAPPING_ADAPTER: ClassVar[u.type_adapter[t.JsonMapping]] = (
        u.json_mapping_adapter()
    )
    "Validates Mapping[str, InfraValue] - the most common infra adapter."

    MUTABLE_INFRA_MAPPING_ADAPTER: ClassVar[
        u.type_adapter[MutableMapping[str, t.JsonValue]]
    ] = u.type_adapter(MutableMapping[str, t.JsonValue])
    "Validates MutableMapping[str, InfraValue] for in-place mutation."

    STR_MAPPING_ADAPTER: ClassVar[u.type_adapter[Mapping[str, str]]] = u.type_adapter(
        Mapping[str, str],
    )
    "Validates Mapping[str, str]."

    CONTAINER_MAPPING_ADAPTER: ClassVar[
        u.type_adapter[Mapping[str, t.Scalar | Path]]
    ] = u.type_adapter(Mapping[str, t.Scalar | Path])
    "Validates flat scalar/path mappings (no nested containers)."

    INFRA_SEQ_ADAPTER: ClassVar[u.type_adapter[t.JsonList]] = u.json_list_adapter()
    "Validates Sequence[InfraValue]."

    STR_SEQ_ADAPTER: ClassVar[u.type_adapter[Sequence[str]]] = u.type_adapter(
        Sequence[str],
    )
    "Validates Sequence[str]."

    NON_EMPTY_STR_SEQ_ADAPTER: ClassVar[u.type_adapter[tuple[t.NonEmptyStr, ...]]] = (
        u.type_adapter(tuple[t.NonEmptyStr, ...])
    )
    "Validates tuple[t.NonEmptyStr, ...] at typed render boundaries."

    STR_ADAPTER: ClassVar[u.type_adapter[str]] = u.type_adapter(str)
    "Validates one string at boundaries whose upstream stubs expose Any."

    BOOL_ADAPTER: ClassVar[u.type_adapter[bool]] = u.type_adapter(bool)
    "Validates one boolean at boundaries whose upstream stubs expose Any."

    DISTRIBUTION_NAME_ADAPTER: ClassVar[u.type_adapter[str]] = u.type_adapter(
        Annotated[str, m.AfterValidator(partial(canonicalize_name, validate=True))],
    )
    "Validates one PEP 503 distribution name into its canonical identity."

    REQUIREMENT_NAME_ADAPTER: ClassVar[u.type_adapter[str]] = u.type_adapter(
        Annotated[
            str,
            m.AfterValidator(Requirement),
            m.AfterValidator(attrgetter("name")),
            m.AfterValidator(canonicalize_name),
        ],
    )
    "Validates one PEP 508 requirement into its canonical distribution identity."


__all__: list[str] = ["FlextInfraTypesAdapters"]
