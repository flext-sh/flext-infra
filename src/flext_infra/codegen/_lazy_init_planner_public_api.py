"""Public-API static helpers for the lazy-init planner."""

from __future__ import annotations

from typing import TYPE_CHECKING, override

from flext_infra import c, m, u
from flext_infra import c, u
from flext_infra.codegen._lazy_init_planner_public_root import (
    FlextInfraCodegenLazyInitPlannerPublicRootMixin,
)

if TYPE_CHECKING:
    from pathlib import Path

    from flext_infra import p


class FlextInfraCodegenLazyInitPlannerPublicApiMixin(
    FlextInfraCodegenLazyInitPlannerPublicRootMixin
):
    """Root public contract helpers for the lazy-init planner."""

    def _declared_public_module_exports(self, pkg_dir: Path) -> frozenset[str]:
        """Return exports explicitly declared by root-level public modules."""
        package_entry = self.rope_workspace.package(pkg_dir)
        if package_entry is None:
            return frozenset()
        exports = set(c.Infra.ALIAS_NAMES)
        for module_entry in package_entry.modules:
            py_file = module_entry.file_path
            if py_file.parent != pkg_dir or py_file.name in {
                c.Infra.INIT_PY,
                "__main__.py",
            }:
                continue
            singleton_export = u.Infra.runtime_singleton_export(py_file.name)
            if py_file.stem.startswith("_") and singleton_export is None:
                continue
            child_entry = self.rope_workspace.package(py_file.parent / py_file.stem)
            if child_entry is not None and child_entry.package_name:
                continue
            convention = self.rope_workspace.convention(
                py_file, rel_path=py_file.relative_to(pkg_dir)
            )
            policy = convention.module_policy
            if not policy.include_in_lazy_init or not policy.export_symbols:
                continue
            exports.update(
                self.rope_workspace.exports(
                    py_file,
                    export_options=m.Infra.ExportOptions(
                        allow_main=policy.allow_main_export,
                        allow_assignments=True,
                        allow_functions=True,
                        require_explicit_all=True,
                    ),
                )
            )
        return frozenset(exports)

    # mro-wkii.17.26 (codex): generated roots derive their API from canonical
    # module declarations; only a hand-authored root participates in cutover.
    @override
    def _root_public_contract_exports(self, pkg_dir: Path) -> frozenset[str]:
        """Return the root ``__all__`` contract resolved by Rope."""
        declared_exports = self._declared_public_module_exports(pkg_dir)
        context = self.rope_workspace.package_context(pkg_dir)
        if context.generated_init:
            return declared_exports
        init_path = pkg_dir / c.Infra.INIT_PY
        if self.rope_workspace.resource(init_path) is None:
            return declared_exports
        return frozenset((*declared_exports, *self.rope_workspace.exports(init_path)))

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
