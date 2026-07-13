"""Public API facade for flext-infra."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, override

from flext_core import r
from flext_infra import t
from flext_infra.base import s
from flext_infra.workspace.rope import FlextInfraRopeWorkspace

if TYPE_CHECKING:
    from pathlib import Path

    from flext_infra import p


class FlextInfra(s[t.JsonDict]):
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


infra = FlextInfra.fetch_global()
"""Shared FlextInfra facade instance."""


__all__: list[str] = ["FlextInfra", "infra"]
