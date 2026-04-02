# pyright: reportMissingTypeStubs=false
"""Semantic Rope analysis helpers."""

from __future__ import annotations

import re
from collections.abc import MutableSequence, Sequence

from rope.base.exceptions import RefactoringError, ResourceNotFoundError

from flext_infra import c, m, p, t
from flext_infra._utilities.rope_core import FlextInfraUtilitiesRopeCore


class FlextInfraUtilitiesRopeAnalysis(FlextInfraUtilitiesRopeCore):
    """Rope-backed semantic analysis helpers."""

    @staticmethod
    def find_definition_offset(
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
        symbol: str,
    ) -> int | None:
        """Return offset of symbol's definition via semantic analysis."""
        source = resource.read()
        try:
            pycore = FlextInfraUtilitiesRopeAnalysis.get_pycore(rope_project)
            pyobject = pycore.resource_to_pyobject(resource)
            attributes = pyobject.get_attributes()
            if symbol not in attributes:
                return None
            pyname = attributes[symbol]
            definition_module, definition_line = pyname.get_definition_location()
            if definition_module is not None:
                definition_resource = definition_module.get_resource()
                if definition_resource is not None:
                    source = definition_resource.read()
            if definition_line is None:
                return None
            return FlextInfraUtilitiesRopeAnalysis._line_offset_for_symbol(
                source=source,
                line_number=definition_line,
                symbol=symbol,
            )
        except (RefactoringError, ResourceNotFoundError, AttributeError):
            pattern = re.compile(
                rf"(?:class|def)\s+({re.escape(symbol)})\b|^({re.escape(symbol)})\s*=",
                re.MULTILINE,
            )
            match = pattern.search(source)
            if match is None:
                return None
            return match.start(1) if match.group(1) is not None else match.start(2)

    @staticmethod
    def get_module_imports(
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
    ) -> t.StrMapping:
        """Return {local_name: fully_qualified_name} for all imports in a module."""
        result: t.MutableStrMapping = {}
        try:
            pycore = FlextInfraUtilitiesRopeAnalysis.get_pycore(rope_project)
            pymodule = pycore.resource_to_pyobject(resource)
            current_module_name = pymodule.get_name()
            for name, pyname in pymodule.get_attributes().items():
                obj = pyname.get_object()
                module = obj.get_module()
                if not isinstance(module, p.Infra.RopePyModuleLike):
                    continue
                module_name = module.get_name()
                object_name = obj.get_name()
                if not module_name or module_name == current_module_name:
                    continue
                result[name] = (
                    module_name
                    if object_name is None or module_name.endswith(f".{object_name}")
                    else f"{module_name}.{object_name}"
                )
        except (RefactoringError, ResourceNotFoundError, AttributeError):
            return result
        return result

    @staticmethod
    def get_module_classes(
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
    ) -> t.StrSequence:
        """Return names of all classes defined in a module."""
        classes: MutableSequence[str] = []
        try:
            pycore = FlextInfraUtilitiesRopeAnalysis.get_pycore(rope_project)
            pymodule = pycore.resource_to_pyobject(resource)
            resource_path = resource.path
            for name, pyname in pymodule.get_attributes().items():
                obj = pyname.get_object()
                if not isinstance(obj, p.Infra.RopeAbstractClassLike):
                    continue
                module = obj.get_module()
                origin = module.get_resource() if module is not None else None
                if origin is None or origin.path != resource_path:
                    continue
                classes.append(name)
        except (RefactoringError, ResourceNotFoundError, AttributeError):
            return classes
        return classes

    @staticmethod
    def find_facade_alias(
        resource: t.Infra.RopeResource,
        family: str,
    ) -> str | None:
        """Find facade alias assignment in a module."""
        for hit in c.Infra.FACADE_ALIAS_RE.finditer(resource.read()):
            if hit.group(1) == family:
                return hit.group(2)
        return None

    @staticmethod
    def get_class_info(
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
    ) -> Sequence[m.Infra.ClassInfo]:
        """Return ClassInfo (name, line, bases) for all classes in a module."""
        result: MutableSequence[m.Infra.ClassInfo] = []
        try:
            pycore = FlextInfraUtilitiesRopeAnalysis.get_pycore(rope_project)
            pymodule = pycore.resource_to_pyobject(resource)
            resource_path = resource.path
            for name, pyname in pymodule.get_attributes().items():
                obj = pyname.get_object()
                if not isinstance(obj, p.Infra.RopeAbstractClassLike):
                    continue
                module = obj.get_module()
                origin = module.get_resource() if module is not None else None
                if origin is None or origin.path != resource_path:
                    continue
                _, line_candidate = pyname.get_definition_location()
                if line_candidate is None:
                    continue
                bases = [
                    base_name
                    for base in obj.get_superclasses()
                    if (base_name := base.get_name()) is not None
                ]
                result.append(
                    m.Infra.ClassInfo(
                        name=name,
                        line=line_candidate,
                        bases=tuple(bases),
                    )
                )
        except (RefactoringError, ResourceNotFoundError, AttributeError):
            return result
        return result

    @staticmethod
    def get_class_symbol_count(
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
        class_name: str,
    ) -> int:
        """Return total attribute count for a class."""
        try:
            pycore = FlextInfraUtilitiesRopeAnalysis.get_pycore(rope_project)
            pymodule = pycore.resource_to_pyobject(resource)
            attributes = pymodule.get_attributes()
            if class_name not in attributes:
                return 0
            obj = attributes[class_name].get_object()
            if not isinstance(obj, p.Infra.RopeAbstractClassLike):
                return 0
            return len(obj.get_attributes())
        except (RefactoringError, ResourceNotFoundError, AttributeError):
            return 0

    @staticmethod
    def get_class_bases(
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
        class_name: str,
    ) -> t.StrSequence:
        """Return base class names for a given class in a module."""
        for info in FlextInfraUtilitiesRopeAnalysis.get_class_info(
            rope_project, resource
        ):
            if info.name == class_name:
                return list(info.bases)
        return []

    @staticmethod
    def get_class_methods(
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
        class_name: str,
        *,
        include_private: bool = False,
    ) -> t.StrMapping:
        """Return {method_name: kind} for methods of a class."""
        result: t.MutableStrMapping = {}
        try:
            pycore = FlextInfraUtilitiesRopeAnalysis.get_pycore(rope_project)
            pymodule = pycore.resource_to_pyobject(resource)
            attributes = pymodule.get_attributes()
            if class_name not in attributes:
                return result
            obj = attributes[class_name].get_object()
            if not isinstance(obj, p.Infra.RopeAbstractClassLike):
                return result
            for name, pyname in obj.get_attributes().items():
                if not include_private and name.startswith("_"):
                    continue
                child = pyname.get_object()
                kind = "method"
                if isinstance(child, p.Infra.RopePyFunctionLike):
                    raw_kind = child.get_kind()
                    if raw_kind in {"staticmethod", "classmethod"}:
                        kind = raw_kind
                result[name] = kind
        except (RefactoringError, ResourceNotFoundError, AttributeError):
            return result
        return result

    @staticmethod
    def get_all_class_names(
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
    ) -> Sequence[tuple[str, int, Sequence[str]]]:
        """Return (name, line, bases) for all classes."""
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
            pycore = FlextInfraUtilitiesRopeAnalysis.get_pycore(rope_project)
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
        """Return all top-level symbols (classes, functions, assignments) with metadata."""
        result: MutableSequence[m.Infra.SymbolInfo] = []
        try:
            pycore = FlextInfraUtilitiesRopeAnalysis.get_pycore(rope_project)
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
        """Return Final-annotated constants inside a class via rope semantic analysis."""
        result: MutableSequence[m.Infra.ConstantInfo] = []
        source = resource.read()
        try:
            pycore = FlextInfraUtilitiesRopeAnalysis.get_pycore(rope_project)
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
            pycore = FlextInfraUtilitiesRopeAnalysis.get_pycore(rope_project)
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


__all__ = ["FlextInfraUtilitiesRopeAnalysis"]
