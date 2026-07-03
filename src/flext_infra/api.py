"""Public API facade for flext-infra."""

from __future__ import annotations

from pathlib import Path
from typing import ClassVar, override

from flext_core import r
from flext_infra.base import s
from flext_infra.constants import c
from flext_infra.protocols import p
from flext_infra.typings import t
from flext_infra.workspace.rope import FlextInfraRopeWorkspace


class FlextInfra(
    s[t.JsonDict],
):
    """Thin public MRO facade over infra services."""

    app_name: ClassVar[str] = "flext-infra"

    def rope_workspace(
        self,
        workspace_root: Path | None = None,
        *,
        project_prefix: str = c.Infra.PKG_PREFIX_HYPHEN,
        src_dir: str = c.Infra.DEFAULT_SRC_DIR,
        ignored_resources: t.StrSequence = c.Infra.ROPE_IGNORED_RESOURCES,
    ) -> p.Infra.RopeWorkspaceDsl:
        """Open the public Rope workspace DSL directly from the facade."""
        resolved_root = (
            self.workspace_root if workspace_root is None else workspace_root
        )
        return FlextInfraRopeWorkspace.open_workspace(
            resolved_root,
            project_prefix=project_prefix,
            src_dir=src_dir,
            ignored_resources=ignored_resources,
        )

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


__all__: list[str] = ["FlextInfra", "infra"]
