# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra.gates package.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from flext_infra.gates.bandit import FlextInfraGatesBandit
    from flext_infra.gates.base_gate import FlextInfraGates
    from flext_infra.gates.codemod import FlextInfraGatesCodemod
    from flext_infra.gates.conflict_markers import FlextInfraGatesConflictMarkers
    from flext_infra.gates.deps import FlextInfraGatesDeps
    from flext_infra.gates.direnv import FlextInfraGatesDirenv
    from flext_infra.gates.duplication import FlextInfraGatesDuplication
    from flext_infra.gates.duplication_evidence import FlextInfraDuplicationEvidence
    from flext_infra.gates.duplication_report import FlextInfraDuplicationReport
    from flext_infra.gates.enforcement_catalog import FlextInfraGatesEnforcementCatalog
    from flext_infra.gates.fresh_import import FlextInfraGatesFreshImport
    from flext_infra.gates.index_declarations import FlextInfraGatesIndexDeclarations
    from flext_infra.gates.layout import FlextInfraGatesLayout
    from flext_infra.gates.loc_cap import FlextInfraGatesLocCap
    from flext_infra.gates.markdown import FlextInfraGatesMarkdown
    from flext_infra.gates.markdown_code import FlextInfraGatesMarkdownCode
    from flext_infra.gates.markdown_code_sources import FlextInfraMarkdownCodeSources
    from flext_infra.gates.markdown_format import FlextInfraGatesMarkdownFormat
    from flext_infra.gates.markdown_list_indent import FlextInfraMarkdownListIndent
    from flext_infra.gates.markdown_support import FlextInfraMarkdownGateBase
    from flext_infra.gates.mypy import FlextInfraGatesMypy
    from flext_infra.gates.project_module import FlextInfraGatesProjectModule
    from flext_infra.gates.pyrefly import FlextInfraGatesPyrefly
    from flext_infra.gates.pyright import FlextInfraGatesPyright
    from flext_infra.gates.ruff_base import FlextInfraGatesRuffGate
    from flext_infra.gates.ruff_format import FlextInfraGatesRuffFormat
    from flext_infra.gates.ruff_lint import FlextInfraGatesRuffLint
    from flext_infra.gates.runtime_integrity import FlextInfraGatesRuntimeIntegrity
    from flext_infra.gates.scanner_gate import FlextInfraGatesScanner
    from flext_infra.gates.smells import FlextInfraGatesSmells


__all__: tuple[str, ...] = (
    "FlextInfraDuplicationEvidence",
    "FlextInfraDuplicationReport",
    "FlextInfraGates",
    "FlextInfraGatesBandit",
    "FlextInfraGatesCodemod",
    "FlextInfraGatesConflictMarkers",
    "FlextInfraGatesDeps",
    "FlextInfraGatesDirenv",
    "FlextInfraGatesDuplication",
    "FlextInfraGatesEnforcementCatalog",
    "FlextInfraGatesFreshImport",
    "FlextInfraGatesIndexDeclarations",
    "FlextInfraGatesLayout",
    "FlextInfraGatesLocCap",
    "FlextInfraGatesMarkdown",
    "FlextInfraGatesMarkdownCode",
    "FlextInfraGatesMarkdownFormat",
    "FlextInfraGatesMypy",
    "FlextInfraGatesProjectModule",
    "FlextInfraGatesPyrefly",
    "FlextInfraGatesPyright",
    "FlextInfraGatesRuffFormat",
    "FlextInfraGatesRuffGate",
    "FlextInfraGatesRuffLint",
    "FlextInfraGatesRuntimeIntegrity",
    "FlextInfraGatesScanner",
    "FlextInfraGatesSmells",
    "FlextInfraMarkdownCodeSources",
    "FlextInfraMarkdownGateBase",
    "FlextInfraMarkdownListIndent",
)

install_lazy_exports(
    __name__,
    globals(),
    {
        "FlextInfraDuplicationEvidence": ".duplication_evidence",
        "FlextInfraDuplicationReport": ".duplication_report",
        "FlextInfraGates": ".base_gate",
        "FlextInfraGatesBandit": ".bandit",
        "FlextInfraGatesCodemod": ".codemod",
        "FlextInfraGatesConflictMarkers": ".conflict_markers",
        "FlextInfraGatesDeps": ".deps",
        "FlextInfraGatesDirenv": ".direnv",
        "FlextInfraGatesDuplication": ".duplication",
        "FlextInfraGatesEnforcementCatalog": ".enforcement_catalog",
        "FlextInfraGatesFreshImport": ".fresh_import",
        "FlextInfraGatesIndexDeclarations": ".index_declarations",
        "FlextInfraGatesLayout": ".layout",
        "FlextInfraGatesLocCap": ".loc_cap",
        "FlextInfraGatesMarkdown": ".markdown",
        "FlextInfraGatesMarkdownCode": ".markdown_code",
        "FlextInfraGatesMarkdownFormat": ".markdown_format",
        "FlextInfraGatesMypy": ".mypy",
        "FlextInfraGatesProjectModule": ".project_module",
        "FlextInfraGatesPyrefly": ".pyrefly",
        "FlextInfraGatesPyright": ".pyright",
        "FlextInfraGatesRuffFormat": ".ruff_format",
        "FlextInfraGatesRuffGate": ".ruff_base",
        "FlextInfraGatesRuffLint": ".ruff_lint",
        "FlextInfraGatesRuntimeIntegrity": ".runtime_integrity",
        "FlextInfraGatesScanner": ".scanner_gate",
        "FlextInfraGatesSmells": ".smells",
        "FlextInfraMarkdownCodeSources": ".markdown_code_sources",
        "FlextInfraMarkdownGateBase": ".markdown_support",
        "FlextInfraMarkdownListIndent": ".markdown_list_indent",
    },
    public_exports=__all__,
)
