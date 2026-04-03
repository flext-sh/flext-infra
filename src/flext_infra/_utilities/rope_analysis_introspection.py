# pyright: reportMissingTypeStubs=false
"""Rope-backed class and module introspection helpers."""

from __future__ import annotations

import re
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

    Extracted mixin providing: get_all_class_names, get_class_nested_classes,
    get_module_symbols, get_class_constants, get_class_inner_classes,
    extract_public_methods_from_dir, extract_public_methods_from_file.
    """

    @staticmethod
    def get_all_class_names(
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
    ) -> Sequence[tuple[str, int, Sequence[str]]]:
        """Return (name, line, bases) for all classes."""
        # Uses get_class_info from the main class via late import
        from flext_infra import FlextInfraUtilitiesRopeAnalysis  # noqa: PLC0415

        return [
            (info.name, info.line, list(info.bases))
            for info in FlextInfraUtilitiesRopeAnalysis.get_class_info(
                rope_project,
                resource,
            )
        ]

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

    @staticmethod
    def get_class_constants(
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
        class_name: str,
    ) -> Sequence[m.Infra.ConstantInfo]:
        """Return Final-annotated constants inside a class."""
        result: MutableSequence[m.Infra.ConstantInfo] = []
        source = resource.read()
        try:
            pycore = FlextInfraUtilitiesRopeAnalysisIntrospection.get_pycore(
                rope_project,
            )
            pymodule = pycore.resource_to_pyobject(resource)
            attributes = pymodule.get_attributes()
            if class_name not in attributes:
                return result
            class_object = attributes[class_name].get_object()
            if not isinstance(class_object, p.Infra.RopeAbstractClassLike):
                return result
            source_lines = source.splitlines()
            for attr_name, pyname in class_object.get_attributes().items():
                _, line_candidate = pyname.get_definition_location()
                if line_candidate is None or line_candidate > len(source_lines):
                    continue
                line_text = source_lines[line_candidate - 1]
                if "Final" not in line_text:
                    continue
                annotation_match = re.search(r":\s*(.+?)\s*=", line_text)
                value_match = re.search(r"=\s*(.+)$", line_text.strip())
                result.append(
                    m.Infra.ConstantInfo(
                        name=attr_name,
                        annotation=annotation_match.group(1).strip()
                        if annotation_match
                        else "",
                        line=line_candidate,
                        value=value_match.group(1).strip() if value_match else "",
                        class_path=class_name,
                    )
                )
        except (RefactoringError, ResourceNotFoundError, AttributeError):
            return result
        return result

    @staticmethod
    def get_class_inner_classes(
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
        class_name: str,
    ) -> Sequence[m.Infra.ClassInfo]:
        """Return ClassInfo for nested classes within a given class."""
        result: MutableSequence[m.Infra.ClassInfo] = []
        try:
            pycore = FlextInfraUtilitiesRopeAnalysisIntrospection.get_pycore(
                rope_project,
            )
            pymodule = pycore.resource_to_pyobject(resource)
            attributes = pymodule.get_attributes()
            if class_name not in attributes:
                return result
            class_object = attributes[class_name].get_object()
            if not isinstance(class_object, p.Infra.RopeAbstractClassLike):
                return result
            for name, pyname in class_object.get_attributes().items():
                child = pyname.get_object()
                if not isinstance(child, p.Infra.RopeAbstractClassLike):
                    continue
                _, line_candidate = pyname.get_definition_location()
                bases = [
                    base_name
                    for base in child.get_superclasses()
                    if (base_name := base.get_name()) is not None
                ]
                result.append(
                    m.Infra.ClassInfo(
                        name=name,
                        line=line_candidate or 0,
                        bases=tuple(bases),
                    )
                )
        except (RefactoringError, ResourceNotFoundError, AttributeError):
            return result
        return result

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
            from flext_infra import FlextInfraUtilitiesRopeAnalysis  # noqa: PLC0415

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
            from flext_infra import FlextInfraUtilitiesRopeAnalysis  # noqa: PLC0415

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
