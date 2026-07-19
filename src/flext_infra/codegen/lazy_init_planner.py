"""Lazy-init planning over generic Rope workspace indexes.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, override

from flext_infra import c, m, p, t, u
from flext_infra.codegen._lazy_init_planner_aliases import (
    FlextInfraCodegenLazyInitPlannerAliasesMixin,
)
from flext_infra.codegen._lazy_init_planner_cache import (
    FlextInfraCodegenLazyInitPlannerCacheMixin,
)
from flext_infra.codegen._lazy_init_planner_children import (
    FlextInfraCodegenLazyInitPlannerChildrenMixin,
)
from flext_infra.codegen._lazy_init_planner_collision import (
    FlextInfraCodegenLazyInitPlannerCollisionMixin,
)
from flext_infra.codegen._lazy_init_planner_exports import (
    FlextInfraCodegenLazyInitPlannerExportsMixin,
)
from flext_infra.codegen._lazy_init_planner_parents import (
    FlextInfraCodegenLazyInitPlannerParentsMixin,
)
from flext_infra.codegen._lazy_init_planner_public_root import (
    FlextInfraCodegenLazyInitPlannerPublicRootMixin,
)


class FlextInfraCodegenLazyInitPlannerBase(m.ArbitraryTypesModel):
    """Pydantic state base for lazy-init planning."""

    rope_workspace: Annotated[
        p.Infra.RopeWorkspaceDsl,
        m.Field(description="Shared Rope workspace DSL reused by the planner"),
    ]
    lazy_init: p.Infra.LazyInitConfig = m.Field(
        description="Validated lazy-init policy document"
    )

    _module_exports_cache: dict[
        tuple[str, bool, bool, bool, bool, bool], t.LazyAliasMap
    ] = u.PrivateAttr(default_factory=dict)
    _package_exports_cache: dict[str, frozenset[str]] = u.PrivateAttr(
        default_factory=dict
    )
    _source_exports_cache: dict[str, frozenset[str]] = u.PrivateAttr(
        default_factory=dict
    )
    _source_plan_cache: dict[str, p.Infra.LazyInitPlan] = u.PrivateAttr(
        default_factory=dict
    )
    _source_exports_visiting: set[str] = u.PrivateAttr(default_factory=set)
    _parent_package_cache: dict[str, t.StrSequence] = u.PrivateAttr(
        default_factory=dict
    )
    _module_file_by_name: dict[str, Path] = u.PrivateAttr(default_factory=dict)
    _registered_imports_cache: frozenset[tuple[str, str]] | None = u.PrivateAttr(
        default_factory=lambda: None
    )
    _version_module_name: str = u.PrivateAttr(
        default_factory=lambda: f"{c.Infra.DUNDER_VERSION}.py"
    )


class FlextInfraCodegenLazyInitPlanner(
    FlextInfraCodegenLazyInitPlannerBase,
    FlextInfraCodegenLazyInitPlannerAliasesMixin,
    FlextInfraCodegenLazyInitPlannerExportsMixin,
    FlextInfraCodegenLazyInitPlannerChildrenMixin,
    FlextInfraCodegenLazyInitPlannerCollisionMixin,
    FlextInfraCodegenLazyInitPlannerParentsMixin,
    FlextInfraCodegenLazyInitPlannerCacheMixin,
    FlextInfraCodegenLazyInitPlannerPublicRootMixin,
):
    """Resolve lazy-init plans using one shared Rope workspace index."""

    @override
    def build_plan(
        self, pkg_dir: Path, *, dir_exports: t.MappingKV[str, t.LazyAliasMap]
    ) -> p.Infra.LazyInitPlan:
        """Build the lazy-init render plan for one package directory."""
        context = self.context(pkg_dir)
        is_test_child_package = (
            context.surface == c.Infra.DIR_TESTS
            and context.current_pkg != c.Infra.DIR_TESTS
        )
        empty_action: c.Infra.LazyInitAction = (
            c.Infra.LazyInitAction.WRITE
            if is_test_child_package
            else (
                c.Infra.LazyInitAction.REMOVE
                if context.generated_init
                else c.Infra.LazyInitAction.SKIP
            )
        )
        if not context.importable:
            return m.Infra.LazyInitPlan(context=context, action=empty_action)
        # mro-wkii.17.26 (codex): one planner boundary owns the complete
        # side-effect-free contract, including versions and child packages.
        if self._is_side_effect_free_package(context.pkg_dir):
            return m.Infra.LazyInitPlan(
                context=context, action=c.Infra.LazyInitAction.WRITE, exports=()
            )
        lazy_map = self._package_exports(context)
        version_map = self._module_exports(
            context.pkg_dir / self._version_module_name,
            f"{context.current_pkg}.{c.Infra.DUNDER_VERSION}",
            export_options=m.Infra.ExportOptions(include_dunder=True),
        )
        # mro-wkii.17.26 (codex): child packages are direct markers; each
        # descendant plan remains the sole owner of its symbols.
        child_lazy = self._merge_children(context.pkg_dir, lazy_map)
        # Version-submodule dunders are emitted as eager imports rather than
        # lazy. The submodule shares its name (``__version__``) with the dunder
        # string it exports; lazy resolution would let Python's import
        # machinery shadow the dunder with the submodule object on first
        # access. Eager binding at __init__.py load time pins the canonical
        # strings in the package dict permanently.
        eager_dunders = dict(version_map)
        for name in eager_dunders:
            lazy_map.pop(name, None)
        self._resolve_aliases(
            lazy_map,
            current_pkg=context.current_pkg,
            pkg_dir=context.pkg_dir,
            surface=context.surface,
        )
        for name in c.Infra.INFRA_ONLY_EXPORTS:
            lazy_map.pop(name, None)
            eager_dunders.pop(name, None)
        if not lazy_map and not eager_dunders:
            return m.Infra.LazyInitPlan(
                context=context, action=c.Infra.LazyInitAction.WRITE, exports=()
            )
        excluded_lazy_names: t.StrSequence = ()
        is_public_project_root = (
            context.pkg_dir.parent.name == c.Infra.DEFAULT_SRC_DIR
            and context.current_pkg
            and "." not in context.current_pkg
            and context.current_pkg.startswith(c.Infra.PKG_PREFIX_UNDERSCORE)
            and u.Infra.matches_project_namespace_package(context.current_pkg)
        )
        is_test_facade_root = (
            context.current_pkg == c.Infra.DIR_TESTS
            and context.pkg_dir.name == c.Infra.DIR_TESTS
            and context.surface == c.Infra.DIR_TESTS
        )
        is_facade_root = is_public_project_root or is_test_facade_root
        export_names = {*lazy_map, *eager_dunders}
        if is_facade_root:
            # __all__ is the public contract, but the complete lazy map remains
            # available while facade modules are still resolving one another.
            export_names, _unused_filtered_lazy_map = self._filter_public_root_exports(
                context=context,
                export_names=export_names,
                lazy_map=lazy_map,
                eager_names=frozenset(eager_dunders),
            )
            child_lazy = ()
            excluded_lazy_names = ()
        preserve_manual_init = (
            not is_facade_root
            and context.init_path.is_file()
            and not context.generated_init
            and bool(
                context.init_path.read_text(encoding=c.Cli.ENCODING_DEFAULT).strip()
            )
        )
        type_checking_map = dict(lazy_map)
        all_export_names = tuple(sorted(export_names))
        plan = m.Infra.LazyInitPlan(
            context=context,
            action=(
                c.Infra.LazyInitAction.SKIP
                if preserve_manual_init
                else c.Infra.LazyInitAction.WRITE
            ),
            exports=u.Infra.ordered_namespace_exports(
                package_dir=context.pkg_dir,
                package_name=context.current_pkg,
                export_names=all_export_names,
            ),
            lazy_map=dict(lazy_map),
            type_checking_map=type_checking_map,
            eager_dunders=eager_dunders,
            child_packages_for_lazy=child_lazy,
            excluded_lazy_names=excluded_lazy_names,
            static_module_order=self._static_module_order(
                lazy_map, current_pkg=context.current_pkg, pkg_dir=context.pkg_dir
            ),
        )
        # mro-pulj (codex): publish the dependency-complete bottom-up plan so
        # later alias resolution never rebuilds this package without children.
        self._source_plan_cache[str(context.pkg_dir.resolve())] = plan
        self._source_exports_cache[context.current_pkg] = frozenset(plan.exports)
        return plan

    def context(self, pkg_dir: Path) -> p.Infra.LazyInitPackageContext:
        """Return the lazy-init package context for the requested package directory."""
        return self.rope_workspace.package_context(pkg_dir)

    def facade_alias_allowlist(
        self, context: p.Infra.LazyInitPackageContext, *, canonical: frozenset[str]
    ) -> frozenset[str]:
        """Return a package's real facade-alias allowlist from the SSOT.

        allowlist = expected_alias(P) UNION (raw exports(P) INTERSECT the
        canonical single-letter alias vocabulary). Both terms are SSOT-derived
        (this planner's own module policy plus the caller's canonical constant);
        never a hardcoded per-package list. Consumed by the import-facade gate.
        """
        package_entry = self._package_entry(context.pkg_dir)
        if package_entry is None:
            return frozenset()
        expected: set[str] = set()
        for module_entry in package_entry.modules:
            convention = self.rope_workspace.convention(
                module_entry.file_path,
                rel_path=module_entry.file_path.relative_to(context.pkg_dir),
            )
            alias = convention.module_policy.expected_alias
            if alias:
                expected.add(alias)
        # A governed root without explicit ``__all__`` cannot enumerate raw
        # exports; fall back to the module-policy expected aliases alone rather
        # than failing the whole allowlist collection.
        try:
            raw = frozenset(self._package_exports(context))
        except ValueError:
            return frozenset(expected)
        return frozenset(expected | (raw & canonical))


__all__: list[str] = ["FlextInfraCodegenLazyInitPlanner"]
