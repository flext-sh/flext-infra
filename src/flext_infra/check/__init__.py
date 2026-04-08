# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Check package."""

from __future__ import annotations

from flext_core.lazy import install_lazy_exports

_LAZY_IMPORTS = {
    "FlextInfraCheckServices": ".services",
    "FlextInfraCliCheck": ".cli",
    "FlextInfraGateRegistry": "._workspace_check_gates",
    "FlextInfraWorkspaceCheckGatesMixin": "._workspace_check_gates",
    "FlextInfraWorkspaceChecker": ".workspace_check",
    "FlextInfraWorkspaceCheckerCli": ".workspace_check_cli",
    "build_parser": ".workspace_check",
    "run_cli": ".workspace_check",
}


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, publish_all=False)
