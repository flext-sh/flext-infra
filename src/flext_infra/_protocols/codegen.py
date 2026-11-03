# AUTO-GENERATED FILE - Source bootstrap protocol domain owner.
"""Canonical owner for partitioned protocol contracts."""

from __future__ import annotations

from flext_infra._protocols._codegen import (
    FlextInfraProtocolsCodegenFix,
    FlextInfraProtocolsCodegenPipeline,
    FlextInfraProtocolsCodegenScaffold,
    FlextInfraProtocolsCodegenTransaction,
)
from flext_infra._protocols._codegen.lazy_init import FlextInfraProtocolsCodegenLazyInit
from flext_infra._protocols.codegen_render import FlextInfraProtocolsCodegenRender
from flext_infra._protocols.codegen_toolchain import FlextInfraProtocolsCodegenToolchain


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
