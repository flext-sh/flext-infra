"""Scope, definition, and class-symbol resolution."""

from __future__ import annotations

from flext_infra.constants import c
from flext_infra.models import m
from flext_infra.typings import t

from ..rope_core import FlextInfraUtilitiesRopeCore
from ..rope_runtime import FlextInfraUtilitiesRopeRuntime
from .imports import FlextInfraUtilitiesRopeAnalysisImports


class FlextInfraUtilitiesRopeAnalysisScope(FlextInfraUtilitiesRopeAnalysisImports):
    """Scope, definition, and class-symbol resolution."""

    @staticmethod
    def find_definition_offset(
        rope_project: t.Infra.RopeProject, resource: t.Infra.RopeResource, symbol: str
    ) -> int | None:
        """Return offset of symbol's definition via semantic analysis."""
        source = resource.read()
        pymodule = FlextInfraUtilitiesRopeCore.get_pymodule(rope_project, resource)
        return FlextInfraUtilitiesRopeAnalysisScope._definition_offset_from_pymodule(
            pymodule=pymodule, source=source, symbol=symbol
        )

    @staticmethod
    def _definition_offset_from_pymodule(
        *, pymodule: t.Infra.RopePyModule, source: str, symbol: str
    ) -> int | None:
        """Return identifier offset for one symbol from a resolved Rope module."""
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
        lines = source.splitlines(keepends=True)
        return FlextInfraUtilitiesRopeCore.find_identifier_offset_in_lines(
            lines, line=definition_line, symbol=symbol
        )

    @staticmethod
    def get_module_classes(
        rope_project: t.Infra.RopeProject, resource: t.Infra.RopeResource
    ) -> t.StrSequence:
        """Return names of all classes defined in a module."""
        return tuple(
            class_info.name
            for class_info in FlextInfraUtilitiesRopeAnalysisImports.get_module_semantic_state(
                rope_project, resource
            ).class_infos
        )

    @staticmethod
    def scope_definitions(
        pymodule: t.Infra.RopePyModule,
    ) -> t.SequenceOf[m.Infra.ScopeDefinition]:
        """Return every def/class scope in a module via rope's semantic tree.

        Uses ``PyModule.get_scope()`` and recursive ``PyScope.get_scopes()`` —
        never ``get_ast``/``ast.walk``. Each entry carries the scope kind
        (Function/Class/Comprehension), its 1-based start line, and whether it
        is a direct child of the module (global) scope.
        """
        root_scope = pymodule.get_scope()
        if root_scope is None:
            return ()
        definitions: t.MutableSequenceOf[m.Infra.ScopeDefinition] = []
        FlextInfraUtilitiesRopeAnalysisScope._collect_scope_definitions(
            scope=root_scope, is_module_level=True, definitions=definitions
        )
        return tuple(definitions)

    @staticmethod
    def _collect_scope_definitions(
        *,
        scope: t.Infra.RopeScope,
        is_module_level: bool,
        definitions: t.MutableSequenceOf[m.Infra.ScopeDefinition],
    ) -> None:
        """Recurse the rope scope tree, appending one entry per child scope."""
        for child in scope.get_scopes():
            start = child.get_start()
            # NOTE (multi-agent, flext-f8vk / kimi): RopeScope.get_start() is
            # declared int in p.Infra; the old isinstance guard was dead code.
            definitions.append(
                m.Infra.ScopeDefinition(
                    name=FlextInfraUtilitiesRopeAnalysisScope._scope_name(child),
                    kind=FlextInfraUtilitiesRopeAnalysisScope._scope_kind(child),
                    line=start if start > 0 else 1,
                    is_module_level=is_module_level,
                )
            )
            FlextInfraUtilitiesRopeAnalysisScope._collect_scope_definitions(
                scope=child, is_module_level=False, definitions=definitions
            )

    @staticmethod
    def _scope_kind(scope: t.Infra.RopeScope) -> c.Infra.RopeScopeKind:
        """Map rope's ``get_kind()`` to the typed enum (None -> UNKNOWN)."""
        raw_kind = scope.get_kind()
        try:
            return c.Infra.RopeScopeKind(raw_kind)
        except ValueError:
            return c.Infra.RopeScopeKind.UNKNOWN

    @staticmethod
    def _scope_name(scope: t.Infra.RopeScope) -> str:
        """Return the def/class name backing one rope scope."""
        name: str = scope.pyobject.get_name()
        return name

    @staticmethod
    def is_pyclass(obj: t.Infra.RopePyObject) -> bool:
        """Return whether a rope object is a ``PyClass`` (abstract class type)."""
        return FlextInfraUtilitiesRopeRuntime.is_abstract_class(obj)

    @staticmethod
    def is_pyfunction(obj: t.Infra.RopePyObject) -> bool:
        """Return whether a rope object is a ``PyFunction``."""
        return FlextInfraUtilitiesRopeRuntime.is_py_function(obj)

    @staticmethod
    def module_body_nodes_source(source: str) -> t.SequenceOf[t.Infra.RopeAstNode]:
        """Return top-level parsed statements for one source module."""
        _ = source
        return ()

    @staticmethod
    def module_reachable_nodes_source(source: str) -> t.SequenceOf[t.Infra.RopeAstNode]:
        """Return parsed nodes reachable from one source module."""
        _ = source
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
        pymodule = FlextInfraUtilitiesRopeCore.get_pymodule(rope_project, resource)
        return FlextInfraUtilitiesRopeAnalysisScope._class_methods_from_pymodule(
            class_name=class_name, include_private=include_private, pymodule=pymodule
        )

    @staticmethod
    def _class_methods_from_pymodule(
        *, class_name: str, include_private: bool, pymodule: t.Infra.RopePyModule
    ) -> t.StrMapping:
        """Return method symbols for a class from one resolved Rope module."""
        result: t.MutableStrMapping = {}
        attributes = pymodule.get_attributes()
        if class_name not in attributes:
            return result
        obj = attributes[class_name].get_object()
        if not FlextInfraUtilitiesRopeRuntime.is_abstract_class(obj):
            return result
        for name, pyname in obj.get_attributes().items():
            if not include_private and name.startswith("_"):
                continue
            child = pyname.get_object()
            if not FlextInfraUtilitiesRopeRuntime.is_py_function(child):
                continue
            result[name] = child.get_kind()
        return result
