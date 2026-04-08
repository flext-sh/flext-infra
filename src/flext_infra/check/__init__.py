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
    "c": ("flext_core.constants", "FlextConstants"),
    "cli": "flext_infra.check.cli",
    "d": ("flext_core.decorators", "FlextDecorators"),
    "e": ("flext_core.exceptions", "FlextExceptions"),
    "h": ("flext_core.handlers", "FlextHandlers"),
    "m": ("flext_core.models", "FlextModels"),
    "p": ("flext_core.protocols", "FlextProtocols"),
    "r": ("flext_core.result", "FlextResult"),
    "run_cli": ("flext_infra.check.workspace_check", "run_cli"),
    "s": ("flext_core.service", "FlextService"),
    "services": "flext_infra.check.services",
    "t": ("flext_core.typings", "FlextTypes"),
    "u": ("flext_core.utilities", "FlextUtilities"),
    "workspace_check": "flext_infra.check.workspace_check",
    "workspace_check_cli": "flext_infra.check.workspace_check_cli",
    "x": ("flext_core.mixins", "FlextMixins"),
}


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, publish_all=False)
