# pyright: reportMissingTypeStubs=false
"""Rope-backed class and module introspection helpers."""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping, MutableSequence, Sequence
from pathlib import Path

from rope.base.exceptions import RefactoringError, ResourceNotFoundError

from flext_infra import (
    FlextInfraUtilitiesDiscovery,
    FlextInfraUtilitiesRopeCore,
    c,
    m,
    p,
    t,
)


class FlextInfraUtilitiesRopeAnalysisIntrospection(
    FlextInfraUtilitiesDiscovery,
    FlextInfraUtilitiesRopeCore,
):
    """Rope-backed class and module introspection helpers.

    Extracted mixin providing: get_class_nested_classes,
    get_module_symbols, extract_public_methods_from_dir,
    extract_public_methods_from_file.
    """

    @staticmethod
    def get_class_nested_classes(
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
        class_name: str,
    ) -> t.StrSequence:
        """Return names of nested classes within a given class."""
        result: list[str] = []
        try:
            pycore = FlextInfraUtilitiesRopeAnalysisIntrospection.get_pycore(
                rope_project,
            )
            pymodule = pycore.resource_to_pyobject(resource)
            attributes = pymodule.get_attributes()
            if class_name not in attributes:
                return result
            obj = attributes[class_name].get_object()
            if not isinstance(obj, p.Infra.RopeAbstractClassLike):
                return result
            for name, pyname in obj.get_attributes().items():
                if isinstance(pyname.get_object(), p.Infra.RopeAbstractClassLike):
                    result.append(name)
        except (RefactoringError, ResourceNotFoundError, AttributeError):
            return result
        return result

    @staticmethod
    def get_module_symbols(
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
    ) -> Sequence[m.Infra.SymbolInfo]:
        """Return all top-level symbols with metadata."""
        result: MutableSequence[m.Infra.SymbolInfo] = []
        try:
            pycore = FlextInfraUtilitiesRopeAnalysisIntrospection.get_pycore(
                rope_project,
            )
            pymodule = pycore.resource_to_pyobject(resource)
            resource_path = resource.path
            for name, pyname in pymodule.get_attributes().items():
                obj = pyname.get_object()
                _, line_candidate = pyname.get_definition_location()
                line = line_candidate or 0
                module = obj.get_module()
                origin = module.get_resource() if module is not None else None
                if origin is not None and origin.path != resource_path:
                    continue
                if isinstance(obj, p.Infra.RopeAbstractClassLike):
                    kind = "class"
                elif isinstance(obj, p.Infra.RopePyFunctionLike):
                    kind = "function"
                else:
                    kind = "assignment"
                result.append(m.Infra.SymbolInfo(name=name, kind=kind, line=line))
        except (RefactoringError, ResourceNotFoundError, AttributeError):
            return result
        return sorted(result, key=lambda symbol: symbol.line)

    @classmethod
    def extract_public_methods_from_dir(
        cls,
        package_dir: Path,
    ) -> Mapping[str, Sequence[t.Infra.Triple[str, str, str]]]:
        """Extract public methods from all Python files in a package directory."""
        result: MutableMapping[str, MutableSequence[t.Infra.Triple[str, str, str]]] = {}
        project_root = cls.discover_project_root_from_file(package_dir / "foo.py")
        if project_root is None:
            return result
        rope_proj = cls.init_rope_project(project_root.parent)
        try:
            from flext_infra import FlextInfraUtilitiesRopeAnalysis

            for py_file in sorted(package_dir.glob(c.Infra.Extensions.PYTHON_GLOB)):
                if py_file.name == c.Infra.Files.INIT_PY:
                    continue
                resource = cls.get_resource_from_path(rope_proj, py_file)
                if resource is None:
                    continue
                classes = FlextInfraUtilitiesRopeAnalysis.get_module_classes(
                    rope_proj, resource
                )
                for class_name in classes:
                    class_methods = FlextInfraUtilitiesRopeAnalysis.get_class_methods(
                        rope_proj,
                        resource,
                        class_name,
                        include_private=False,
                    )
                    methods = result.setdefault(class_name, [])
                    for method_name, method_kind in class_methods.items():
                        methods.append((
                            method_name,
                            cls._method_kind_label(method_kind),
                            py_file.name,
                        ))
        finally:
            rope_proj.close()
        return result

    @classmethod
    def extract_public_methods_from_file(
        cls,
        file_path: Path,
    ) -> Mapping[str, Sequence[t.Infra.Triple[str, str, str]]]:
        """Extract public methods from a single Python file."""
        if not file_path.exists():
            return {}
        result: MutableMapping[str, MutableSequence[t.Infra.Triple[str, str, str]]] = {}
        project_root = cls.discover_project_root_from_file(file_path)
        if project_root is None:
            return result
        rope_proj = cls.init_rope_project(project_root.parent)
        try:
            from flext_infra import FlextInfraUtilitiesRopeAnalysis

            resource = cls.get_resource_from_path(rope_proj, file_path)
            if resource is None:
                return {}
            classes = FlextInfraUtilitiesRopeAnalysis.get_module_classes(
                rope_proj, resource
            )
            for class_name in classes:
                class_methods = FlextInfraUtilitiesRopeAnalysis.get_class_methods(
                    rope_proj,
                    resource,
                    class_name,
                    include_private=False,
                )
                methods = result.setdefault(class_name, [])
                for method_name, method_kind in class_methods.items():
                    methods.append((
                        method_name,
                        cls._method_kind_label(method_kind),
                        file_path.name,
                    ))
        finally:
            rope_proj.close()
        return result

    @staticmethod
    def _method_kind_label(method_kind: str) -> str:
        """Normalize Rope method kinds to census labels."""
        if method_kind == "staticmethod":
            return "static"
        if method_kind == "classmethod":
            return "class"
        return "instance"


__all__ = ["FlextInfraUtilitiesRopeAnalysisIntrospection"]
