"""Public API facade for flext-infra."""

from __future__ import annotations

from pathlib import Path
from typing import ClassVar, Self, override

from flext_core import r

from flext_infra import (
    FlextInfraRopeWorkspace,
    c,
    p,
    s,
    t,
)


class FlextInfra(
    s[dict[str, t.JsonValue]],
):
    """Thin public MRO facade over infra services."""

    app_name: ClassVar[str] = "flext-infra"
    _instance: ClassVar[Self | None] = None

    @classmethod
    def fetch_global(cls) -> Self:
        """Return the shared infra facade instance (canonical domain verb)."""
        if cls._instance is None:
            cls._instance = cls.model_validate({})
        return cls._instance

    def rope_workspace(
        self,
        workspace_root: Path | None = None,
        *,
        project_prefix: str = c.Infra.PKG_PREFIX_HYPHEN,
        src_dir: str = c.Infra.DEFAULT_SRC_DIR,
        ignored_resources: tuple[str, ...] = c.Infra.ROPE_IGNORED_RESOURCES,
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
    def execute(self) -> p.Result[dict[str, t.JsonValue]]:
        """Execute a lightweight facade health report."""
        report: dict[str, t.JsonValue] = {
            "service": "flext-infra",
            "status": "ok",
            "workspace_root": str(self.workspace_root),
            "apply_changes": self.apply_changes,
        }
        return r[dict[str, t.JsonValue]].ok(report)


infra = FlextInfra.fetch_global()


__all__: list[str] = ["FlextInfra", "infra"]
