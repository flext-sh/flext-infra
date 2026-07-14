"""Public-API static helpers for the lazy-init planner."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, override

from flext_infra import c, u
from flext_infra.codegen._lazy_init_planner_public_root import (
    FlextInfraCodegenLazyInitPlannerPublicRootMixin,
)

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraCodegenLazyInitPlannerPublicApiMixin(
    FlextInfraCodegenLazyInitPlannerPublicRootMixin
):
    """Root public contract helpers for the lazy-init planner."""

    # mro-wkii.17.26 (codex): preserve the declared ABI while one scaffold
    # template replaces project-specific root initializer implementations.
    @override
    def _root_public_contract_exports(self, pkg_dir: Path) -> frozenset[str]:
        """Return the root ``__all__`` contract resolved by Rope."""
        init_path = pkg_dir / c.Infra.INIT_PY
        if self.rope_workspace.resource(init_path) is None:
            return frozenset()
        return frozenset(self.rope_workspace.exports(init_path))

    # mro-pulj (codex): the generated initializer freezes direct imports
    # independently from wildcard publication, replacing root sidecars.
    @staticmethod
    def _root_direct_import_contract(pkg_dir: Path) -> frozenset[str]:
        """Return the generated direct-import contract when already declared."""
        init_path = pkg_dir / c.Infra.INIT_PY
        if not init_path.is_file():
            return frozenset()
        source = u.Cli.files_read_text(init_path).unwrap()
        for name, value in u.Infra.get_module_level_assignments(source):
            if name == c.Infra.ROOT_DIRECT_IMPORTS_CONTRACT:
                return frozenset(c.Infra.STRING_LITERAL_RE.findall(value))
        return frozenset()

    if TYPE_CHECKING:
        rope_workspace: p.Infra.RopeWorkspaceDsl


__all__: list[str] = ["FlextInfraCodegenLazyInitPlannerPublicApiMixin"]
