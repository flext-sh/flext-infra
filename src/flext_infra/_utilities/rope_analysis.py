"""Semantic Rope analysis helpers."""

from __future__ import annotations

import re
from collections.abc import MutableSequence, Sequence
from typing import TYPE_CHECKING

from rope.base.exceptions import RefactoringError, ResourceNotFoundError

from flext_infra import c, m
from flext_infra._utilities.rope_analysis_introspection import (
    FlextInfraUtilitiesRopeAnalysisIntrospection,
)
from flext_infra._utilities.rope_core import FlextInfraUtilitiesRopeCore

if TYPE_CHECKING:
    from flext_infra import t


class FlextInfraUtilitiesRopeAnalysis(
    FlextInfraUtilitiesRopeAnalysisIntrospection,
    FlextInfraUtilitiesRopeCore,
):
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
                if module is None:
                    continue
                module_name = module.get_name()
                object_name = (
                    obj.get_name()
                    if FlextInfraUtilitiesRopeAnalysis.is_rope_named_object_like(obj)
                    else None
                )
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
                if not FlextInfraUtilitiesRopeAnalysis.is_rope_abstract_class_like(obj):
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
    def _source_class_info(source: str) -> dict[str, m.Infra.ClassInfo]:
        """Parse class declarations directly from source as a fallback to rope."""
        class_info: dict[str, m.Infra.ClassInfo] = {}
        for lineno, line in enumerate(source.splitlines(), start=1):
            match = c.Infra.SourceCode.CLASS_WITH_BASES_RE.match(line)
            if not match:
                continue
            name = match.group(1)
            bases: list[str] = []
            for base_part in match.group(2).split(","):
                base_clean = base_part.split("[")[0].strip()
                terminal = base_clean.rsplit(".", maxsplit=1)[-1]
                if terminal:
                    bases.append(terminal)
            class_info[name] = m.Infra.ClassInfo(
                name=name,
                line=lineno,
                bases=tuple(bases),
            )
        return class_info

    @staticmethod
    def get_class_info(
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
    ) -> Sequence[m.Infra.ClassInfo]:
        """Return ClassInfo (name, line, bases) for all classes in a module."""
        result: MutableSequence[m.Infra.ClassInfo] = []
        try:
            source_info = FlextInfraUtilitiesRopeAnalysis._source_class_info(
                resource.read(),
            )
            pycore = FlextInfraUtilitiesRopeAnalysis.get_pycore(rope_project)
            pymodule = pycore.resource_to_pyobject(resource)
            resource_path = resource.path
            for name, pyname in pymodule.get_attributes().items():
                obj = pyname.get_object()
                if not FlextInfraUtilitiesRopeAnalysis.is_rope_abstract_class_like(obj):
                    continue
                module = obj.get_module()
                origin = module.get_resource() if module is not None else None
                if origin is None or origin.path != resource_path:
                    continue
                _, line_candidate = pyname.get_definition_location()
                source_class = source_info.get(name)
                if line_candidate is None and source_class is not None:
                    line_candidate = source_class.line
                if line_candidate is None:
                    continue
                bases = [
                    base_name
                    for base in obj.get_superclasses()
                    if (base_name := base.get_name()) is not None
                ]
                if source_class is not None and source_class.bases:
                    bases = list(dict.fromkeys([*bases, *source_class.bases]))
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
            if not FlextInfraUtilitiesRopeAnalysis.is_rope_abstract_class_like(obj):
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
            if not FlextInfraUtilitiesRopeAnalysis.is_rope_abstract_class_like(obj):
                return result
            for name, pyname in obj.get_attributes().items():
                if not include_private and name.startswith("_"):
                    continue
                child = pyname.get_object()
                kind = "method"
                if FlextInfraUtilitiesRopeAnalysis.is_rope_pyfunction_like(child):
                    raw_kind = child.get_kind()
                    if raw_kind in {"staticmethod", "classmethod"}:
                        kind = raw_kind
                result[name] = kind
        except (RefactoringError, ResourceNotFoundError, AttributeError):
            return result
        return result


__all__ = ["FlextInfraUtilitiesRopeAnalysis"]
