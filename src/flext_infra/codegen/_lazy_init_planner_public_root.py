"""Root public-export decisions for the lazy-init planner.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_infra import c, m, t, u


class FlextInfraCodegenLazyInitPlannerPublicRootMixin:
    """Public root-facade export filtering helpers."""

    def _filter_public_root_exports(
        self,
        *,
        context: m.Infra.LazyInitPackageContext,
        export_names: set[str],
        lazy_map: t.MutableLazyAliasMap,
        eager_names: frozenset[str],
    ) -> t.Pair[set[str], t.MutableLazyAliasMap]:
        """Publish direct module declarations and inherited facade bindings.

        Returns:
            The declared names and their corresponding lazy targets.

        """
        governed_lazy_map = {
            name: target
            for name, target in lazy_map.items()
            if self._is_declared_root_export(
                target,
                root_pkg=context.current_pkg,
            )
        }
        lazy_map.clear()
        lazy_map.update(governed_lazy_map)
        public_export_names = {
            name for name in export_names if name in eager_names
        } | set(governed_lazy_map)
        filtered_lazy_map = {
            name: target
            for name, target in lazy_map.items()
            if name in public_export_names
        }
        return public_export_names, filtered_lazy_map

    @staticmethod
    def _is_declared_root_export(
        target: t.StrPair,
        *,
        root_pkg: str,
    ) -> bool:
        """Keep each local declaration at its owning directory.

        Returns:
            Whether the target is direct or belongs to an upstream facade.

        """
        module_path, _attr_name = target
        return module_path.rsplit(".", maxsplit=1)[
            0
        ] == root_pkg or not module_path.startswith(f"{root_pkg}.")

    @staticmethod
    def _is_private_owner(module_path: str, *, root_pkg: str) -> bool:
        """Return whether a module below ``root_pkg`` sits behind a private segment.

        Any underscore-prefixed source segment below the root marks the owner as
        private; its symbols stay behind their facade and never widen the root ABI.

        Returns:
            Whether a module below ``root_pkg`` sits behind a private segment.

        """
        if not module_path.startswith(f"{root_pkg}."):
            return False
        tail = module_path[len(root_pkg) + 1 :].split(".")
        return any(part.startswith("_") and not part.startswith("__") for part in tail)

    @staticmethod
    def _is_facade_root(context: m.Infra.LazyInitPackageContext) -> bool:
        """Return whether a package is a public project root or the tests facade root.

        Returns:
            Whether a package is a public project root or the tests facade root.

        """
        is_public_project_root = bool(
            context.pkg_dir.parent.name == c.Infra.DEFAULT_SRC_DIR
            and context.current_pkg
            and "." not in context.current_pkg
            # Why: governed consumer packages
            # are first-class project roots; package prefixes are not architecture.
            and u.Infra.matches_project_namespace_package(context.current_pkg),
        )
        is_test_facade_root = (
            context.current_pkg == c.Infra.DIR_TESTS
            and context.pkg_dir.name == c.Infra.DIR_TESTS
            and context.surface == c.Infra.DIR_TESTS
        )
        return is_public_project_root or is_test_facade_root


__all__: list[str] = ["FlextInfraCodegenLazyInitPlannerPublicRootMixin"]
