"""Workspace orchestration discovery helpers.

Keeps project lookup and workspace bootstrap preparation concerns isolated from the
main public orchestrator facade.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Protocol

from flext_core import r
from flext_infra.constants import c
from flext_infra.models import m
from flext_infra.protocols import p
from flext_infra.typings import t
from flext_infra.utilities import u
from flext_infra.workspace.sync import FlextInfraSyncService

if TYPE_CHECKING:

    class _WorkspaceOrchestratorProtocol(Protocol):
        @property
        def root(self) -> Path: ...

        @property
        def project_names(self) -> t.StrSequence | None: ...


class FlextInfraWorkspaceOrchestratorDiscoveryMixin:
    """Resolve workspace projects and materialize project-level artifacts."""

    def _resolved_projects(
        self: _WorkspaceOrchestratorProtocol,
    ) -> p.Result[t.SequenceOf[m.Infra.ProjectInfo]]:
        """Resolve selected projects using workspace discovery."""
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
        """Map a project info object into a relative make target."""
        project_path = project.path.resolve()
        resolved_workspace_root = workspace_root.resolve()
        try:
            return str(project_path.relative_to(resolved_workspace_root))
        except ValueError:
            return str(project_path)

    @staticmethod
    def _prepare_projects(
        projects: t.SequenceOf[m.Infra.ProjectInfo],
        *,
        workspace_root: Path,
    ) -> p.Result[bool]:
        """Ensure each selected project has ``base.mk`` and ``Makefile``."""
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
                workspace_root=project_root,
                canonical_root=workspace_root,
                apply_changes=True,
            ).execute()
            if sync_result.failure:
                sync_error = sync_result.error or "workspace sync failed"
                return r[bool].fail(f"{project.name}: {sync_error}")
        return r[bool].ok(True)


__all__: list[str] = [
    "FlextInfraWorkspaceOrchestratorDiscoveryMixin",
]
