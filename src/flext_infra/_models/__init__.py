# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Models package."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING as _TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if _TYPE_CHECKING:
    from flext_core import FlextTypes

    from flext_infra._models import base, census, cli_inputs, rope, scan
    from flext_infra._models.base import FlextInfraModelsBase
    from flext_infra._models.census import FlextInfraModelsCensus
    from flext_infra._models.cli_inputs import FlextInfraModelsCliInputs
    from flext_infra._models.rope import FlextInfraModelsRope
    from flext_infra._models.scan import FlextInfraModelsScan

_LAZY_IMPORTS: Mapping[str, str | Sequence[str]] = {
    "FlextInfraModelsBase": "flext_infra._models.base",
    "FlextInfraModelsCensus": "flext_infra._models.census",
    "FlextInfraModelsCliInputs": "flext_infra._models.cli_inputs",
    "FlextInfraModelsRope": "flext_infra._models.rope",
    "FlextInfraModelsScan": "flext_infra._models.scan",
    "base": "flext_infra._models.base",
    "census": "flext_infra._models.census",
    "cli_inputs": "flext_infra._models.cli_inputs",
    "rope": "flext_infra._models.rope",
    "scan": "flext_infra._models.scan",
}


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)
