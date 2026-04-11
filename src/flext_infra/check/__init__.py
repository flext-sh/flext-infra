# AUTO-GENERATED FILE — Regenerate with: make gen
"""Check package."""

from __future__ import annotations

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

_LAZY_IMPORTS = build_lazy_import_map(
    {
        ".workspace_check": (
            "FlextInfraWorkspaceChecker",
            "run_cli",
        ),
        ".workspace_check_cli": (
            "FlextInfraCliCheck",
            "FlextInfraWorkspaceCheckerCli",
        ),
        ".workspace_check_gates": (
            "FlextInfraGateRegistry",
            "FlextInfraWorkspaceCheckGatesMixin",
        ),
    },
)


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, publish_all=False)
