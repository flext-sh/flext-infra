# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Base.mk template engine service.

Provides services for managing, validating, and rendering base.mk templates
for workspace build orchestration.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING as _TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if _TYPE_CHECKING:
    from flext_core import FlextTypes
    from flext_infra.basemk import _constants, _models, cli, engine, generator
    from flext_infra.basemk._constants import FlextInfraBasemkConstants
    from flext_infra.basemk._models import FlextInfraBasemkModels
    from flext_infra.basemk.cli import FlextInfraCliBasemk
    from flext_infra.basemk.engine import FlextInfraBaseMkTemplateEngine
    from flext_infra.basemk.generator import FlextInfraBaseMkGenerator

_LAZY_IMPORTS: FlextTypes.LazyImportIndex = {
    "FlextInfraBaseMkGenerator": "flext_infra.basemk.generator",
    "FlextInfraBaseMkTemplateEngine": "flext_infra.basemk.engine",
    "FlextInfraBasemkConstants": "flext_infra.basemk._constants",
    "FlextInfraBasemkModels": "flext_infra.basemk._models",
    "FlextInfraCliBasemk": "flext_infra.basemk.cli",
    "_constants": "flext_infra.basemk._constants",
    "_models": "flext_infra.basemk._models",
    "cli": "flext_infra.basemk.cli",
    "engine": "flext_infra.basemk.engine",
    "generator": "flext_infra.basemk.generator",
}


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)
