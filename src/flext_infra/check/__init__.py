# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Check package."""

from __future__ import annotations

from flext_core.lazy import install_lazy_exports

_LAZY_IMPORTS = {
    "FlextInfraCheckServices": (
        "flext_infra.check.services",
        "FlextInfraCheckServices",
    ),
    "FlextInfraCliCheck": ("flext_infra.check.cli", "FlextInfraCliCheck"),
    "FlextInfraGateRegistry": (
        "flext_infra.check._workspace_check_gates",
        "FlextInfraGateRegistry",
    ),
    "FlextInfraWorkspaceCheckGatesMixin": (
        "flext_infra.check._workspace_check_gates",
        "FlextInfraWorkspaceCheckGatesMixin",
    ),
    "FlextInfraWorkspaceChecker": (
        "flext_infra.check.workspace_check",
        "FlextInfraWorkspaceChecker",
    ),
    "FlextInfraWorkspaceCheckerCli": (
        "flext_infra.check.workspace_check_cli",
        "FlextInfraWorkspaceCheckerCli",
    ),
    "build_parser": ("flext_infra.check.workspace_check", "build_parser"),
    "cli": "flext_infra.check.cli",
    "run_cli": ("flext_infra.check.workspace_check", "run_cli"),
    "services": "flext_infra.check.services",
    "workspace_check": "flext_infra.check.workspace_check",
    "workspace_check_cli": "flext_infra.check.workspace_check_cli",
}


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, publish_all=False)
