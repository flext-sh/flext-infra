# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Check package."""

from __future__ import annotations

import typing as _t

from flext_core.lazy import install_lazy_exports

if _t.TYPE_CHECKING:
    import flext_infra.check._workspace_check_gates as _flext_infra_check__workspace_check_gates

    _workspace_check_gates = _flext_infra_check__workspace_check_gates
    import flext_infra.check.cli as _flext_infra_check_cli
    from flext_infra.check._workspace_check_gates import (
        FlextInfraGateRegistry,
        FlextInfraWorkspaceCheckGatesMixin,
    )

    cli = _flext_infra_check_cli
    import flext_infra.check.services as _flext_infra_check_services
    from flext_infra.check.cli import FlextInfraCliCheck

    services = _flext_infra_check_services
    import flext_infra.check.workspace_check as _flext_infra_check_workspace_check

    workspace_check = _flext_infra_check_workspace_check
    import flext_infra.check.workspace_check_cli as _flext_infra_check_workspace_check_cli
    from flext_infra.check.workspace_check import (
        FlextInfraWorkspaceChecker,
        build_parser,
        run_cli,
    )

    workspace_check_cli = _flext_infra_check_workspace_check_cli
    from flext_core.decorators import FlextDecorators as d
    from flext_core.exceptions import FlextExceptions as e
    from flext_core.handlers import FlextHandlers as h
    from flext_core.mixins import FlextMixins as x
    from flext_core.result import FlextResult as r
    from flext_core.service import FlextService as s
    from flext_infra.check.workspace_check_cli import FlextInfraWorkspaceCheckerCli
_LAZY_IMPORTS = {
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
    "_workspace_check_gates": "flext_infra.check._workspace_check_gates",
    "build_parser": ("flext_infra.check.workspace_check", "build_parser"),
    "cli": "flext_infra.check.cli",
    "d": ("flext_core.decorators", "FlextDecorators"),
    "e": ("flext_core.exceptions", "FlextExceptions"),
    "h": ("flext_core.handlers", "FlextHandlers"),
    "r": ("flext_core.result", "FlextResult"),
    "run_cli": ("flext_infra.check.workspace_check", "run_cli"),
    "s": ("flext_core.service", "FlextService"),
    "services": "flext_infra.check.services",
    "workspace_check": "flext_infra.check.workspace_check",
    "workspace_check_cli": "flext_infra.check.workspace_check_cli",
    "x": ("flext_core.mixins", "FlextMixins"),
}

__all__ = [
    "FlextInfraCliCheck",
    "FlextInfraGateRegistry",
    "FlextInfraWorkspaceCheckGatesMixin",
    "FlextInfraWorkspaceChecker",
    "FlextInfraWorkspaceCheckerCli",
    "_workspace_check_gates",
    "build_parser",
    "cli",
    "d",
    "e",
    "h",
    "r",
    "run_cli",
    "s",
    "services",
    "workspace_check",
    "workspace_check_cli",
    "x",
]


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)
