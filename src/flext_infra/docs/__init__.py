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
    from flext_infra.docs import (
        auditor as auditor,
        builder as builder,
        cli as cli,
        fixer as fixer,
        generator as generator,
        validator as validator,
    )
    from flext_infra.docs.auditor import (
        FlextInfraDocAuditor as FlextInfraDocAuditor,
        main as main,
    )
    from flext_infra.docs.builder import FlextInfraDocBuilder as FlextInfraDocBuilder
    from flext_infra.docs.cli import (
        FlextInfraCliDocs as FlextInfraCliDocs,
        FlextInfraDocsCli as FlextInfraDocsCli,
    )
    from flext_infra.docs.fixer import FlextInfraDocFixer as FlextInfraDocFixer
    from flext_infra.docs.generator import (
        FlextInfraDocGenerator as FlextInfraDocGenerator,
    )
    from flext_infra.docs.validator import (
        FlextInfraDocValidator as FlextInfraDocValidator,
    )

_LAZY_IMPORTS: Mapping[str, Sequence[str]] = {
    "FlextInfraCliDocs": ["flext_infra.docs.cli", "FlextInfraCliDocs"],
    "FlextInfraDocAuditor": ["flext_infra.docs.auditor", "FlextInfraDocAuditor"],
    "FlextInfraDocBuilder": ["flext_infra.docs.builder", "FlextInfraDocBuilder"],
    "FlextInfraDocFixer": ["flext_infra.docs.fixer", "FlextInfraDocFixer"],
    "FlextInfraDocGenerator": ["flext_infra.docs.generator", "FlextInfraDocGenerator"],
    "FlextInfraDocValidator": ["flext_infra.docs.validator", "FlextInfraDocValidator"],
    "FlextInfraDocsCli": ["flext_infra.docs.cli", "FlextInfraDocsCli"],
    "auditor": ["flext_infra.docs.auditor", ""],
    "builder": ["flext_infra.docs.builder", ""],
    "cli": ["flext_infra.docs.cli", ""],
    "fixer": ["flext_infra.docs.fixer", ""],
    "generator": ["flext_infra.docs.generator", ""],
    "main": ["flext_infra.docs.auditor", "main"],
    "validator": ["flext_infra.docs.validator", ""],
}

_EXPORTS: Sequence[str] = [
    "FlextInfraCliDocs",
    "FlextInfraDocAuditor",
    "FlextInfraDocBuilder",
    "FlextInfraDocFixer",
    "FlextInfraDocGenerator",
    "FlextInfraDocValidator",
    "FlextInfraDocsCli",
    "auditor",
    "builder",
    "cli",
    "fixer",
    "generator",
    "main",
    "validator",
]


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, _EXPORTS)
