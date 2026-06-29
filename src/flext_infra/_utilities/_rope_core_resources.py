"""Rope resource path helpers for FlextInfraUtilitiesRopeCore."""

from __future__ import annotations

from pathlib import Path

from rope.base.exceptions import ResourceNotFoundError
from rope.base.project import Project
from rope.base.resources import File

from flext_core import t
from flext_infra._constants.namespace import FlextInfraConstantsNamespace
from flext_infra._constants.validate import FlextInfraConstantsSharedInfra
from flext_infra._utilities.file_iteration import FlextInfraUtilitiesFileIteration


class FlextInfraUtilitiesRopeCoreResourcesMixin:
    """Filesystem-to-Rope resource helpers."""

    @staticmethod
    def get_resource_from_path(
        rope_project: Project,
        file_path: Path,
    ) -> File | None:
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
    def fetch_python_resource(
        rope_project: Project,
        file_path: Path,
        *,
        skip_protected: bool = False,
        skip_settings: bool = False,
        skip_alias_modules: bool = False,
        skip_init_py: bool = False,
    ) -> File | None:
        """Resolve a Python source as a Rope resource, or None when skipped."""
        if not FlextInfraUtilitiesRopeCoreResourcesMixin._python_resource_allowed(
            file_path,
            skip_protected=skip_protected,
            skip_settings=skip_settings,
            skip_alias_modules=skip_alias_modules,
            skip_init_py=skip_init_py,
        ):
            return None
        return FlextInfraUtilitiesRopeCoreResourcesMixin.get_resource_from_path(
            rope_project,
            file_path,
        )

    @staticmethod
    def _python_resource_allowed(
        file_path: Path,
        *,
        skip_protected: bool,
        skip_settings: bool,
        skip_alias_modules: bool,
        skip_init_py: bool,
    ) -> bool:
        """Return whether a path should be exposed as a Python Rope resource."""
        return (
            file_path.suffix == FlextInfraConstantsSharedInfra.EXT_PYTHON
            and not (
                skip_init_py
                and file_path.name == FlextInfraConstantsSharedInfra.INIT_PY
            )
            and not (
                skip_protected
                and file_path.name
                in FlextInfraConstantsNamespace.NAMESPACE_PROTECTED_FILES
            )
            and not (
                skip_settings
                and file_path.name
                in FlextInfraConstantsNamespace.NAMESPACE_SETTINGS_FILE_NAMES
            )
            and not (
                skip_alias_modules
                and file_path.stem
                in FlextInfraConstantsNamespace.NAMESPACE_CANONICAL_ALIAS_MODULE_STEMS
            )
        )

    @staticmethod
    def python_resources(
        rope_project: Project,
    ) -> t.SequenceOf[File]:
        """Return stable Python file resources for one Rope project."""
        return tuple(
            resource
            for file_path in FlextInfraUtilitiesRopeCoreResourcesMixin.python_file_paths(
                rope_project
            )
            if (
                resource
                := FlextInfraUtilitiesRopeCoreResourcesMixin.get_resource_from_path(
                    rope_project,
                    file_path,
                )
            )
            is not None
        )

    @staticmethod
    def python_file_paths(
        rope_project: Project,
    ) -> t.SequenceOf[Path]:
        """Return stable Python file paths for one Rope project."""
        root_real_path = getattr(getattr(rope_project, "root", None), "real_path", None)
        if not isinstance(root_real_path, str):
            return ()
        file_paths = FlextInfraUtilitiesFileIteration.iter_python_files(
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
        rope_project: Project,
        resource: File,
    ) -> Path | None:
        """Resolve one Rope resource back to an absolute filesystem path."""
        root_real_path = getattr(getattr(rope_project, "root", None), "real_path", None)
        if not isinstance(root_real_path, str):
            return None
        return Path(root_real_path, resource.path).resolve()


__all__: list[str] = ["FlextInfraUtilitiesRopeCoreResourcesMixin"]
