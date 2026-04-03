"""CLI input models for codegen commands.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from flext_infra import c


class FlextInfraModelsCliInputsCodegen:
    """Namespaced CLI input models for codegen and docs commands."""

    class CliInputBase(BaseModel):
        """Base for all CLI input models."""

        model_config = ConfigDict(populate_by_name=True)

        workspace: Annotated[
            str,
            Field(default=".", description="Workspace root"),
        ] = "."

    class ApplyMixin(BaseModel):
        """Shared apply flag for mutating commands."""

        apply: Annotated[
            bool,
            Field(default=False, description="Apply changes"),
        ] = False

    class OutputDirMixin(BaseModel):
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

    class CodegenLazyInitInput(CliInputBase):
        """CLI input for lazy-init."""

        check: Annotated[
            bool,
            Field(default=False, description="Check mode (no writes)"),
        ] = False

    class CodegenCensusInput(CliInputBase):
        """CLI input for census."""

        output_format: Annotated[
            str,
            Field(default="text", description="Output format (json|text)"),
        ] = "text"
        class_to_analyze: Annotated[
            str | None,
            Field(
                default=None,
                description="Full class path to analyze (e.g. flext_core.FlextConstants)",
            ),
        ] = None

    class CodegenDeduplicateInput(ApplyMixin, CliInputBase):
        """CLI input for deduplicate."""

        class_to_analyze: Annotated[
            str,
            Field(
                description="Full class path to deduplicate (e.g. flext_core.FlextConstants)",
            ),
        ]

    class CodegenScaffoldInput(ApplyMixin, CliInputBase):
        """CLI input for scaffold."""

    class CodegenAutoFixInput(ApplyMixin, CliInputBase):
        """CLI input for auto-fix."""

    class CodegenPyTypedInput(CliInputBase):
        """CLI input for py-typed."""

        check: Annotated[
            bool,
            Field(default=False, description="Check mode (no writes)"),
        ] = False

    class CodegenPipelineInput(ApplyMixin, CliInputBase):
        """CLI input for pipeline."""

        output_format: Annotated[
            str,
            Field(default="text", description="Output format (json|text)"),
        ] = "text"

    class CodegenConsolidateInput(ApplyMixin, CliInputBase):
        """CLI input for constant consolidation."""

        output_format: Annotated[
            str,
            Field(default="text", description="Output format (json|text)"),
        ] = "text"
        project: Annotated[
            str | None,
            Field(default=None, description="Single project to consolidate"),
        ] = None

    class CodegenConstantsQualityGateInput(CliInputBase):
        """CLI input for constants-quality-gate."""

        before_report: Annotated[
            str | None,
            Field(
                default=None,
                description="Path to pre-refactor report JSON for comparison",
            ),
        ] = None
        baseline_file: Annotated[
            str | None,
            Field(
                default=None,
                description="Path to baseline JSON payload for comparison",
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
