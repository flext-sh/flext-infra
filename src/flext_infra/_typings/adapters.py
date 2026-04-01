"""Centralized TypeAdapter instances for flext-infra.

Provides SSOT TypeAdapter singletons for common validation patterns.
All modules should import these via ``t.Infra.<ADAPTER_NAME>`` instead
of creating local TypeAdapter instances.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping, Sequence
from typing import ClassVar

from flext_core import FlextTypes
from pydantic import JsonValue, TypeAdapter

from flext_infra._typings.base import FlextInfraTypesBase


class FlextInfraTypesAdapters:
    """Centralized TypeAdapter instances for infrastructure validation.

    Usage::

        from flext_infra import t

        validated = t.Infra.INFRA_MAPPING_ADAPTER.validate_python(raw)
    """

    # ── Mapping adapters ─────────────────────────────────────────────
    INFRA_MAPPING_ADAPTER: ClassVar[
        TypeAdapter[Mapping[str, FlextInfraTypesBase.InfraValue]]
    ] = TypeAdapter(Mapping[str, FlextInfraTypesBase.InfraValue])
    "Validates Mapping[str, InfraValue] — the most common infra adapter."

    MUTABLE_INFRA_MAPPING_ADAPTER: ClassVar[
        TypeAdapter[MutableMapping[str, FlextInfraTypesBase.InfraValue]]
    ] = TypeAdapter(MutableMapping[str, FlextInfraTypesBase.InfraValue])
    "Validates MutableMapping[str, InfraValue] for in-place mutation."

    STR_MAPPING_ADAPTER: ClassVar[TypeAdapter[Mapping[str, str]]] = TypeAdapter(
        Mapping[str, str],
    )
    "Validates Mapping[str, str]."

    JSON_DICT_ADAPTER: ClassVar[TypeAdapter[Mapping[str, JsonValue]]] = TypeAdapter(
        Mapping[str, JsonValue],
    )
    "Validates Mapping[str, JsonValue]."

    CONTAINER_MAPPING_ADAPTER: ClassVar[TypeAdapter[FlextTypes.ContainerMapping]] = (
        TypeAdapter(FlextTypes.ContainerMapping)
    )
    "Validates ContainerMapping (t.ContainerMapping)."

    # ── Sequence adapters ────────────────────────────────────────────
    INFRA_SEQ_ADAPTER: ClassVar[
        TypeAdapter[Sequence[FlextInfraTypesBase.InfraValue]]
    ] = TypeAdapter(Sequence[FlextInfraTypesBase.InfraValue])
    "Validates Sequence[InfraValue]."

    CONTAINER_DICT_SEQ_ADAPTER: ClassVar[
        TypeAdapter[Sequence[FlextInfraTypesBase.ContainerDict]]
    ] = TypeAdapter(Sequence[FlextInfraTypesBase.ContainerDict])
    "Validates Sequence[ContainerDict]."

    JSON_SEQ_ADAPTER: ClassVar[TypeAdapter[Sequence[JsonValue]]] = TypeAdapter(
        Sequence[JsonValue],
    )
    "Validates Sequence[JsonValue]."

    STR_SEQ_ADAPTER: ClassVar[TypeAdapter[Sequence[str]]] = TypeAdapter(
        Sequence[str],
    )
    "Validates Sequence[str]."

    STR_MAPPING_SEQ_ADAPTER: ClassVar[TypeAdapter[Sequence[FlextTypes.StrMapping]]] = (
        TypeAdapter(Sequence[FlextTypes.StrMapping])
    )
    "Validates Sequence[StrMapping]."

    STR_SEQ_SIMPLE_ADAPTER: ClassVar[TypeAdapter[FlextTypes.StrSequence]] = TypeAdapter(
        FlextTypes.StrSequence
    )
    "Validates StrSequence (t.StrSequence)."

    # ── Scalar adapters ──────────────────────────────────────────────
    JSON_VALUE_ADAPTER: ClassVar[TypeAdapter[JsonValue]] = TypeAdapter(JsonValue)
    "Validates a single JsonValue."

    INFRA_SEQ_MAPPING_ADAPTER: ClassVar[
        TypeAdapter[Sequence[Mapping[str, FlextInfraTypesBase.InfraValue]]]
    ] = TypeAdapter(Sequence[Mapping[str, FlextInfraTypesBase.InfraValue]])
    "Validates Sequence[Mapping[str, InfraValue]]."
