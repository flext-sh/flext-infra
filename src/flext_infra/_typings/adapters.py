"""Centralized TypeAdapter instances for flext-infra.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

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
    INFRA_MAPPING_ADAPTER: ClassVar[m.TypeAdapter[t.JsonMapping]] = (
        u.json_mapping_adapter()
    )
    "Validates t.MappingKV[str, InfraValue] - the most common infra adapter."

    MUTABLE_INFRA_MAPPING_ADAPTER: ClassVar[
        m.TypeAdapter[MutableMapping[str, t.JsonValue]]
    ] = u.type_adapter(MutableMapping[str, t.JsonValue])
    "Validates MutableMapping[str, InfraValue] for in-place mutation."

    STR_MAPPING_ADAPTER: ClassVar[m.TypeAdapter[t.StrMapping]] = u.type_adapter(
        Mapping[str, str],
    )
    "Validates t.StrMapping."

    CONTAINER_MAPPING_ADAPTER: ClassVar[
        m.TypeAdapter[t.MappingKV[str, t.Scalar | Path]]
    ] = u.type_adapter(Mapping[str, t.Scalar | Path])
    "Validates flat scalar/path mappings (no nested containers)."

    INFRA_SEQ_ADAPTER: ClassVar[m.TypeAdapter[t.JsonList]] = u.json_list_adapter()
    "Validates t.SequenceOf[InfraValue]."

    STR_SEQ_ADAPTER: ClassVar[m.TypeAdapter[t.StrSequence]] = u.type_adapter(
        Sequence[str],
    )
    "Validates t.StrSequence."

    NON_EMPTY_STR_SEQ_ADAPTER: ClassVar[
        m.TypeAdapter[t.VariadicTuple[t.NonEmptyStr]]
    ] = u.type_adapter(tuple[t.NonEmptyStr, ...])
    "Validates t.VariadicTuple[t.NonEmptyStr] at typed render boundaries."

    STR_ADAPTER: ClassVar[m.TypeAdapter[str]] = u.type_adapter(str)
    "Validates one string at boundaries whose upstream stubs expose Any."

    BOOL_ADAPTER: ClassVar[m.TypeAdapter[bool]] = u.type_adapter(bool)
    "Validates one boolean at boundaries whose upstream stubs expose Any."

    DISTRIBUTION_NAME_ADAPTER: ClassVar[m.TypeAdapter[str]] = u.type_adapter(
        Annotated[str, m.AfterValidator(partial(canonicalize_name, validate=True))],
    )
    "Validates one PEP 503 distribution name into its canonical identity."

    REQUIREMENT_NAME_ADAPTER: ClassVar[m.TypeAdapter[str]] = u.type_adapter(
        Annotated[
            str,
            m.AfterValidator(Requirement),
            m.AfterValidator(attrgetter("name")),
            m.AfterValidator(canonicalize_name),
        ],
    )
    "Validates one PEP 508 requirement into its canonical distribution identity."


__all__: list[str] = ["FlextInfraTypesAdapters"]
