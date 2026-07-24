"""Child-package merging for the lazy-init planner."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra import c

if TYPE_CHECKING:
    from pathlib import Path

    from flext_infra import m, p, t


class FlextInfraCodegenLazyInitPlannerChildrenMixin:
    if TYPE_CHECKING:
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
        self,
        pkg_dir: Path,
        lazy_map: t.MutableLazyAliasMap,
        dir_exports: t.MappingKV[str, t.LazyAliasMap],
    ) -> t.StrSequence:
        """Merge direct child packages into the parent lazy map."""
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
            is_fixture_child = self._is_fixture_package(child_dir)
            child_exports = dir_exports.get(str(resolved_child_dir), {})
            if child_entry is None or not child_entry.package_name:
                continue
            if resolved_child_dir.parent != resolved_pkg_dir:
                continue
            # mro-pulj (codex): private fixture modules are pytest-owned plugin
            # boundaries and never bubble into their production package root.
            if is_fixture_child:
                continue
            direct.append(child_entry.package_name)
            self._add(
                lazy_map,
                child_entry.package_name.rsplit(".", maxsplit=1)[-1],
                (child_entry.package_name, ""),
            )
            for name, (module_name, attr) in child_exports.items():
                if (
                    attr
                    and name not in c.Infra.ALIAS_NAMES
                    and name != "main"
                    and self._publish(name, allow_main=False)
                ):
                    self._add(lazy_map, name, (module_name, attr))
        return tuple(sorted(direct))

    @staticmethod
    def _is_fixture_package(pkg_dir: Path) -> bool:
        """Return True when the directory is the ``_fixtures`` convention package."""
        return pkg_dir.name == "_fixtures"

    @classmethod
    def _is_private_test_fixture_package(cls, pkg_dir: Path, surface: str) -> bool:
        """Return True when the package is a private fixture under the tests surface."""
        return surface == "tests" and cls._is_fixture_package(pkg_dir)
