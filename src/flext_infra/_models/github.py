"""Domain models for the github subpackage."""

from __future__ import annotations

from argparse import Namespace
from collections.abc import MutableSequence
from pathlib import Path
from typing import Annotated, ClassVar

from pydantic import ConfigDict, Field

from flext_core import FlextModels
from flext_infra import c, t
from flext_infra._models.mixins import FlextInfraModelsMixins


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
            t.NonNegativeInt,
            Field(description="Elapsed time in seconds"),
        ]
        exit_code: Annotated[int, Field(description="Process exit code")]
        log_path: Annotated[
            str | None,
            Field(default=None, description="Log file path"),
        ] = None

    class PrOrchestrationResult(FlextModels.ArbitraryTypesModel):
        """Aggregated result of workspace-wide PR orchestration."""

        total: Annotated[
            t.NonNegativeInt,
            Field(description="Total repositories processed"),
        ]
        success: Annotated[t.NonNegativeInt, Field(description="Successful executions")]
        fail: Annotated[t.NonNegativeInt, Field(description="Failed executions")]
        results: t.Infra.VariadicTuple[
            FlextInfraGithubModels.PrExecutionResultModel
        ] = Field(default_factory=tuple, description="Per-repository results")

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

    class PrWorkspaceArgs(
        FlextInfraModelsMixins.GithubWorkspaceControlMixin,
        FlextInfraModelsMixins.GithubPrWorkspacePayloadMixin,
        FlextModels.ArbitraryTypesModel,
    ):
        """Parsed PR workspace arguments from CLI."""

        model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True, extra="forbid")

        pr_number: Annotated[str, Field(default="", description="PR number")] = ""

        @staticmethod
        def _bool_flag(value: t.Scalar) -> bool:
            if isinstance(value, bool):
                return value
            if isinstance(value, int):
                return value == 1
            return False

        @classmethod
        def from_cli_namespace(
            cls,
            args: Namespace,
        ) -> FlextInfraGithubModels.PrWorkspaceArgs:
            return cls.model_validate(
                {
                    "include_root": cls._bool_flag(getattr(args, "include_root", 0)),
                    "branch": str(getattr(args, "branch", "")),
                    "checkpoint": cls._bool_flag(getattr(args, "checkpoint", 1)),
                    "fail_fast": cls._bool_flag(getattr(args, "fail_fast", 1)),
                    "pr_action": str(getattr(args, "pr_action", "status")),
                    "pr_base": str(getattr(args, "pr_base", "")),
                    "pr_head": str(getattr(args, "pr_head", "")),
                    "pr_number": str(getattr(args, "pr_number", "") or ""),
                    "pr_title": str(getattr(args, "pr_title", "")),
                    "pr_body": str(getattr(args, "pr_body", "")),
                    "pr_draft": cls._bool_flag(getattr(args, "pr_draft", 0)),
                    "pr_merge_method": str(
                        getattr(args, "pr_merge_method", "squash"),
                    ),
                    "pr_auto": cls._bool_flag(getattr(args, "pr_auto", 0)),
                    "pr_delete_branch": cls._bool_flag(
                        getattr(args, "pr_delete_branch", 1),
                    ),
                    "pr_checks_strict": cls._bool_flag(
                        getattr(args, "pr_checks_strict", 1),
                    ),
                    "pr_release_on_merge": cls._bool_flag(
                        getattr(args, "pr_release_on_merge", 0),
                    ),
                },
            )

        def as_orchestrate_dict(self) -> t.StrMapping:
            return {
                c.Infra.ReportKeys.ACTION: self.pr_action,
                "base": self.pr_base,
                "head": self.pr_head,
                "number": self.pr_number,
                "title": self.pr_title,
                "body": self.pr_body,
                "draft": "1" if self.pr_draft else "0",
                "merge_method": self.pr_merge_method,
                "auto": "1" if self.pr_auto else "0",
                "delete_branch": "1" if self.pr_delete_branch else "0",
                "checks_strict": "1" if self.pr_checks_strict else "0",
                "release_on_merge": "1" if self.pr_release_on_merge else "0",
            }

    class SyncOperation(
        FlextInfraModelsMixins.ProjectNameMixin,
        FlextModels.ArbitraryTypesModel,
    ):
        """Describe one workflow synchronization operation."""

        model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True, extra="forbid")
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

    class GithubSyncContext(
        FlextInfraModelsMixins.ProjectNameFieldMixin,
        FlextModels.ArbitraryTypesModel,
    ):
        """Bundled parameters for the workflow-sync call chain."""

        project_root: Annotated[Path, Field(description="Project root path")]
        rendered_template: Annotated[str, Field(description="Rendered workflow body")]
        apply: Annotated[bool, Field(description="Whether writes are enabled")]
        prune: Annotated[bool, Field(description="Whether pruning is enabled")]

        @property
        def workflows_dir(self) -> Path:
            return self.project_root / ".github" / "workflows"

        @property
        def ci_destination(self) -> Path:
            return self.workflows_dir / "ci.yml"

    class GithubPrRepoContext(
        FlextInfraModelsMixins.WorkspaceRootPathMixin,
        FlextModels.ArbitraryTypesModel,
    ):
        """Bundled parameters for the PR-per-repo processing chain."""

        effective_args: Annotated[
            t.StrMapping,
            Field(description="Effective PR orchestration arguments"),
        ]
        branch: Annotated[str, Field(description="Branch override")]
        checkpoint: Annotated[
            bool, Field(description="Whether checkpointing is enabled")
        ]
        results: Annotated[
            MutableSequence[FlextInfraGithubModels.PrExecutionResultModel],
            Field(description="Accumulated PR execution results"),
        ] = Field(description="Accumulated PR execution results")

    class WorkflowSyncParams(FlextModels.ContractModel):
        """Bundled parameters for github_sync_workspace_workflows."""

        source_workflow: Annotated[
            Path | None,
            Field(default=None, description="Override source workflow path"),
        ] = None
        report_path: Annotated[
            Path | None,
            Field(default=None, description="Output report file path"),
        ] = None
        apply: Annotated[
            bool,
            Field(default=False, description="Apply changes"),
        ] = False
        prune: Annotated[
            bool,
            Field(default=False, description="Remove non-canonical workflows"),
        ] = False

    class PrOrchestrateParams(
        FlextInfraModelsMixins.GithubWorkspaceControlMixin,
        FlextModels.ContractModel,
    ):
        """Bundled parameters for github_pr_orchestrate."""

        projects: Annotated[
            t.StrSequence | None,
            Field(default=None, description="Project filter list"),
        ] = None
        pr_args: Annotated[
            t.StrMapping | None,
            Field(default=None, description="PR argument overrides"),
        ] = None


__all__ = ["FlextInfraGithubModels"]
