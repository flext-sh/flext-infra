"""Shared Rope lifecycle helpers."""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import ClassVar

import rope.refactor.importutils as rope_importutils
from rope.base.change import ChangeContents, ChangeSet
from rope.base.exceptions import (
    ModuleSyntaxError,
    RefactoringError,
    ResourceNotFoundError,
)
from rope.base.project import Project
from rope.base.pyobjects import AbstractClass
from rope.base.pyobjectsdef import PyFunction, PyModule
from rope.base.resources import File
from rope.refactor.importutils.importinfo import FromImport
from rope.refactor.importutils.module_imports import ModuleImports

from flext_infra import FlextInfraUtilitiesIteration, c, t


class FlextInfraUtilitiesRopeCore:
    """Core Rope lifecycle helpers."""

    SYNTAX_ERRORS: ClassVar[tuple[type[BaseException], ...]] = (
        SyntaxError,
        ModuleSyntaxError,
    )
    RUNTIME_ERRORS: ClassVar[tuple[type[BaseException], ...]] = (
        RefactoringError,
        ResourceNotFoundError,
        AttributeError,
    )
    ABSTRACT_CLASS_TYPES: ClassVar[tuple[type[AbstractClass], ...]] = (AbstractClass,)
    PY_FUNCTION_TYPES: ClassVar[tuple[type[PyFunction], ...]] = (PyFunction,)

    @staticmethod
    def init_rope_project(
        workspace_root: Path,
        *,
        project_prefix: str = c.Infra.Packages.PREFIX_HYPHEN,
        src_dir: str = c.Infra.Paths.DEFAULT_SRC_DIR,
        ignored_resources: tuple[str, ...] = c.Infra.ROPE_IGNORED_RESOURCES,
    ) -> Project:
        """Create a rope Project over workspace_root with no disk artifacts."""
        _ = project_prefix
        _ = src_dir
        resolved_root = workspace_root.resolve()
        source_folders = sorted({
            str(scan_path.relative_to(resolved_root))
            for project_root in FlextInfraUtilitiesIteration.discover_project_roots(
                resolved_root,
                scan_dirs=frozenset(c.Infra.MRO_SCAN_DIRECTORIES),
            )
            for dir_name in c.Infra.MRO_SCAN_DIRECTORIES
            if (scan_path := project_root / dir_name).is_dir()
        })
        return Project(
            str(resolved_root),
            ropefolder="",
            save_objectdb=False,
            ignored_resources=list(ignored_resources),
            source_folders=source_folders,
        )

    @staticmethod
    @contextmanager
    def open_project(
        workspace_root: Path,
    ) -> Generator[Project]:
        """Open one Rope project and always close it through the core boundary."""
        rope_project = FlextInfraUtilitiesRopeCore.init_rope_project(workspace_root)
        try:
            yield rope_project
        finally:
            rope_project.close()

    @staticmethod
    def project_root_path(rope_project: t.Infra.RopeProject) -> Path | None:
        """Return the filesystem root path from Rope's dynamic project object."""
        root = getattr(rope_project, "root", None)
        root_real_path = getattr(root, "real_path", "")
        return Path(root_real_path) if isinstance(root_real_path, str) else None

    @staticmethod
    def get_resource_from_path(
        rope_project: t.Infra.RopeProject,
        file_path: Path,
    ) -> t.Infra.RopeResource | None:
        """Return rope File for a filesystem Path, or None if outside project."""
        try:
            project_root = FlextInfraUtilitiesRopeCore.project_root_path(rope_project)
            if project_root is None:
                return None
            relative_path = str(file_path.resolve().relative_to(project_root))
            resource = rope_project.get_resource(relative_path)
            if isinstance(resource, File):
                return resource
        except (ResourceNotFoundError, ValueError):
            return None
        return None

    @staticmethod
    def get_pymodule(
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
    ) -> t.Infra.RopePyModule:
        """Resolve one concrete rope PyModule through the validated API boundary."""
        pymodule = rope_project.get_pymodule(resource)
        if not isinstance(pymodule, PyModule):
            msg = "rope project returned non-PyModule"
            raise TypeError(msg)
        return pymodule

    @staticmethod
    def get_module_imports_for_pymodule(
        rope_project: t.Infra.RopeProject,
        pymodule: t.Infra.RopePyModule,
    ) -> t.Infra.RopeModuleImports:
        """Resolve module imports through Rope's concrete Project/PyModule API."""
        module_imports = rope_importutils.get_module_imports(
            rope_project,
            pymodule,
        )
        if not isinstance(module_imports, ModuleImports):
            msg = "rope module imports helper does not satisfy RopeModuleImports"
            raise TypeError(msg)
        return module_imports

    @staticmethod
    def get_module_imports(
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
    ) -> t.Infra.RopeModuleImports | None:
        try:
            pymodule = FlextInfraUtilitiesRopeCore.get_pymodule(
                rope_project,
                resource,
            )
            return FlextInfraUtilitiesRopeCore.get_module_imports_for_pymodule(
                rope_project,
                pymodule,
            )
        except (RefactoringError, ResourceNotFoundError, AttributeError):
            return None

    @staticmethod
    def absolute_from_import_any(
        import_info: object,
    ) -> t.Infra.RopeFromImport | None:
        """Expose absolute from-import narrowing through the public Rope boundary."""
        return (
            import_info
            if isinstance(import_info, FromImport) and import_info.level == 0
            else None
        )

    @staticmethod
    def absolute_from_import(
        import_info: object,
        *,
        module_name: str,
    ) -> t.Infra.RopeFromImport | None:
        """Expose absolute from-import matching through the public Rope boundary."""
        absolute_import = FlextInfraUtilitiesRopeCore.absolute_from_import_any(
            import_info,
        )
        return (
            absolute_import
            if absolute_import is not None
            and absolute_import.module_name == module_name
            else None
        )

    @staticmethod
    def apply_source_change(
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
        content: str,
        *,
        description: str,
    ) -> None:
        """Apply a single-file content change via rope ChangeSet."""
        change_set = ChangeSet(description)
        change_set.add_change(ChangeContents(resource, content))
        rope_project.do(change_set)

    @staticmethod
    def line_offset_for_symbol(
        *,
        source: str,
        line_number: int,
        symbol: str,
    ) -> int | None:
        """Convert Rope line metadata into a character offset via the public core API."""
        lines = source.splitlines(keepends=True)
        if line_number < 1 or line_number > len(lines):
            return None
        line = lines[line_number - 1]
        column = line.find(symbol)
        if column < 0:
            return None
        return sum(len(item) for item in lines[: line_number - 1]) + column


__all__ = ["FlextInfraUtilitiesRopeCore"]
