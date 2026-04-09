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

from pydantic import TypeAdapter

from flext_core import t
from flext_infra import FlextInfraTypesBase


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

    STR_MAPPING_ADAPTER: ClassVar[TypeAdapter[t.StrMapping]] = TypeAdapter(
        t.StrMapping,
    )
    "Validates t.StrMapping."

    CONTAINER_MAPPING_ADAPTER: ClassVar[TypeAdapter[t.ContainerMapping]] = TypeAdapter(
        t.ContainerMapping
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

    STR_SEQ_ADAPTER: ClassVar[TypeAdapter[t.StrSequence]] = TypeAdapter(
        t.StrSequence,
    )
    "Validates t.StrSequence."

    STR_MAPPING_SEQ_ADAPTER: ClassVar[TypeAdapter[Sequence[t.StrMapping]]] = (
        TypeAdapter(Sequence[t.StrMapping])
    )
    "Validates Sequence[StrMapping]."

    # ── Composite adapters ────────────────────────────────────────────
    INFRA_SEQ_MAPPING_ADAPTER: ClassVar[
        TypeAdapter[Sequence[Mapping[str, FlextInfraTypesBase.InfraValue]]]
    ] = TypeAdapter(Sequence[Mapping[str, FlextInfraTypesBase.InfraValue]])
    "Validates Sequence[Mapping[str, InfraValue]]."
