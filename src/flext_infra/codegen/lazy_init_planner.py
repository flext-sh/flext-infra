"""Lazy-init planning over generic Rope workspace indexes.

Copyright (c) 2026 FLEXT Team. All rights reserved.
src/flext_infra/codegen/lazy_init_planner
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import MutableMapping
from pathlib import Path
from typing import Annotated, override

from flext_infra import c, m, p, r, t, u
from flext_infra.codegen import FlextInfraCodegenLazyInitPlannerPublicRootMixin
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
from flext_infra.workspace import FlextInfraRopeWorkspace


class FlextInfraCodegenLazyInitPlanner(
    m.ArbitraryTypesModel,
    FlextInfraCodegenLazyInitPlannerAliasesMixin,
    FlextInfraCodegenLazyInitPlannerExportsMixin,
    FlextInfraCodegenLazyInitPlannerChildrenMixin,
    FlextInfraCodegenLazyInitPlannerCollisionMixin,
    FlextInfraCodegenLazyInitPlannerParentsMixin,
    FlextInfraCodegenLazyInitPlannerCacheMixin,
    FlextInfraCodegenLazyInitPlannerPublicRootMixin,
):
    """Resolve lazy-init plans using one shared Rope workspace index."""

    rope_workspace: Annotated[
        p.Infra.RopeWorkspaceDsl,
        m.Field(description="Shared Rope workspace DSL reused by the planner"),
    ]
    lazy_init: m.Infra.LazyInitConfig = m.Field(
        description="Validated lazy-init policy document",
    )
    _module_exports_cache: MutableMapping[
        tuple[str, bool, bool, bool, bool, bool],
        t.LazyAliasMap,
    ] = m.PrivateAttr(
        default_factory=dict[tuple[str, bool, bool, bool, bool, bool], t.LazyAliasMap],
    )
    _package_exports_cache: MutableMapping[str, frozenset[str]] = m.PrivateAttr(
        default_factory=dict[str, frozenset[str]],
    )
    _source_exports_cache: MutableMapping[str, frozenset[str]] = m.PrivateAttr(
        default_factory=dict[str, frozenset[str]],
    )
    _source_plan_cache: MutableMapping[str, m.Infra.LazyInitPlan] = m.PrivateAttr(
        default_factory=dict[str, m.Infra.LazyInitPlan],
    )
    _plan_receipts: MutableMapping[str, m.Infra.CodegenPhaseAnalysis] = m.PrivateAttr(
        default_factory=dict[str, m.Infra.CodegenPhaseAnalysis],
    )
    _parent_package_cache: MutableMapping[str, t.StrSequence] = m.PrivateAttr(
        default_factory=dict[str, t.StrSequence],
    )
    _module_file_by_name: MutableMapping[str, Path] = m.PrivateAttr(
        default_factory=dict[str, Path],
    )
    _project_layout_cache: MutableMapping[Path, m.Infra.RopeProjectLayout] = (
        m.PrivateAttr(
            default_factory=dict[Path, m.Infra.RopeProjectLayout],
        )
    )
    _version_module_name: str = m.PrivateAttr(
        default_factory=lambda: f"{c.Infra.DUNDER_VERSION}.py",
    )
    _collision_count: int = m.PrivateAttr(default_factory=int)

    def plan_all_inits(
        self,
        pkg_dirs: t.SequenceOf[Path],
        *,
        target_package_dir: Path | None = None,
    ) -> p.Result[t.VariadicTuple[m.Infra.LazyInitPlan]]:
        """Resolve selected plans bottom-up and reject ambiguous ownership.

        Returns:
            The selected plans, or failure after the complete collision inventory.

        """
        dir_exports: MutableMapping[str, t.LazyAliasMap] = {}
        planned: list[m.Infra.LazyInitPlan] = []
        repository_root = self.rope_workspace.repository_root
        progress_interval = max(1, len(pkg_dirs) // 20) if pkg_dirs else 1
        for idx, pkg_dir in enumerate(pkg_dirs, start=1):
            report_progress = (
                idx == 1 or idx == len(pkg_dirs) or idx % progress_interval == 0
            )
            if report_progress:
                rel_path = (
                    pkg_dir.relative_to(repository_root)
                    if repository_root in pkg_dir.parents
                    else pkg_dir
                )
                u.Cli.info(f"lazy-init: progress {idx}/{len(pkg_dirs)} — {rel_path}")
            package_key = str(pkg_dir.resolve())
            plan = self._source_plan_cache.get(package_key)
            if plan is None:
                plan, receipt = self._isolated_plan(pkg_dir, dir_exports=dir_exports)
            else:
                receipt = self.source_receipt(pkg_dir)
                self.rope_workspace.rope_project.replay_source_consumption(receipt)
            self._source_plan_cache[package_key] = plan
            self._plan_receipts[package_key] = receipt
            if report_progress:
                u.Cli.info(
                    f"lazy-init: resolved {idx}/{len(pkg_dirs)} "
                    f"package={plan.context.current_pkg} "
                    f"importable={plan.context.importable} "
                    f"action={plan.action} exports={len(plan.lazy_map)}"
                )
            if plan.lazy_map:
                dir_exports[str(pkg_dir.resolve())] = dict(plan.lazy_map)
            should_process = (
                target_package_dir is None
                or pkg_dir.resolve() == target_package_dir.resolve()
                or (
                    target_package_dir.name == c.Infra.DIR_TESTS
                    and pkg_dir.resolve().is_relative_to(target_package_dir.resolve())
                )
            )
            if should_process:
                planned.append(plan)
            if (
                target_package_dir is not None
                and pkg_dir.resolve() == target_package_dir.resolve()
            ):
                break
        u.Cli.info(f"lazy-init: resolved {len(planned)} package artifact plans")
        if self._collision_count:
            return r[t.VariadicTuple[m.Infra.LazyInitPlan]].fail(
                "lazy-init public export ownership is ambiguous: "
                f"{self._collision_count} collision(s)",
            )
        return r[t.VariadicTuple[m.Infra.LazyInitPlan]].ok(tuple(planned))

    def _isolated_plan(
        self,
        pkg_dir: Path,
        *,
        dir_exports: t.MappingKV[str, t.LazyAliasMap],
    ) -> t.Pair[m.Infra.LazyInitPlan, m.Infra.CodegenPhaseAnalysis]:
        """Resolve one artifact with fresh native and planner caches in the same epoch.

        Structural indexes are rebuilt until their live selection owner can supply
        an authenticated, content-free reusable inventory. No semantic cache is copied.

        Returns:
            The isolated plan bound to its original consumption receipt.

        """
        project = self.rope_workspace.rope_project
        with (
            project.source_consumption() as consumption,
            project.source_consumer() as consumer,
            FlextInfraRopeWorkspace.open_workspace(
                self.rope_workspace.repository_root,
                rope_repository_root=self.rope_workspace.rope_repository_root,
                source_project=consumer,
                workspace_index=self.rope_workspace.workspace_index,
                index_receipt=self.rope_workspace.source_index_receipt,
            ) as workspace,
        ):
            planner = type(self)(rope_workspace=workspace, lazy_init=self.lazy_init)
            planner.seed_source_plans(self._source_plan_cache, self._plan_receipts)
            plan = planner.build_plan(pkg_dir, dir_exports=dir_exports)
            self._collision_count += planner.collision_count
        receipt = consumption.receipt()
        return plan.model_copy(
            update={
                "source_states": receipt.inputs,
                "source_directories": receipt.source_directories,
                "source_query_topology": receipt.source_query_topology,
            }
        ), receipt

    @property
    def collision_count(self) -> int:
        """The export collisions observed by this isolated planner."""
        return self._collision_count

    def seed_source_plans(
        self,
        plans: t.MappingKV[str, m.Infra.LazyInitPlan],
        receipts: t.MappingKV[str, m.Infra.CodegenPhaseAnalysis],
    ) -> None:
        """Seed prior package decisions without copying native semantic caches."""
        self._source_plan_cache.update(plans)
        self._plan_receipts.update(receipts)

    @property
    def source_plans(self) -> t.MappingKV[str, m.Infra.LazyInitPlan]:
        """Expose immutable decisions, never native semantic cache objects."""
        return self._source_plan_cache

    def source_receipt(self, package_dir: Path) -> m.Infra.CodegenPhaseAnalysis:
        """Return only the sealed receipt minted for an actual package decision.

        Raises:
            ValueError: If the package lacks its original provenance.

        """
        receipt = self._plan_receipts.get(str(package_dir.resolve()))
        if receipt is None:
            msg = f"lazy-init package lacks original provenance: {package_dir}"
            raise ValueError(msg)
        return receipt

    @override
    def build_plan(
        self,
        pkg_dir: Path,
        *,
        dir_exports: t.MappingKV[str, t.LazyAliasMap],
    ) -> m.Infra.LazyInitPlan:
        """Build the lazy-init render plan for one package directory.

        Returns:
            The resulting ``m.Infra.LazyInitPlan``.

        """
        context = self.context(pkg_dir)
        self.rope_workspace.rope_project.source_state(
            context.init_path,
            required=False,
        )
        selected = (
            self.rope_workspace.rope_project.source_text(context.init_path).encode(
                c.DEFAULT_ENCODING
            )
            if self.rope_workspace.rope_project.source_query(
                context.init_path, "isfile"
            )
            else None
        )
        if u.Infra.codegen_initializer_is_authored(selected):
            return self._authored_plan(context)
        if not context.importable or self._shadows_stdlib_module(pkg_dir):
            return self._residue_plan(context)
        is_test_child_package = (
            context.surface == c.Infra.DIR_TESTS
            and context.current_pkg != c.Infra.DIR_TESTS
        )
        empty_action: c.Infra.LazyInitAction = (
            c.Infra.LazyInitAction.WRITE
            if is_test_child_package or self._keeps_facade_when_empty(context)
            else (
                c.Infra.LazyInitAction.REMOVE
                if context.generated_init
                else c.Infra.LazyInitAction.SKIP
            )
        )
        lazy_map = self._package_exports(context)
        self._merge_version_module(context, lazy_map)
        child_lazy = self._merge_children(context.pkg_dir, lazy_map, dir_exports)
        self._resolve_aliases(
            lazy_map,
            current_pkg=context.current_pkg,
            pkg_dir=context.pkg_dir,
            surface=context.surface,
        )
        eager_dunders: t.MutableLazyAliasMap = {
            name: lazy_map.pop(name)
            for name in (c.Infra.DUNDER_VERSION,)
            if lazy_map.get(name)
            == (f"{context.current_pkg}.{Path(self._version_module_name).stem}", name)
        }
        # Inject test runtime aliases (tm, td, tf, tk, etc.) for the tests facade root.
        # The tests package (e.g., flext_api.tests) is a facade root that should
        # publish these aliases from flext_tests.
        is_test_facade_root = (
            context.current_pkg == c.Infra.DIR_TESTS
            and context.pkg_dir.name == c.Infra.DIR_TESTS
            and context.surface == c.Infra.DIR_TESTS
        )
        if is_test_facade_root:
            for alias_name, target in c.Infra.TEST_RUNTIME_ALIAS_TARGETS.items():
                if alias_name not in lazy_map:
                    lazy_map[alias_name] = target
        if not lazy_map and not eager_dunders:
            return self._publish_plan(
                m.Infra.LazyInitPlan(
                    context=context,
                    action=empty_action,
                    lazy_map={},
                    eager_dunders={},
                    inline_constants={},
                ),
            )
        excluded_lazy_names: t.StrSequence = ()
        is_facade_root = self._is_facade_root(context)
        export_names = {*lazy_map, *eager_dunders}
        if not is_facade_root:
            # A nested package's own modules commonly consume
            # the project root's already-published facade aliases directly
            # (``from <root> import c, m, p, ...``) without defining any
            # local class of their own under that alias. _resolve_aliases
            # then inherits the ROOT's own alias entry (package_name ==
            # this package's own project root) into lazy_map so internal
            # code can still resolve it, but republishing it as part of
            # THIS package's own __all__/TYPE_CHECKING contract is a pure
            # upstream re-export, not a local owner: it is redundant with
            # the root's own contract and, being an absolute self-import of
            # the project root, fails the relative-owner validation in
            # generate_type_checking. Exclude only that exact self-pointing
            # case (an alias whose target is literally the project root
            # under its own name) here, at the one place that decides the
            # publishable contract; every alias with a genuine local or
            # foreign-parent owner (module path does not equal the bare
            # root package) stays published exactly as before.
            root_pkg_name = context.current_pkg.split(".", maxsplit=1)[0]
            if root_pkg_name and root_pkg_name != context.current_pkg:
                export_names = {
                    name
                    for name in export_names
                    if name not in c.Infra.ALIAS_NAMES
                    or lazy_map.get(name) != (root_pkg_name, name)
                }
        if is_facade_root:
            # __all__ is the one public
            # contract (dir()/star-import/docs already respect it). Do NOT
            # narrow lazy_map/_LAZY_MODULES to match -- internal fragments across
            # the package rely on lazy __getattr__ resolving the root facade
            # (`from flext_core import c`) during their own eager import chain;
            # pruning the lazy map to the public subset breaks that resolution
            # with a circular ImportError the moment any pruned name is touched
            # before __init__ finishes executing. Only export_names (-> __all__)
            # is filtered; lazy_map stays the full discovered set.
            export_names, filtered_lazy_map = self._filter_public_root_exports(
                context=context,
                export_names=export_names,
                lazy_map=lazy_map,
                eager_names=frozenset(eager_dunders),
            )
            lazy_map = filtered_lazy_map
            child_lazy = ()
            excluded_lazy_names = ()
        all_export_names = tuple(sorted(export_names))
        plan = m.Infra.LazyInitPlan(
            context=context,
            action=c.Infra.LazyInitAction.WRITE,
            ownership="generator",
            disposition="planned",
            exports=u.Infra.ordered_namespace_exports(
                package_dir=context.pkg_dir,
                package_name=context.current_pkg,
                export_names=all_export_names,
            ),
            lazy_map=dict(lazy_map),
            eager_dunders=eager_dunders,
            inline_constants={},
            wildcard_runtime_modules=(),
            child_packages_for_lazy=child_lazy,
            excluded_lazy_names=excluded_lazy_names,
        )
        self._source_exports_cache[context.current_pkg] = frozenset(plan.exports)
        return self._publish_plan(plan)

    def _authored_plan(
        self,
        context: m.Infra.LazyInitPackageContext,
    ) -> m.Infra.LazyInitPlan:
        """Retain an authored initializer, cached for its consumers.

        Returns:
            The retained plan for the package's authored initializer.

        """
        exports = self._module_exports(
            context.init_path,
            context.current_pkg,
            export_options=m.Infra.ExportOptions(
                include_dunder=True,
                allow_assignments=True,
                allow_functions=True,
                require_explicit_all=True,
            ),
        )
        self._source_exports_cache[context.current_pkg] = frozenset(exports)
        return self._publish_plan(
            m.Infra.LazyInitPlan(
                context=context,
                action=c.Infra.LazyInitAction.RETAIN,
                ownership="authored",
                disposition="retained",
                exports=tuple(sorted(exports)),
                lazy_map=exports,
                eager_dunders={},
                inline_constants={},
            ),
        )

    def _residue_plan(
        self,
        context: m.Infra.LazyInitPackageContext,
    ) -> m.Infra.LazyInitPlan:
        """Remove or skip an unrenderable package's generator residue.

        No generated content can repair a package name that shadows a stdlib
        module, so the plan removes generator-owned residue and otherwise skips
        the directory. The ALL_SCAN_PATTERNS contract is unchanged: every
        surface is still scanned; only directories that cannot legally be
        packages are not rendered, and ``_merge_children`` applies the same
        predicate to the parent.

        Returns:
            The remove-or-skip plan for the unrenderable package.

        """
        residue_action = (
            c.Infra.LazyInitAction.REMOVE
            if context.generated_init
            else c.Infra.LazyInitAction.SKIP
        )
        return self._publish_plan(
            m.Infra.LazyInitPlan(
                context=context,
                action=residue_action,
                lazy_map={},
                eager_dunders={},
                inline_constants={},
            ),
        )

    def _merge_version_module(
        self,
        context: m.Infra.LazyInitPackageContext,
        lazy_map: t.MutableLazyAliasMap,
    ) -> None:
        """Merge the package's version module exports into the lazy map."""
        if not self.rope_workspace.rope_project.source_query(
            context.pkg_dir / self._version_module_name,
            "isfile",
        ):
            return
        lazy_map.update(
            self._module_exports(
                context.pkg_dir / self._version_module_name,
                f"{context.current_pkg}.{c.Infra.DUNDER_VERSION}",
                export_options=m.Infra.ExportOptions(
                    include_dunder=True,
                    require_explicit_all=True,
                ),
            ),
        )

    def _publish_plan(self, plan: m.Infra.LazyInitPlan) -> m.Infra.LazyInitPlan:
        """Publish one bottom-up plan so parents follow it in the same pass.

        Later alias resolution never rebuilds a package
        without its children. Every plan, including REMOVE and
        SKIP decided before rendering, is published so the parent inventory in
        ``_merge_children`` sees the child's action instead of the on-disk
        initializer.

        Returns:
            The resulting ``m.Infra.LazyInitPlan``.

        """
        if plan.ownership is None and plan.action in {
            c.Infra.LazyInitAction.WRITE,
            c.Infra.LazyInitAction.REMOVE,
        }:
            plan = plan.model_copy(
                update={"ownership": "generator", "disposition": "planned"},
            )
        self._consume_exported_bases(plan)
        self._source_plan_cache[str(plan.context.pkg_dir.resolve())] = plan
        return plan

    def _consume_exported_bases(self, plan: m.Infra.LazyInitPlan) -> None:
        """Attribute native class ancestry before sealing a package's source receipt.

        Explicit export-name inventories do not evaluate Rope's lazy base bindings.
        Resolve only this package's published local bindings; child decisions already
        replay their own receipts, and unrelated supplier modules are not traversed.

        Raises:
            ValueError: A published dependency source has no workspace resource.

        """
        project = self.rope_workspace.rope_project
        pending: list[p.Infra.RopePyObject] = []
        for module_name, name in dict.fromkeys(plan.lazy_map.values()):
            source = self._module_file(module_name)
            if source is None or source.parent != plan.context.pkg_dir:
                continue
            resource = self.rope_workspace.resource(source)
            if resource is None:
                msg = f"unindexed publication dependency source: {source}"
                raise ValueError(msg)
            module = u.Infra.resolve_pymodule(project, resource).get_module()
            binding = module.get_attributes().get(name)
            if binding is not None:
                pending.append(binding.get_object())
        visited: set[int] = set()
        while pending:
            owner = pending.pop()
            if u.Infra.instance_object(owner):
                owner = owner.get_type()
            if not u.Infra.abstract_class(owner) or id(owner) in visited:
                continue
            visited.add(id(owner))
            pending.extend(owner.get_superclasses())

    @override
    def context(self, pkg_dir: Path) -> m.Infra.LazyInitPackageContext:
        """Return the lazy-init package context for the requested package directory.

        Returns:
            The lazy-init package context for the requested package directory.

        """
        return self.rope_workspace.package_context(pkg_dir)


__all__: list[str] = ["FlextInfraCodegenLazyInitPlanner"]
