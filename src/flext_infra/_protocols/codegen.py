# AUTO-GENERATED FILE - Source bootstrap protocol domain owner.
"""Canonical owner for partitioned protocol contracts."""

from __future__ import annotations

from flext_infra._protocols._codegen.fix import FlextInfraProtocolsCodegenFix
from flext_infra._protocols._codegen.lazy_init import FlextInfraProtocolsCodegenLazyInit
from flext_infra._protocols._codegen.pipeline import FlextInfraProtocolsCodegenPipeline
from flext_infra._protocols._codegen.scaffold import FlextInfraProtocolsCodegenScaffold
from flext_infra._protocols._codegen.transaction import (
    FlextInfraProtocolsCodegenTransaction,
)
from flext_infra._protocols.codegen_render import FlextInfraProtocolsCodegenRender
from flext_infra._protocols.codegen_toolchain import FlextInfraProtocolsCodegenToolchain


class FlextInfraProtocolsCodegen(
    FlextInfraProtocolsCodegenToolchain,
    FlextInfraProtocolsCodegenRender,
    FlextInfraProtocolsCodegenTransaction,
    FlextInfraProtocolsCodegenScaffold,
    FlextInfraProtocolsCodegenFix,
    FlextInfraProtocolsCodegenLazyInit,
    FlextInfraProtocolsCodegenPipeline,
):
    """Canonical structural contracts for the codegen domain."""


__all__: tuple[str, ...] = ("FlextInfraProtocolsCodegen",)
