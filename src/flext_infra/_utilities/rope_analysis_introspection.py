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
