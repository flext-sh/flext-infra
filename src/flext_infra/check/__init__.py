# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Check services for quality gate execution."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from flext_infra.check import cli, services, workspace_check
    from flext_infra.check.cli import *
    from flext_infra.check.services import *
    from flext_infra.check.workspace_check import *

_LAZY_IMPORTS: Mapping[str, str | Sequence[str]] = {
    "FlextInfraCliCheck": "flext_infra.check.cli",
    "FlextInfraConfigFixer": "flext_infra.check.services",
    "FlextInfraWorkspaceChecker": "flext_infra.check.services",
    "build_parser": "flext_infra.check.workspace_check",
    "cli": "flext_infra.check.cli",
    "main": "flext_infra.check.workspace_check",
    "run_cli": "flext_infra.check.workspace_check",
    "services": "flext_infra.check.services",
    "workspace_check": "flext_infra.check.workspace_check",
}


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, sorted(_LAZY_IMPORTS))
