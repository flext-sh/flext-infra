"""Multi-project orchestration service.

Executes make verbs across projects with per-project logging and structured
results. Migrated from scripts/workspace_orchestrator.py.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, override

from flext_infra import (
    FlextInfraProjectSelectionServiceBase,
    FlextInfraSyncService,
    c,
    m,
    p,
    r,
    t,
    u,
)
from flext_infra.workspace._orchestrator_loop import (
    FlextInfraOrchestratorLoopMixin,
)
from flext_infra.workspace._orchestrator_run import (
    FlextInfraOrchestratorRunMixin,
)

logger = u.fetch_logger(__name__)


class FlextInfraOrchestratorService(
    FlextInfraProjectSelectionServiceBase[bool],
    FlextInfraOrchestratorRunMixin,
    FlextInfraOrchestratorLoopMixin,
):
    """Infrastructure service for multi-project make orchestration.

    Executes a make verb across a list of projects sequentially, capturing
    per-project output and timing. Supports fail-fast mode to stop on
    first failure.

    """

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
        """Return normalized make arguments."""
        return u.Infra.normalize_make_args(self.make_arg)

    def _resolved_projects(self) -> p.Result[t.SequenceOf[m.Infra.ProjectInfo]]:
        """Resolve the selected project names through canonical discovery."""
        return u.Infra.resolve_projects(
            self.root,
            self.project_names or (),
            include_attached=True,
        )

    @staticmethod
    def _project_target(
        project: m.Infra.ProjectInfo,
        *,
        workspace_root: Path,
    ) -> str:
        """Return the relative make target directory for one project."""
        return str(project.path.resolve().relative_to(workspace_root))

    def _prepare_projects(
        self,
        projects: t.SequenceOf[m.Infra.ProjectInfo],
        *,
        workspace_root: Path,
    ) -> p.Result[bool]:
        """Ensure selected projects have generated make infrastructure."""
        for project in projects:
            project_root = project.path.resolve()
            needs_sync = any(
                not (project_root / filename).is_file()
                for filename in (
                    c.Infra.BASE_MK,
                    c.Infra.MAKEFILE_FILENAME,
                )
            )
            if not needs_sync:
                continue
            sync_result = FlextInfraSyncService(
                workspace=project_root,
                canonical_root=workspace_root,
                apply_changes=True,
            ).execute()
            if sync_result.failure:
                sync_error = sync_result.error or "workspace sync failed"
                return r[bool].fail(f"{project.name}: {sync_error}")
        return r[bool].ok(True)

    @override
    def execute(self) -> p.Result[bool]:
        """Execute the workspace-orchestrate CLI flow."""
        allowed_verbs = c.Infra.ORCHESTRATED_PROJECT_VERBS
        result: p.Result[bool]
        if self.verb not in allowed_verbs:
            allowed = ", ".join(allowed_verbs)
            result = r[bool].fail(
                f"unsupported orchestrate verb '{self.verb}' (allowed: {allowed})",
            )
        else:
            resolved_projects = self._resolved_projects()
            if resolved_projects.failure:
                result = r[bool].fail(
                    resolved_projects.error or "project resolution failed"
                )
            else:
                projects = resolved_projects.value
                if not projects:
                    result = r[bool].fail("no projects discovered")
                else:
                    workspace_root = self.root
                    prepare_result = self._prepare_projects(
                        projects, workspace_root=workspace_root
                    )
                    if prepare_result.failure:
                        result = prepare_result
                    else:
                        orchestrate_result = self.orchestrate(
                            projects=[
                                self._project_target(
                                    project, workspace_root=workspace_root
                                )
                                for project in projects
                            ],
                            verb=self.verb,
                            fail_fast=self.fail_fast,
                            make_args=self.make_args,
                        )
                        if orchestrate_result.failure:
                            result = r[bool].fail(
                                orchestrate_result.error
                                or "orchestration completed with failures"
                            )
                        else:
                            failures = sum(
                                1
                                for item in orchestrate_result.value
                                if item.exit_code != 0
                            )
                            if failures:
                                result = r[bool].fail(
                                    f"orchestration completed with failures: {failures}"
                                )
                            else:
                                result = r[bool].ok(True)
        return result


__all__: list[str] = ["FlextInfraOrchestratorService"]
