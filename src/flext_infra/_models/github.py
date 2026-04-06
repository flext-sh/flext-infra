"""Domain models for the github subpackage."""

from __future__ import annotations

from collections.abc import MutableSequence
from pathlib import Path
from typing import Annotated

from pydantic import Field

from flext_core import FlextModels
from flext_infra import FlextInfraModelsCliInputsOps, FlextInfraModelsMixins, t


class FlextInfraGithubModels:
    """Models for GitHub PR orchestration and repository management."""

    class GithubPullRequestOutcome(FlextModels.ArbitraryTypesModel):
        """Outcome of a single pull-request command on one repository."""

        display: Annotated[
            t.NonEmptyStr,
            Field(description="Repository display name"),
        ]
        status: Annotated[t.NonEmptyStr, Field(description="Execution status")]
        elapsed: Annotated[
            t.NonNegativeInt,
            Field(description="Elapsed time in seconds"),
        ]
        exit_code: Annotated[int, Field(description="Process exit code")]
        log_path: Annotated[
            str | None,
            Field(default=None, description="Log file path"),
        ] = None

        @property
        def message(self) -> str:
            """Return the CLI-facing success or failure summary."""
            return f"{self.display}: {self.status} (exit={self.exit_code})"

    class GithubPullRequestWorkspaceReport(FlextModels.ArbitraryTypesModel):
        """Aggregated report for workspace-wide pull-request execution."""

        total: Annotated[
            t.NonNegativeInt,
            Field(description="Total repositories processed"),
        ]
        success: Annotated[t.NonNegativeInt, Field(description="Successful executions")]
        fail: Annotated[t.NonNegativeInt, Field(description="Failed executions")]
        outcomes: t.Infra.VariadicTuple[
            FlextInfraGithubModels.GithubPullRequestOutcome
        ] = Field(default_factory=tuple, description="Per-repository outcomes")

        @property
        def message(self) -> str:
            """Return the CLI-facing workspace summary."""
            return f"workspace PR run: {self.success}/{self.total} successful"

    class RepoUrls(FlextModels.ArbitraryTypesModel):
        """Repository URL pair with SSH and HTTPS variants."""

        ssh_url: Annotated[str, Field(default="", description="SSH clone URL")]
        https_url: Annotated[str, Field(default="", description="HTTPS clone URL")]

    class GithubWorkflowLintOutcome(FlextModels.ArbitraryTypesModel):
        """Outcome payload for workflow lint execution."""

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

        @property
        def message(self) -> str:
            """Return the CLI-facing lint summary."""
            if self.status == "ok":
                return "workflow lint passed"
            if self.status == "skipped" and self.reason:
                return f"workflow lint skipped: {self.reason}"
            if self.detail:
                return f"workflow lint failed: {self.detail}"
            if self.reason:
                return f"workflow lint failed: {self.reason}"
            return "workflow lint failed"

    class GithubWorkflowSyncOperation(
        FlextInfraModelsMixins.ProjectNameMixin,
        FlextModels.ArbitraryTypesModel,
    ):
        """Describe one workflow synchronization operation."""

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

    class GithubWorkflowSyncReport(FlextModels.ArbitraryTypesModel):
        """Structured report for a workflow synchronization request."""

        mode: Annotated[str, Field(description="Execution mode")]
        summary: Annotated[
            t.ContainerMapping,
            Field(description="Count of operations by action"),
        ]
        operations: t.Infra.VariadicTuple[
            FlextInfraGithubModels.GithubWorkflowSyncOperation
        ] = Field(default_factory=tuple, description="Workflow operations")

        @classmethod
        def from_operations(
            cls,
            *,
            apply: bool,
            operations: MutableSequence[
                FlextInfraGithubModels.GithubWorkflowSyncOperation
            ],
        ) -> FlextInfraGithubModels.GithubWorkflowSyncReport:
            """Build a typed report from collected operations."""
            summary: dict[str, int] = {}
            for operation in operations:
                summary[operation.action] = summary.get(operation.action, 0) + 1
            return cls(
                mode="apply" if apply else "dry-run",
                summary=summary,
                operations=tuple(operations),
            )

        @property
        def message(self) -> str:
            """Return the CLI-facing sync summary."""
            return f"github workflows {self.mode}: {len(self.operations)} operations"

    class GithubWorkflowSyncContext(
        FlextInfraModelsMixins.ProjectNameFieldMixin,
        FlextModels.ArbitraryTypesModel,
    ):
        """Resolved context for syncing workflows in one project."""

        project_root: Annotated[Path, Field(description="Project root path")]
        rendered_template: Annotated[str, Field(description="Rendered workflow body")]
        request: Annotated[
            FlextInfraModelsCliInputsOps.GithubWorkflowSyncRequest,
            Field(description="Original sync request"),
        ]

        @property
        def workflows_dir(self) -> Path:
            return self.project_root / ".github" / "workflows"

        @property
        def ci_destination(self) -> Path:
            return self.workflows_dir / "ci.yml"

        @property
        def apply(self) -> bool:
            return self.request.apply

        @property
        def prune(self) -> bool:
            return self.request.prune

    class GithubPullRequestWorkspaceContext(
        FlextInfraModelsMixins.WorkspaceRootPathMixin,
        FlextModels.ArbitraryTypesModel,
    ):
        """Resolved context for workspace-wide pull-request execution."""

        request: Annotated[
            FlextInfraModelsCliInputsOps.GithubPullRequestWorkspaceRequest,
            Field(description="Original workspace pull-request request"),
        ]
        outcomes: Annotated[
            MutableSequence[FlextInfraGithubModels.GithubPullRequestOutcome],
            Field(description="Accumulated pull-request outcomes"),
        ] = Field(description="Accumulated pull-request outcomes")


__all__ = ["FlextInfraGithubModels"]
