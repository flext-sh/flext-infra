"""Centralized TypeAdapter instances for flext-infra.

Provides SSOT TypeAdapter singletons for common validation patterns.
All modules should import these via ``t.Infra.<ADAPTER_NAME>`` instead
of creating local TypeAdapter instances.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    MutableMapping,
    Sequence,
)
from typing import ClassVar

from flext_cli import t
from flext_core import m

from flext_infra import FlextInfraTypesBase


class FlextInfraTypesAdapters:
    """Centralized TypeAdapter instances for infrastructure validation.

    Usage::

        from flext_infra import t

        validated = t.Infra.INFRA_MAPPING_ADAPTER.validate_python(raw)
    """

    # ── Mapping adapters ─────────────────────────────────────────────
    INFRA_MAPPING_ADAPTER: ClassVar[
        m.TypeAdapter[FlextInfraTypesBase.ContainerDict]
    ] = t.Cli.JSON_MAPPING_ADAPTER
    "Validates Mapping[str, InfraValue] — the most common infra adapter."

    MUTABLE_INFRA_MAPPING_ADAPTER: ClassVar[
        m.TypeAdapter[MutableMapping[str, FlextInfraTypesBase.InfraValue]]
    ] = m.TypeAdapter(MutableMapping[str, FlextInfraTypesBase.InfraValue])
    "Validates MutableMapping[str, InfraValue] for in-place mutation."

    STR_MAPPING_ADAPTER: ClassVar[m.TypeAdapter[t.StrMapping]] = m.TypeAdapter(
        t.StrMapping,
    )
    "Validates t.StrMapping."

    CONTAINER_MAPPING_ADAPTER: ClassVar[m.TypeAdapter[t.FlatContainerMapping]] = (
        t.flat_container_mapping_adapter()
    )
    "Validates flat container mappings through the shared flext-core adapter."

    # ── Sequence adapters ────────────────────────────────────────────
    INFRA_SEQ_ADAPTER: ClassVar[m.TypeAdapter[FlextInfraTypesBase.InfraSequence]] = (
        t.Cli.JSON_LIST_ADAPTER
    )
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
