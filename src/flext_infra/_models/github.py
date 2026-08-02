"""Domain models for the github subpackage."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

from flext_cli import m
from flext_infra import t
from flext_infra._models.mixins import FlextInfraModelsMixins as mm


class FlextInfraModelsGithub:
    """Models for GitHub PR orchestration and repository management."""

    class GithubPullRequestRequest(
        mm.GithubPullRequestFieldsMixin, mm.WriteMixin, m.ContractModel
    ):
        """CLI/service request for a single-repository PR action."""

        repo_root: Annotated[str, m.Field(..., description="Repository root directory")]

        @property
        def repo_root_path(self) -> Path:
            """Resolved repository root path."""
            return Path(self.repo_root).resolve()

    class GithubPullRequestWorkspaceRequest(
        mm.WorkspaceCliRequestMixin,
        mm.GithubPullRequestFieldsMixin,
        mm.WriteMixin,
        m.ContractModel,
    ):
        """CLI/service request for workspace-wide PR automation."""

    class GithubPullRequestOutcome(m.ArbitraryTypesModel):
        """Outcome of a single pull-request command on one repository."""

        display: Annotated[
            t.NonEmptyStr, m.Field(description="Repository display name")
        ]
        status: Annotated[t.NonEmptyStr, m.Field(description="Execution status")]
        elapsed: Annotated[
            t.NonNegativeInt, m.Field(description="Elapsed time in seconds")
        ]
        exit_code: Annotated[int, m.Field(description="Process exit code")]
        log_path: Annotated[str | None, m.Field(description="Log file path")] = None

        @property
        def message(self) -> str:
            """CLI-facing success or failure summary."""
            return f"{self.display}: {self.status} (exit={self.exit_code})"

    class GithubPullRequestWorkspaceReport(m.ArbitraryTypesModel):
        """Aggregated report for workspace-wide pull-request execution."""

        total: Annotated[
            t.NonNegativeInt, m.Field(description="Total repositories processed")
        ]
        success: Annotated[
            t.NonNegativeInt, m.Field(description="Successful executions")
        ]
        fail: Annotated[t.NonNegativeInt, m.Field(description="Failed executions")]
        outcomes: t.VariadicTuple[FlextInfraModelsGithub.GithubPullRequestOutcome] = (
            m.Field(default_factory=tuple, description="Per-repository outcomes")
        )

        @property
        def message(self) -> str:
            """CLI-facing workspace summary."""
            return f"workspace PR run: {self.success}/{self.total} successful"

    class RepoUrls(m.ArbitraryTypesModel):
        """Repository URL pair with SSH and HTTPS variants."""

        ssh_url: Annotated[str, m.Field(description="SSH clone URL")] = ""
        https_url: Annotated[str, m.Field(description="HTTPS clone URL")] = ""

    class GithubPullRequestWorkspaceContext(
        mm.WorkspaceRootPathMixin, m.ArbitraryTypesModel
    ):
        """Resolved context for workspace-wide pull-request execution."""

        request: Annotated[
            FlextInfraModelsGithub.GithubPullRequestWorkspaceRequest,
            m.Field(description="Original workspace pull-request request"),
        ]
        outcomes: Annotated[
            t.MutableSequenceOf[FlextInfraModelsGithub.GithubPullRequestOutcome],
            m.Field(description="Accumulated pull-request outcomes"),
        ] = m.Field(description="Accumulated pull-request outcomes")


__all__: list[str] = ["FlextInfraModelsGithub"]
