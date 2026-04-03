# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Check package."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING as _TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if _TYPE_CHECKING:
    from flext_core import FlextTypes
    from flext_core.constants import FlextConstants as c
    from flext_core.decorators import FlextDecorators as d
    from flext_core.exceptions import FlextExceptions as e
    from flext_core.handlers import FlextHandlers as h
    from flext_core.mixins import FlextMixins as x
    from flext_core.models import FlextModels as m
    from flext_core.protocols import FlextProtocols as p
    from flext_core.result import FlextResult as r
    from flext_core.service import FlextService as s
    from flext_core.typings import FlextTypes as t
    from flext_core.utilities import FlextUtilities as u
    from flext_infra.check import (
        _constants,
        _models,
        cli,
        services,
        workspace_check,
        workspace_check_cli,
    )
    from flext_infra.check._constants import FlextInfraCheckConstants
    from flext_infra.check._models import FlextInfraCheckModels
    from flext_infra.check.cli import FlextInfraCliCheck
    from flext_infra.check.services import (
        FlextInfraConfigFixer,
        FlextInfraWorkspaceChecker,
    )
    from flext_infra.check.workspace_check import build_parser, main, run_cli
    from flext_infra.check.workspace_check_cli import FlextInfraWorkspaceCheckerCli

_LAZY_IMPORTS: FlextTypes.LazyImportIndex = {
    "FlextInfraCheckConstants": "flext_infra.check._constants",
    "FlextInfraCheckModels": "flext_infra.check._models",
    "FlextInfraCliCheck": "flext_infra.check.cli",
    "FlextInfraConfigFixer": "flext_infra.check.services",
    "FlextInfraWorkspaceChecker": "flext_infra.check.services",
    "FlextInfraWorkspaceCheckerCli": "flext_infra.check.workspace_check_cli",
    "_constants": "flext_infra.check._constants",
    "_models": "flext_infra.check._models",
    "build_parser": "flext_infra.check.workspace_check",
    "c": ("flext_core.constants", "FlextConstants"),
    "cli": "flext_infra.check.cli",
    "d": ("flext_core.decorators", "FlextDecorators"),
    "e": ("flext_core.exceptions", "FlextExceptions"),
    "h": ("flext_core.handlers", "FlextHandlers"),
    "m": ("flext_core.models", "FlextModels"),
    "main": "flext_infra.check.workspace_check",
    "p": ("flext_core.protocols", "FlextProtocols"),
    "r": ("flext_core.result", "FlextResult"),
    "run_cli": "flext_infra.check.workspace_check",
    "s": ("flext_core.service", "FlextService"),
    "services": "flext_infra.check.services",
    "t": ("flext_core.typings", "FlextTypes"),
    "u": ("flext_core.utilities", "FlextUtilities"),
    "workspace_check": "flext_infra.check.workspace_check",
    "workspace_check_cli": "flext_infra.check.workspace_check_cli",
    "x": ("flext_core.mixins", "FlextMixins"),
}


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)
