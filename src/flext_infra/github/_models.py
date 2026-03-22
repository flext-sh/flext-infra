"""Domain models for the github subpackage."""

from __future__ import annotations

from typing import Annotated

from pydantic import ConfigDict, Field

from flext_core import FlextModels
from flext_infra import t


class FlextInfraGithubModels:
    """Models for GitHub PR orchestration and repository management."""

    class PrExecutionResultModel(FlextModels.ArbitraryTypesModel):
        """Result of a single PR operation on a repository."""

        display: Annotated[
            t.NonEmptyStr,
            Field(description="Repository display name"),
        ]
        status: Annotated[t.NonEmptyStr, Field(description="Execution status")]
        elapsed: Annotated[
            t.NonNegativeInt, Field(description="Elapsed time in seconds")
        ]
        exit_code: Annotated[int, Field(description="Process exit code")]
        log_path: Annotated[
            str | None,
            Field(default=None, description="Log file path"),
        ] = None

    # Alias for backward compatibility
    PrExecutionResult = PrExecutionResultModel

    class PrOrchestrationResult(FlextModels.ArbitraryTypesModel):
        """Aggregated result of workspace-wide PR orchestration."""

        total: Annotated[
            t.NonNegativeInt, Field(description="Total repositories processed")
        ]
        success: Annotated[t.NonNegativeInt, Field(description="Successful executions")]
        fail: Annotated[t.NonNegativeInt, Field(description="Failed executions")]
        results: Annotated[
            tuple[FlextInfraGithubModels._PrExecutionResultModel, ...],
            Field(
                default_factory=tuple,
                description="Per-repository results",
            ),
        ] = Field(default_factory=tuple)

    class RepoUrls(FlextModels.ArbitraryTypesModel):
        """Repository URL pair with SSH and HTTPS variants."""

        ssh_url: Annotated[str, Field(default="", description="SSH clone URL")]
        https_url: Annotated[str, Field(default="", description="HTTPS clone URL")]

    class WorkflowLintResult(FlextModels.ArbitraryTypesModel):
        """Structured result payload for workflow lint execution."""

        status: Annotated[t.NonEmptyStr, Field(description="Lint status")]
        reason: Annotated[
            str | None,
            Field(default=None, description="Skip reason"),
        ] = None
        detail: Annotated[
            str | None,
            Field(default=None, description="Failure detail"),
        ] = None
        exit_code: Annotated[
            int | None,
            Field(default=None, description="Process exit code"),
        ] = None
        stdout: Annotated[
            str | None,
            Field(default=None, description="Captured stdout"),
        ] = None
        stderr: Annotated[
            str | None,
            Field(default=None, description="Captured stderr"),
        ] = None

    class PrWorkspaceArgs(FlextModels.ArbitraryTypesModel):
        """Parsed PR workspace arguments from CLI."""

        model_config = ConfigDict(frozen=True, extra="forbid")

        include_root: Annotated[
            bool,
            Field(default=True, description="Include root project"),
        ]
        branch: Annotated[str, Field(default="", description="Branch name filter")]
        checkpoint: Annotated[
            bool,
            Field(default=True, description="Enable checkpoints"),
        ]
        fail_fast: Annotated[
            bool,
            Field(default=False, description="Stop on first failure"),
        ]
        pr_action: Annotated[str, Field(default="status", description="PR action")]
        pr_base: Annotated[str, Field(default="main", description="Base branch")]
        pr_head: Annotated[str, Field(default="", description="Head branch")]
        pr_number: Annotated[str, Field(default="", description="PR number")]
        pr_title: Annotated[str, Field(default="", description="PR title")]
        pr_body: Annotated[str, Field(default="", description="PR body")]
        pr_draft: Annotated[bool, Field(default=False, description="Draft PR")]
        pr_merge_method: Annotated[
            str,
            Field(default="squash", description="Merge method"),
        ]
        pr_auto: Annotated[bool, Field(default=False, description="Auto-merge")]
        pr_delete_branch: Annotated[
            bool,
            Field(default=False, description="Delete branch on merge"),
        ]
        pr_checks_strict: Annotated[
            bool,
            Field(default=False, description="Strict checks required"),
        ]
        pr_release_on_merge: Annotated[
            bool,
            Field(default=True, description="Release on merge"),
        ]

    class SyncOperation(FlextModels.ArbitraryTypesModel):
        """Describe one workflow synchronization operation."""

        model_config = ConfigDict(frozen=True, extra="forbid")

        project: Annotated[str, Field(..., description="Project name.")]
        path: Annotated[
            str,
            Field(..., description="File path relative to project root."),
        ]
        action: Annotated[
            str,
            Field(
                ...,
                description="Sync action (create, update, noop, prune).",
            ),
        ]
        reason: Annotated[str, Field(..., description="Reason for the action.")]


__all__ = ["FlextInfraGithubModels"]
