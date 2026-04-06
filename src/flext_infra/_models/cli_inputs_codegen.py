"""CLI input models for codegen commands.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import Annotated

from pydantic import Field

from flext_core import FlextModels
from flext_infra import FlextInfraModelsMixins, c


class FlextInfraModelsCliInputsCodegen:
    """Namespaced CLI input models for codegen and docs commands."""

    class BaseMkGenerateInput(
        FlextInfraModelsMixins.OptionalProjectNameFieldMixin,
        FlextInfraModelsMixins.WriteMixin,
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
        FlextInfraModelsMixins.WriteMixin,
        FlextModels.ContractModel,
    ):
        check: Annotated[
            bool,
            Field(default=False, description="Enable check mode"),
        ] = False
        output_dir: Annotated[
            str | None,
            Field(
                default=f"{c.Infra.Reporting.REPORTS_DIR_NAME}/docs",
                description="Output directory for reports",
            ),
        ] = f"{c.Infra.Reporting.REPORTS_DIR_NAME}/docs"
        strict: Annotated[
            bool,
            Field(default=False, description="Strict mode"),
        ] = False

    class DocsFixInput(
        FlextInfraModelsMixins.WriteMixin,
        FlextModels.ContractModel,
    ):
        output_dir: Annotated[
            str | None,
            Field(
                default=f"{c.Infra.Reporting.REPORTS_DIR_NAME}/docs",
                description="Output directory for reports",
            ),
        ] = f"{c.Infra.Reporting.REPORTS_DIR_NAME}/docs"

    class DocsBuildInput(
        FlextInfraModelsMixins.WriteMixin,
        FlextModels.ContractModel,
    ):
        output_dir: Annotated[
            str | None,
            Field(
                default=f"{c.Infra.Reporting.REPORTS_DIR_NAME}/docs",
                description="Output directory for reports",
            ),
        ] = f"{c.Infra.Reporting.REPORTS_DIR_NAME}/docs"

    class DocsGenerateInput(
        FlextInfraModelsMixins.WriteMixin,
        FlextModels.ContractModel,
    ):
        output_dir: Annotated[
            str | None,
            Field(
                default=f"{c.Infra.Reporting.REPORTS_DIR_NAME}/docs",
                description="Output directory for reports",
            ),
        ] = f"{c.Infra.Reporting.REPORTS_DIR_NAME}/docs"

    class DocsValidateInput(
        FlextInfraModelsMixins.WriteMixin,
        FlextModels.ContractModel,
    ):
        check: Annotated[
            bool,
            Field(default=False, description="Enable check mode"),
        ] = False
        output_dir: Annotated[
            str | None,
            Field(
                default=f"{c.Infra.Reporting.REPORTS_DIR_NAME}/docs",
                description="Output directory for reports",
            ),
        ] = f"{c.Infra.Reporting.REPORTS_DIR_NAME}/docs"


__all__ = ["FlextInfraModelsCliInputsCodegen"]
