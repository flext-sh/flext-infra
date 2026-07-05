"""Multi-project orchestration service."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, override

from flext_core import r
from flext_infra.base_selection import FlextInfraProjectSelectionServiceBase
from flext_infra.constants import c
from flext_infra.models import m
from flext_infra.typings import t
from flext_infra.utilities import u
from flext_infra.workspace._orchestrator_discovery import (
    FlextInfraWorkspaceOrchestratorDiscoveryMixin,
)
from flext_infra.workspace._orchestrator_execution import (
    FlextInfraWorkspaceOrchestratorExecutionMixin,
)

if TYPE_CHECKING:
    from flext_infra.protocols import p


class FlextInfraOrchestratorService(
    FlextInfraProjectSelectionServiceBase[bool],
    FlextInfraWorkspaceOrchestratorDiscoveryMixin,
    FlextInfraWorkspaceOrchestratorExecutionMixin,
):
    """Infrastructure service for multi-project make orchestration."""

    verb: Annotated[str, m.Field(description="Make verb to execute")]
    fail_fast: Annotated[bool, m.Field(description="Stop on first failure")] = False
    make_arg: Annotated[
        t.StrSequence,
        m.Field(
            default_factory=tuple,
            description="Additional arguments passed to each make invocation.",
        ),
    ] = m.Field(default_factory=tuple)

    @property
    def make_args(self) -> t.StrSequence:
        """Normalized make arguments."""
        return u.Infra.normalize_make_args(self.make_arg)

    @override
    def execute(self) -> p.Result[bool]:
        """Execute the workspace-orchestrate CLI flow."""
        allowed_verbs = c.Infra.ORCHESTRATED_PROJECT_VERBS
        if self.verb not in allowed_verbs:
            allowed = ", ".join(allowed_verbs)
            return r[bool].fail(
                f"unsupported orchestrate verb '{self.verb}' (allowed: {allowed})",
            )

        resolved_projects = self._resolved_projects()
        if resolved_projects.failure:
            return r[bool].fail(resolved_projects.error or "project resolution failed")

        projects = resolved_projects.value
        if not projects:
            return r[bool].fail("no projects discovered")

        workspace_root = self.root
        prepare_result = self._prepare_projects(
            projects,
            workspace_root=workspace_root,
        )
        if prepare_result.failure:
            return prepare_result

        orchestrate_result = self.orchestrate(
            projects=[
                self._project_target(project, workspace_root=workspace_root)
                for project in projects
            ],
            verb=self.verb,
            fail_fast=self.fail_fast,
            make_args=self.make_args,
        )
        if orchestrate_result.failure:
            return r[bool].fail(
                orchestrate_result.error or "orchestration completed with failures",
            )
        return r[bool].ok(True)


__all__: list[str] = ["FlextInfraOrchestratorService"]
