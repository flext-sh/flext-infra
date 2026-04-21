"""Shared Rope lifecycle helpers."""

from __future__ import annotations

from collections.abc import (
    Generator,
    Sequence,
)
from contextlib import contextmanager
from pathlib import Path
from typing import ClassVar

import rope.refactor.importutils as rope_importutils
from flext_infra import FlextInfraUtilitiesIteration, c, t
from rope.base.exceptions import (
    ModuleSyntaxError,
    RefactoringError,
    ResourceNotFoundError,
)
from rope.base.project import Project
from rope.base.pyobjects import AbstractClass
from rope.base.pyobjectsdef import PyFunction, PyModule
from rope.base.resources import File


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
        project_prefix: str = c.Infra.PKG_PREFIX_HYPHEN,
        src_dir: str = c.Infra.DEFAULT_SRC_DIR,
        ignored_resources: tuple[str, ...] = c.Infra.ROPE_IGNORED_RESOURCES,
    ) -> Project:
        """Create a rope Project over workspace_root with no disk artifacts."""
        _ = (project_prefix, src_dir)
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
    def get_resource_from_path(
        rope_project: t.Infra.RopeProject,
        file_path: Path,
    ) -> t.Infra.RopeResource | None:
        """Return rope File for a filesystem Path, or None if outside project."""
        try:
            root_real_path = getattr(
                getattr(rope_project, "root", None),
                "real_path",
                None,
            )
            if not isinstance(root_real_path, str):
                return None
            relative_path = str(file_path.resolve().relative_to(Path(root_real_path)))
            resource = rope_project.get_resource(relative_path)
            return resource if isinstance(resource, File) else None
        except (ResourceNotFoundError, ValueError):
            return None

    @staticmethod
    def python_resources(
        rope_project: t.Infra.RopeProject,
    ) -> Sequence[t.Infra.RopeResource]:
        """Return stable Python file resources for one Rope project."""
        return tuple(
            resource
            for file_path in FlextInfraUtilitiesRopeCore.python_file_paths(rope_project)
            if (
                resource := FlextInfraUtilitiesRopeCore.get_resource_from_path(
                    rope_project,
                    file_path,
                )
            )
            is not None
        )

    @staticmethod
    def python_file_paths(
        rope_project: t.Infra.RopeProject,
    ) -> Sequence[Path]:
        """Return stable Python file paths for one Rope project."""
        root_real_path = getattr(getattr(rope_project, "root", None), "real_path", None)
        if not isinstance(root_real_path, str):
            return ()
        file_paths = FlextInfraUtilitiesIteration.iter_python_files(
            Path(root_real_path),
        )
        if file_paths.failure:
            return ()
        return tuple(
            sorted(
                file_paths.unwrap(),
                key=lambda file_path: file_path.as_posix(),
            ),
        )

    @staticmethod
    def resource_file_path(
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
    ) -> Path | None:
        """Resolve one Rope resource back to an absolute filesystem path."""
        root_real_path = getattr(getattr(rope_project, "root", None), "real_path", None)
        if not isinstance(root_real_path, str):
            return None
        return Path(root_real_path, resource.path).resolve()

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
    def get_module_imports(
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
    ) -> t.Infra.RopeModuleImports | None:
        try:
            module_imports = rope_importutils.get_module_imports(
                rope_project,
                FlextInfraUtilitiesRopeCore.get_pymodule(rope_project, resource),
            )
        except (RefactoringError, ResourceNotFoundError, AttributeError):
            return None
        return module_imports


__all__: list[str] = ["FlextInfraUtilitiesRopeCore"]
