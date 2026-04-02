"""CLI input models for flext-infra commands.

Each inner class maps 1:1 to a CLI command. Fields become CLI options
via FlextCliCli.model_command() / register_result_route().

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_infra._models.cli_inputs_codegen import FlextInfraModelsCliInputsCodegen
from flext_infra._models.cli_inputs_ops import FlextInfraModelsCliInputsOps


class FlextInfraModelsCliInputs(
    FlextInfraModelsCliInputsCodegen,
    FlextInfraModelsCliInputsOps,
):
    """Namespaced CLI input models for flext-infra commands."""


__all__ = ["FlextInfraModelsCliInputs"]
