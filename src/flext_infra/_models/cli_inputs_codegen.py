"""CLI input models for codegen commands.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

from pydantic import ConfigDict, Field

from flext_core import FlextModels
from flext_infra import c
from flext_infra.base import apply_option_json_schema_extra


class FlextInfraModelsCliInputsCodegen:
    """Namespaced CLI input models for codegen and docs commands."""

    class CliInputBase(FlextModels.FrozenStrictModel):
        """Base for all CLI input models."""

        model_config = ConfigDict(populate_by_name=True)

        apply: Annotated[
            bool,
            Field(
                default=False,
                description="Apply changes",
                json_schema_extra=apply_option_json_schema_extra,
            ),
        ] = False

        workspace: Annotated[
            str,
            Field(default=".", description="Workspace root"),
        ] = "."

        @property
        def workspace_path(self) -> Path:
            """Return the resolved workspace path for CLI execution."""
            return Path(self.workspace).resolve()

    class ApplyMixin(FlextModels.FrozenStrictModel):
        """Shared apply flag for mutating commands."""

        apply: Annotated[
            bool,
            Field(
                default=False,
                description="Apply changes",
                json_schema_extra=apply_option_json_schema_extra,
            ),
        ] = False

    class OutputDirMixin(FlextModels.FrozenStrictModel):
        """Shared output directory option for report-producing commands."""

        output_dir: Annotated[
            str,
            Field(
                default=f"{c.Infra.Reporting.REPORTS_DIR_NAME}/docs",
                description="Output directory for reports",
            ),
        ] = f"{c.Infra.Reporting.REPORTS_DIR_NAME}/docs"

    class BaseMkGenerateInput(CliInputBase):
        """CLI input for base.mk generation."""

        output: Annotated[
            str | None,
            Field(
                default=None,
                description="Write generated content to file path (defaults to stdout)",
            ),
        ] = None
        project_name: Annotated[
            str | None,
            Field(
                default=None,
                description="Override project name in generated base.mk",
            ),
        ] = None

    class DocsProjectMixin(CliInputBase):
        project: Annotated[
            str | None,
            Field(default=None, description="Single project name"),
        ] = None
        projects: Annotated[
            str | None,
            Field(default=None, description="Comma-separated project names"),
        ] = None

    class DocsAuditInput(OutputDirMixin, DocsProjectMixin):
        check: Annotated[
            bool,
            Field(default=False, description="Enable check mode"),
        ] = False
        strict: Annotated[
            bool,
            Field(default=False, description="Strict mode"),
        ] = False

    class DocsFixInput(ApplyMixin, OutputDirMixin, DocsProjectMixin):
        pass

    class DocsBuildInput(OutputDirMixin, DocsProjectMixin):
        pass

    class DocsGenerateInput(ApplyMixin, OutputDirMixin, DocsProjectMixin):
        pass

    class DocsValidateInput(ApplyMixin, OutputDirMixin, DocsProjectMixin):
        check: Annotated[
            bool,
            Field(default=False, description="Enable check mode"),
        ] = False


__all__ = ["FlextInfraModelsCliInputsCodegen"]
