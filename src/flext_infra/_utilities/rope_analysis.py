"""Semantic Rope analysis helpers."""

from __future__ import annotations

import importlib.util as _importlib_util
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

from rope.base import libutils as rope_libutils
from rope.base.pynames import (
    DefinedName as RopeDefinedName,
    ImportedName as RopeImportedName,
)
from rope.base.pynamesdef import AssignedName as RopeAssignedName

from flext_infra._utilities.rope_core import FlextInfraUtilitiesRopeCore
from flext_infra.constants import c
from flext_infra.models import m

if TYPE_CHECKING:
    from flext_infra import p, t


class FlextInfraUtilitiesRopeAnalysis:
    """Rope-backed semantic analysis helpers."""

    _parse_project: ClassVar[t.Infra.RopeProject | None] = None
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
        """Resource cache key."""
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
        """Package name for module."""
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
        """Resolve import module."""
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
    def get_module_semantic_state(
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
    ) -> m.Infra.ModuleSemanticState:
        """Return local classes plus declared and semantic imports in one pass.

        Uses rope's ``PyModule.get_attributes()`` for class discovery and
        ``rope.refactor.importutils.get_module_imports`` for import-table
        construction — no ``ast`` walking is performed.
        """
        cache_key = FlextInfraUtilitiesRopeAnalysis._resource_cache_key(
            rope_project,
            resource,
        )
        cached = FlextInfraUtilitiesRopeAnalysis._SEMANTIC_STATE_CACHE.get(cache_key)
        if cached is not None:
            return cached
        try:
            pymodule = FlextInfraUtilitiesRopeCore.get_pymodule(
                rope_project,
                resource,
            )
            state = (
                FlextInfraUtilitiesRopeAnalysis._module_semantic_state_from_pymodule(
                    rope_project=rope_project,
                    resource=resource,
                    pymodule=pymodule,
                )
            )
        except FlextInfraUtilitiesRopeCore.RUNTIME_ERRORS:
            state = FlextInfraUtilitiesRopeAnalysis._empty_module_semantic_state()
        FlextInfraUtilitiesRopeAnalysis._SEMANTIC_STATE_CACHE[cache_key] = state
        return state

    @staticmethod
    def _empty_module_semantic_state() -> m.Infra.ModuleSemanticState:
        """Return an empty semantic state."""
        return m.Infra.ModuleSemanticState(
            class_infos=(),
            declared_imports={},
            semantic_imports={},
        )

    @staticmethod
    def _module_semantic_state_from_pymodule(
        *,
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
        pymodule: t.Infra.RopePyModule,
    ) -> m.Infra.ModuleSemanticState:
        """Build semantic state from one resolved Rope module."""
        current_package = FlextInfraUtilitiesRopeAnalysis._package_name_for_module(
            pymodule.get_name(),
            resource,
        )
        declared_imports, semantic_imports = (
            FlextInfraUtilitiesRopeAnalysis._module_import_maps(
                rope_project=rope_project,
                resource=resource,
                current_package=current_package,
            )
        )
        return m.Infra.ModuleSemanticState(
            class_infos=tuple(
                FlextInfraUtilitiesRopeAnalysis._module_class_infos(
                    pymodule=pymodule,
                    resource=resource,
                )
            ),
            declared_imports=declared_imports,
            semantic_imports=semantic_imports,
        )

    @staticmethod
    def _module_class_infos(
        *,
        pymodule: t.Infra.RopePyModule,
        resource: t.Infra.RopeResource,
    ) -> t.SequenceOf[m.Infra.ClassInfo]:
        """Return local class infos for one resolved Rope module."""
        class_infos: t.MutableSequenceOf[m.Infra.ClassInfo] = []
        ast_bases_by_class = {
            class_info.name: class_info.bases
            for class_info in FlextInfraUtilitiesRopeAnalysis.class_info_from_source(
                resource.read()
            )
        }
        for name, pyname in pymodule.get_attributes().items():
            if not FlextInfraUtilitiesRopeAnalysis._is_local_name(pyname, resource):
                continue
            obj = pyname.get_object()
            if not isinstance(obj, FlextInfraUtilitiesRopeCore.ABSTRACT_CLASS_TYPES):
                continue
            location = pyname.get_definition_location()
            line = location[1] if location and location[1] else 1
            bases = tuple(
                base_name
                for superclass in obj.get_superclasses()
                if (
                    base_name := FlextInfraUtilitiesRopeAnalysis._superclass_name(
                        superclass
                    )
                )
            )
            if not bases:
                bases = ast_bases_by_class.get(name, ())
            class_infos.append(m.Infra.ClassInfo(name=name, line=line, bases=bases))
        return tuple(class_infos)

    @staticmethod
    def _superclass_name(
        superclass: p.AttributeProbe,
        *,
        visited: frozenset[int] | None = None,
    ) -> str:
        """Return a superclass name from Rope objects with uneven public APIs."""
        visited_ids = visited or frozenset()
        superclass_id = id(superclass)
        if superclass_id in visited_ids:
            return ""
        next_visited = visited_ids | {superclass_id}
        get_name = getattr(superclass, "get_name", None)
        if callable(get_name):
            name = get_name()
            if isinstance(name, str) and name:
                return name
        get_type = getattr(superclass, "get_type", None)
        if callable(get_type):
            superclass_type = get_type()
            if superclass_type is not None:
                type_name = FlextInfraUtilitiesRopeAnalysis._superclass_name(
                    superclass_type,
                    visited=next_visited,
                )
                if type_name:
                    return type_name
        for attr_name in ("name", "_name"):
            name = getattr(superclass, attr_name, "")
            if isinstance(name, str) and name:
                return name
        return ""

    @staticmethod
    def _module_import_maps(
        *,
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
        current_package: str,
    ) -> tuple[dict[str, str], dict[str, str]]:
        """Return declared and semantic import maps for one module."""
        semantic_imports: dict[str, str] = {}
        declared_imports: dict[str, str] = {}
        module_imports = FlextInfraUtilitiesRopeCore.get_module_imports(
            rope_project,
            resource,
        )
        raw_imports = (
            getattr(module_imports, "imports", ()) if module_imports is not None else ()
        )
        import_stmts: tuple[t.Infra.RopeImportStatement, ...] = tuple(raw_imports)
        for import_stmt in import_stmts:
            FlextInfraUtilitiesRopeAnalysis._merge_import_statement(
                current_package=current_package,
                declared_imports=declared_imports,
                import_stmt=import_stmt,
                semantic_imports=semantic_imports,
            )
        return declared_imports, semantic_imports

    @staticmethod
    def _merge_import_statement(
        *,
        current_package: str,
        declared_imports: dict[str, str],
        import_stmt: t.Infra.RopeImportStatement,
        semantic_imports: dict[str, str],
    ) -> None:
        """Merge one Rope import statement into the import maps."""
        info = import_stmt.import_info
        if info is None:
            return
        module_name = getattr(info, "module_name", "") or ""
        resolved_module = FlextInfraUtilitiesRopeAnalysis._resolved_import_module(
            current_package=current_package,
            module_name=module_name,
            level=getattr(info, "level", 0) or 0,
        )
        for alias_name, alias_as in info.names_and_aliases or ():
            FlextInfraUtilitiesRopeAnalysis._merge_import_alias(
                alias_name=alias_name,
                alias_as=alias_as,
                declared_imports=declared_imports,
                module_name=module_name,
                resolved_module=resolved_module,
                semantic_imports=semantic_imports,
            )

    @staticmethod
    def _resolved_import_module(
        *,
        current_package: str,
        module_name: str,
        level: int,
    ) -> str:
        """Resolve the module path represented by one Rope import info."""
        return (
            FlextInfraUtilitiesRopeAnalysis._resolve_import_module(
                current_package=current_package,
                module_name=module_name,
                level=level,
            )
            if module_name
            else ""
        )

    @staticmethod
    def _merge_import_alias(
        *,
        alias_name: str,
        alias_as: str | None,
        declared_imports: dict[str, str],
        module_name: str,
        resolved_module: str,
        semantic_imports: dict[str, str],
    ) -> None:
        """Merge one import alias into declared and semantic maps."""
        if alias_name == "*":
            return
        if module_name:
            local_name = alias_as or alias_name
            target = (
                f"{resolved_module}.{alias_name}" if resolved_module else alias_name
            )
        else:
            local_name = alias_as or alias_name.partition(".")[0]
            target = alias_name
        if not local_name:
            return
        declared_imports[local_name] = target
        semantic_imports[local_name] = target

    @staticmethod
    def find_definition_offset(
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
        symbol: str,
    ) -> int | None:
        """Return offset of symbol's definition via semantic analysis."""
        result: int | None = None
        source = resource.read()
        try:
            pymodule = FlextInfraUtilitiesRopeCore.get_pymodule(
                rope_project,
                resource,
            )
            result = FlextInfraUtilitiesRopeAnalysis._definition_offset_from_pymodule(
                pymodule=pymodule,
                source=source,
                symbol=symbol,
            )
        except FlextInfraUtilitiesRopeCore.RUNTIME_ERRORS:
            pass
        return result

    @staticmethod
    def _definition_offset_from_pymodule(
        *,
        pymodule: t.Infra.RopePyModule,
        source: str,
        symbol: str,
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
            lines,
            line=definition_line,
            symbol=symbol,
        )

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
        export_options: m.Infra.ExportOptions | None = None,
    ) -> t.StrSequence:
        """Return module-local export names from Rope metadata."""
        resolved_export_options = export_options or m.Infra.ExportOptions()
        cache_key = (
            *FlextInfraUtilitiesRopeAnalysis._resource_cache_key(
                rope_project,
                resource,
            ),
            resolved_export_options.include_dunder,
            resolved_export_options.allow_main,
            resolved_export_options.allow_assignments,
            resolved_export_options.allow_functions,
            resolved_export_options.require_explicit_all,
        )
        cached = FlextInfraUtilitiesRopeAnalysis._EXPORT_NAMES_CACHE.get(cache_key)
        export_names: t.StrSequence
        if cached is not None:
            export_names = cached
        else:
            try:
                pymodule = FlextInfraUtilitiesRopeCore.get_pymodule(
                    rope_project,
                    resource,
                )
                export_names = FlextInfraUtilitiesRopeAnalysis._module_export_names(
                    export_options=resolved_export_options,
                    pymodule=pymodule,
                    resource=resource,
                )
                FlextInfraUtilitiesRopeAnalysis._EXPORT_NAMES_CACHE[cache_key] = (
                    export_names
                )
            except FlextInfraUtilitiesRopeCore.RUNTIME_ERRORS:
                FlextInfraUtilitiesRopeAnalysis._EXPORT_NAMES_CACHE[cache_key] = ()
                export_names = ()
        return export_names

    @staticmethod
    def _module_export_names(
        *,
        export_options: m.Infra.ExportOptions,
        pymodule: t.Infra.RopePyModule,
        resource: t.Infra.RopeResource,
    ) -> t.StrSequence:
        """Return export names for one resolved Rope module."""
        attributes = pymodule.get_attributes()
        if export_options.include_dunder:
            return FlextInfraUtilitiesRopeAnalysis._dunder_export_names(
                attributes=attributes,
                resource=resource,
            )
        explicit_all = FlextInfraUtilitiesRopeAnalysis._explicit_export_names(
            attributes=attributes,
            pymodule=pymodule,
            resource=resource,
        )
        if explicit_all is not None:
            return tuple(dict.fromkeys(explicit_all))
        if export_options.require_explicit_all:
            return ()
        return FlextInfraUtilitiesRopeAnalysis._implicit_export_names(
            attributes=attributes,
            export_options=export_options,
            resource=resource,
        )

    @staticmethod
    def _dunder_export_names(
        *,
        attributes: t.MappingKV[str, t.Infra.RopePyName],
        resource: t.Infra.RopeResource,
    ) -> t.StrSequence:
        """Return locally assigned dunder export names."""
        return tuple(
            dict.fromkeys(
                name
                for name, pyname in attributes.items()
                if name != c.Infra.DUNDER_ALL
                and name.startswith("__")
                and name.endswith("__")
                and isinstance(pyname, RopeAssignedName)
                and FlextInfraUtilitiesRopeAnalysis._is_local_name(pyname, resource)
            )
        )

    @staticmethod
    def _explicit_export_names(
        *,
        attributes: t.MappingKV[str, t.Infra.RopePyName],
        pymodule: t.Infra.RopePyModule,
        resource: t.Infra.RopeResource,
    ) -> t.StrSequence | None:
        """Return explicit ``__all__`` export names when declared locally."""
        explicit_all_name = attributes.get(c.Infra.DUNDER_ALL)
        if not isinstance(explicit_all_name, RopeAssignedName):
            return None
        if not FlextInfraUtilitiesRopeAnalysis._is_local_name(
            explicit_all_name,
            resource,
        ):
            return None
        return FlextInfraUtilitiesRopeAnalysis._explicit_all_names(
            explicit_all_name,
            pymodule,
        )

    @staticmethod
    def _implicit_export_names(
        *,
        attributes: t.MappingKV[str, t.Infra.RopePyName],
        export_options: m.Infra.ExportOptions,
        resource: t.Infra.RopeResource,
    ) -> t.StrSequence:
        """Return implicit export names accepted by the export options."""
        names: t.MutableSequenceOf[str] = []
        for name, pyname in attributes.items():
            if name == c.Infra.DUNDER_ALL:
                continue
            if not FlextInfraUtilitiesRopeAnalysis._is_local_name(pyname, resource):
                continue
            if FlextInfraUtilitiesRopeAnalysis._is_export_name(
                export_options=export_options,
                name=name,
                pyname=pyname,
            ):
                names.append(name)
        return tuple(dict.fromkeys(names))

    @staticmethod
    def _is_export_name(
        *,
        export_options: m.Infra.ExportOptions,
        name: str,
        pyname: t.Infra.RopePyName,
    ) -> bool:
        """Return whether one Rope name is exportable under the options."""
        if isinstance(pyname, RopeImportedName):
            return False
        if isinstance(pyname, RopeAssignedName):
            allow_assignments: bool = export_options.allow_assignments
            return allow_assignments
        if not isinstance(pyname, RopeDefinedName):
            return False
        obj = pyname.get_object()
        if isinstance(obj, FlextInfraUtilitiesRopeCore.ABSTRACT_CLASS_TYPES):
            return True
        if not isinstance(obj, FlextInfraUtilitiesRopeCore.PY_FUNCTION_TYPES):
            return False
        allow_main: bool = export_options.allow_main
        allow_functions: bool = export_options.allow_functions
        return (allow_main and name == "main") or allow_functions

    @staticmethod
    def _explicit_all_names(
        pyname: t.Infra.RopeAssignedName,
        pymodule: t.Infra.RopePyModule,
    ) -> t.StrSequence | None:
        """Return literal ``__all__`` names from a Rope-cached source slice.

        Reads the assignment's source range via the module's ``source_code``
        and extracts string literals with ``c.Infra.STRING_LITERAL_RE`` —
        avoiding ``ast`` walking entirely.
        """
        for assignment in pyname.assignments:
            node = assignment.ast_node
            start = getattr(node, "lineno", None)
            end = getattr(node, "end_lineno", None) or start
            if start is None:
                continue
            lines = pymodule.source_code.splitlines()
            slice_text = "\n".join(lines[start - 1 : end])
            return tuple(dict.fromkeys(c.Infra.STRING_LITERAL_RE.findall(slice_text)))
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
    def is_imported_name(pyname: t.Infra.RopePyName) -> bool:
        """Return whether a rope ``PyName`` is an ``ImportedName``."""
        return isinstance(pyname, RopeImportedName)

    @staticmethod
    def is_pyclass(obj: object) -> bool:
        """Return whether a rope object is a ``PyClass`` (abstract class type)."""
        return isinstance(obj, FlextInfraUtilitiesRopeCore.ABSTRACT_CLASS_TYPES)

    @staticmethod
    def is_pyfunction(obj: object) -> bool:
        """Return whether a rope object is a ``PyFunction``."""
        return isinstance(obj, FlextInfraUtilitiesRopeCore.PY_FUNCTION_TYPES)

    @staticmethod
    def module_has_docstring_source(source: str) -> bool:
        """Return whether ``source`` starts with a module docstring (rope-parsed)."""
        pymodule = FlextInfraUtilitiesRopeAnalysis.parse_string_module(source)
        if pymodule is None:
            return False
        try:
            return bool(pymodule.get_doc())
        except FlextInfraUtilitiesRopeCore.RUNTIME_ERRORS:
            return False

    @staticmethod
    def symbol_has_docstring_source(source: str, symbol_name: str) -> bool:
        """Return whether ``symbol_name`` in ``source`` carries a docstring (rope-parsed)."""
        pymodule = FlextInfraUtilitiesRopeAnalysis.parse_string_module(source)
        if pymodule is None:
            return False
        try:
            pyname = pymodule.get_attributes().get(symbol_name)
            if pyname is None:
                return False
            return bool(pyname.get_object().get_doc())
        except FlextInfraUtilitiesRopeCore.RUNTIME_ERRORS:
            return False

    @staticmethod
    def assignment_docstrings_source(source: str) -> t.StrSequence:
        """Return assignment names followed by a string-literal expression (rope-parsed).

        Iterates the parsed module's body via ``_fields`` access and pairs each
        ``Assign``/``AnnAssign`` target with the next sibling ``Expr(Constant(str))``.
        """
        pymodule = FlextInfraUtilitiesRopeAnalysis.parse_string_module(source)
        if pymodule is None:
            return ()
        module_ast = pymodule.get_ast()
        body = getattr(module_ast, "body", []) or []
        names: list[str] = []
        previous_targets: list[str] = []
        for statement in body:
            kind = FlextInfraUtilitiesRopeAnalysis.node_kind(statement)
            if kind in {"Assign", "AnnAssign"}:
                previous_targets = (
                    FlextInfraUtilitiesRopeAnalysis._statement_target_names(
                        statement,
                    )
                )
                continue
            if kind == "Expr" and previous_targets:
                value = getattr(statement, "value", None)
                if (
                    value is not None
                    and FlextInfraUtilitiesRopeAnalysis.node_kind(value) == "Constant"
                    and isinstance(getattr(value, "value", None), str)
                ):
                    names.extend(previous_targets)
            previous_targets = []
        return tuple(dict.fromkeys(names))

    @staticmethod
    def _statement_target_names(statement: object) -> list[str]:
        """Extract target names from an Assign/AnnAssign statement."""
        kind = FlextInfraUtilitiesRopeAnalysis.node_kind(statement)
        if kind == "AnnAssign":
            target = getattr(statement, "target", None)
            name = getattr(target, "id", "") if target is not None else ""
            return [name] if name else []
        targets = getattr(statement, "targets", []) or []
        names: list[str] = []
        for target in targets:
            name = getattr(target, "id", "")
            if isinstance(name, str) and name:
                names.append(name)
        return names

    @staticmethod
    def export_target_modules_source(
        source: str,
        package_name: str,
        exports: t.StrSequence,
    ) -> dict[str, str]:
        """Map exports → defining module via rope's parsed-source import table."""
        export_names = {name for name in exports if name}
        target_map: dict[str, str] = dict.fromkeys(export_names, package_name)
        pymodule = FlextInfraUtilitiesRopeAnalysis.parse_string_module(source)
        if pymodule is None:
            return target_map
        module_ast = pymodule.get_ast()
        for node in FlextInfraUtilitiesRopeAnalysis.walk_ast_nodes(module_ast):
            kind = FlextInfraUtilitiesRopeAnalysis.node_kind(node)
            if kind == "ImportFrom":
                module_name = getattr(node, "module", "") or ""
                names = getattr(node, "names", []) or []
                for alias in names:
                    local = getattr(alias, "asname", None) or getattr(alias, "name", "")
                    if isinstance(local, str) and local in export_names and module_name:
                        target_map[local] = module_name
            elif kind == "Import":
                names = getattr(node, "names", []) or []
                for alias in names:
                    raw_name = getattr(alias, "name", "") or ""
                    local = getattr(alias, "asname", None) or raw_name.partition(".")[0]
                    if isinstance(local, str) and local in export_names and raw_name:
                        module_name = (
                            raw_name.rsplit(".", maxsplit=1)[0]
                            if "." in raw_name
                            else raw_name
                        )
                        target_map[local] = module_name
        return target_map

    @staticmethod
    def parse_string_module(source: str) -> t.Infra.RopePyModule | None:
        """Parse ``source`` to a rope ``PyModule`` via a shared parsing project.

        Uses rope's ``libutils.get_string_module`` so callers don't need to
        manage temporary files. Returns ``None`` on parse failure.
        """
        rope_project = FlextInfraUtilitiesRopeAnalysis._shared_parse_project()
        try:
            pymodule = rope_libutils.get_string_module(rope_project, source)
        except FlextInfraUtilitiesRopeCore.RUNTIME_ERRORS:
            return None
        return pymodule

    @staticmethod
    def _shared_parse_project() -> t.Infra.RopeProject:
        """Return a process-wide rope project usable for string parsing."""
        cached = FlextInfraUtilitiesRopeAnalysis._parse_project
        if cached is None:
            cached = FlextInfraUtilitiesRopeCore.init_rope_project(
                Path("/home/marlonsc/flext"),
            )
            FlextInfraUtilitiesRopeAnalysis._parse_project = cached
        return cached

    @staticmethod
    def decorator_names(pyfunction: object) -> t.StrSequence:
        """Extract decorator names from a rope ``PyFunction`` (no ast import)."""
        decorators = getattr(pyfunction, "decorators", None) or ()
        names: list[str] = []
        for decorator in decorators:
            name = getattr(decorator, "id", None) or getattr(decorator, "attr", None)
            if isinstance(name, str) and name:
                names.append(name)
                continue
            func = getattr(decorator, "func", None)
            inner = getattr(func, "id", None) or getattr(func, "attr", None)
            if isinstance(inner, str) and inner:
                names.append(inner)
        return names

    @staticmethod
    def first_decorator_line(pyfunction: object, *, default_line: int) -> int:
        """Return the lowest line number among ``pyfunction``'s decorators."""
        decorators = getattr(pyfunction, "decorators", None) or ()
        candidate_lines = [
            decorator.lineno
            for decorator in decorators
            if isinstance(getattr(decorator, "lineno", None), int)
        ]
        return min(candidate_lines) if candidate_lines else default_line

    @staticmethod
    def node_kind(node: object) -> str:
        """Return an AST node's class name (e.g. ``"AnnAssign"``) without importing ast."""
        return type(node).__name__

    @staticmethod
    def walk_ast_nodes(root: object) -> t.SequenceOf[object]:
        """Recursively yield every AST node reachable from ``root`` via ``_fields``.

        Equivalent to ``ast.walk`` but uses only public attribute access on
        rope-provided AST objects, so no ``import ast`` is needed at the
        consumer layer.
        """
        collected: list[object] = []
        stack: list[object] = [root]
        while stack:
            node = stack.pop()
            collected.append(node)
            for field_name in getattr(node, "_fields", ()):
                value = getattr(node, field_name, None)
                if isinstance(value, list):
                    stack.extend(item for item in value if hasattr(item, "_fields"))
                elif hasattr(value, "_fields"):
                    stack.append(value)
        return collected

    @staticmethod
    def name_of(node: object) -> str:
        """Return ``node.id`` (Name) or ``node.attr`` (Attribute) or ``""``."""
        identifier = getattr(node, "id", None)
        if isinstance(identifier, str) and identifier:
            return identifier
        attr = getattr(node, "attr", None)
        if isinstance(attr, str) and attr:
            return attr
        return ""

    @staticmethod
    def line_col_range(node: object) -> tuple[int, int, int, int] | None:
        """Return ``(lineno, col_offset, end_lineno, end_col_offset)`` for an AST node."""
        lineno = getattr(node, "lineno", None)
        col_offset = getattr(node, "col_offset", None)
        end_lineno = getattr(node, "end_lineno", None) or lineno
        end_col_offset = getattr(node, "end_col_offset", None) or col_offset
        if not (
            isinstance(lineno, int)
            and isinstance(col_offset, int)
            and isinstance(end_lineno, int)
            and isinstance(end_col_offset, int)
        ):
            return None
        return (lineno, col_offset, end_lineno, end_col_offset)

    @staticmethod
    def _body_nodes(node: p.AttributeProbe) -> t.SequenceOf[p.AttributeProbe]:
        """Return direct AST body children for a Rope AST node."""
        body = getattr(node, "body", ())
        if not isinstance(body, (list, tuple)):
            return ()
        nodes: list[p.AttributeProbe] = [
            child for child in body if hasattr(child, "_fields")
        ]
        return tuple(nodes)

    @staticmethod
    def _class_body_nodes(
        tree: p.AttributeProbe,
        *,
        class_name: str,
    ) -> t.SequenceOf[p.AttributeProbe]:
        """Return direct body nodes for a top-level class name."""
        for node in FlextInfraUtilitiesRopeAnalysis._body_nodes(tree):
            if FlextInfraUtilitiesRopeAnalysis.node_kind(node) != "ClassDef":
                continue
            if getattr(node, "name", "") == class_name:
                return FlextInfraUtilitiesRopeAnalysis._body_nodes(node)
        return ()

    @staticmethod
    def _assignment_target_names(node: p.AttributeProbe) -> t.StrSequence:
        """Return direct assignment target names represented by one AST node."""
        node_kind = FlextInfraUtilitiesRopeAnalysis.node_kind(node)
        if node_kind == "AnnAssign":
            target_name = FlextInfraUtilitiesRopeAnalysis.name_of(
                getattr(node, "target", None)
            )
            return (target_name,) if target_name else ()
        if node_kind != "Assign":
            return ()
        targets = getattr(node, "targets", ())
        if not isinstance(targets, (list, tuple)):
            return ()
        names: list[str] = []
        for target in targets:
            target_name = FlextInfraUtilitiesRopeAnalysis.name_of(target)
            if target_name:
                names.append(target_name)
        return tuple(names)

    @staticmethod
    def _class_symbol_names(
        class_body: t.SequenceOf[p.AttributeProbe],
    ) -> t.StrSequence:
        """Return direct method, nested-class and attribute symbols for a class body."""
        names: set[str] = set()
        for node in class_body:
            node_kind = FlextInfraUtilitiesRopeAnalysis.node_kind(node)
            if node_kind in {"AsyncFunctionDef", "ClassDef", "FunctionDef"}:
                node_name = getattr(node, "name", "")
                if isinstance(node_name, str) and node_name:
                    names.add(node_name)
                continue
            names.update(FlextInfraUtilitiesRopeAnalysis._assignment_target_names(node))
        return tuple(sorted(names))

    @staticmethod
    def get_class_info(
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
    ) -> t.SequenceOf[m.Infra.ClassInfo]:
        """Return ClassInfo (name, line, bases) for all classes in a module."""
        class_infos: t.SequenceOf[m.Infra.ClassInfo] = (
            FlextInfraUtilitiesRopeAnalysis.get_module_semantic_state(
                rope_project,
                resource,
            ).class_infos
        )
        return class_infos

    @staticmethod
    def class_info_from_source(source: str) -> t.SequenceOf[m.Infra.ClassInfo]:
        """Return class info from the current source text without Rope resource cache."""
        pymodule = FlextInfraUtilitiesRopeAnalysis.parse_string_module(source)
        if pymodule is None:
            return ()
        body = getattr(pymodule.get_ast(), "body", ())
        if not isinstance(body, (list, tuple)):
            return ()
        return tuple(
            class_info
            for node in body
            if (
                class_info := FlextInfraUtilitiesRopeAnalysis._class_info_from_ast(node)
            )
            is not None
        )

    @staticmethod
    def _class_info_from_ast(node: object) -> m.Infra.ClassInfo | None:
        """Return ClassInfo for one top-level ClassDef AST node."""
        if FlextInfraUtilitiesRopeAnalysis.node_kind(node) != "ClassDef":
            return None
        name = getattr(node, "name", "")
        if not isinstance(name, str) or not name:
            return None
        line = getattr(node, "lineno", 1)
        raw_bases = getattr(node, "bases", ())
        if not isinstance(raw_bases, (list, tuple)):
            raw_bases = ()
        return m.Infra.ClassInfo(
            name=name,
            line=line if isinstance(line, int) and line > 0 else 1,
            bases=tuple(
                base_name
                for base in raw_bases
                if (base_name := FlextInfraUtilitiesRopeAnalysis._class_base_name(base))
            ),
        )

    @staticmethod
    def _class_base_name(node: object) -> str:
        """Return terminal base name from an AST base expression."""
        for attr_name in ("id", "attr", "name"):
            value = getattr(node, attr_name, "")
            if isinstance(value, str) and value:
                return value
        subscript_value = getattr(node, "value", None)
        if subscript_value is not None:
            return FlextInfraUtilitiesRopeAnalysis._class_base_name(subscript_value)
        return ""

    @staticmethod
    def get_class_symbol_count(
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
        class_name: str,
    ) -> int:
        """Return direct symbol count for a top-level class without semantic imports."""
        try:
            pymodule = FlextInfraUtilitiesRopeCore.get_pymodule(
                rope_project,
                resource,
            )
            tree: p.AttributeProbe = pymodule.get_ast()
        except FlextInfraUtilitiesRopeCore.RUNTIME_ERRORS:
            return 0
        class_body = FlextInfraUtilitiesRopeAnalysis._class_body_nodes(
            tree,
            class_name=class_name,
        )
        return len(FlextInfraUtilitiesRopeAnalysis._class_symbol_names(class_body))

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
        try:
            pymodule = FlextInfraUtilitiesRopeCore.get_pymodule(
                rope_project,
                resource,
            )
        except FlextInfraUtilitiesRopeCore.RUNTIME_ERRORS:
            return {}
        return FlextInfraUtilitiesRopeAnalysis._class_methods_from_pymodule(
            class_name=class_name,
            include_private=include_private,
            pymodule=pymodule,
        )

    @staticmethod
    def _class_methods_from_pymodule(
        *,
        class_name: str,
        include_private: bool,
        pymodule: t.Infra.RopePyModule,
    ) -> t.StrMapping:
        """Return method symbols for a class from one resolved Rope module."""
        result: t.MutableStrMapping = {}
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
            result[name] = child.get_kind()
        return result

    # ------------------------------------------------------------------
    # Path-based rope queries for consumers that previously called
    # ``ast.parse`` on file contents. Each method opens (and closes) a
    # rope project, fetches the cached ``PyModule``, and returns a
    # consumer-shaped result via rope's ``PyObject`` API — no ``ast``
    # parsing, walking, or pattern matching is performed.
    # ------------------------------------------------------------------

    @staticmethod
    def _open_pymodule(
        project_root: Path,
        file_path: Path,
    ) -> tuple[t.Infra.RopePyModule, t.Infra.RopeProject] | None:
        """Open a rope project and resolve ``file_path`` to a ``PyModule``."""
        rope_project = FlextInfraUtilitiesRopeCore.init_rope_project(project_root)
        resource = FlextInfraUtilitiesRopeCore.fetch_python_resource(
            rope_project,
            file_path,
        )
        if resource is None:
            rope_project.close()
            return None
        try:
            pymodule = FlextInfraUtilitiesRopeCore.get_pymodule(
                rope_project,
                resource,
            )
        except FlextInfraUtilitiesRopeCore.RUNTIME_ERRORS:
            rope_project.close()
            return None
        return pymodule, rope_project

    @classmethod
    def module_has_docstring(cls, project_root: Path, file_path: Path) -> bool:
        """Return whether ``file_path``'s module carries a docstring (rope)."""
        opened = cls._open_pymodule(project_root, file_path)
        if opened is None:
            return False
        pymodule, rope_project = opened
        try:
            return bool(pymodule.get_doc())
        finally:
            rope_project.close()

    @classmethod
    def symbol_has_docstring(
        cls,
        project_root: Path,
        file_path: Path,
        symbol_name: str,
    ) -> bool:
        """Return whether ``symbol_name`` carries a docstring via rope."""
        opened = cls._open_pymodule(project_root, file_path)
        if opened is None:
            return False
        pymodule, rope_project = opened
        try:
            pyname = pymodule.get_attributes().get(symbol_name)
            if pyname is None:
                return False
            return bool(pyname.get_object().get_doc())
        finally:
            rope_project.close()

    @classmethod
    def export_target_modules(
        cls,
        project_root: Path,
        file_path: Path,
        package_name: str,
        exports: t.StrSequence,
    ) -> dict[str, str]:
        """Map exports → defining module via rope's import table."""
        export_names = {name for name in exports if name}
        target_map: dict[str, str] = dict.fromkeys(export_names, package_name)
        opened = cls._open_pymodule(project_root, file_path)
        if opened is None:
            return target_map
        pymodule, rope_project = opened
        try:
            resource = pymodule.get_resource()
            if resource is None:
                return target_map
            declared = cls.get_declared_module_imports(rope_project, resource)
            for local_name, declared_path in declared.items():
                if local_name not in export_names:
                    continue
                module_name = (
                    declared_path.rsplit(".", maxsplit=1)[0]
                    if "." in declared_path
                    else declared_path
                )
                if module_name:
                    target_map[local_name] = module_name
        finally:
            rope_project.close()
        return target_map

    @classmethod
    def parent_constants_targets(
        cls,
        constants_file: Path,
        project_root: Path,
        *,
        return_module: bool,
        current_root: str,
    ) -> t.StrSequence:
        """Resolve parent ``Constants`` import targets via rope semantic state.

        Uses ``get_module_semantic_state`` (PyObject-backed class info plus
        ``get_module_imports`` declared-imports table) — no ``ast`` walks.
        """
        opened = cls._open_pymodule(project_root, constants_file)
        if opened is None:
            return ()
        pymodule, rope_project = opened
        try:
            resource = pymodule.get_resource()
            if resource is None:
                return ()
            state = cls.get_module_semantic_state(rope_project, resource)
        finally:
            rope_project.close()
        seen: set[str] = set()
        resolved: list[str] = []
        for class_info in state.class_infos:
            if "Constants" not in class_info.name:
                continue
            for base_name in class_info.bases:
                full_path = state.declared_imports.get(
                    base_name,
                    "",
                ) or state.declared_imports.get(
                    base_name.split(".", maxsplit=1)[0],
                    "",
                )
                if not full_path:
                    continue
                package_root = full_path.split(".", maxsplit=1)[0]
                if package_root == current_root:
                    continue
                target = (
                    package_root
                    if return_module
                    else full_path.rsplit(".", maxsplit=1)[-1]
                )
                if target and target not in seen:
                    seen.add(target)
                    resolved.append(target)
        return tuple(resolved)


__all__: list[str] = ["FlextInfraUtilitiesRopeAnalysis"]
