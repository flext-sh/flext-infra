# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Models package."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from flext_infra._models import (
        base as base,
        census as census,
        cli_inputs as cli_inputs,
        cst as cst,
        rope as rope,
        scan as scan,
    )
    from flext_infra._models.base import FlextInfraModelsBase as FlextInfraModelsBase
    from flext_infra._models.census import (
        FlextInfraModelsCensus as FlextInfraModelsCensus,
    )
    from flext_infra._models.cli_inputs import (
        FlextInfraModelsCliInputs as FlextInfraModelsCliInputs,
    )
    from flext_infra._models.cst import FlextInfraModelsCst as FlextInfraModelsCst
    from flext_infra._models.rope import FlextInfraModelsRope as FlextInfraModelsRope
    from flext_infra._models.scan import FlextInfraModelsScan as FlextInfraModelsScan

_LAZY_IMPORTS: Mapping[str, Sequence[str]] = {
    "FlextInfraModelsBase": ["flext_infra._models.base", "FlextInfraModelsBase"],
    "FlextInfraModelsCensus": ["flext_infra._models.census", "FlextInfraModelsCensus"],
    "FlextInfraModelsCliInputs": [
        "flext_infra._models.cli_inputs",
        "FlextInfraModelsCliInputs",
    ],
    "FlextInfraModelsCst": ["flext_infra._models.cst", "FlextInfraModelsCst"],
    "FlextInfraModelsRope": ["flext_infra._models.rope", "FlextInfraModelsRope"],
    "FlextInfraModelsScan": ["flext_infra._models.scan", "FlextInfraModelsScan"],
    "base": ["flext_infra._models.base", ""],
    "census": ["flext_infra._models.census", ""],
    "cli_inputs": ["flext_infra._models.cli_inputs", ""],
    "cst": ["flext_infra._models.cst", ""],
    "rope": ["flext_infra._models.rope", ""],
    "scan": ["flext_infra._models.scan", ""],
}

_EXPORTS: Sequence[str] = [
    "FlextInfraModelsBase",
    "FlextInfraModelsCensus",
    "FlextInfraModelsCliInputs",
    "FlextInfraModelsCst",
    "FlextInfraModelsRope",
    "FlextInfraModelsScan",
    "base",
    "census",
    "cli_inputs",
    "cst",
    "rope",
    "scan",
]


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, _EXPORTS)
