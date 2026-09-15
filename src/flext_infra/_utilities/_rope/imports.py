"""Import resolution and semantic state analysis."""

from __future__ import annotations

import importlib.util as _importlib_util
from collections.abc import MutableMapping
from typing import TYPE_CHECKING

from flext_infra.constants import c
from flext_infra.models import m
from flext_infra.typings import t

from ..rope_core import FlextInfraUtilitiesRopeCore
from ..rope_runtime import FlextInfraUtilitiesRopeRuntime
from .base import FlextInfraUtilitiesRopeAnalysisBase
from .nodes import FlextInfraUtilitiesRopeAnalysisNodes

if TYPE_CHECKING:
    from flext_infra.protocols import p


class FlextInfraUtilitiesRopeAnalysisImports(FlextInfraUtilitiesRopeAnalysisNodes):
    """Import resolution and semantic state analysis."""

    @staticmethod
    def _resource_cache_key(
        rope_project: t.Infra.RopeProject, resource: t.Infra.RopeResource
    ) -> t.Triple[str, str, int]:
        """Resource cache key."""
        file_path = FlextInfraUtilitiesRopeCore.resource_file_path(
            rope_project, resource
        )
        mtime_ns = (
            file_path.stat().st_mtime_ns
            if file_path is not None and file_path.exists()
            else 0
        )
        project_root = getattr(getattr(rope_project, "root", None), "real_path", "")
        return (str(project_root), resource.path, mtime_ns)

    @staticmethod
    def package_name_for_module(
        module_name: str, resource: t.Infra.RopeResource
    ) -> str:
        """Return the dotted package prefix for one Rope module."""
        return FlextInfraUtilitiesRopeAnalysisImports._package_name_for_module(
            module_name, resource
        )

    @staticmethod
    def _package_name_for_module(
        module_name: str, resource: t.Infra.RopeResource
    ) -> str:
        """Package name for module."""
        if (
            resource.path.endswith(f"/{c.Infra.INIT_PY}")
            or resource.path == c.Infra.INIT_PY
        ):
            return module_name
        return module_name.rsplit(".", maxsplit=1)[0] if "." in module_name else ""

    @staticmethod
    def resolve_import_module(
        *, current_package: str, module_name: str, level: int
    ) -> str:
        """Resolve one declared import to an absolute module name."""
        return FlextInfraUtilitiesRopeAnalysisImports._resolve_import_module(
            current_package=current_package, module_name=module_name, level=level
        )

    @staticmethod
    def _resolve_import_module(
        *, current_package: str, module_name: str, level: int
    ) -> str:
        """Resolve import module."""
        if level <= 0:
            return module_name
        return _importlib_util.resolve_name(
            f"{'.' * level}{module_name}", current_package
        )

    @staticmethod
    def get_module_semantic_state(
        rope_project: t.Infra.RopeProject, resource: t.Infra.RopeResource
    ) -> m.Infra.ModuleSemanticState:
        """Return local classes plus declared and semantic imports in one pass.

        Uses rope's ``PyModule.get_attributes()`` for class discovery and
        ``rope.refactor.importutils.get_module_imports`` for import-table
        construction — no ``ast`` walking is performed.
        """
        cache_key = FlextInfraUtilitiesRopeAnalysisImports._resource_cache_key(
            rope_project, resource
        )
        cached = FlextInfraUtilitiesRopeAnalysisBase._SEMANTIC_STATE_CACHE.get(
            cache_key
        )
        if cached is not None:
            return cached
        pymodule = FlextInfraUtilitiesRopeCore.get_pymodule(rope_project, resource)
        state = (
            FlextInfraUtilitiesRopeAnalysisImports._module_semantic_state_from_pymodule(
                rope_project=rope_project, resource=resource, pymodule=pymodule
            )
        )
        FlextInfraUtilitiesRopeAnalysisBase._SEMANTIC_STATE_CACHE[cache_key] = state
        return state

    @staticmethod
    def _empty_module_semantic_state() -> m.Infra.ModuleSemanticState:
        """Return an empty semantic state."""
        return m.Infra.ModuleSemanticState(
            class_infos=(), declared_imports={}, semantic_imports={}
        )

    @staticmethod
    def _module_semantic_state_from_pymodule(
        *,
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
        pymodule: t.Infra.RopePyModule,
    ) -> m.Infra.ModuleSemanticState:
        """Build semantic state from one resolved Rope module."""
        current_package = (
            FlextInfraUtilitiesRopeAnalysisImports._package_name_for_module(
                pymodule.get_name(), resource
            )
        )
        declared_imports, semantic_imports = (
            FlextInfraUtilitiesRopeAnalysisImports._module_import_maps(
                rope_project=rope_project,
                resource=resource,
                current_package=current_package,
            )
        )
        return m.Infra.ModuleSemanticState(
            class_infos=tuple(
                FlextInfraUtilitiesRopeAnalysisImports._module_class_infos(
                    pymodule=pymodule, resource=resource
                )
            ),
            declared_imports=declared_imports,
            semantic_imports=semantic_imports,
        )

    @staticmethod
    def _module_class_infos(
        *, pymodule: t.Infra.RopePyModule, resource: t.Infra.RopeResource
    ) -> t.SequenceOf[m.Infra.ClassInfo]:
        """Return local class infos for one resolved Rope module."""
        class_infos: t.MutableSequenceOf[m.Infra.ClassInfo] = []
        ast_bases_by_class = {
            class_info.name: class_info.bases
            for class_info in FlextInfraUtilitiesRopeAnalysisNodes.class_info_from_source(
                resource.read()
            )
        }
        for name, pyname in pymodule.get_attributes().items():
            if not FlextInfraUtilitiesRopeAnalysisImports._is_local_name(
                pyname, resource
            ):
                continue
            obj = pyname.get_object()
            if not FlextInfraUtilitiesRopeRuntime.is_abstract_class(obj):
                continue
            location = pyname.get_definition_location()
            line = location[1] if location and location[1] else 1
            bases = tuple(
                base_name
                for superclass in obj.get_superclasses()
                if (
                    base_name
                    := FlextInfraUtilitiesRopeAnalysisImports._superclass_name(
                        superclass
                    )
                )
            )
            if not bases:
                bases = ast_bases_by_class.get(name, ())
            class_infos.append(m.Infra.ClassInfo(name=name, line=line, bases=bases))
        return tuple(class_infos)

    @staticmethod
    def _is_local_name(
        pyname: t.Infra.RopePyName, resource: t.Infra.RopeResource
    ) -> bool:
        """Return whether one Rope name is defined in ``resource``."""
        # NOTE (multi-agent, flext-f8vk / kimi): p.Infra declares
        # get_definition_location() as tuple-always (every other caller
        # unpacks directly); the old None guard was dead code.
        module, line = pyname.get_definition_location()
        origin = module.get_resource() if module is not None else None
        return line is not None and origin is not None and origin.path == resource.path

    @staticmethod
    def superclass_name(superclass: p.AttributeProbe) -> str:
        """Return a superclass name from Rope objects with uneven public APIs."""
        return FlextInfraUtilitiesRopeAnalysisImports._superclass_name(superclass)

    @staticmethod
    def _superclass_name(
        superclass: p.AttributeProbe, *, visited: frozenset[int] | None = None
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
                type_name = FlextInfraUtilitiesRopeAnalysisImports._superclass_name(
                    superclass_type, visited=next_visited
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
    ) -> tuple[MutableMapping[str, str], MutableMapping[str, str]]:
        """Return declared and semantic import maps for one module."""
        semantic_imports: MutableMapping[str, str] = {}
        declared_imports: MutableMapping[str, str] = {}
        module_imports = FlextInfraUtilitiesRopeCore.get_module_imports(
            rope_project, resource
        )
        raw_imports = getattr(module_imports, "imports", ())
        import_stmts: t.VariadicTuple[t.Infra.RopeImportStatement] = tuple(raw_imports)
        for import_stmt in import_stmts:
            FlextInfraUtilitiesRopeAnalysisImports._merge_import_statement(
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
        declared_imports: MutableMapping[str, str],
        import_stmt: t.Infra.RopeImportStatement,
        semantic_imports: MutableMapping[str, str],
    ) -> None:
        """Merge one Rope import statement into the import maps."""
        info = import_stmt.import_info
        module_name = getattr(info, "module_name", "") or ""
        resolved_module = (
            FlextInfraUtilitiesRopeAnalysisImports._resolved_import_module(
                current_package=current_package,
                module_name=module_name,
                level=getattr(info, "level", 0) or 0,
            )
        )
        for alias_name, alias_as in info.names_and_aliases or ():
            FlextInfraUtilitiesRopeAnalysisImports._merge_import_alias(
                alias_name=alias_name,
                alias_as=alias_as,
                declared_imports=declared_imports,
                module_name=module_name,
                resolved_module=resolved_module,
                semantic_imports=semantic_imports,
            )

    @staticmethod
    def _resolved_import_module(
        *, current_package: str, module_name: str, level: int
    ) -> str:
        """Resolve the module path represented by one Rope import info."""
        return (
            FlextInfraUtilitiesRopeAnalysisImports._resolve_import_module(
                current_package=current_package, module_name=module_name, level=level
            )
            if module_name
            else ""
        )

    @staticmethod
    def _merge_import_alias(
        *,
        alias_name: str,
        alias_as: str | None,
        declared_imports: MutableMapping[str, str],
        module_name: str,
        resolved_module: str,
        semantic_imports: MutableMapping[str, str],
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
    def get_semantic_module_imports(
        rope_project: t.Infra.RopeProject, resource: t.Infra.RopeResource
    ) -> t.StrMapping:
        """Return {local_name: fully_qualified_name} for all imports in a module."""
        imports: t.StrMapping = (
            FlextInfraUtilitiesRopeAnalysisImports.get_module_semantic_state(
                rope_project, resource
            ).semantic_imports
        )
        return imports

    @staticmethod
    def get_declared_module_imports(
        rope_project: t.Infra.RopeProject, resource: t.Infra.RopeResource
    ) -> t.StrMapping:
        """Return {local_name: declared import path} without resolving re-exports."""
        imports: t.StrMapping = (
            FlextInfraUtilitiesRopeAnalysisImports.get_module_semantic_state(
                rope_project, resource
            ).declared_imports
        )
        return imports

    @staticmethod
    def relative_import_module_name(
        *, current_module: str, imported_module: str, level: int, package_module: bool
    ) -> str:
        """Resolve a parsed ``from`` import module into an absolute module name."""
        if level == 0:
            return imported_module
        current_parts = current_module.split(".")
        base_count = len(current_parts) - level + (1 if package_module else 0)
        base = ".".join(current_parts[: max(base_count, 0)])
        return ".".join(part for part in (base, imported_module) if part)


__all__ = ["FlextInfraUtilitiesRopeAnalysisImports"]
