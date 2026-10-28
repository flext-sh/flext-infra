# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra.gates package.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from flext_infra.gates.bandit import FlextInfraBanditGate
    from flext_infra.gates.base_gate import FlextInfraGate
    from flext_infra.gates.codemod import FlextInfraCodemodGate
    from flext_infra.gates.conflict_markers import FlextInfraConflictMarkersGate
    from flext_infra.gates.deps import FlextInfraDepsGate
    from flext_infra.gates.direnv import FlextInfraDirenvGate
    from flext_infra.gates.duplication import FlextInfraDuplicationGate
    from flext_infra.gates.duplication_evidence import FlextInfraDuplicationEvidence
    from flext_infra.gates.duplication_report import FlextInfraDuplicationReportMixin
    from flext_infra.gates.enforcement_catalog import FlextInfraEnforcementCatalogGate
    from flext_infra.gates.fresh_import import FlextInfraFreshImportGate
    from flext_infra.gates.index_declarations import FlextInfraIndexDeclarationsGate
    from flext_infra.gates.layout import FlextInfraLayoutGate
    from flext_infra.gates.lint_freeze import FlextInfraLintConfigFreezeGate
    from flext_infra.gates.loc_cap import FlextInfraLocCapGate
    from flext_infra.gates.markdown import FlextInfraMarkdownGate
    from flext_infra.gates.markdown_code import FlextInfraMarkdownCodeGate
    from flext_infra.gates.markdown_code_sources import FlextInfraMarkdownCodeSources
    from flext_infra.gates.markdown_format import FlextInfraMarkdownFormatGate
    from flext_infra.gates.markdown_support import FlextInfraMarkdownGateBase
    from flext_infra.gates.mypy import FlextInfraMypyGate
    from flext_infra.gates.project_module import FlextInfraProjectModuleGate
    from flext_infra.gates.pyrefly import FlextInfraPyreflyGate
    from flext_infra.gates.pyright import FlextInfraPyrightGate
    from flext_infra.gates.readonly_namespace import FlextInfraReadonlyNamespace
    from flext_infra.gates.ruff_format import FlextInfraRuffFormatGate
    from flext_infra.gates.ruff_lint import FlextInfraRuffLintGate
    from flext_infra.gates.runtime_integrity import FlextInfraRuntimeIntegrityGate
    from flext_infra.gates.scanner_gate import FlextInfraScannerGateMixin
    from flext_infra.gates.smells import FlextInfraSmellsGate


__all__: tuple[str, ...] = (
    "FlextInfraBanditGate",
    "FlextInfraCodemodGate",
    "FlextInfraConflictMarkersGate",
    "FlextInfraDepsGate",
    "FlextInfraDirenvGate",
    "FlextInfraDuplicationEvidence",
    "FlextInfraDuplicationGate",
    "FlextInfraDuplicationReportMixin",
    "FlextInfraEnforcementCatalogGate",
    "FlextInfraFreshImportGate",
    "FlextInfraGate",
    "FlextInfraIndexDeclarationsGate",
    "FlextInfraLayoutGate",
    "FlextInfraLintConfigFreezeGate",
    "FlextInfraLocCapGate",
    "FlextInfraMarkdownCodeGate",
    "FlextInfraMarkdownCodeSources",
    "FlextInfraMarkdownFormatGate",
    "FlextInfraMarkdownGate",
    "FlextInfraMarkdownGateBase",
    "FlextInfraMypyGate",
    "FlextInfraProjectModuleGate",
    "FlextInfraPyreflyGate",
    "FlextInfraPyrightGate",
    "FlextInfraReadonlyNamespace",
    "FlextInfraRuffFormatGate",
    "FlextInfraRuffLintGate",
    "FlextInfraRuntimeIntegrityGate",
    "FlextInfraScannerGateMixin",
    "FlextInfraSmellsGate",
)

install_lazy_exports(
    __name__,
    globals(),
    MappingProxyType({
        "FlextInfraBanditGate": ".bandit",
        "FlextInfraCodemodGate": ".codemod",
        "FlextInfraConflictMarkersGate": ".conflict_markers",
        "FlextInfraDepsGate": ".deps",
        "FlextInfraDirenvGate": ".direnv",
        "FlextInfraDuplicationEvidence": ".duplication_evidence",
        "FlextInfraDuplicationGate": ".duplication",
        "FlextInfraDuplicationReportMixin": ".duplication_report",
        "FlextInfraEnforcementCatalogGate": ".enforcement_catalog",
        "FlextInfraFreshImportGate": ".fresh_import",
        "FlextInfraGate": ".base_gate",
        "FlextInfraIndexDeclarationsGate": ".index_declarations",
        "FlextInfraLayoutGate": ".layout",
        "FlextInfraLintConfigFreezeGate": ".lint_freeze",
        "FlextInfraLocCapGate": ".loc_cap",
        "FlextInfraMarkdownCodeGate": ".markdown_code",
        "FlextInfraMarkdownCodeSources": ".markdown_code_sources",
        "FlextInfraMarkdownFormatGate": ".markdown_format",
        "FlextInfraMarkdownGate": ".markdown",
        "FlextInfraMarkdownGateBase": ".markdown_support",
        "FlextInfraMypyGate": ".mypy",
        "FlextInfraProjectModuleGate": ".project_module",
        "FlextInfraPyreflyGate": ".pyrefly",
        "FlextInfraPyrightGate": ".pyright",
        "FlextInfraReadonlyNamespace": ".readonly_namespace",
        "FlextInfraRuffFormatGate": ".ruff_format",
        "FlextInfraRuffLintGate": ".ruff_lint",
        "FlextInfraRuntimeIntegrityGate": ".runtime_integrity",
        "FlextInfraScannerGateMixin": ".scanner_gate",
        "FlextInfraSmellsGate": ".smells",
    }),
    public_exports=__all__,
)
