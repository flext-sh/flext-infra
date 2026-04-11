"""Semantic Rope analysis helpers."""

from __future__ import annotations

from collections.abc import MutableSequence, Sequence
from typing import TYPE_CHECKING

from flext_infra import (
    FlextInfraUtilitiesRopeCore,
    c,
    m,
)

if TYPE_CHECKING:
    from flext_infra import t


class FlextInfraUtilitiesRopeAnalysis:
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
            pymodule = FlextInfraUtilitiesRopeCore.get_pymodule(
                rope_project,
                resource,
            )
            attributes = pymodule.get_attributes()
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
            return FlextInfraUtilitiesRopeCore.line_offset_for_symbol(
                source=source,
                line_number=definition_line,
                symbol=symbol,
            )
        except FlextInfraUtilitiesRopeCore.RUNTIME_ERRORS:
            return None

    @staticmethod
    def get_semantic_module_imports(
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
    ) -> t.StrMapping:
        """Return {local_name: fully_qualified_name} for all imports in a module."""
        result: t.MutableStrMapping = {}
        try:
            pymodule = FlextInfraUtilitiesRopeCore.get_pymodule(
                rope_project,
                resource,
            )
            current_module_name = pymodule.get_name()
            for name, pyname in pymodule.get_attributes().items():
                obj = pyname.get_object()
                module = obj.get_module()
                if module is None:
                    continue
                module_name = module.get_name()
                object_name_getter = getattr(obj, "get_name", None)
                object_name = (
                    object_name_getter() if callable(object_name_getter) else None
                )
                if not module_name or module_name == current_module_name:
                    continue
                result[name] = (
                    module_name
                    if object_name is None or module_name.endswith(f".{object_name}")
                    else f"{module_name}.{object_name}"
                )
        except FlextInfraUtilitiesRopeCore.RUNTIME_ERRORS:
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
            pymodule = FlextInfraUtilitiesRopeCore.get_pymodule(
                rope_project,
                resource,
            )
            resource_path = resource.path
            for name, pyname in pymodule.get_attributes().items():
                obj = pyname.get_object()
                if not isinstance(obj, FlextInfraUtilitiesRopeCore.ABSTRACT_CLASS_TYPES):
                    continue
                module = obj.get_module()
                origin = module.get_resource() if module is not None else None
                if origin is None or origin.path != resource_path:
                    continue
                classes.append(name)
        except FlextInfraUtilitiesRopeCore.RUNTIME_ERRORS:
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
            pymodule = FlextInfraUtilitiesRopeCore.get_pymodule(
                rope_project,
                resource,
            )
            resource_path = resource.path
            for name, pyname in pymodule.get_attributes().items():
                obj = pyname.get_object()
                if not isinstance(obj, FlextInfraUtilitiesRopeCore.ABSTRACT_CLASS_TYPES):
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
        except FlextInfraUtilitiesRopeCore.RUNTIME_ERRORS:
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
            pymodule = FlextInfraUtilitiesRopeCore.get_pymodule(
                rope_project,
                resource,
            )
            attributes = pymodule.get_attributes()
            if class_name not in attributes:
                return 0
            obj = attributes[class_name].get_object()
            if not isinstance(obj, FlextInfraUtilitiesRopeCore.ABSTRACT_CLASS_TYPES):
                return 0
            return len(obj.get_attributes())
        except FlextInfraUtilitiesRopeCore.RUNTIME_ERRORS:
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
        return ()

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
            pymodule = FlextInfraUtilitiesRopeCore.get_pymodule(
                rope_project,
                resource,
            )
            attributes = pymodule.get_attributes()
            if class_name not in attributes:
                return result
            obj = attributes[class_name].get_object()
            if not isinstance(obj, FlextInfraUtilitiesRopeCore.ABSTRACT_CLASS_TYPES):
                return result
            for name, pyname in obj.get_attributes().items():
                if not include_private and name.startswith("_"):
                    continue
                child = pyname.get_object()
                if not isinstance(child, FlextInfraUtilitiesRopeCore.PY_FUNCTION_TYPES):
                    continue
                kind = child.get_kind()
                result[name] = kind
        except FlextInfraUtilitiesRopeCore.RUNTIME_ERRORS:
            return result
        return result


__all__ = ["FlextInfraUtilitiesRopeAnalysis"]
