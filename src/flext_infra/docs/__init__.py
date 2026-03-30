# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Documentation services.

Provides services for documentation generation, validation, and maintenance
across the workspace.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from flext_infra.docs import auditor, builder, cli, fixer, generator, validator
    from flext_infra.docs.auditor import *
    from flext_infra.docs.builder import *
    from flext_infra.docs.cli import *
    from flext_infra.docs.fixer import *
    from flext_infra.docs.generator import *
    from flext_infra.docs.validator import *

_LAZY_IMPORTS: Mapping[str, str | Sequence[str]] = {
    "FlextInfraCliDocs": "flext_infra.docs.cli",
    "FlextInfraDocAuditor": "flext_infra.docs.auditor",
    "FlextInfraDocBuilder": "flext_infra.docs.builder",
    "FlextInfraDocFixer": "flext_infra.docs.fixer",
    "FlextInfraDocGenerator": "flext_infra.docs.generator",
    "FlextInfraDocValidator": "flext_infra.docs.validator",
    "FlextInfraDocsCli": "flext_infra.docs.cli",
    "auditor": "flext_infra.docs.auditor",
    "builder": "flext_infra.docs.builder",
    "cli": "flext_infra.docs.cli",
    "fixer": "flext_infra.docs.fixer",
    "generator": "flext_infra.docs.generator",
    "main": "flext_infra.docs.auditor",
    "validator": "flext_infra.docs.validator",
}


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, sorted(_LAZY_IMPORTS))
