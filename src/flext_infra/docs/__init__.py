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
from typing import TYPE_CHECKING as _TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if _TYPE_CHECKING:
    from flext_core import FlextTypes
    from flext_infra.docs import (
        _constants,
        _models,
        auditor,
        builder,
        cli,
        fixer,
        generator,
        validator,
    )
    from flext_infra.docs._constants import FlextInfraDocsConstants
    from flext_infra.docs._models import FlextInfraDocsModels
    from flext_infra.docs.auditor import FlextInfraDocAuditor, main
    from flext_infra.docs.builder import FlextInfraDocBuilder
    from flext_infra.docs.cli import FlextInfraCliDocs, FlextInfraDocsCli
    from flext_infra.docs.fixer import FlextInfraDocFixer
    from flext_infra.docs.generator import FlextInfraDocGenerator
    from flext_infra.docs.validator import FlextInfraDocValidator

_LAZY_IMPORTS: FlextTypes.LazyImportIndex = {
    "FlextInfraCliDocs": "flext_infra.docs.cli",
    "FlextInfraDocAuditor": "flext_infra.docs.auditor",
    "FlextInfraDocBuilder": "flext_infra.docs.builder",
    "FlextInfraDocFixer": "flext_infra.docs.fixer",
    "FlextInfraDocGenerator": "flext_infra.docs.generator",
    "FlextInfraDocValidator": "flext_infra.docs.validator",
    "FlextInfraDocsCli": "flext_infra.docs.cli",
    "FlextInfraDocsConstants": "flext_infra.docs._constants",
    "FlextInfraDocsModels": "flext_infra.docs._models",
    "_constants": "flext_infra.docs._constants",
    "_models": "flext_infra.docs._models",
    "auditor": "flext_infra.docs.auditor",
    "builder": "flext_infra.docs.builder",
    "cli": "flext_infra.docs.cli",
    "fixer": "flext_infra.docs.fixer",
    "generator": "flext_infra.docs.generator",
    "main": "flext_infra.docs.auditor",
    "validator": "flext_infra.docs.validator",
}


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)
