"""CLI input models for codegen commands.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import Annotated

from pydantic import Field

from flext_core import FlextModels
from flext_infra._models.mixins import FlextInfraModelsMixins


class FlextInfraModelsCliInputsCodegen:
    """Namespaced CLI input models for codegen and docs commands."""

    class BaseMkGenerateInput(
        FlextInfraModelsMixins.OptionalProjectNameFieldMixin,
        FlextInfraModelsMixins.CliInputBase,
        FlextModels.ContractModel,
    ):
        """CLI input for base.mk generation."""

        output: Annotated[
            str | None,
            Field(
                default=None,
                description="Write generated content to file path (defaults to stdout)",
            ),
        ] = None

    class DocsAuditInput(
        FlextInfraModelsMixins.CheckMixin,
        FlextInfraModelsMixins.OutputDirMixin,
        FlextInfraModelsMixins.ProjectSelectionMixin,
        FlextInfraModelsMixins.CliInputBase,
        FlextModels.ContractModel,
    ):
        strict: Annotated[
            bool,
            Field(default=False, description="Strict mode"),
        ] = False

    class DocsFixInput(
        FlextInfraModelsMixins.OutputDirMixin,
        FlextInfraModelsMixins.ProjectSelectionMixin,
        FlextInfraModelsMixins.CliInputBase,
        FlextModels.ContractModel,
    ):
        pass

    class DocsBuildInput(
        FlextInfraModelsMixins.OutputDirMixin,
        FlextInfraModelsMixins.ProjectSelectionMixin,
        FlextInfraModelsMixins.CliInputBase,
        FlextModels.ContractModel,
    ):
        pass

    class DocsGenerateInput(
        FlextInfraModelsMixins.OutputDirMixin,
        FlextInfraModelsMixins.ProjectSelectionMixin,
        FlextInfraModelsMixins.CliInputBase,
        FlextModels.ContractModel,
    ):
        pass

    class DocsValidateInput(
        FlextInfraModelsMixins.CheckMixin,
        FlextInfraModelsMixins.OutputDirMixin,
        FlextInfraModelsMixins.ProjectSelectionMixin,
        FlextInfraModelsMixins.CliInputBase,
        FlextModels.ContractModel,
    ):
        pass


__all__ = ["FlextInfraModelsCliInputsCodegen"]
