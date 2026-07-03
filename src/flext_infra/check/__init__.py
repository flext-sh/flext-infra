# AUTO-GENERATED FILE — Regenerate with: make gen
"""Check package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from flext_infra.check.workspace_check import (
        FlextInfraWorkspaceChecker as FlextInfraWorkspaceChecker,
    )
    from flext_infra.check.workspace_check_gates import (
        FlextInfraGateRegistry as FlextInfraGateRegistry,
        FlextInfraWorkspaceCheckGatesMixin as FlextInfraWorkspaceCheckGatesMixin,
    )
_LAZY_IMPORTS = build_lazy_import_map(
    {
        ".workspace_check": ("FlextInfraWorkspaceChecker",),
        ".workspace_check_gates": (
            "FlextInfraGateRegistry",
            "FlextInfraWorkspaceCheckGatesMixin",
        ),
    },
)
    from flext_core.typings import FlextTypes
    from flext_infra.check.services import (
        CheckIssue,
        FlextInfraConfigFixer,
        FlextInfraWorkspaceChecker,
        GateExecution,
        ProjectResult,
    )
    from flext_infra.check.workspace_check import build_parser, main, run_cli

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    "CheckIssue": ("flext_infra.check.services", "CheckIssue"),
    "FlextInfraConfigFixer": ("flext_infra.check.services", "FlextInfraConfigFixer"),
    "FlextInfraWorkspaceChecker": (
        "flext_infra.check.services",
        "FlextInfraWorkspaceChecker",
    ),
    "GateExecution": ("flext_infra.check.services", "GateExecution"),
    "ProjectResult": ("flext_infra.check.services", "ProjectResult"),
    "build_parser": ("flext_infra.check.workspace_check", "build_parser"),
    "main": ("flext_infra.check.workspace_check", "main"),
    "run_cli": ("flext_infra.check.workspace_check", "run_cli"),
}

__all__ = [
    "CheckIssue",
    "FlextInfraConfigFixer",
    "FlextInfraWorkspaceChecker",
    "GateExecution",
    "ProjectResult",
    "build_parser",
    "main",
    "run_cli",
]


install_lazy_exports(
    __name__,
    globals(),
    _LAZY_IMPORTS,
    publish_all=False,
)
