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

from flext_core import m, t
from flext_infra import FlextInfraTypesBase


class FlextInfraTypesAdapters:
    """Centralized TypeAdapter instances for infrastructure validation.

    Usage::

        from flext_infra import t

        validated = t.Infra.INFRA_MAPPING_ADAPTER.validate_python(raw)
    """

    # ── Mapping adapters ─────────────────────────────────────────────
    INFRA_MAPPING_ADAPTER: ClassVar[
        m.TypeAdapter[Mapping[str, FlextInfraTypesBase.InfraValue]]
    ] = m.TypeAdapter(Mapping[str, FlextInfraTypesBase.InfraValue])
    "Validates Mapping[str, InfraValue] — the most common infra adapter."

    MUTABLE_INFRA_MAPPING_ADAPTER: ClassVar[
        m.TypeAdapter[MutableMapping[str, FlextInfraTypesBase.InfraValue]]
    ] = m.TypeAdapter(MutableMapping[str, FlextInfraTypesBase.InfraValue])
    "Validates MutableMapping[str, InfraValue] for in-place mutation."

    STR_MAPPING_ADAPTER: ClassVar[m.TypeAdapter[t.StrMapping]] = m.TypeAdapter(
        t.StrMapping,
    )
    "Validates t.StrMapping."

    CONTAINER_MAPPING_ADAPTER: ClassVar[m.TypeAdapter[t.RecursiveContainerMapping]] = (
        m.TypeAdapter(t.RecursiveContainerMapping)
    )
    "Validates ContainerMapping (t.RecursiveContainerMapping)."

    # ── Sequence adapters ────────────────────────────────────────────
    INFRA_SEQ_ADAPTER: ClassVar[
        m.TypeAdapter[Sequence[FlextInfraTypesBase.InfraValue]]
    ] = m.TypeAdapter(Sequence[FlextInfraTypesBase.InfraValue])
    "Validates Sequence[InfraValue]."

    CONTAINER_DICT_SEQ_ADAPTER: ClassVar[
        m.TypeAdapter[Sequence[FlextInfraTypesBase.ContainerDict]]
    ] = m.TypeAdapter(Sequence[FlextInfraTypesBase.ContainerDict])
    "Validates Sequence[ContainerDict]."

    STR_SEQ_ADAPTER: ClassVar[m.TypeAdapter[t.StrSequence]] = m.TypeAdapter(
        t.StrSequence,
    )
    "Validates t.StrSequence."

    STR_MAPPING_SEQ_ADAPTER: ClassVar[m.TypeAdapter[Sequence[t.StrMapping]]] = (
        m.TypeAdapter(Sequence[t.StrMapping])
    )
    "Validates Sequence[StrMapping]."

    # ── Composite adapters ────────────────────────────────────────────
    INFRA_SEQ_MAPPING_ADAPTER: ClassVar[
        m.TypeAdapter[Sequence[Mapping[str, FlextInfraTypesBase.InfraValue]]]
    ] = m.TypeAdapter(Sequence[Mapping[str, FlextInfraTypesBase.InfraValue]])
    "Validates Sequence[Mapping[str, InfraValue]]."
