"""Semantic Rope analysis helpers."""

from __future__ import annotations

import ast as _ast
import importlib.util as _importlib_util
from collections.abc import (
    MutableSequence,
    Sequence,
)
from typing import TYPE_CHECKING, ClassVar

from flext_infra import (
    FlextInfraUtilitiesRopeCore,
    c,
    m,
)
from rope.base.pynames import (
    DefinedName as RopeDefinedName,
    ImportedName as RopeImportedName,
)
from rope.base.pynamesdef import AssignedName as RopeAssignedName

if TYPE_CHECKING:
    from flext_infra import t


class FlextInfraUtilitiesRopeAnalysis:
    """Rope-backed semantic analysis helpers."""

    _SEMANTIC_STATE_CACHE: ClassVar[
        dict[tuple[str, str, int], m.Infra.ModuleSemanticState]
    ] = {}
    _EXPORT_NAMES_CACHE: ClassVar[
        dict[tuple[str, str, int, bool, bool, bool, bool, bool], t.StrSequence]
    ] = {}

    @staticmethod
    def _resource_cache_key(
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
    ) -> tuple[str, str, int]:
        file_path = FlextInfraUtilitiesRopeCore.resource_file_path(
            rope_project,
            resource,
        )
        mtime_ns = (
            file_path.stat().st_mtime_ns
            if file_path is not None and file_path.exists()
            else 0
        )
        project_root = getattr(
            getattr(rope_project, "root", None),
            "real_path",
            "",
        )
        return (str(project_root), resource.path, mtime_ns)

    @staticmethod
    def _package_name_for_module(
        module_name: str,
        resource: t.Infra.RopeResource,
    ) -> str:
        if (
            resource.path.endswith(f"/{c.Infra.INIT_PY}")
            or resource.path == c.Infra.INIT_PY
        ):
            return module_name
        return module_name.rsplit(".", maxsplit=1)[0] if "." in module_name else ""

    @staticmethod
    def _resolve_import_module(
        *,
        current_package: str,
        module_name: str,
        level: int,
    ) -> str:
        if level <= 0:
            return module_name
        try:
            return _importlib_util.resolve_name(
                f"{'.' * level}{module_name}",
                current_package,
            )
        except (ImportError, ValueError):
            return module_name

    @staticmethod
    def _root_name(expr: _ast.expr) -> str:
        match expr:
            case _ast.Name(id=name):
                return name
            case _ast.Attribute(value=value):
                return FlextInfraUtilitiesRopeAnalysis._root_name(value)
            case _ast.Subscript(value=value):
                return FlextInfraUtilitiesRopeAnalysis._root_name(value)
            case _ast.Call(func=func):
                return FlextInfraUtilitiesRopeAnalysis._root_name(func)
            case _:
                return ""

    @staticmethod
    def _target_names(target: _ast.expr) -> tuple[str, ...]:
        match target:
            case _ast.Name(id=name):
                return (name,)
            case _ast.Tuple(elts=elts) | _ast.List(elts=elts):
                return tuple(
                    name
                    for item in elts
                    for name in FlextInfraUtilitiesRopeAnalysis._target_names(item)
                )
            case _:
                return ()

    @staticmethod
    def _explicit_all_from_node(
        node: _ast.Assign | _ast.AnnAssign,
    ) -> t.StrSequence | None:
        targets = node.targets if isinstance(node, _ast.Assign) else (node.target,)
        if c.Infra.DUNDER_ALL not in {
            name
            for target in targets
            for name in FlextInfraUtilitiesRopeAnalysis._target_names(target)
        }:
            return None
        if node.value is None:
            return None
        try:
            value = _ast.literal_eval(node.value)
        except (ValueError, TypeError, SyntaxError):
            return None
        items: list[str] | tuple[str, ...]
        match value:
            case list() | tuple():
                items = value
            case _:
                return None
        return tuple(items)

    @staticmethod
    def get_module_semantic_state(
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
    ) -> m.Infra.ModuleSemanticState:
        """Return local classes plus declared and semantic imports in one pass."""
        cache_key = FlextInfraUtilitiesRopeAnalysis._resource_cache_key(
            rope_project,
            resource,
        )
        cached = FlextInfraUtilitiesRopeAnalysis._SEMANTIC_STATE_CACHE.get(cache_key)
        if cached is not None:
            return cached
        class_infos: MutableSequence[m.Infra.ClassInfo] = []
        semantic_imports: dict[str, str] = {}
        declared_imports: dict[str, str] = {}
        try:
            pymodule = FlextInfraUtilitiesRopeCore.get_pymodule(
                rope_project,
                resource,
            )
            module_ast = pymodule.get_ast()
            attributes = pymodule.get_attributes()
            current_package = FlextInfraUtilitiesRopeAnalysis._package_name_for_module(
                pymodule.get_name(),
                resource,
            )
            for node in module_ast.body:
                match node:
                    case _ast.ClassDef(name=name, lineno=line):
                        base_names: tuple[str, ...] = ()
                        pyname = attributes.get(name)
                        if pyname is not None:
                            obj = pyname.get_object()
                            if isinstance(
                                obj,
                                FlextInfraUtilitiesRopeCore.ABSTRACT_CLASS_TYPES,
                            ):
                                base_names = tuple(
                                    superclass.get_name()
                                    for superclass in obj.get_superclasses()
                                    if superclass.get_name()
                                )
                        class_infos.append(
                            m.Infra.ClassInfo(
                                name=name,
                                line=line,
                                bases=base_names,
                            ),
                        )
                    case _ast.Import(names=aliases):
                        for alias in aliases:
                            local_name = alias.asname or alias.name.partition(".")[0]
                            if not local_name:
                                continue
                            declared_imports[local_name] = alias.name
                            semantic_imports[local_name] = alias.name
                    case _ast.ImportFrom(
                        module=module_name, names=aliases, level=level
                    ):
                        resolved_module = (
                            FlextInfraUtilitiesRopeAnalysis._resolve_import_module(
                                current_package=current_package,
                                module_name=module_name or "",
                                level=level,
                            )
                        )
                        for alias in aliases:
                            if alias.name == "*":
                                continue
                            local_name = alias.asname or alias.name
                            target = (
                                f"{resolved_module}.{alias.name}"
                                if resolved_module
                                else alias.name
                            )
                            declared_imports[local_name] = target
                            semantic_imports[local_name] = target
                    case _:
                        continue
        except FlextInfraUtilitiesRopeCore.RUNTIME_ERRORS:
            state = m.Infra.ModuleSemanticState(
                class_infos=tuple(class_infos),
                declared_imports=declared_imports,
                semantic_imports=semantic_imports,
            )
            FlextInfraUtilitiesRopeAnalysis._SEMANTIC_STATE_CACHE[cache_key] = state
            return state
        state = m.Infra.ModuleSemanticState(
            class_infos=tuple(class_infos),
            declared_imports=declared_imports,
            semantic_imports=semantic_imports,
        )
        FlextInfraUtilitiesRopeAnalysis._SEMANTIC_STATE_CACHE[cache_key] = state
        return state

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
            lines = source.splitlines(keepends=True)
            if definition_line < 1 or definition_line > len(lines):
                return None
            line = lines[definition_line - 1]
            column = line.find(symbol)
            if column < 0:
                return None
            return sum(len(item) for item in lines[: definition_line - 1]) + column
        except FlextInfraUtilitiesRopeCore.RUNTIME_ERRORS:
            return None

    @staticmethod
    def get_semantic_module_imports(
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
    ) -> t.StrMapping:
        """Return {local_name: fully_qualified_name} for all imports in a module."""
        return FlextInfraUtilitiesRopeAnalysis.get_module_semantic_state(
            rope_project,
            resource,
        ).semantic_imports

    @staticmethod
    def get_declared_module_imports(
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
    ) -> t.StrMapping:
        """Return {local_name: declared import path} without resolving re-exports."""
        return FlextInfraUtilitiesRopeAnalysis.get_module_semantic_state(
            rope_project,
            resource,
        ).declared_imports

    @staticmethod
    def get_module_classes(
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
    ) -> t.StrSequence:
        """Return names of all classes defined in a module."""
        return tuple(
            class_info.name
            for class_info in FlextInfraUtilitiesRopeAnalysis.get_module_semantic_state(
                rope_project,
                resource,
            ).class_infos
        )

    @staticmethod
    def get_module_export_names(
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
        *,
        include_dunder: bool = False,
        allow_main: bool = False,
        allow_assignments: bool = False,
        allow_functions: bool = False,
        require_explicit_all: bool = False,
    ) -> t.StrSequence:
        """Return module-local export names from Rope metadata."""
        cache_key = (
            *FlextInfraUtilitiesRopeAnalysis._resource_cache_key(
                rope_project,
                resource,
            ),
            include_dunder,
            allow_main,
            allow_assignments,
            allow_functions,
            require_explicit_all,
        )
        cached = FlextInfraUtilitiesRopeAnalysis._EXPORT_NAMES_CACHE.get(cache_key)
        if cached is not None:
            return cached
        try:
            pymodule = FlextInfraUtilitiesRopeCore.get_pymodule(
                rope_project,
                resource,
            )
            attributes = pymodule.get_attributes()
            if include_dunder:
                exports = tuple(
                    dict.fromkeys(
                        name
                        for name, pyname in attributes.items()
                        if name != c.Infra.DUNDER_ALL
                        and name.startswith("__")
                        and name.endswith("__")
                        and isinstance(pyname, RopeAssignedName)
                        and FlextInfraUtilitiesRopeAnalysis._is_local_name(
                            pyname,
                            resource,
                        )
                    )
                )
                FlextInfraUtilitiesRopeAnalysis._EXPORT_NAMES_CACHE[cache_key] = exports
                return exports
            explicit_all: t.StrSequence | None = None
            explicit_all_name = attributes.get(c.Infra.DUNDER_ALL)
            if isinstance(explicit_all_name, RopeAssignedName) and (
                FlextInfraUtilitiesRopeAnalysis._is_local_name(
                    explicit_all_name,
                    resource,
                )
            ):
                explicit_all = FlextInfraUtilitiesRopeAnalysis._explicit_all_names(
                    explicit_all_name,
                )
            if explicit_all is not None:
                exports = tuple(dict.fromkeys(explicit_all))
                FlextInfraUtilitiesRopeAnalysis._EXPORT_NAMES_CACHE[cache_key] = exports
                return exports
            if require_explicit_all:
                FlextInfraUtilitiesRopeAnalysis._EXPORT_NAMES_CACHE[cache_key] = ()
                return ()
            names: MutableSequence[str] = []
            for name, pyname in attributes.items():
                if name == c.Infra.DUNDER_ALL or not (
                    FlextInfraUtilitiesRopeAnalysis._is_local_name(pyname, resource)
                ):
                    continue
                if isinstance(pyname, RopeImportedName):
                    continue
                if isinstance(pyname, RopeDefinedName):
                    obj = pyname.get_object()
                    if isinstance(
                        obj,
                        FlextInfraUtilitiesRopeCore.ABSTRACT_CLASS_TYPES,
                    ):
                        names.append(name)
                        continue
                    if (
                        allow_main
                        and name == "main"
                        and isinstance(
                            obj,
                            FlextInfraUtilitiesRopeCore.PY_FUNCTION_TYPES,
                        )
                    ):
                        names.append(name)
                        continue
                    if allow_functions and isinstance(
                        obj,
                        FlextInfraUtilitiesRopeCore.PY_FUNCTION_TYPES,
                    ):
                        names.append(name)
                        continue
                if allow_assignments and isinstance(pyname, RopeAssignedName):
                    names.append(name)
        except FlextInfraUtilitiesRopeCore.RUNTIME_ERRORS:
            FlextInfraUtilitiesRopeAnalysis._EXPORT_NAMES_CACHE[cache_key] = ()
            return ()
        exports = tuple(dict.fromkeys(names))
        FlextInfraUtilitiesRopeAnalysis._EXPORT_NAMES_CACHE[cache_key] = exports
        return exports

    @staticmethod
    def _explicit_all_names(
        pyname: t.Infra.RopeAssignedName,
    ) -> t.StrSequence | None:
        """Return literal string names assigned to ``__all__`` via Rope metadata."""
        names: MutableSequence[str] = []
        for assignment in pyname.assignments:
            node = assignment.ast_node
            if not isinstance(node, _ast.List | _ast.Tuple):
                continue
            names.extend(
                item.value
                for item in node.elts
                if isinstance(item, _ast.Constant) and isinstance(item.value, str)
            )
            return tuple(dict.fromkeys(names))
        return None

    @staticmethod
    def _is_local_name(
        pyname: t.Infra.RopePyName,
        resource: t.Infra.RopeResource,
    ) -> bool:
        """Return whether one Rope name is defined in ``resource``."""
        location = pyname.get_definition_location()
        if location is None:
            return False
        module, line = location
        origin = module.get_resource() if module is not None else None
        return line is not None and origin is not None and origin.path == resource.path

    @staticmethod
    def get_class_info(
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
    ) -> Sequence[m.Infra.ClassInfo]:
        """Return ClassInfo (name, line, bases) for all classes in a module."""
        return FlextInfraUtilitiesRopeAnalysis.get_module_semantic_state(
            rope_project,
            resource,
        ).class_infos

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


__all__: list[str] = ["FlextInfraUtilitiesRopeAnalysis"]
