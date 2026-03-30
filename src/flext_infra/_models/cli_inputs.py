"""CLI input models for flext-infra commands.

Each inner class maps 1:1 to a CLI command. Fields become CLI options
via FlextCliCli.model_command() / register_result_route().

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, Field

from flext_infra import c


class FlextInfraModelsCliInputs:
    """CLI input models -- composed into m.Infra via MRO."""

    # ── BaseMk ───────────────────────────────────────────

    class BaseMkGenerateInput(BaseModel):
        """CLI input for base.mk generation -- fields become CLI options."""

        workspace: Annotated[
            str | None, Field(default=None, description="Workspace root directory")
        ]
        output: Annotated[
            str | None,
            Field(
                default=None,
                description="Write generated content to file path (defaults to stdout)",
            ),
        ]
        project_name: Annotated[
            str | None,
            Field(
                default=None,
                description="Override project name in generated base.mk",
            ),
        ]

    # ── Codegen ──────────────────────────────────────────

    class CodegenLazyInitInput(BaseModel):
        """CLI input for lazy-init -- fields become CLI options."""

        workspace: Annotated[str, Field(default=".", description="Workspace root")]
        check: Annotated[
            bool, Field(default=False, description="Check mode (no writes)")
        ]

    class CodegenCensusInput(BaseModel):
        """CLI input for census -- fields become CLI options."""

        workspace: Annotated[str, Field(default=".", description="Workspace root")]
        output_format: Annotated[
            str, Field(default="text", description="Output format (json|text)")
        ]
        class_to_analyze: Annotated[
            str | None,
            Field(
                default=None,
                description="Full class path to analyze (e.g. flext_core.FlextConstants)",
            ),
        ]

    class CodegenDeduplicateInput(BaseModel):
        """CLI input for deduplicate -- fields become CLI options."""

        workspace: Annotated[str, Field(default=".", description="Workspace root")]
        apply: Annotated[bool, Field(default=False, description="Apply changes")]
        class_to_analyze: Annotated[
            str,
            Field(
                description="Full class path to deduplicate (e.g. flext_core.FlextConstants)",
            ),
        ]

    class CodegenScaffoldInput(BaseModel):
        """CLI input for scaffold -- fields become CLI options."""

        workspace: Annotated[str, Field(default=".", description="Workspace root")]
        apply: Annotated[bool, Field(default=False, description="Apply changes")]

    class CodegenAutoFixInput(BaseModel):
        """CLI input for auto-fix -- fields become CLI options."""

        workspace: Annotated[str, Field(default=".", description="Workspace root")]
        apply: Annotated[bool, Field(default=False, description="Apply changes")]

    class CodegenPyTypedInput(BaseModel):
        """CLI input for py-typed -- fields become CLI options."""

        workspace: Annotated[str, Field(default=".", description="Workspace root")]
        check: Annotated[
            bool, Field(default=False, description="Check mode (no writes)")
        ]

    class CodegenPipelineInput(BaseModel):
        """CLI input for pipeline -- fields become CLI options."""

        workspace: Annotated[str, Field(default=".", description="Workspace root")]
        apply: Annotated[bool, Field(default=False, description="Apply changes")]
        output_format: Annotated[
            str, Field(default="text", description="Output format (json|text)")
        ]

    class CodegenConstantsQualityGateInput(BaseModel):
        """CLI input for constants-quality-gate -- fields become CLI options."""

        workspace: Annotated[str, Field(default=".", description="Workspace root")]
        before_report: Annotated[
            str | None,
            Field(
                default=None,
                description="Path to pre-refactor report JSON for comparison",
            ),
        ]
        baseline_file: Annotated[
            str | None,
            Field(
                default=None,
                description="Path to baseline JSON payload for comparison",
            ),
        ]

    # ── Docs ─────────────────────────────────────────────

    class DocsAuditInput(BaseModel):
        """CLI input for audit -- fields become CLI options."""

        workspace: Annotated[
            str | None, Field(default=None, description="Workspace root directory")
        ]
        project: Annotated[
            str | None, Field(default=None, description="Single project name")
        ]
        projects: Annotated[
            str | None,
            Field(default=None, description="Comma-separated project names"),
        ]
        check: Annotated[bool, Field(default=False, description="Enable check mode")]
        strict: Annotated[bool, Field(default=False, description="Strict mode")]
        output_dir: Annotated[
            str,
            Field(
                default=f"{c.Infra.Reporting.REPORTS_DIR_NAME}/docs",
                description="Output directory for reports",
            ),
        ]

    class DocsFixInput(BaseModel):
        """CLI input for fix -- fields become CLI options."""

        workspace: Annotated[
            str | None, Field(default=None, description="Workspace root directory")
        ]
        project: Annotated[
            str | None, Field(default=None, description="Single project name")
        ]
        projects: Annotated[
            str | None,
            Field(default=None, description="Comma-separated project names"),
        ]
        apply: Annotated[bool, Field(default=False, description="Apply changes")]
        output_dir: Annotated[
            str,
            Field(
                default=f"{c.Infra.Reporting.REPORTS_DIR_NAME}/docs",
                description="Output directory for reports",
            ),
        ]

    class DocsBuildInput(BaseModel):
        """CLI input for build -- fields become CLI options."""

        workspace: Annotated[
            str | None, Field(default=None, description="Workspace root directory")
        ]
        project: Annotated[
            str | None, Field(default=None, description="Single project name")
        ]
        projects: Annotated[
            str | None,
            Field(default=None, description="Comma-separated project names"),
        ]
        output_dir: Annotated[
            str,
            Field(
                default=f"{c.Infra.Reporting.REPORTS_DIR_NAME}/docs",
                description="Output directory for reports",
            ),
        ]

    class DocsGenerateInput(BaseModel):
        """CLI input for generate -- fields become CLI options."""

        workspace: Annotated[
            str | None, Field(default=None, description="Workspace root directory")
        ]
        project: Annotated[
            str | None, Field(default=None, description="Single project name")
        ]
        projects: Annotated[
            str | None,
            Field(default=None, description="Comma-separated project names"),
        ]
        apply: Annotated[bool, Field(default=False, description="Apply changes")]
        output_dir: Annotated[
            str,
            Field(
                default=f"{c.Infra.Reporting.REPORTS_DIR_NAME}/docs",
                description="Output directory for reports",
            ),
        ]

    class DocsValidateInput(BaseModel):
        """CLI input for validate -- fields become CLI options."""

        workspace: Annotated[
            str | None, Field(default=None, description="Workspace root directory")
        ]
        project: Annotated[
            str | None, Field(default=None, description="Single project name")
        ]
        projects: Annotated[
            str | None,
            Field(default=None, description="Comma-separated project names"),
        ]
        apply: Annotated[bool, Field(default=False, description="Apply changes")]
        check: Annotated[bool, Field(default=False, description="Enable check mode")]
        output_dir: Annotated[
            str,
            Field(
                default=f"{c.Infra.Reporting.REPORTS_DIR_NAME}/docs",
                description="Output directory for reports",
            ),
        ]

    # ── GitHub ───────────────────────────────────────────

    class GithubWorkflowsInput(BaseModel):
        """CLI input for workflows sync -- fields become CLI options."""

        workspace: Annotated[str, Field(default=".", description="Workspace root")]
        apply: Annotated[bool, Field(default=False, description="Apply changes")]
        prune: Annotated[bool, Field(default=False, description="Remove unknown files")]
        report: Annotated[
            str | None, Field(default=None, description="Output report file")
        ]

    class GithubLintInput(BaseModel):
        """CLI input for workflow lint -- fields become CLI options."""

        workspace: Annotated[str, Field(default=".", description="Workspace root")]
        strict: Annotated[
            bool,
            Field(default=False, description="Fail on strict mode warnings"),
        ]
        report: Annotated[
            str | None, Field(default=None, description="Output report file")
        ]

    class GithubPrInput(BaseModel):
        """CLI input for single-project PR management -- fields become CLI options."""

        repo_root: Annotated[str, Field(..., description="Repository root directory")]
        action: Annotated[
            str,
            Field(
                default="status",
                description="PR action (status/create/view/checks/merge/close)",
            ),
        ]
        base: Annotated[str, Field(default="main", description="Base branch")]
        head: Annotated[str | None, Field(default=None, description="Head branch")]
        number: Annotated[int | None, Field(default=None, description="PR number")]
        title: Annotated[str | None, Field(default=None, description="PR title")]
        body: Annotated[str | None, Field(default=None, description="PR body")]
        draft: Annotated[bool, Field(default=False, description="Create as draft")]
        merge_method: Annotated[
            str,
            Field(default="squash", description="Merge method (merge/squash/rebase)"),
        ]
        auto: Annotated[bool, Field(default=False, description="Auto-merge")]
        delete_branch: Annotated[
            bool, Field(default=True, description="Delete head branch on merge")
        ]
        checks_strict: Annotated[
            bool, Field(default=True, description="Fail if checks fail")
        ]
        release_on_merge: Annotated[
            bool,
            Field(default=True, description="Run release workflow on merge"),
        ]

    class GithubPrWorkspaceInput(BaseModel):
        """CLI input for workspace-wide PR management -- fields become CLI options."""

        workspace: Annotated[str, Field(default=".", description="Workspace root")]
        project: Annotated[
            str | None,
            Field(
                default=None,
                description="Project to process (comma-separated for multiple)",
            ),
        ]
        include_root: Annotated[
            bool, Field(default=False, description="Include root project")
        ]
        branch: Annotated[str, Field(default="", description="Branch name filter")]
        checkpoint: Annotated[
            bool, Field(default=True, description="Enable checkpoints")
        ]
        fail_fast: Annotated[
            bool, Field(default=True, description="Stop on first failure")
        ]
        pr_action: Annotated[str, Field(default="status", description="PR action")]
        pr_base: Annotated[str, Field(default="", description="Base branch")]
        pr_head: Annotated[str, Field(default="", description="Head branch")]
        pr_number: Annotated[int | None, Field(default=None, description="PR number")]
        pr_title: Annotated[str, Field(default="", description="PR title")]
        pr_body: Annotated[str, Field(default="", description="PR body")]
        pr_draft: Annotated[bool, Field(default=False, description="Draft PR")]
        pr_merge_method: Annotated[
            str, Field(default="squash", description="Merge method")
        ]
        pr_auto: Annotated[bool, Field(default=False, description="Auto-merge")]
        pr_delete_branch: Annotated[
            bool, Field(default=True, description="Delete branch on merge")
        ]
        pr_checks_strict: Annotated[
            bool, Field(default=True, description="Strict checks required")
        ]
        pr_release_on_merge: Annotated[
            bool, Field(default=False, description="Release on merge")
        ]

    # ── Refactor ─────────────────────────────────────────

    class RefactorCentralizeInput(BaseModel):
        """CLI input for pydantic centralization -- fields become CLI options."""

        workspace: Annotated[str, Field(default=".", description="Workspace root")]
        apply: Annotated[bool, Field(default=False, description="Apply changes")]
        normalize_remaining: Annotated[
            bool,
            Field(
                default=False,
                description="Remove remaining BaseModel/TypedDict bases in non-allowed files",
            ),
        ]

    class RefactorMigrateMroInput(BaseModel):
        """CLI input for MRO migration -- fields become CLI options."""

        workspace: Annotated[str, Field(default=".", description="Workspace root")]
        apply: Annotated[bool, Field(default=False, description="Apply changes")]
        target: Annotated[
            str,
            Field(
                default="all",
                description="Migration target scope (constants/typings/protocols/models/utilities/all)",
            ),
        ]

    class RefactorNamespaceEnforceInput(BaseModel):
        """CLI input for namespace enforcement -- fields become CLI options."""

        workspace: Annotated[str, Field(default=".", description="Workspace root")]
        apply: Annotated[bool, Field(default=False, description="Apply changes")]
        diff: Annotated[
            bool, Field(default=False, description="Show diff without applying")
        ]
        project: Annotated[
            str | None,
            Field(
                default=None,
                description="Project to process (comma-separated for multiple)",
            ),
        ]

    class RefactorUltraworkModelsInput(BaseModel):
        """CLI input for ultrawork-models -- fields become CLI options."""

        workspace: Annotated[str, Field(default=".", description="Workspace root")]
        apply: Annotated[bool, Field(default=False, description="Apply changes")]
        normalize_remaining: Annotated[
            bool,
            Field(
                default=False,
                description="Remove remaining BaseModel/TypedDict bases in non-allowed files",
            ),
        ]

    class RefactorCensusInput(BaseModel):
        """CLI input for MRO family census -- fields become CLI options."""

        workspace: Annotated[str, Field(default=".", description="Workspace root")]
        family: Annotated[
            str,
            Field(
                default="u",
                description="MRO family to census (c/t/p/m/u)",
            ),
        ]
        json_output: Annotated[
            str | None,
            Field(default=None, description="Path to write JSON report"),
        ]

    # ── Release ──────────────────────────────────────────

    class ReleaseRunInput(BaseModel):
        """CLI input for release orchestration -- fields become CLI options."""

        workspace: Annotated[
            str | None, Field(default=None, description="Workspace root directory")
        ]
        apply: Annotated[bool, Field(default=False, description="Apply changes")]
        phase: Annotated[str, Field(default="all", description="Release phase")]
        version: Annotated[str, Field(default="", description="Version string")]
        tag: Annotated[str, Field(default="", description="Git tag (e.g. v1.0.0)")]
        bump: Annotated[
            str, Field(default="", description="Bump type (major/minor/patch)")
        ]
        interactive: Annotated[
            int, Field(default=1, description="Interactive mode (1=yes, 0=no)")
        ]
        push: Annotated[bool, Field(default=False, description="Push to remote")]
        dev_suffix: Annotated[bool, Field(default=False, description="Add dev suffix")]
        next_dev: Annotated[
            bool, Field(default=False, description="Prepare next dev version")
        ]
        next_bump: Annotated[
            str,
            Field(default="minor", description="Bump type for next dev version"),
        ]
        create_branches: Annotated[
            int,
            Field(default=1, description="Create release branches (1=yes, 0=no)"),
        ]
        projects: Annotated[
            list[str] | None,
            Field(default=None, description="Project names to release"),
        ]

    # ── Validate ─────────────────────────────────────────

    class ValidateBaseMkInput(BaseModel):
        """CLI input for basemk-validate -- fields become CLI options."""

        workspace: Annotated[
            str | None, Field(default=None, description="Workspace root directory")
        ]

    class ValidateInventoryInput(BaseModel):
        """CLI input for inventory -- fields become CLI options."""

        workspace: Annotated[
            str | None, Field(default=None, description="Workspace root directory")
        ]
        output_dir: Annotated[
            str | None, Field(default=None, description="Output directory")
        ]

    class ValidatePytestDiagInput(BaseModel):
        """CLI input for pytest-diag -- fields become CLI options."""

        junit: Annotated[str, Field(..., description="JUnit XML path")]
        log: Annotated[str, Field(..., description="Pytest log path")]
        failed: Annotated[
            str | None,
            Field(default=None, description="Path to write failed cases"),
        ]
        errors: Annotated[
            str | None,
            Field(default=None, description="Path to write error traces"),
        ]
        warnings: Annotated[
            str | None,
            Field(default=None, description="Path to write warnings"),
        ]
        slowest: Annotated[
            str | None,
            Field(default=None, description="Path to write slowest entries"),
        ]
        skips: Annotated[
            str | None,
            Field(default=None, description="Path to write skipped cases"),
        ]

    class ValidateScanInput(BaseModel):
        """CLI input for scan -- fields become CLI options."""

        workspace: Annotated[
            str | None, Field(default=None, description="Workspace root directory")
        ]
        pattern: Annotated[str, Field(..., description="Regex pattern")]
        include: Annotated[
            list[str] | None, Field(default=None, description="Include glob")
        ]
        exclude: Annotated[
            list[str] | None, Field(default=None, description="Exclude glob")
        ]
        match: Annotated[
            str,
            Field(
                default=c.Infra.MatchModes.PRESENT,
                description="Violation mode (present or absent)",
            ),
        ]

    class ValidateSkillValidateInput(BaseModel):
        """CLI input for skill-validate -- fields become CLI options."""

        workspace: Annotated[
            str | None, Field(default=None, description="Workspace root directory")
        ]
        skill: Annotated[str, Field(..., description="Skill folder name")]
        mode: Annotated[
            str,
            Field(
                default=c.Infra.Modes.BASELINE,
                description="Validation mode (baseline or strict)",
            ),
        ]

    class ValidateStubValidateInput(BaseModel):
        """CLI input for stub-validate -- fields become CLI options."""

        workspace: Annotated[
            str | None, Field(default=None, description="Workspace root directory")
        ]
        project: Annotated[
            list[str] | None,
            Field(default=None, description="Project to validate"),
        ]
        all_projects: Annotated[
            bool,
            Field(default=False, description="Validate all projects", alias="all"),
        ]

    # ── Workspace ────────────────────────────────────────

    class WorkspaceDetectInput(BaseModel):
        """CLI input for workspace detection."""

        workspace: Annotated[
            str, Field(default=".", description="Workspace root directory")
        ]

    class WorkspaceSyncInput(BaseModel):
        """CLI input for base.mk sync."""

        workspace: Annotated[
            str, Field(default=".", description="Workspace root directory")
        ]
        canonical_root: Annotated[
            str, Field(default="", description="Canonical workspace root")
        ]
        apply: Annotated[
            bool,
            Field(default=False, description="Apply changes (default is dry-run)"),
        ]

    class WorkspaceOrchestrateInput(BaseModel):
        """CLI input for project orchestration."""

        verb: Annotated[str, Field(description="Make verb to execute")]
        projects: Annotated[
            str,
            Field(default="", description="Comma-separated project directories"),
        ]
        fail_fast: Annotated[
            bool, Field(default=False, description="Stop on first failure")
        ]
        make_arg: Annotated[
            str,
            Field(default="", description="Comma-separated additional make arguments"),
        ]

    class WorkspaceMigrateInput(BaseModel):
        """CLI input for workspace migration."""

        workspace: Annotated[
            str, Field(default=".", description="Workspace root directory")
        ]
        apply: Annotated[
            bool,
            Field(default=False, description="Apply changes (default is dry-run)"),
        ]

    # ── Maintenance ──────────────────────────────────────

    class MaintenanceRunInput(BaseModel):
        """CLI input for maintenance command -- fields become CLI options."""

        check: Annotated[bool, Field(default=False, description="Run in check mode")]
        verbose: Annotated[bool, Field(default=False, description="Verbose output")]
