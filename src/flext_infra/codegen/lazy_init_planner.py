"""Lazy-init planning over generic Rope workspace indexes."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Annotated

from pydantic import Field, PrivateAttr

from flext_infra import c, m, p, t, u


class FlextInfraCodegenLazyInitPlanner(m.ArbitraryTypesModel):
    """Resolve lazy-init plans using one shared Rope workspace index."""

    rope_workspace: Annotated[
        p.Infra.RopeWorkspaceDsl,
        t.SkipValidation,
        Field(description="Shared Rope workspace DSL reused by the planner"),
    ]
    lazy_init: m.Infra.LazyInitConfig = Field(
        description="Validated lazy-init policy document",
    )

    _module_exports_cache: dict[
        tuple[str, bool, bool, bool],
        t.Infra.LazyImportMap,
    ] = PrivateAttr(default_factory=dict)
    _package_exports_cache: dict[str, frozenset[str]] = PrivateAttr(
        default_factory=dict
    )
    _source_exports_cache: dict[str, frozenset[str]] = PrivateAttr(default_factory=dict)
    _source_plan_cache: dict[str, m.Infra.LazyInitPlan] = PrivateAttr(
        default_factory=dict
    )
    _source_exports_visiting: set[str] = PrivateAttr(default_factory=set)
    _parent_package_cache: dict[str, t.StrSequence] = PrivateAttr(default_factory=dict)
    _version_module_name: str = PrivateAttr(default=f"{c.Infra.DUNDER_VERSION}.py")

    def build_plan(
        self,
        pkg_dir: Path,
        *,
        dir_exports: Mapping[str, t.Infra.LazyImportMap],
    ) -> m.Infra.LazyInitPlan:
        """Build the lazy-init render plan for one package directory."""
        context = self._context(pkg_dir)
        empty_action: t.Infra.LazyInitAction = (
            "remove" if context.generated_init else "skip"
        )
        if not context.importable:
            return m.Infra.LazyInitPlan(context=context, action=empty_action)
        lazy_map = self._package_exports(context)
        version_map = self._module_exports(
            context.pkg_dir / self._version_module_name,
            f"{context.current_pkg}.{c.Infra.DUNDER_VERSION}",
            include_dunder=True,
        )
        child_lazy, child_tc = self._merge_children(
            context.pkg_dir, lazy_map, dir_exports
        )
        for name, target in version_map.items():
            lazy_map.setdefault(name, target)
        self._resolve_aliases(
            lazy_map,
            current_pkg=context.current_pkg,
            pkg_dir=context.pkg_dir,
            surface=context.surface,
        )
        for name in c.Infra.INFRA_ONLY_EXPORTS:
            lazy_map.pop(name, None)
        if not lazy_map:
            return m.Infra.LazyInitPlan(context=context, action=empty_action)
        return m.Infra.LazyInitPlan(
            context=context,
            action="write",
            exports=tuple(sorted(lazy_map)),
            lazy_map=dict(lazy_map),
            wildcard_runtime_modules=tuple(
                sorted({module_name for module_name, _attr in version_map.values()}),
            ),
            child_packages_for_lazy=child_lazy,
            child_packages_for_tc=child_tc,
        )

    def _context(self, pkg_dir: Path) -> m.Infra.LazyInitPackageContext:
        return self.rope_workspace.context(pkg_dir)

    def _package_exports(
        self,
        context: m.Infra.LazyInitPackageContext,
    ) -> t.Infra.MutableLazyImportMap:
        package_entry = self._package_entry(context.pkg_dir)
        if package_entry is None:
            return {}
        index: t.Infra.MutableLazyImportMap = {}
        skip_names = {c.Infra.INIT_PY, "__main__.py", self._version_module_name}
        for module_entry in package_entry.modules:
            py_file = module_entry.file_path
            child_dir = py_file.parent / py_file.stem
            child_entry = self._package_entry(child_dir)
            if py_file.name in skip_names or (
                child_entry is not None and child_entry.package_name
            ):
                continue
            convention = self.rope_workspace.convention(
                py_file,
                rel_path=py_file.relative_to(context.pkg_dir),
            )
            policy = convention.module_policy
            if not policy.include_in_lazy_init or not module_entry.module_name:
                continue
            targets = self._module_exports(
                py_file,
                convention.module_name,
                allow_main=policy.allow_main_export,
                allow_assignments=policy.allow_type_alias
                or policy.expected_alias is not None,
            )
            if (
                policy.expected_alias
                and targets
                and "." not in context.current_pkg
                and u.Infra.is_root_namespace_file(py_file.name)
            ):
                targets.setdefault(
                    policy.expected_alias,
                    (module_entry.module_name, policy.expected_alias),
                )
            if not policy.export_symbols or (
                not targets
                and not policy.enforce_contract
                and "." in context.current_pkg
            ):
                self._add(index, py_file.stem, (module_entry.module_name, ""))
                continue
            for name, target in targets.items():
                self._add(index, name, target)
        return index

    def _module_exports(
        self,
        py_file: Path,
        module_path: str,
        *,
        include_dunder: bool = False,
        allow_main: bool = False,
        allow_assignments: bool = False,
    ) -> t.Infra.MutableLazyImportMap:
        cache_key = (
            str(py_file.resolve()),
            include_dunder,
            allow_main,
            allow_assignments,
        )
        cached = self._module_exports_cache.get(cache_key)
        if cached is not None:
            return dict(cached)
        if self.rope_workspace.resource(py_file) is None:
            return {}
        names = self.rope_workspace.exports(
            py_file,
            include_dunder=include_dunder,
            allow_main=allow_main,
            allow_assignments=allow_assignments,
        )
        exports = {
            name: (module_path, name)
            for name in names
            if include_dunder or self._publish(name, allow_main=allow_main)
        }
        self._module_exports_cache[cache_key] = exports
        return dict(exports)

    def _merge_children(
        self,
        pkg_dir: Path,
        lazy_map: t.Infra.MutableLazyImportMap,
        dir_exports: Mapping[str, t.Infra.LazyImportMap],
    ) -> tuple[t.StrSequence, t.StrSequence]:
        package_entry = self._package_entry(pkg_dir)
        if package_entry is None:
            return ((), ())
        direct: list[str] = []
        descendants: list[str] = []
        for child_dir in package_entry.descendant_child_dirs:
            child_init = child_dir / c.Infra.INIT_PY
            if not child_init.is_file():
                continue
            child_entry = self._package_entry(child_dir)
            if child_entry is None or not child_entry.package_name:
                continue
            descendants.append(child_entry.package_name)
            if child_dir.parent != pkg_dir:
                continue
            direct.append(child_entry.package_name)
            for name, (module_name, attr) in dir_exports.get(
                str(child_dir), {}
            ).items():
                if (
                    attr
                    and name not in c.Infra.ALIAS_NAMES
                    and name != "main"
                    and self._publish(name, allow_main=False)
                ):
                    self._add(lazy_map, name, (module_name, attr))
        return (tuple(sorted(direct)), tuple(sorted(descendants)))

    def _resolve_aliases(
        self,
        lazy_map: t.Infra.MutableLazyImportMap,
        *,
        current_pkg: str,
        pkg_dir: Path,
        surface: str,
    ) -> None:
        if not current_pkg or "." in current_pkg:
            return
        inherited_key = (
            surface if surface in self.lazy_init.inherited_exports else "src"
        )
        inherited_packages = self._resolve_transitive_parent_packages((
            *self._parent_packages(pkg_dir),
            self._source_package_name(pkg_dir, inherited_key),
        ))
        for alias_name in self.lazy_init.inherited_exports.get(inherited_key, ()):
            existing = lazy_map.get(alias_name)
            if existing is not None and existing[0].startswith(current_pkg):
                continue
            package_name = self._resolve_inherited_alias_source(
                inherited_packages,
                alias_name,
            )
            if package_name:
                lazy_map[alias_name] = (package_name, alias_name)

    def _resolve_transitive_parent_packages(
        self,
        package_names: t.StrSequence,
    ) -> tuple[str, ...]:
        ordered: list[str] = []
        for package_name in package_names:
            if not package_name or package_name in ordered:
                continue
            package_dir = self.rope_workspace.workspace_index.package_dir_by_name.get(
                package_name
            )
            if package_dir is not None:
                ordered.extend(
                    self._resolve_transitive_parent_packages(
                        self._parent_packages(package_dir)
                    )
                )
            if package_name not in ordered:
                ordered.append(package_name)
        return tuple(ordered)

    def _parent_packages(self, pkg_dir: Path) -> t.StrSequence:
        cache_key = str(pkg_dir.resolve())
        cached = self._parent_package_cache.get(cache_key)
        if cached is not None:
            return cached
        package_entry = self._package_entry(pkg_dir)
        current_pkg = package_entry.package_name if package_entry is not None else ""
        constants_path = (pkg_dir / c.Infra.CONSTANTS_PY).resolve()
        if self.rope_workspace.resource(constants_path) is None:
            self._parent_package_cache[cache_key] = ()
            return ()
        state = self.rope_workspace.semantic(constants_path)
        base_packages = tuple(
            package_name
            for class_info in state.class_infos
            if "Constants" in class_info.name
            for base_name in class_info.bases
            if (
                package_name := self._package_name_from_target(
                    state.declared_imports.get(base_name)
                    or state.semantic_imports.get(base_name, "")
                )
            )
        )
        declared_packages = tuple(
            package_name
            for target in state.declared_imports.values()
            if (package_name := self._package_name_from_target(target))
        )
        parents = tuple(
            dict.fromkeys(
                package_name
                for package_name in (*base_packages, *declared_packages)
                if package_name and package_name != current_pkg
            )
        )
        self._parent_package_cache[cache_key] = parents
        return parents

    def _resolve_inherited_alias_source(
        self,
        package_names: t.StrSequence,
        alias_name: str,
    ) -> str:
        for package_name in reversed(tuple(name for name in package_names if name)):
            if alias_name in self._export_names_for_package(package_name):
                return package_name
        return ""

    def _export_names_for_package(self, package_name: str) -> frozenset[str]:
        cached = self._package_exports_cache.get(package_name)
        if cached is not None:
            return cached
        exports = frozenset((
            *self._package_init_exports(package_name),
            *self._source_export_names_for_package(package_name),
        ))
        self._package_exports_cache[package_name] = exports
        return exports

    def _package_init_exports(self, package_name: str) -> frozenset[str]:
        package_dir = self.rope_workspace.workspace_index.package_dir_by_name.get(
            package_name
        )
        if package_dir is None:
            return frozenset()
        init_path = package_dir / c.Infra.INIT_PY
        if self.rope_workspace.resource(init_path) is None:
            return frozenset()
        return frozenset(
            self.rope_workspace.exports(
                init_path,
                allow_assignments=True,
            ),
        )

    def _source_export_names_for_package(self, package_name: str) -> frozenset[str]:
        cached = self._source_exports_cache.get(package_name)
        if cached is not None:
            return cached
        if package_name in self._source_exports_visiting:
            return frozenset()
        package_dir = self.rope_workspace.workspace_index.package_dir_by_name.get(
            package_name
        )
        if package_dir is None:
            return frozenset()
        self._source_exports_visiting.add(package_name)
        try:
            cache_key = str(package_dir.resolve())
            plan = self._source_plan_cache.get(cache_key)
            if plan is None:
                plan = self.build_plan(package_dir, dir_exports={})
                self._source_plan_cache[cache_key] = plan
            exports = frozenset(plan.exports)
        finally:
            self._source_exports_visiting.remove(package_name)
        self._source_exports_cache[package_name] = exports
        return exports

    def _source_package_name(self, pkg_dir: Path, inherited_key: str) -> str:
        if inherited_key == "src":
            return ""
        package_entry = self._package_entry(pkg_dir)
        if package_entry is None or package_entry.project_root is None:
            return ""
        return self.rope_workspace.workspace_index.project_package_by_root.get(
            str(package_entry.project_root),
            "",
        )

    def _package_name_from_target(self, target: str) -> str:
        parts = tuple(part for part in target.split(".") if part)
        for size in range(len(parts), 0, -1):
            package_name = ".".join(parts[:size])
            if package_name in self.rope_workspace.workspace_index.package_dir_by_name:
                return package_name
        return ""

    def _package_entry(
        self,
        pkg_dir: Path,
    ) -> m.Infra.RopePackageIndexEntry | None:
        return self.rope_workspace.package(pkg_dir)

    @staticmethod
    def _publish(name: str, *, allow_main: bool) -> bool:
        return (
            not name.startswith("_")
            and name not in c.Infra.INFRA_ONLY_EXPORTS
            and name not in {c.Infra.DUNDER_INIT, "pytestmark"}
            and (name != "main" or allow_main)
        )

    @staticmethod
    def _add(
        index: t.Infra.MutableLazyImportMap,
        name: str,
        target: t.Infra.StrPair,
    ) -> None:
        existing = index.get(name)
        if existing is None or existing == target:
            index[name] = target
            return
        left = f"{existing[0]}.{existing[1]}".rstrip(".")
        right = f"{target[0]}.{target[1]}".rstrip(".")
        message = f"export collision for {name!r}: {left} != {right}"
        raise ValueError(message)


__all__: list[str] = ["FlextInfraCodegenLazyInitPlanner"]
