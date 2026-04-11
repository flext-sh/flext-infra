"""Lazy-init export planning."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from flext_infra import (
    FlextInfraUtilitiesCodegenNamespace,
    FlextInfraUtilitiesDiscovery,
    FlextInfraUtilitiesDocsScope,
    FlextInfraUtilitiesRope,
    c,
    m,
    t,
)
from flext_infra._utilities.base import FlextInfraUtilitiesBase
from flext_infra._utilities.iteration import FlextInfraUtilitiesIteration


class FlextInfraUtilitiesCodegenLazyAliases:
    """Build lazy-init plans from package files, Rope exports, and MRO aliases."""

    def __init__(self, workspace_root: Path | None = None) -> None:
        self._workspace_root = workspace_root or Path.cwd()
        self._lazy_init = FlextInfraUtilitiesBase.load_tool_config().unwrap().lazy_init

    def build_lazy_init_plan(
        self,
        pkg_dir: Path,
        *,
        dir_exports: Mapping[str, t.Infra.LazyImportMap],
    ) -> m.Infra.LazyInitPlan:
        init_path = pkg_dir / c.Infra.INIT_PY
        current_pkg = FlextInfraUtilitiesDiscovery.discover_package_from_file(init_path)
        context = m.Infra.LazyInitPackageContext(
            pkg_dir=pkg_dir,
            init_path=init_path,
            current_pkg=current_pkg,
            surface=current_pkg.split(".", maxsplit=1)[0] if current_pkg else "",
            generated_init=init_path.is_file()
            and init_path.read_text(encoding=c.Infra.ENCODING_DEFAULT).startswith(
                c.Infra.AUTOGEN_HEADER,
            ),
            importable=bool(current_pkg),
        )
        empty_action: t.Infra.LazyInitAction = (
            "remove" if context.generated_init else "skip"
        )
        if not context.importable:
            return m.Infra.LazyInitPlan(context=context, action=empty_action)
        with FlextInfraUtilitiesRope.open_project(self._workspace_root) as project:
            lazy_map = self._package_exports(project, pkg_dir, context.current_pkg)
            version_map = self._rope_exports(
                project,
                pkg_dir / "__version__.py",
                f"{context.current_pkg}.{c.Infra.DUNDER_VERSION}",
                include_dunder=True,
            )
        child_lazy, child_tc = self._merge_children(pkg_dir, lazy_map, dir_exports)
        for name, target in version_map.items():
            lazy_map.setdefault(name, target)
        self._resolve_aliases(
            lazy_map,
            current_pkg=context.current_pkg,
            pkg_dir=pkg_dir,
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
                sorted({module for module, _attr in version_map.values()}),
            ),
            child_packages_for_lazy=child_lazy,
            child_packages_for_tc=child_tc,
        )

    @classmethod
    def _package_exports(
        cls,
        project: t.Infra.RopeProject,
        pkg_dir: Path,
        current_pkg: str,
    ) -> t.Infra.MutableLazyImportMap:
        index: t.Infra.MutableLazyImportMap = {}
        skip_names = {c.Infra.INIT_PY, "__main__.py", "__version__.py"}
        for py_file in FlextInfraUtilitiesIteration.iter_directory_python_files(
            pkg_dir
        ):
            if (
                py_file.parent != pkg_dir
                or py_file.name in skip_names
                or (py_file.parent / py_file.stem / c.Infra.INIT_PY).exists()
            ):
                continue
            rel_path = py_file.relative_to(pkg_dir)
            policy = FlextInfraUtilitiesCodegenNamespace.module_policy(
                py_file,
                rel_path=rel_path,
                current_pkg=current_pkg,
            )
            module_path = (
                FlextInfraUtilitiesDiscovery.discover_package_from_file(py_file)
                if policy.include_in_lazy_init
                else ""
            )
            if not module_path:
                continue
            targets = cls._rope_exports(
                project,
                py_file,
                module_path,
                allow_main=policy.allow_main_export,
            )
            if (
                policy.expected_alias
                and targets
                and "." not in current_pkg
                and FlextInfraUtilitiesCodegenNamespace.is_root_namespace_file(
                    py_file.name,
                )
            ):
                targets.setdefault(
                    policy.expected_alias, (module_path, policy.expected_alias)
                )
            if not policy.export_symbols or (
                not targets and not policy.enforce_contract and "." in current_pkg
            ):
                cls._add(index, py_file.stem, (module_path, ""))
                continue
            for name, target in targets.items():
                cls._add(index, name, target)
        return index

    @classmethod
    def _rope_exports(
        cls,
        project: t.Infra.RopeProject,
        py_file: Path,
        module_path: str,
        *,
        include_dunder: bool = False,
        allow_main: bool = False,
    ) -> t.Infra.MutableLazyImportMap:
        if not py_file.is_file():
            return {}
        resource = FlextInfraUtilitiesRope.get_resource_from_path(project, py_file)
        if resource is None:
            return {}
        try:
            names = FlextInfraUtilitiesRope.get_module_export_names(
                project,
                resource,
                include_dunder=include_dunder,
                allow_main=allow_main,
            )
        except FlextInfraUtilitiesRope.RUNTIME_ERRORS:
            return {}
        return {
            name: (module_path, name)
            for name in names
            if include_dunder or cls._publish(name, allow_main=allow_main)
        }

    @classmethod
    def _merge_children(
        cls,
        pkg_dir: Path,
        lazy_map: t.Infra.MutableLazyImportMap,
        dir_exports: Mapping[str, t.Infra.LazyImportMap],
    ) -> tuple[t.StrSequence, t.StrSequence]:
        direct: list[str] = []
        descendants: list[str] = []
        for key, exports in sorted(dir_exports.items()):
            child_dir = Path(key)
            if child_dir == pkg_dir or pkg_dir not in child_dir.parents:
                continue
            child_pkg = FlextInfraUtilitiesDiscovery.discover_package_from_file(
                child_dir / c.Infra.INIT_PY,
            )
            if not child_pkg:
                continue
            descendants.append(child_pkg)
            if child_dir.parent != pkg_dir:
                continue
            direct.append(child_pkg)
            for name, (module, attr) in exports.items():
                if (
                    attr
                    and not name.isupper()
                    and name not in c.Infra.ALIAS_NAMES
                    and name != "main"
                    and cls._publish(name, allow_main=False)
                ):
                    cls._add(lazy_map, name, (module, attr))
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
            surface if surface in self._lazy_init.inherited_exports else "src"
        )
        allowed = self._lazy_init.inherited_exports.get(inherited_key, ())
        parent_packages = FlextInfraUtilitiesDiscovery.resolve_parent_constants_mro(
            pkg_dir,
            return_module=True,
        )
        project_root = FlextInfraUtilitiesDiscovery.discover_project_root_from_file(
            pkg_dir
        )
        source_name = (
            FlextInfraUtilitiesDocsScope.package_name(project_root)
            if inherited_key != "src" and project_root
            else ""
        )
        for package_name in (*parent_packages, source_name):
            for alias_name in allowed:
                if package_name:
                    lazy_map.setdefault(alias_name, (package_name, alias_name))

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


__all__ = ["FlextInfraUtilitiesCodegenLazyAliases"]
