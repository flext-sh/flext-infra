"""Project-level docstring, export, and constants analysis."""

from __future__ import annotations

from collections.abc import MutableMapping
from pathlib import Path

from flext_infra.typings import t

from .ast import FlextInfraUtilitiesRopeAnalysisAst


class FlextInfraUtilitiesRopeAnalysisAnalysis(FlextInfraUtilitiesRopeAnalysisAst):
    """Project-level docstring, export, and constants analysis."""

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
        cls, project_root: Path, file_path: Path, symbol_name: str
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
    ) -> MutableMapping[str, str]:
        """Map exports → defining module via rope's import table."""
        export_names = {name for name in exports if name}
        target_map: MutableMapping[str, str] = dict.fromkeys(export_names, package_name)
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
            source_class_bases = {
                class_info.name: class_info.bases
                for class_info in cls.class_info_from_source(resource.read())
            }
            state = cls.get_module_semantic_state(rope_project, resource)
        finally:
            rope_project.close()
        seen: set[str] = set()
        resolved: list[str] = []
        for class_info in state.class_infos:
            if "Constants" not in class_info.name:
                continue
            for base_name in (
                *class_info.bases,
                *source_class_bases.get(class_info.name, ()),
            ):
                full_path = state.declared_imports.get(
                    base_name, ""
                ) or state.declared_imports.get(base_name.split(".", maxsplit=1)[0], "")
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


__all__ = ["FlextInfraUtilitiesRopeAnalysisAnalysis"]
