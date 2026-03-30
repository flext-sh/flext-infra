# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Check services for quality gate execution."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from flext_infra.check import (
        cli as cli,
        services as services,
        workspace_check as workspace_check,
    )
    from flext_infra.check.cli import FlextInfraCliCheck as FlextInfraCliCheck
    from flext_infra.check.services import (
        FlextInfraConfigFixer as FlextInfraConfigFixer,
        FlextInfraWorkspaceChecker as FlextInfraWorkspaceChecker,
    )
    from flext_infra.check.workspace_check import (
        build_parser as build_parser,
        main as main,
        run_cli as run_cli,
    )

_LAZY_IMPORTS: Mapping[str, Sequence[str]] = {
    "FlextInfraCliCheck": ["flext_infra.check.cli", "FlextInfraCliCheck"],
    "FlextInfraConfigFixer": ["flext_infra.check.services", "FlextInfraConfigFixer"],
    "FlextInfraWorkspaceChecker": [
        "flext_infra.check.services",
        "FlextInfraWorkspaceChecker",
    ],
    "build_parser": ["flext_infra.check.workspace_check", "build_parser"],
    "cli": ["flext_infra.check.cli", ""],
    "main": ["flext_infra.check.workspace_check", "main"],
    "run_cli": ["flext_infra.check.workspace_check", "run_cli"],
    "services": ["flext_infra.check.services", ""],
    "workspace_check": ["flext_infra.check.workspace_check", ""],
}

_EXPORTS: Sequence[str] = [
    "FlextInfraCliCheck",
    "FlextInfraConfigFixer",
    "FlextInfraWorkspaceChecker",
    "build_parser",
    "cli",
    "main",
    "run_cli",
    "services",
    "workspace_check",
]


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, _EXPORTS)
