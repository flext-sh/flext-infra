"""Thin compatibility wrapper for lazy-init planning."""

from __future__ import annotations

from collections.abc import (
    Mapping,
)
from pathlib import Path

from flext_infra import (
    FlextInfraCodegenLazyInitPlanner,
    FlextInfraRopeWorkspace,
    FlextInfraUtilitiesBase as ub,
    m,
    t,
)


class FlextInfraUtilitiesCodegenLazyAliases:
    """Delegate legacy utility callers to the canonical lazy-init planner."""

    def __init__(self, workspace_root: Path | None = None) -> None:
        self._workspace_root = workspace_root or Path.cwd()

    def build_lazy_init_plan(
        self,
        pkg_dir: Path,
        *,
        dir_exports: Mapping[str, t.Infra.LazyImportMap],
    ) -> m.Infra.LazyInitPlan:
        """Build one lazy-init plan using the shared Rope-backed planner owner."""
        lazy_init = ub.load_tool_config().unwrap().lazy_init
        with FlextInfraRopeWorkspace.open_workspace(self._workspace_root) as rope:
            planner = FlextInfraCodegenLazyInitPlanner(
                rope_workspace=rope,
                lazy_init=lazy_init,
            )
            return planner.build_plan(pkg_dir, dir_exports=dir_exports)


__all__: list[str] = ["FlextInfraUtilitiesCodegenLazyAliases"]
