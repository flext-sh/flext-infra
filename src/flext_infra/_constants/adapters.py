"""Centralized TypeAdapter constants for flext-infra.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import MutableMapping
from pathlib import Path
from typing import Final

from flext_cli import t
from flext_core import m


class FlextInfraConstantsAdapters:
    """SSOT TypeAdapter singletons for infrastructure validation."""

    # NOTE (multi-agent): mro-i6nq.10 removes the constants-to-typings cycle.
    INFRA_MAPPING_ADAPTER: Final[m.TypeAdapter[t.JsonMapping]] = (
        t.Cli.JSON_MAPPING_ADAPTER
    )
    "Validates t.MappingKV[str, InfraValue] - the most common infra adapter."

    MUTABLE_INFRA_MAPPING_ADAPTER: Final[
        m.TypeAdapter[MutableMapping[str, t.JsonValue]]
    ] = m.TypeAdapter(MutableMapping[str, t.JsonValue])
    "Validates MutableMapping[str, InfraValue] for in-place mutation."

    STR_MAPPING_ADAPTER: Final[m.TypeAdapter[t.StrMapping]] = m.TypeAdapter(
        t.StrMapping,
    )
    "Validates t.StrMapping."

    CONTAINER_MAPPING_ADAPTER: Final[
        m.TypeAdapter[t.MappingKV[str, t.Scalar | Path]]
    ] = m.TypeAdapter(t.MappingKV[str, t.Scalar | Path])
    "Validates flat scalar/path mappings (no nested containers)."

    INFRA_SEQ_ADAPTER: Final[m.TypeAdapter[t.JsonList]] = t.Cli.JSON_LIST_ADAPTER
    "Validates t.SequenceOf[InfraValue]."

    CONTAINER_DICT_SEQ_ADAPTER: Final[m.TypeAdapter[t.SequenceOf[t.JsonMapping]]] = (
        m.TypeAdapter(t.SequenceOf[t.JsonMapping])
    )
    "Validates t.SequenceOf[ContainerDict]."

    STR_SEQ_ADAPTER: Final[m.TypeAdapter[t.StrSequence]] = m.TypeAdapter(
        t.StrSequence,
    )
    "Validates t.StrSequence."

    STR_MAPPING_SEQ_ADAPTER: Final[m.TypeAdapter[t.SequenceOf[t.StrMapping]]] = (
        m.TypeAdapter(t.SequenceOf[t.StrMapping])
    )
    "Validates t.SequenceOf[StrMapping]."


__all__: list[str] = ["FlextInfraConstantsAdapters"]
