"""Public API facade for flext-infra."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, override

from flext_core import r
from flext_infra import m, t
from flext_infra.base import s
from flext_infra.basemk.generator import FlextInfraBaseMkGenerator
from flext_infra.basemk.renderer import FlextInfraBaseMkTemplateRenderer
from flext_infra.release.managed_git_tool import FlextInfraManagedGitToolRelease
from flext_infra.services._workspace.environment import (
    FlextInfraWorkspaceEnvironmentMixin,
)
from flext_infra.workspace.rope import FlextInfraRopeWorkspace

if TYPE_CHECKING:
    from pathlib import Path

    from flext_infra import p


class FlextInfra(FlextInfraWorkspaceEnvironmentMixin, s[t.JsonDict]):
    """Thin public MRO facade over infra services."""

    app_name: ClassVar[str] = "flext-infra"

    def rope_workspace(
        self, workspace_root: Path | None = None
    ) -> p.Infra.RopeWorkspaceDsl:
        """Open the public Rope workspace DSL directly from the facade."""
        # NOTE (multi-agent, mro-wkii.17.24): Rope reads its source policy
        # directly from config.Infra at the service boundary.
        resolved_root = (
            self.workspace_root if workspace_root is None else workspace_root
        )
        return FlextInfraRopeWorkspace.open_workspace(resolved_root)

    def generate_basemk(
        self, request: m.Infra.BaseMkRenderRequest
    ) -> p.Result[m.Infra.BaseMkRenderResult]:
        """Render canonical base.mk content directly from the facade."""
        result_type = m.Infra.BaseMkRenderResult
        settings = FlextInfraBaseMkTemplateRenderer.default_config().model_copy(
            update={"project_name": request.project_name}
        )
        rendered = FlextInfraBaseMkGenerator(
            project_name=request.project_name
        ).generate_basemk(settings)
        if rendered.failure:
            return r[result_type].fail(rendered.error or "base.mk render failed")
        return r[result_type].ok(result_type(content=rendered.value))

    def release_managed_git_tool(
        self, spec: m.Infra.ManagedGitToolRelease, *, apply: bool = False
    ) -> p.Result[m.Infra.ManagedGitToolReleaseResult]:
        """Run the sole generic exact-Git executable release owner."""
        return FlextInfraManagedGitToolRelease.release(spec, apply=apply)

    @override
    def execute(self) -> p.Result[t.JsonDict]:
        """Execute a lightweight facade health report."""
        report: t.JsonDict = {
            "service": "flext-infra",
            "status": "ok",
            "workspace_root": str(self.workspace_root),
            "apply_changes": self.apply_changes,
        }
        return r[t.JsonDict].ok(report)


infra: FlextInfra = FlextInfra.fetch_global()
"""Shared FlextInfra facade instance."""


__all__: list[str] = ["FlextInfra", "infra"]
