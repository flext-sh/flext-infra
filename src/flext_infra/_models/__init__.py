# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Models package."""

from __future__ import annotations

import typing as _t

from flext_core.lazy import install_lazy_exports
from flext_infra._models.base import FlextInfraModelsBase
from flext_infra._models.census import FlextInfraModelsCensus
from flext_infra._models.cli_inputs import FlextInfraModelsCliInputs
from flext_infra._models.cli_inputs_codegen import FlextInfraModelsCliInputsCodegen
from flext_infra._models.cli_inputs_ops import FlextInfraModelsCliInputsOps
from flext_infra._models.rope import FlextInfraModelsRope
from flext_infra._models.scan import FlextInfraModelsScan

if _t.TYPE_CHECKING:
    import flext_infra._models.base as _flext_infra__models_base

    base = _flext_infra__models_base
    import flext_infra._models.census as _flext_infra__models_census

    census = _flext_infra__models_census
    import flext_infra._models.cli_inputs as _flext_infra__models_cli_inputs

    cli_inputs = _flext_infra__models_cli_inputs
    import flext_infra._models.cli_inputs_codegen as _flext_infra__models_cli_inputs_codegen

    cli_inputs_codegen = _flext_infra__models_cli_inputs_codegen
    import flext_infra._models.cli_inputs_ops as _flext_infra__models_cli_inputs_ops

    cli_inputs_ops = _flext_infra__models_cli_inputs_ops
    import flext_infra._models.rope as _flext_infra__models_rope

    rope = _flext_infra__models_rope
    import flext_infra._models.scan as _flext_infra__models_scan

    scan = _flext_infra__models_scan

    _ = (
        FlextInfraModelsBase,
        FlextInfraModelsCensus,
        FlextInfraModelsCliInputs,
        FlextInfraModelsCliInputsCodegen,
        FlextInfraModelsCliInputsOps,
        FlextInfraModelsRope,
        FlextInfraModelsScan,
        base,
        census,
        cli_inputs,
        cli_inputs_codegen,
        cli_inputs_ops,
        rope,
        scan,
    )
_LAZY_IMPORTS = {
    "FlextInfraModelsBase": "flext_infra._models.base",
    "FlextInfraModelsCensus": "flext_infra._models.census",
    "FlextInfraModelsCliInputs": "flext_infra._models.cli_inputs",
    "FlextInfraModelsCliInputsCodegen": "flext_infra._models.cli_inputs_codegen",
    "FlextInfraModelsCliInputsOps": "flext_infra._models.cli_inputs_ops",
    "FlextInfraModelsRope": "flext_infra._models.rope",
    "FlextInfraModelsScan": "flext_infra._models.scan",
    "base": "flext_infra._models.base",
    "census": "flext_infra._models.census",
    "cli_inputs": "flext_infra._models.cli_inputs",
    "cli_inputs_codegen": "flext_infra._models.cli_inputs_codegen",
    "cli_inputs_ops": "flext_infra._models.cli_inputs_ops",
    "rope": "flext_infra._models.rope",
    "scan": "flext_infra._models.scan",
}

__all__ = [
    "FlextInfraModelsBase",
    "FlextInfraModelsCensus",
    "FlextInfraModelsCliInputs",
    "FlextInfraModelsCliInputsCodegen",
    "FlextInfraModelsCliInputsOps",
    "FlextInfraModelsRope",
    "FlextInfraModelsScan",
    "base",
    "census",
    "cli_inputs",
    "cli_inputs_codegen",
    "cli_inputs_ops",
    "rope",
    "scan",
]


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)
