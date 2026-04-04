"""CLI input models for operations commands (github, refactor, release, validate, workspace).

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

from pydantic import Field

from flext_infra import FlextInfraModelsCliInputsCodegen, c, t


class FlextInfraModelsCliInputsOps:
    """Namespaced CLI input models for github, refactor, release, validate, and workspace."""

    class GithubReportMixin(FlextInfraModelsCliInputsCodegen.CliInputBase):
        report: Annotated[
            str | None,
            Field(default=None, description="Output report file"),
        ] = None

        @property
        def report_path(self) -> Path | None:
            """Return the resolved report path when provided."""
            return Path(self.report).resolve() if self.report else None

    class GithubWorkflowsInput(
        FlextInfraModelsCliInputsCodegen.ApplyMixin,
        GithubReportMixin,
    ):
        prune: Annotated[
            bool,
            Field(default=False, description="Remove unknown files"),
        ] = False

    class GithubLintInput(GithubReportMixin):
        strict: Annotated[
            bool,
            Field(default=False, description="Fail on strict mode warnings"),
        ] = False

    class GithubPrInput(FlextInfraModelsCliInputsCodegen.CliInputBase):
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

        @property
        def repo_root_path(self) -> Path:
            """Return the resolved repository root path."""
            return Path(self.repo_root).resolve()

    class GithubPrWorkspaceInput(FlextInfraModelsCliInputsCodegen.CliInputBase):
        project: Annotated[
            t.StrSequence,
            Field(
                default_factory=list,
                description="Project to process; repeat --projects NAME as needed",
            ),
        ] = Field(
            default_factory=list,
            description="Project to process; repeat --projects NAME as needed",
        )
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

    class RefactorCentralizeInput(
        FlextInfraModelsCliInputsCodegen.ApplyMixin,
        FlextInfraModelsCliInputsCodegen.CliInputBase,
    ):
        normalize_remaining: Annotated[
            bool,
            Field(
                default=False,
                description="Remove remaining BaseModel/TypedDict bases in non-allowed files",
            ),
        ] = False

    class RefactorMigrateMroInput(
        FlextInfraModelsCliInputsCodegen.ApplyMixin,
        FlextInfraModelsCliInputsCodegen.CliInputBase,
    ):
        target: Annotated[
            str,
            Field(
                default="all",
                description="Migration target scope (constants/typings/protocols/models/utilities/all)",
            ),
        ] = "all"

    class RefactorNamespaceEnforceInput(
        FlextInfraModelsCliInputsCodegen.ApplyMixin,
        FlextInfraModelsCliInputsCodegen.CliInputBase,
    ):
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

        @property
        def project_names(self) -> list[str] | None:
            """Return normalized project filters when provided."""
            if self.project is None:
                return None
            values = [
                value.strip() for value in self.project.split(",") if value.strip()
            ]
            return values or None

    class RefactorMigrateRuntimeAliasImportsInput(
        FlextInfraModelsCliInputsCodegen.ApplyMixin,
        FlextInfraModelsCliInputsCodegen.CliInputBase,
    ):
        aliases: Annotated[
            str,
            Field(
                default="r,s",
                description="Comma-separated runtime aliases to migrate to local MRO imports",
            ),
        ] = "r,s"
        project: Annotated[
            str | None,
            Field(
                default=None,
                description="Project to process (comma-separated for multiple)",
            ),
        ] = None

        @property
        def alias_names(self) -> list[str]:
            """Return normalized runtime alias names."""
            return [alias.strip() for alias in self.aliases.split(",") if alias.strip()]

        @property
        def project_names(self) -> list[str] | None:
            """Return normalized project filters when provided."""
            if self.project is None:
                return None
            values = [
                value.strip() for value in self.project.split(",") if value.strip()
            ]
            return values or None

    class RefactorUltraworkModelsInput(
        FlextInfraModelsCliInputsCodegen.ApplyMixin,
        FlextInfraModelsCliInputsCodegen.CliInputBase,
    ):
        normalize_remaining: Annotated[
            bool,
            Field(
                default=False,
                description="Remove remaining BaseModel/TypedDict bases in non-allowed files",
            ),
        ] = False

    class RefactorCensusInput(FlextInfraModelsCliInputsCodegen.CliInputBase):
        family: Annotated[
            str,
            Field(default="u", description="MRO family to census (c/t/p/m/u)"),
        ] = "u"
        json_output: Annotated[
            str | None,
            Field(default=None, description="Path to write JSON report"),
        ] = None

        @property
        def json_output_path(self) -> Path | None:
            """Return the resolved JSON export path when provided."""
            return Path(self.json_output).resolve() if self.json_output else None

    class ReleaseRunInput(
        FlextInfraModelsCliInputsCodegen.ApplyMixin,
        FlextInfraModelsCliInputsCodegen.CliInputBase,
    ):
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
            t.StrSequence | None,
            Field(default=None, description="Project names to release"),
        ] = None

        @property
        def phase_names(self) -> list[str]:
            """Return the normalized phase sequence for release execution."""
            if self.phase == "all":
                return [
                    c.Infra.Verbs.VALIDATE,
                    c.Infra.VERSION,
                    c.Infra.Directories.BUILD,
                    "publish",
                ]
            return [part.strip() for part in self.phase.split(",") if part.strip()]

    class ValidateBaseMkInput(FlextInfraModelsCliInputsCodegen.CliInputBase):
        """CLI input for basemk-validate."""

    class ValidateInventoryInput(FlextInfraModelsCliInputsCodegen.CliInputBase):
        """CLI input for inventory."""

        output_dir: Annotated[
            str | None,
            Field(default=None, description="Output directory"),
        ] = None

        @property
        def output_dir_path(self) -> Path | None:
            """Return the resolved output directory when provided."""
            return Path(self.output_dir).resolve() if self.output_dir else None

    class ValidatePytestDiagInput(FlextInfraModelsCliInputsCodegen.CliInputBase):
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

        @property
        def junit_path(self) -> Path:
            """Return the resolved JUnit XML path."""
            return Path(self.junit).resolve()

        @property
        def log_path(self) -> Path:
            """Return the resolved pytest log path."""
            return Path(self.log).resolve()

    class ValidateScanInput(FlextInfraModelsCliInputsCodegen.CliInputBase):
        """CLI input for scan."""

        pattern: Annotated[str, Field(..., description="Regex pattern")]
        include: Annotated[
            t.StrSequence | None,
            Field(default=None, description="Include glob"),
        ] = None
        exclude: Annotated[
            t.StrSequence | None,
            Field(default=None, description="Exclude glob"),
        ] = None
        match: Annotated[
            str,
            Field(
                default=c.Infra.MatchModes.PRESENT,
                description="Violation mode (present or absent)",
            ),
        ] = c.Infra.MatchModes.PRESENT

        @property
        def include_patterns(self) -> list[str]:
            """Return include globs as a concrete list."""
            return list(self.include or ())

        @property
        def exclude_patterns(self) -> list[str]:
            """Return exclude globs as a concrete list."""
            return list(self.exclude or ())

    class ValidateSkillValidateInput(FlextInfraModelsCliInputsCodegen.CliInputBase):
        """CLI input for skill-validate."""

        skill: Annotated[str, Field(..., description="Skill folder name")]
        mode: Annotated[
            str,
            Field(
                default=c.Infra.Modes.BASELINE,
                description="Validation mode (baseline or strict)",
            ),
        ] = c.Infra.Modes.BASELINE

    class ValidateStubValidateInput(FlextInfraModelsCliInputsCodegen.CliInputBase):
        """CLI input for stub-validate."""

        project: Annotated[
            t.StrSequence | None,
            Field(default=None, description="Project to validate"),
        ] = None
        all_projects: Annotated[
            bool,
            Field(default=False, description="Validate all projects", alias="all"),
        ] = False

        @property
        def project_dirs(self) -> list[Path] | None:
            """Return resolved project directories for targeted validation."""
            if self.all_projects or not self.project:
                return None
            return [self.workspace_path / name for name in self.project]

    class WorkspaceDetectInput(FlextInfraModelsCliInputsCodegen.CliInputBase):
        """CLI input for workspace detection."""

    class WorkspaceSyncInput(
        FlextInfraModelsCliInputsCodegen.ApplyMixin,
        FlextInfraModelsCliInputsCodegen.CliInputBase,
    ):
        """CLI input for base.mk sync."""

        canonical_root: Annotated[
            str,
            Field(default="", description="Canonical workspace root"),
        ] = ""

        @property
        def canonical_root_path(self) -> Path | None:
            """Return the resolved canonical root when provided."""
            return Path(self.canonical_root).resolve() if self.canonical_root else None

    class WorkspaceOrchestrateInput(FlextInfraModelsCliInputsCodegen.CliInputBase):
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
            t.StrSequence,
            Field(
                default_factory=list,
                description="Additional make arguments; repeat --make-arg KEY=VALUE",
            ),
        ] = Field(
            default_factory=list,
            description="Additional make arguments; repeat --make-arg KEY=VALUE",
        )

        @property
        def project_names(self) -> list[str]:
            """Return normalized project names from comma/space-separated input."""
            raw_projects = self.projects.replace(",", " ")
            return [
                project.strip() for project in raw_projects.split() if project.strip()
            ]

        @property
        def make_args(self) -> list[str]:
            """Return normalized make arguments without blank entries."""
            return [make_arg.strip() for make_arg in self.make_arg if make_arg.strip()]

    class WorkspaceMigrateInput(
        FlextInfraModelsCliInputsCodegen.ApplyMixin,
        FlextInfraModelsCliInputsCodegen.CliInputBase,
    ):
        dry_run: Annotated[
            bool,
            Field(default=False, description="Preview changes without writing"),
        ] = False

    class MaintenanceRunInput(FlextInfraModelsCliInputsCodegen.CliInputBase):
        """CLI input for maintenance command."""

        check: Annotated[
            bool,
            Field(default=False, description="Run in check mode"),
        ] = False
        verbose: Annotated[
            bool,
            Field(default=False, description="Verbose output"),
        ] = False


__all__ = ["FlextInfraModelsCliInputsOps"]
