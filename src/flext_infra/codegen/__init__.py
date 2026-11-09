# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra.codegen package.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from flext_infra.codegen.census import FlextInfraCodegenCensus
    from flext_infra.codegen.conform import FlextInfraCodegenConform
    from flext_infra.codegen.consolidator import FlextInfraCodegenConsolidator
    from flext_infra.codegen.constants_quality_gate import FlextInfraGatesCodegenQuality
    from flext_infra.codegen.execution import FlextInfraCodegenExecution
    from flext_infra.codegen.fixer import FlextInfraCodegenFixer
    from flext_infra.codegen.layout import FlextInfraCodegenLayout
    from flext_infra.codegen.lazy_init import FlextInfraCodegenLazyInit
    from flext_infra.codegen.make_bootstrap import FlextInfraCodegenMakeBootstrap
    from flext_infra.codegen.mise_toolchain_proof import (
        FlextInfraCodegenMiseToolchainProof,
    )
    from flext_infra.codegen.mise_toolchain_repair import (
        FlextInfraCodegenMiseToolchainRepair,
    )
    from flext_infra.codegen.py_typed import FlextInfraCodegenPyTyped
    from flext_infra.codegen.scaffolder import FlextInfraCodegenScaffolder
    from flext_infra.codegen.staged_package import FlextInfraStagedPackage
    from flext_infra.codegen.version_file import FlextInfraCodegenVersionFile


__all__: tuple[str, ...] = (
    "FlextInfraCodegenCensus",
    "FlextInfraCodegenConform",
    "FlextInfraCodegenConsolidator",
    "FlextInfraCodegenExecution",
    "FlextInfraCodegenFixer",
    "FlextInfraCodegenLayout",
    "FlextInfraCodegenLazyInit",
    "FlextInfraCodegenMakeBootstrap",
    "FlextInfraCodegenMiseToolchainProof",
    "FlextInfraCodegenMiseToolchainRepair",
    "FlextInfraCodegenPyTyped",
    "FlextInfraCodegenScaffolder",
    "FlextInfraCodegenVersionFile",
    "FlextInfraGatesCodegenQuality",
    "FlextInfraStagedPackage",
)

install_lazy_exports(
    __name__,
    globals(),
    {
        "FlextInfraCodegenCensus": ".census",
        "FlextInfraCodegenConform": ".conform",
        "FlextInfraCodegenConsolidator": ".consolidator",
        "FlextInfraCodegenExecution": ".execution",
        "FlextInfraCodegenFixer": ".fixer",
        "FlextInfraCodegenLayout": ".layout",
        "FlextInfraCodegenLazyInit": ".lazy_init",
        "FlextInfraCodegenMakeBootstrap": ".make_bootstrap",
        "FlextInfraCodegenMiseToolchainProof": ".mise_toolchain_proof",
        "FlextInfraCodegenMiseToolchainRepair": ".mise_toolchain_repair",
        "FlextInfraCodegenPyTyped": ".py_typed",
        "FlextInfraCodegenScaffolder": ".scaffolder",
        "FlextInfraCodegenVersionFile": ".version_file",
        "FlextInfraGatesCodegenQuality": ".constants_quality_gate",
        "FlextInfraStagedPackage": ".staged_package",
    },
    public_exports=__all__,
)
