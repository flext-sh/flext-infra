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
    _source_plan_cache: dict[str, m.Infra.LazyInitPlan] = u.PrivateAttr(
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
        empty_action: c.Infra.LazyInitAction = (
            c.Infra.LazyInitAction.REMOVE
            if context.generated_init
            else c.Infra.LazyInitAction.SKIP
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
        export_names = {*lazy_map, *eager_dunders}
        if is_public_project_root:
            # mro-wkii.17.26 (codex): the public root publishes direct owners;
            # child packages remain independently generated static contracts.
            export_names, lazy_map = self._filter_public_root_exports(
                context=context,
                export_names=export_names,
                lazy_map=lazy_map,
                eager_names=frozenset(eager_dunders),
            )
            child_lazy = ()
        type_checking_map = dict(lazy_map)
        all_export_names = tuple(sorted(export_names))
        plan = m.Infra.LazyInitPlan(
            context=context,
            action=c.Infra.LazyInitAction.WRITE,
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
        )
        # mro-pulj (codex): publish the dependency-complete bottom-up plan so
        # later alias resolution never rebuilds this package without children.
        self._source_plan_cache[str(context.pkg_dir.resolve())] = plan
        self._source_exports_cache[context.current_pkg] = frozenset(plan.exports)
        return plan

    def context(self, pkg_dir: Path) -> p.Infra.LazyInitPackageContext:
        """Return the lazy-init package context for the requested package directory."""
        return self.rope_workspace.package_context(pkg_dir)


__all__: list[str] = ["FlextInfraCodegenLazyInitPlanner"]
