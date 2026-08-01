"""Workspace orchestration discovery helpers.

Keeps project lookup and workspace bootstrap preparation concerns isolated from the
main public orchestrator facade.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from flext_core import r
from flext_infra import c, m, u
from flext_infra.codegen.conform import FlextInfraCodegenConform

if TYPE_CHECKING:
    from pathlib import Path

    from flext_infra import p, t

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
            self.root, self.project_names or (), include_attached=True
        )

    @staticmethod
    def _project_target(project: m.Infra.ProjectInfo, *, workspace_root: Path) -> str:
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
    ) -> p.Result[bool]:
        """Conform each selected project through the sole project writer."""
        for project in projects:
            project_root = project.path.resolve()
            conform_result = FlextInfraCodegenConform.execute_request(
                m.Infra.CodegenConformRequest(
                    root=project_root,
                    scope=c.Infra.CodegenConformScope.SELF,
                    mode=c.Infra.CodegenConformMode.APPLY,
                )
            )
            if conform_result.failure:
                conform_error = conform_result.error or "project conform failed"
                return r[bool].fail(f"{project.name}: {conform_error}")
        return r[bool].ok(True)


__all__: list[str] = ["FlextInfraWorkspaceOrchestratorDiscoveryMixin"]
