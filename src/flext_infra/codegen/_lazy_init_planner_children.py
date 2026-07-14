"""Child-package merging for the lazy-init planner."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra import c

if TYPE_CHECKING:
    from pathlib import Path

    from flext_infra import m, p, t


class FlextInfraCodegenLazyInitPlannerChildrenMixin:
    if TYPE_CHECKING:
        # mro-wkii.17.26 (codex): declare the validated policy supplied by the MRO base.
        lazy_init: m.Infra.LazyInitConfig
        rope_workspace: p.Infra.RopeWorkspaceDsl

        def _package_entry(
            self, pkg_dir: Path
        ) -> m.Infra.RopePackageIndexEntry | None: ...

        def _add(
            self, index: t.MutableLazyAliasMap, name: str, target: t.StrPair
        ) -> None: ...

        @staticmethod
        def _publish(name: str, *, allow_main: bool) -> bool: ...

    def _merge_children(
        self, pkg_dir: Path, lazy_map: t.MutableLazyAliasMap
    ) -> t.StrSequence:
        """Register direct child packages without flattening their exports."""
        package_entry = self._package_entry(pkg_dir)
        if package_entry is None:
            return ()
        resolved_pkg_dir = pkg_dir.resolve()
        direct: list[str] = []
        for child_dir in package_entry.descendant_child_dirs:
            # mro-pulj (codex): do not merge retired root registries into the
            # inline map that replaces them.
            if child_dir.name in c.Infra.OBSOLETE_ROOT_SUPPORT_NAMES:
                continue
            resolved_child_dir = child_dir.resolve()
            child_init = child_dir / c.Infra.INIT_PY
            if not child_init.is_file():
                continue
            child_entry = self._package_entry(child_dir)
            if child_entry is None or not child_entry.package_name:
                continue
            if resolved_child_dir.parent != resolved_pkg_dir:
                continue
            # mro-wkii.17.26 (codex): privacy controls parent publication;
            # side-effect policy controls only the child's own initializer.
            if child_dir.name.startswith("_"):
                continue
            direct.append(child_entry.package_name)
            self._add(
                lazy_map,
                child_entry.package_name.rsplit(".", maxsplit=1)[-1],
                (child_entry.package_name, ""),
            )
        return tuple(sorted(direct))

    def _excluded_child_lazy_names(
        self,
        child_packages: t.StrSequence,
        allowed_export_names: frozenset[str],
        runtime_lazy_names: frozenset[str],
        dir_exports: t.MappingKV[str, t.LazyAliasMap],
    ) -> t.StrSequence:
        """Return child exports that must not leak through runtime lazy merges."""
        return tuple(
            sorted({
                name
                for child_package in child_packages
                for name in self._merged_child_export_names(child_package, dir_exports)
                if name not in allowed_export_names and name not in runtime_lazy_names
            })
        )

    def _child_packages_without_main_export(
        self,
        child_packages: t.StrSequence,
        dir_exports: t.MappingKV[str, t.LazyAliasMap],
    ) -> t.StrSequence:
        """Return child packages safe to merge into a root facade."""
        return tuple(
            child_package
            for child_package in child_packages
            if "main" not in self._merged_child_export_names(child_package, dir_exports)
        )

    def _public_root_child_packages(
        self,
        child_packages: t.StrSequence,
        dir_exports: t.MappingKV[str, t.LazyAliasMap],
    ) -> t.StrSequence:
        """Return child packages whose exports may flow through a public root."""
        return tuple(
            child_package
            for child_package in child_packages
            if self._is_public_root_child_package(
                child_package,
                self._merged_child_export_names(child_package, dir_exports),
            )
        )

    def _merged_child_export_names(
        self, child_package: str, dir_exports: t.MappingKV[str, t.LazyAliasMap]
    ) -> frozenset[str]:
        """Return export names from the child lazy map produced bottom-up."""
        child_dir = self.rope_workspace.workspace_index.package_dir_by_name.get(
            child_package
        )
        if child_dir is None:
            return self._export_names_for_package(child_package)
        child_exports = dir_exports.get(str(child_dir.resolve()))
        if child_exports is None:
            return self._export_names_for_package(child_package)
        return frozenset(child_exports)

    @staticmethod
    def _is_internal_root_child_package(child_package: str) -> bool:
        """Return whether a child package is implementation-only at the root."""
        child_name = child_package.rsplit(".", maxsplit=1)[-1]
        return child_name.startswith("_") or (
            child_name in c.Infra.PUBLIC_ROOT_INTERNAL_CHILD_PACKAGES
        )

    @staticmethod
    def _is_public_root_child_package(
        child_package: str, export_names: frozenset[str]
    ) -> bool:
        """Return whether a child package may bubble into a public root."""
        public_names = frozenset(
            name
            for name in export_names
            if name not in c.Infra.ALIAS_NAMES
            and name != "main"
            and not name.startswith("_")
        )
        if not public_names:
            return False
        if FlextInfraCodegenLazyInitPlannerChildrenMixin._is_internal_root_child_package(
            child_package
        ):
            return False
        child_name = child_package.rsplit(".", maxsplit=1)[-1]
        if child_name in c.Infra.LOCAL_INFERRED_SEGMENTS:
            return True
        return all(
            FlextInfraCodegenLazyInitPlannerChildrenMixin._is_public_root_child_export(
                child_package, name
            )
            for name in public_names
        )

    @staticmethod
    def _is_public_root_child_export(child_package: str, name: str) -> bool:
        """Return whether one child export may bubble into a public root."""
        if name in c.Infra.ALIAS_NAMES or name == "main":
            return False
        if FlextInfraCodegenLazyInitPlannerChildrenMixin._is_internal_root_child_package(
            child_package
        ):
            return False
        child_name = child_package.rsplit(".", maxsplit=1)[-1]
        if child_name in c.Infra.LOCAL_INFERRED_SEGMENTS:
            return True
        return name[:1].isupper() and not name.isupper()

    def _is_side_effect_free_package(self, pkg_dir: Path) -> bool:
        """Return whether config forbids eager sibling imports for this package."""
        return pkg_dir.name in self.lazy_init.side_effect_free_packages
