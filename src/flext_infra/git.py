"""Public Git orchestration service for flext-infra consumers."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Annotated, override

from flext_core import r
from flext_infra import c, m, u
from flext_infra.base import s

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraGitService(s[m.Infra.GitOperationReport]):
    """Thin orchestrator over ``u.Infra`` Git primitives with one request model."""

    operation: Annotated[
        c.Infra.GitOperation, m.Field(description="Public Git service operation")
    ]
    repository: Annotated[
        Path | None, m.Field(description="Repository path; defaults to workspace_root")
    ] = None

    def _repo(self) -> Path:
        """Resolve the single repository root for this invocation."""
        return (self.repository or self.workspace_root).expanduser().resolve()

    @override
    def execute(self) -> p.Result[m.Infra.GitOperationReport]:
        """Execute the selected Git operation and return a typed report."""
        repo = self._repo()
        if self.operation == c.Infra.GitOperation.STATUS:
            status = u.Infra.git_capture(
                repo, ("status", "--porcelain", "--untracked-files=all")
            )
            if status.failure:
                return r.fail(status.error or "git status failed")
            porcelain = status.value
            return r.ok(
                m.Infra.GitOperationReport(
                    summary="status captured", primary_root=None, porcelain=porcelain
                )
            )
        if self.operation == c.Infra.GitOperation.PRIMARY_ROOT:
            primary = u.Infra.git_primary_worktree_root(repo)
            if primary.failure:
                return r.fail(primary.error or "failed to resolve primary worktree")
            return r.ok(
                m.Infra.GitOperationReport(
                    summary="primary root resolved",
                    primary_root=primary.value,
                    porcelain=None,
                )
            )
        workspace = u.Infra.git_workspace_root(repo)
        if workspace.failure:
            return r.fail(workspace.error or "failed to resolve workspace root")
        return r.ok(
            m.Infra.GitOperationReport(
                summary="workspace root resolved",
                primary_root=workspace.value,
                porcelain=None,
            )
        )


__all__: list[str] = ["FlextInfraGitService"]
