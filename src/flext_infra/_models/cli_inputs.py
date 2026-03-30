"""CLI input models for flext-infra commands.

Each inner class maps 1:1 to a CLI command. Fields become CLI options
via FlextCliCli.model_command() / register_result_route().

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from flext_infra import c


class FlextInfraModelsCliInputs:
    """Namespaced CLI input models for flext-infra commands."""

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

    class GithubReportMixin(CliInputBase):
        report: Annotated[
            str | None,
            Field(default=None, description="Output report file"),
        ] = None

    class GithubWorkflowsInput(ApplyMixin, GithubReportMixin):
        prune: Annotated[
            bool,
            Field(default=False, description="Remove unknown files"),
        ] = False

    class GithubLintInput(GithubReportMixin):
        strict: Annotated[
            bool,
            Field(default=False, description="Fail on strict mode warnings"),
        ] = False

    class GithubPrInput(CliInputBase):
        repo_root: Annotated[str, Field(..., description="Repository root directory")]
        action: Annotated[
            str,
            Field(
                default="status",
                description="PR action (status/create/view/checks/merge/close)",
            ),
        ] = "status"
        base: Annotated[str, Field(default="main", description="Base branch")] = "main"
        head: Annotated[str | None, Field(default=None, description="Head branch")] = (
            None
        )
        number: Annotated[int | None, Field(default=None, description="PR number")] = (
            None
        )
        title: Annotated[str | None, Field(default=None, description="PR title")] = None
        body: Annotated[str | None, Field(default=None, description="PR body")] = None
        draft: Annotated[
            bool,
            Field(default=False, description="Create as draft"),
        ] = False
        merge_method: Annotated[
            str,
            Field(default="squash", description="Merge method (merge/squash/rebase)"),
        ] = "squash"
        auto: Annotated[bool, Field(default=False, description="Auto-merge")] = False
        delete_branch: Annotated[
            bool,
            Field(default=True, description="Delete head branch on merge"),
        ] = True
        checks_strict: Annotated[
            bool,
            Field(default=True, description="Fail if checks fail"),
        ] = True
        release_on_merge: Annotated[
            bool,
            Field(default=True, description="Run release workflow on merge"),
        ] = True

    class GithubPrWorkspaceInput(CliInputBase):
        project: Annotated[
            list[str],
            Field(
                default_factory=list,
                description="Project to process; repeat --project NAME as needed",
            ),
        ] = Field(default_factory=list)
        include_root: Annotated[
            bool,
            Field(default=False, description="Include root project"),
        ] = False
        branch: Annotated[
            str,
            Field(default="", description="Branch name filter"),
        ] = ""
        checkpoint: Annotated[
            bool,
            Field(default=True, description="Enable checkpoints"),
        ] = True
        fail_fast: Annotated[
            bool,
            Field(default=True, description="Stop on first failure"),
        ] = True
        pr_action: Annotated[str, Field(default="status", description="PR action")] = (
            "status"
        )
        pr_base: Annotated[str, Field(default="", description="Base branch")] = ""
        pr_head: Annotated[str, Field(default="", description="Head branch")] = ""
        pr_number: Annotated[
            int | None,
            Field(default=None, description="PR number"),
        ] = None
        pr_title: Annotated[str, Field(default="", description="PR title")] = ""
        pr_body: Annotated[str, Field(default="", description="PR body")] = ""
        pr_draft: Annotated[bool, Field(default=False, description="Draft PR")] = False
        pr_merge_method: Annotated[
            str,
            Field(default="squash", description="Merge method"),
        ] = "squash"
        pr_auto: Annotated[bool, Field(default=False, description="Auto-merge")] = False
        pr_delete_branch: Annotated[
            bool,
            Field(default=True, description="Delete branch on merge"),
        ] = True
        pr_checks_strict: Annotated[
            bool,
            Field(default=True, description="Strict checks required"),
        ] = True
        pr_release_on_merge: Annotated[
            bool,
            Field(default=False, description="Release on merge"),
        ] = False

    class RefactorCentralizeInput(ApplyMixin, CliInputBase):
        normalize_remaining: Annotated[
            bool,
            Field(
                default=False,
                description="Remove remaining BaseModel/TypedDict bases in non-allowed files",
            ),
        ] = False

    class RefactorMigrateMroInput(ApplyMixin, CliInputBase):
        target: Annotated[
            str,
            Field(
                default="all",
                description="Migration target scope (constants/typings/protocols/models/utilities/all)",
            ),
        ] = "all"

    class RefactorNamespaceEnforceInput(ApplyMixin, CliInputBase):
        diff: Annotated[
            bool,
            Field(default=False, description="Show diff without applying"),
        ] = False
        project: Annotated[
            str | None,
            Field(
                default=None,
                description="Project to process (comma-separated for multiple)",
            ),
        ] = None

    class RefactorUltraworkModelsInput(ApplyMixin, CliInputBase):
        normalize_remaining: Annotated[
            bool,
            Field(
                default=False,
                description="Remove remaining BaseModel/TypedDict bases in non-allowed files",
            ),
        ] = False

    class RefactorCensusInput(CliInputBase):
        family: Annotated[
            str,
            Field(default="u", description="MRO family to census (c/t/p/m/u)"),
        ] = "u"
        json_output: Annotated[
            str | None,
            Field(default=None, description="Path to write JSON report"),
        ] = None

    class ReleaseRunInput(ApplyMixin, CliInputBase):
        phase: Annotated[str, Field(default="all", description="Release phase")] = "all"
        version: Annotated[str, Field(default="", description="Version string")] = ""
        tag: Annotated[str, Field(default="", description="Git tag (e.g. v1.0.0)")] = ""
        bump: Annotated[
            str,
            Field(default="", description="Bump type (major/minor/patch)"),
        ] = ""
        interactive: Annotated[
            int,
            Field(default=1, description="Interactive mode (1=yes, 0=no)"),
        ] = 1
        push: Annotated[bool, Field(default=False, description="Push to remote")] = (
            False
        )
        dev_suffix: Annotated[
            bool,
            Field(default=False, description="Add dev suffix"),
        ] = False
        next_dev: Annotated[
            bool,
            Field(default=False, description="Prepare next dev version"),
        ] = False
        next_bump: Annotated[
            str,
            Field(default="minor", description="Bump type for next dev version"),
        ] = "minor"
        create_branches: Annotated[
            int,
            Field(default=1, description="Create release branches (1=yes, 0=no)"),
        ] = 1
        projects: Annotated[
            list[str] | None,
            Field(default=None, description="Project names to release"),
        ] = None

    class ValidateBaseMkInput(CliInputBase):
        """CLI input for basemk-validate."""

        pass

    class ValidateInventoryInput(CliInputBase):
        """CLI input for inventory."""

        output_dir: Annotated[
            str | None,
            Field(default=None, description="Output directory"),
        ] = None

    class ValidatePytestDiagInput(CliInputBase):
        """CLI input for pytest-diag."""

        junit: Annotated[str, Field(..., description="JUnit XML path")]
        log: Annotated[str, Field(..., description="Pytest log path")]
        failed: Annotated[
            str | None,
            Field(default=None, description="Path to write failed cases"),
        ] = None
        errors: Annotated[
            str | None,
            Field(default=None, description="Path to write error traces"),
        ] = None
        warnings: Annotated[
            str | None,
            Field(default=None, description="Path to write warnings"),
        ] = None
        slowest: Annotated[
            str | None,
            Field(default=None, description="Path to write slowest entries"),
        ] = None
        skips: Annotated[
            str | None,
            Field(default=None, description="Path to write skipped cases"),
        ] = None

    class ValidateScanInput(CliInputBase):
        """CLI input for scan."""

        pattern: Annotated[str, Field(..., description="Regex pattern")]
        include: Annotated[
            list[str] | None,
            Field(default=None, description="Include glob"),
        ] = None
        exclude: Annotated[
            list[str] | None,
            Field(default=None, description="Exclude glob"),
        ] = None
        match: Annotated[
            str,
            Field(
                default=c.Infra.MatchModes.PRESENT,
                description="Violation mode (present or absent)",
            ),
        ] = c.Infra.MatchModes.PRESENT

    class ValidateSkillValidateInput(CliInputBase):
        """CLI input for skill-validate."""

        skill: Annotated[str, Field(..., description="Skill folder name")]
        mode: Annotated[
            str,
            Field(
                default=c.Infra.Modes.BASELINE,
                description="Validation mode (baseline or strict)",
            ),
        ] = c.Infra.Modes.BASELINE

    class ValidateStubValidateInput(CliInputBase):
        """CLI input for stub-validate."""

        project: Annotated[
            list[str] | None,
            Field(default=None, description="Project to validate"),
        ] = None
        all_projects: Annotated[
            bool,
            Field(default=False, description="Validate all projects", alias="all"),
        ] = False

    class WorkspaceDetectInput(CliInputBase):
        """CLI input for workspace detection."""

        pass

    class WorkspaceSyncInput(ApplyMixin, CliInputBase):
        """CLI input for base.mk sync."""

        canonical_root: Annotated[
            str,
            Field(default="", description="Canonical workspace root"),
        ] = ""

    class WorkspaceOrchestrateInput(CliInputBase):
        """CLI input for project orchestration."""

        verb: Annotated[str, Field(description="Make verb to execute")]
        projects: Annotated[
            str,
            Field(default="", description="Comma-separated project directories"),
        ] = ""
        fail_fast: Annotated[
            bool,
            Field(default=False, description="Stop on first failure"),
        ] = False
        make_arg: Annotated[
            list[str],
            Field(
                default_factory=list,
                description="Additional make arguments; repeat --make-arg KEY=VALUE",
            ),
        ] = Field(default_factory=list)

    class WorkspaceMigrateInput(ApplyMixin, CliInputBase):
        dry_run: Annotated[
            bool,
            Field(default=False, description="Preview changes without writing"),
        ] = False

    class MaintenanceRunInput(CliInputBase):
        """CLI input for maintenance command."""

        check: Annotated[
            bool,
            Field(default=False, description="Run in check mode"),
        ] = False
        verbose: Annotated[
            bool,
            Field(default=False, description="Verbose output"),
        ] = False


__all__ = ["FlextInfraModelsCliInputs"]
