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
from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from flext_infra.basemk import cli, engine, generator
    from flext_infra.basemk.cli import *
    from flext_infra.basemk.engine import *
    from flext_infra.basemk.generator import *

_LAZY_IMPORTS: Mapping[str, str | Sequence[str]] = {
    "FlextInfraBaseMkGenerator": "flext_infra.basemk.generator",
    "FlextInfraBaseMkTemplateEngine": "flext_infra.basemk.engine",
    "FlextInfraCliBasemk": "flext_infra.basemk.cli",
    "cli": "flext_infra.basemk.cli",
    "engine": "flext_infra.basemk.engine",
    "generator": "flext_infra.basemk.generator",
}


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, sorted(_LAZY_IMPORTS))
