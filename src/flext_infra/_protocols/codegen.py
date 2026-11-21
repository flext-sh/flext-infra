# AUTO-GENERATED FILE - Source bootstrap protocol domain owner.
"""Canonical owner for partitioned protocol contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
src/flext_infra/_protocols/codegen
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_infra._protocols import (
    FlextInfraProtocolsCodegenRender,
    FlextInfraProtocolsCodegenToolchain,
)
from flext_infra._protocols._codegen import (
    FlextInfraProtocolsCodegenFix,
    FlextInfraProtocolsCodegenLazyInit,
    FlextInfraProtocolsCodegenPipeline,
    FlextInfraProtocolsCodegenScaffold,
    FlextInfraProtocolsCodegenTransaction,
)


class FlextInfraProtocolsCodegen(
    FlextInfraProtocolsCodegenToolchain,
    FlextInfraProtocolsCodegenRender,
    FlextInfraProtocolsCodegenLazyInit,
    FlextInfraProtocolsCodegenTransaction,
    FlextInfraProtocolsCodegenScaffold,
    FlextInfraProtocolsCodegenFix,
    FlextInfraProtocolsCodegenPipeline,
):
    """Canonical structural contracts for the codegen domain."""


__all__: tuple[str, ...] = ("FlextInfraProtocolsCodegen",)
