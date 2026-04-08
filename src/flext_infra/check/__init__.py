# AUTO-GENERATED FILE — Regenerate with: make gen
"""Check package."""

from __future__ import annotations

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

_LAZY_IMPORTS = build_lazy_import_map(
    {
        "._workspace_check_gates": (
            "FlextInfraGateRegistry",
            "FlextInfraWorkspaceCheckGatesMixin",
        ),
        ".cli": ("FlextInfraCliCheck",),
        ".services": ("FlextInfraCheckServices",),
        ".workspace_check": (
            "FlextInfraWorkspaceChecker",
            "build_parser",
            "run_cli",
        ),
        ".workspace_check_cli": ("FlextInfraWorkspaceCheckerCli",),
    },
)


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, publish_all=False)
