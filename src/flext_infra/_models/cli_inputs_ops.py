"""CLI input models for operations commands (github, refactor, release, validate, workspace).

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

from pydantic import Field

from flext_core import FlextModels
from flext_infra import FlextInfraModelsMixins, c, t


class FlextInfraModelsCliInputsOps:
    """Namespaced CLI input models for github, refactor, release, validate, and workspace."""

    class GithubWorkflowSyncRequest(
        FlextInfraModelsMixins.ReportPathMixin,
        FlextModels.ContractModel,
    ):
        prune: Annotated[
            bool,
            Field(default=False, description="Remove unknown files"),
        ] = False

    class GithubWorkflowLintRequest(
        FlextInfraModelsMixins.ReportPathMixin,
        FlextModels.ContractModel,
    ):
        strict: Annotated[
            bool,
            Field(default=False, description="Fail on strict mode warnings"),
        ] = False

    class GithubPullRequestRequest(
        FlextInfraModelsMixins.GithubPullRequestFieldsMixin,
        FlextInfraModelsMixins.CliInputBase,
        FlextModels.ContractModel,
    ):
        repo_root: Annotated[str, Field(..., description="Repository root directory")]

        @property
        def repo_root_path(self) -> Path:
            """Return the resolved repository root path."""
            return Path(self.repo_root).resolve()

    class GithubPullRequestWorkspaceRequest(
        FlextInfraModelsMixins.GithubWorkspaceCliRequestMixin,
        FlextInfraModelsMixins.GithubPullRequestFieldsMixin,
        FlextInfraModelsMixins.ProjectSelectionMixin,
        FlextInfraModelsMixins.CliInputBase,
        FlextModels.ContractModel,
    ):
        """Request for running a pull-request action across workspace projects."""

    class RefactorCentralizeInput(
        FlextInfraModelsMixins.CliInputBase,
        FlextModels.ContractModel,
    ):
        normalize_remaining: Annotated[
            bool,
            Field(
                default=False,
                description="Remove remaining BaseModel/TypedDict bases in non-allowed files",
            ),
        ] = False

    class RefactorMigrateMroInput(
        FlextInfraModelsMixins.CliInputBase,
        FlextModels.ContractModel,
    ):
        target: Annotated[
            str,
            Field(
                default="all",
                description="Migration target scope (constants/typings/protocols/models/utilities/all)",
            ),
        ] = "all"

    class RefactorNamespaceEnforceInput(
        FlextInfraModelsMixins.ProjectSelectionMixin,
        FlextInfraModelsMixins.CliInputBase,
        FlextModels.ContractModel,
    ):
        diff: Annotated[
            bool,
            Field(default=False, description="Show diff without applying"),
        ] = False

    class RefactorMigrateRuntimeAliasImportsInput(
        FlextInfraModelsMixins.AliasSelectionMixin,
        FlextInfraModelsMixins.ProjectSelectionMixin,
        FlextInfraModelsMixins.CliInputBase,
        FlextModels.ContractModel,
    ):
        """CLI input for runtime alias migration."""

    class RefactorUltraworkModelsInput(
        FlextInfraModelsMixins.CliInputBase,
        FlextModels.ContractModel,
    ):
        normalize_remaining: Annotated[
            bool,
            Field(
                default=False,
                description="Remove remaining BaseModel/TypedDict bases in non-allowed files",
            ),
        ] = False

    class RefactorCensusInput(
        FlextInfraModelsMixins.JsonOutputPathMixin,
        FlextModels.ContractModel,
    ):
        family: Annotated[
            str,
            Field(default="u", description="MRO family to census (c/t/p/m/u)"),
        ] = "u"

    class ReleaseRunInput(
        FlextInfraModelsMixins.ReleaseVersionTagMixin,
        FlextInfraModelsMixins.ReleaseAutomationMixin,
        FlextInfraModelsMixins.ReleasePhaseMixin,
        FlextInfraModelsMixins.ProjectSelectionMixin,
        FlextInfraModelsMixins.CliInputBase,
        FlextModels.ContractModel,
    ):
        bump: Annotated[
            str,
            Field(default="", description="Bump type (major/minor/patch)"),
        ] = ""
        interactive: Annotated[
            int,
            Field(default=1, description="Interactive mode (1=yes, 0=no)"),
        ] = 1
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

    class ValidateBaseMkInput(
        FlextInfraModelsMixins.CliInputBase,
        FlextModels.ContractModel,
    ):
        """CLI input for basemk-validate."""

    class ValidateInventoryInput(
        FlextInfraModelsMixins.OutputDirPathMixin,
        FlextModels.ContractModel,
    ):
        """CLI input for inventory."""

    class ValidatePytestDiagInput(
        FlextInfraModelsMixins.CliInputBase,
        FlextModels.ContractModel,
    ):
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

    class ValidateScanInput(
        FlextInfraModelsMixins.CliInputBase,
        FlextModels.ContractModel,
    ):
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
        def include_patterns(self) -> t.StrSequence:
            """Return include globs as a concrete list."""
            return list(self.include or ())

        @property
        def exclude_patterns(self) -> t.StrSequence:
            """Return exclude globs as a concrete list."""
            return list(self.exclude or ())

    class ValidateSkillValidateInput(
        FlextInfraModelsMixins.CliInputBase,
        FlextModels.ContractModel,
    ):
        """CLI input for skill-validate."""

        skill: Annotated[str, Field(..., description="Skill folder name")]
        mode: Annotated[
            str,
            Field(
                default=c.Infra.Modes.BASELINE,
                description="Validation mode (baseline or strict)",
            ),
        ] = c.Infra.Modes.BASELINE

    class ValidateStubValidateInput(
        FlextInfraModelsMixins.ProjectSelectionMixin,
        FlextInfraModelsMixins.CliInputBase,
        FlextModels.ContractModel,
    ):
        """CLI input for stub-validate."""

        all_projects: Annotated[
            bool,
            Field(default=False, description="Validate all projects", alias="all"),
        ] = False

        @property
        def project_dirs(self) -> list[Path] | None:
            """Return resolved project directories for targeted validation."""
            names = self.project_names
            if self.all_projects or not names:
                return None
            return [self.workspace_path / name for name in names]

    class WorkspaceDetectInput(
        FlextInfraModelsMixins.CliInputBase,
        FlextModels.ContractModel,
    ):
        """CLI input for workspace detection."""

    class WorkspaceSyncInput(
        FlextInfraModelsMixins.CanonicalRootMixin,
        FlextInfraModelsMixins.CliInputBase,
        FlextModels.ContractModel,
    ):
        """CLI input for base.mk sync."""

    class WorkspaceOrchestrateInput(
        FlextInfraModelsMixins.MakeArgMixin,
        FlextInfraModelsMixins.ProjectSelectionMixin,
        FlextInfraModelsMixins.CliInputBase,
        FlextModels.ContractModel,
    ):
        """CLI input for project orchestration."""

        verb: Annotated[str, Field(description="Make verb to execute")]
        fail_fast: Annotated[
            bool,
            Field(default=False, description="Stop on first failure"),
        ] = False

    class WorkspaceMigrateInput(
        FlextInfraModelsMixins.CliInputBase,
        FlextModels.ContractModel,
    ):
        dry_run: Annotated[
            bool,
            Field(default=False, description="Preview changes without writing"),
        ] = False


__all__ = ["FlextInfraModelsCliInputsOps"]
