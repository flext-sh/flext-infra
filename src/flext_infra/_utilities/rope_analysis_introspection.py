"""Rope-backed class and module introspection helpers."""

from __future__ import annotations

from collections.abc import (
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)
from pathlib import Path
from typing import ClassVar

from flext_infra import (
    FlextInfraUtilitiesDiscovery,
    FlextInfraUtilitiesRopeCore,
    c,
    m,
    p,
    t,
)


class FlextInfraUtilitiesRopeAnalysisIntrospection:
    """Rope-backed class and module introspection helpers.

    Extracted mixin providing: get_class_nested_classes,
    get_module_symbols, extract_public_methods_from_dir.
    """

    _METHOD_KIND_LABELS: ClassVar[t.StrMapping] = {
        "staticmethod": "static",
        "classmethod": "class",
    }

    @staticmethod
    def _project_root_for_file(
        workspace_root: Path,
        file_path: Path,
    ) -> Path | None:
        scan_dirs = frozenset(c.Infra.MRO_SCAN_DIRECTORIES)
        for parent in file_path.parents:
            if (
                parent.name in scan_dirs
                and (parent.parent / "pyproject.toml").is_file()
            ):
                return parent.parent.resolve()
            if parent == workspace_root:
                return workspace_root
        return None

    @staticmethod
    def _package_name_for_dir(
        package_dir: Path,
        *,
        project_root: Path,
    ) -> str:
        try:
            relative_parts = package_dir.relative_to(project_root).parts
        except ValueError:
            return ""
        if not relative_parts:
            return ""
        root_name = relative_parts[0]
        package_parts = (
            relative_parts[1:]
            if root_name == c.Infra.DEFAULT_SRC_DIR
            else relative_parts
            if root_name in c.Infra.ROOT_WRAPPER_SEGMENTS
            else ()
        )
        return ".".join(package_parts)

    @classmethod
    def _module_name_for_file(
        cls,
        file_path: Path,
        *,
        project_root: Path,
    ) -> str:
        if file_path.name == c.Infra.INIT_PY:
            return cls._package_name_for_dir(
                file_path.parent,
                project_root=project_root,
            )
        package_name = cls._package_name_for_dir(
            file_path.parent,
            project_root=project_root,
        )
        return f"{package_name}.{file_path.stem}" if package_name else ""

    @classmethod
    def index_rope_workspace(
        cls,
        rope_project: t.Infra.RopeProject,
        workspace_root: Path,
    ) -> m.Infra.RopeWorkspaceIndex:
        """Build a generic Rope workspace index for package-oriented planning."""
        resolved_root = workspace_root.resolve()
        modules_by_path: dict[str, m.Infra.RopeModuleIndexEntry] = {}
        modules_by_dir: dict[Path, list[m.Infra.RopeModuleIndexEntry]] = {}
        package_dir_by_name: dict[str, Path] = {}
        project_package_by_root: dict[str, str] = {}
        package_dirs: set[Path] = set()
        for file_path in FlextInfraUtilitiesRopeCore.python_file_paths(rope_project):
            resolved_file_path = file_path.resolve()
            try:
                resource_path = resolved_file_path.relative_to(resolved_root).as_posix()
            except ValueError:
                continue
            package_dir = resolved_file_path.parent
            is_package_init = resolved_file_path.name == c.Infra.INIT_PY
            project_root = cls._project_root_for_file(
                resolved_root,
                resolved_file_path,
            )
            module_name = (
                cls._module_name_for_file(
                    resolved_file_path,
                    project_root=project_root,
                )
                if project_root is not None
                else ""
            )
            package_name = (
                cls._package_name_for_dir(
                    package_dir,
                    project_root=project_root,
                )
                if project_root is not None
                else module_name
                if is_package_init
                else module_name.rsplit(".", maxsplit=1)[0]
                if "." in module_name
                else ""
            )
            entry = m.Infra.RopeModuleIndexEntry(
                file_path=resolved_file_path,
                resource_path=resource_path,
                module_name=module_name,
                package_name=package_name,
                package_dir=package_dir,
                project_root=project_root,
                is_package_init=is_package_init,
            )
            modules_by_path[str(resolved_file_path)] = entry
            modules_by_dir.setdefault(package_dir, []).append(entry)
            package_dirs.add(package_dir)
            if package_name:
                package_dir_by_name[package_name] = package_dir
                if (
                    project_root is not None
                    and "." not in package_name
                    and package_dir.parent.name == c.Infra.DEFAULT_SRC_DIR
                ):
                    project_package_by_root[str(project_root)] = package_name
        sorted_package_dirs = tuple(sorted(package_dirs))
        package_dir_set = frozenset(sorted_package_dirs)
        direct_children_by_dir: dict[Path, list[Path]] = {
            package_dir: [] for package_dir in sorted_package_dirs
        }
        descendants_by_dir: dict[Path, list[Path]] = {
            package_dir: [] for package_dir in sorted_package_dirs
        }
        for package_dir in sorted_package_dirs:
            parent_dir = package_dir.parent
            if parent_dir in package_dir_set:
                direct_children_by_dir[parent_dir].append(package_dir)
            for ancestor_dir in package_dir.parents:
                if ancestor_dir == package_dir:
                    continue
                if ancestor_dir in package_dir_set:
                    descendants_by_dir[ancestor_dir].append(package_dir)
        packages_by_dir: dict[str, m.Infra.RopePackageIndexEntry] = {}
        for package_dir in sorted_package_dirs:
            dir_modules = tuple(
                sorted(
                    modules_by_dir.get(package_dir, ()),
                    key=lambda entry: entry.file_path.name,
                ),
            )
            init_path = (package_dir / c.Infra.INIT_PY).resolve()
            init_entry = modules_by_path.get(str(init_path))
            project_root = (
                init_entry.project_root
                if init_entry is not None
                else next(
                    (
                        entry.project_root
                        for entry in dir_modules
                        if entry.project_root is not None
                    ),
                    None,
                )
            )
            package_name = (
                cls._package_name_for_dir(
                    package_dir,
                    project_root=project_root,
                )
                if project_root is not None
                else init_entry.package_name
                if init_entry is not None
                else ""
            )
            if package_name and package_name not in package_dir_by_name:
                package_dir_by_name[package_name] = package_dir
            if (
                project_root is not None
                and "." not in package_name
                and package_dir.parent.name == c.Infra.DEFAULT_SRC_DIR
                and str(project_root) not in project_package_by_root
            ):
                project_package_by_root[str(project_root)] = package_name
            direct_child_dirs = tuple(direct_children_by_dir.get(package_dir, ()))
            descendant_child_dirs = tuple(descendants_by_dir.get(package_dir, ()))
            packages_by_dir[str(package_dir)] = m.Infra.RopePackageIndexEntry(
                package_dir=package_dir,
                init_path=init_path,
                package_name=package_name,
                project_root=project_root,
                modules=dir_modules,
                direct_child_dirs=direct_child_dirs,
                descendant_child_dirs=descendant_child_dirs,
            )
        return m.Infra.RopeWorkspaceIndex(
            workspace_root=resolved_root,
            package_dirs=sorted_package_dirs,
            packages_by_dir=packages_by_dir,
            modules_by_path=modules_by_path,
            package_dir_by_name=package_dir_by_name,
            project_package_by_root=project_package_by_root,
        )

    @staticmethod
    def get_class_nested_classes(
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
        class_name: str,
    ) -> t.StrSequence:
        """Return names of nested classes within a given class."""
        result: list[str] = []
        try:
            pymodule = FlextInfraUtilitiesRopeCore.get_pymodule(rope_project, resource)
            attributes = pymodule.get_attributes()
            if class_name not in attributes:
                return result
            obj = attributes[class_name].get_object()
            if not isinstance(obj, FlextInfraUtilitiesRopeCore.ABSTRACT_CLASS_TYPES):
                return result
            for name, pyname in obj.get_attributes().items():
                child = pyname.get_object()
                if isinstance(child, FlextInfraUtilitiesRopeCore.ABSTRACT_CLASS_TYPES):
                    result.append(name)
        except FlextInfraUtilitiesRopeCore.RUNTIME_ERRORS:
            return result
        return result

    @staticmethod
    def get_module_symbols(
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
    ) -> Sequence[m.Infra.SymbolInfo]:
        """Return top-level symbols defined in one module through Rope metadata."""
        result: MutableSequence[m.Infra.SymbolInfo] = []
        try:
            pymodule = FlextInfraUtilitiesRopeCore.get_pymodule(rope_project, resource)
            resource_path = resource.path
            for name, pyname in pymodule.get_attributes().items():
                obj = pyname.get_object()
                module, line = pyname.get_definition_location()
                origin = module.get_resource() if module is not None else None
                if line is None or origin is None or origin.path != resource_path:
                    continue
                kind = "assignment"
                if isinstance(obj, FlextInfraUtilitiesRopeCore.ABSTRACT_CLASS_TYPES):
                    kind = "class"
                elif isinstance(obj, FlextInfraUtilitiesRopeCore.PY_FUNCTION_TYPES):
                    kind = "function"
                result.append(m.Infra.SymbolInfo(name=name, kind=kind, line=line))
        except FlextInfraUtilitiesRopeCore.RUNTIME_ERRORS:
            return result
        return sorted(result, key=lambda symbol: symbol.line)

    @classmethod
    def extract_public_methods_from_dir(
        cls: type[p.Infra.RopeAnalysisMethods],
        package_dir: Path,
    ) -> Mapping[str, Sequence[t.Triple[str, str, str]]]:
        """Extract public methods from all Python files in a package directory."""
        result: MutableMapping[str, MutableSequence[t.Triple[str, str, str]]] = {}
        project_root = FlextInfraUtilitiesDiscovery.project_root(
            package_dir / "foo.py",
        )
        if project_root is None:
            return result
        with FlextInfraUtilitiesRopeCore.open_project(project_root.parent) as rope_proj:
            for py_file in sorted(package_dir.glob(c.Infra.EXT_PYTHON_GLOB)):
                if py_file.name == c.Infra.INIT_PY:
                    continue
                resource = cls.get_resource_from_path(rope_proj, py_file)
                if resource is None:
                    continue
                classes = cls.get_module_classes(rope_proj, resource)
                for class_name in classes:
                    class_methods = cls.get_class_methods(
                        rope_proj,
                        resource,
                        class_name,
                        include_private=False,
                    )
                    methods = result.setdefault(class_name, [])
                    for method_name, method_kind in class_methods.items():
                        methods.append((
                            method_name,
                            FlextInfraUtilitiesRopeAnalysisIntrospection._METHOD_KIND_LABELS.get(
                                method_kind, "instance"
                            ),
                            py_file.name,
                        ))
        return result


__all__: list[str] = ["FlextInfraUtilitiesRopeAnalysisIntrospection"]
