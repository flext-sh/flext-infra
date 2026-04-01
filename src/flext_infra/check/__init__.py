# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Check services for quality gate execution."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING as _TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if _TYPE_CHECKING:
    from flext_core import FlextTypes

    from flext_infra.check import _constants, _models, cli, services, workspace_check
    from flext_infra.check._constants import FlextInfraCheckConstants
    from flext_infra.check._models import FlextInfraCheckModels
    from flext_infra.check.cli import FlextInfraCliCheck
    from flext_infra.check.services import (
        FlextInfraConfigFixer,
        FlextInfraWorkspaceChecker,
    )
    from flext_infra.check.workspace_check import build_parser, main, run_cli

_LAZY_IMPORTS: Mapping[str, str | Sequence[str]] = {
    "FlextInfraCheckConstants": "flext_infra.check._constants",
    "FlextInfraCheckModels": "flext_infra.check._models",
    "FlextInfraCliCheck": "flext_infra.check.cli",
    "FlextInfraConfigFixer": "flext_infra.check.services",
    "FlextInfraWorkspaceChecker": "flext_infra.check.services",
    "_constants": "flext_infra.check._constants",
    "_models": "flext_infra.check._models",
    "build_parser": "flext_infra.check.workspace_check",
    "cli": "flext_infra.check.cli",
    "main": "flext_infra.check.workspace_check",
    "run_cli": "flext_infra.check.workspace_check",
    "services": "flext_infra.check.services",
    "workspace_check": "flext_infra.check.workspace_check",
}


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)
