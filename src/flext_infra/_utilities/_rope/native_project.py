"""Native Rope resource and module interface over declared import roots.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager
from typing import Self, cast, overload, override

from rope.base.project import Project
from rope.base.resources import File, Folder, Resource

from flext_infra import c, p, t


class FlextInfraRopeNativeProject(Project):
    """Preserve native SDK identities behind the consumed project interface."""

    fscommands: p.Infra.RopeProjectFiles
    _frozen_folders: tuple[list[File | Folder], list[File | Folder]] | None = None
    _snapshot_python_path_folders: list[File | Folder] | None = None
    _custom_source_folders: list[File | Folder]

    @property
    @override
    def root(self) -> p.Infra.RopeRoot:
        """Declared project root folder.

        Returns:
            The native project root folder.

        Raises:
            TypeError: The SDK published a non-folder root.

        """
        root = super().root
        if not isinstance(root, Folder):
            message = "Rope project root must be a native folder"
            raise TypeError(message)
        return root

    @override
    def get_pymodule(
        self,
        resource: Resource | p.Infra.RopeResource,
        force_errors: bool = False,
    ) -> t.Infra.RopeNativeParsedModule:
        """Resolve a native resource while preserving the SDK return classes.

        Returns:
            The original native module or package.

        Raises:
            TypeError: The caller did not supply a native resource.

        """
        if not isinstance(resource, Resource):
            message = "Rope module lookup requires a native resource"
            raise TypeError(message)
        native = cast("p.Infra.RopeProject", super())
        return native.get_pymodule(
            cast("p.Infra.RopeResource", resource),
            force_errors=force_errors,
        )

    @override
    def get_module(
        self,
        name: str,
        folder: Folder | p.Infra.RopeRoot | None = None,
    ) -> t.Infra.RopeNativeSemanticModule:
        """Resolve the native semantic module elected by the SDK.

        Returns:
            The original native builtin, package, or source module.

        """
        native = cast("p.Infra.RopeProject", super())
        return native.get_module(name, self._native_folder(folder))

    @override
    def get_relative_module(
        self,
        name: str,
        folder: Folder | p.Infra.RopeRoot,
        level: int,
    ) -> t.Infra.RopeNativeParsedModule:
        """Resolve a relative import from its native declaring resource.

        Returns:
            The original native package or source module.

        """
        native = cast("p.Infra.RopeProject", super())
        return native.get_relative_module(name, self._native_folder(folder), level)

    @override
    def find_module(
        self,
        modname: str,
        folder: p.Infra.RopeRoot | Folder | None = None,
    ) -> File | Folder | None:
        """Admit the resource elected by Rope's native module finder.

        Returns:
            The native module resource, or no matching module.

        Raises:
            TypeError: The elected resource is not a native file or folder.

        """
        native = cast("p.Infra.RopeProject", super())
        found = native.find_module(modname, self._native_folder(folder))
        if found is not None and not isinstance(found, File | Folder):
            message = "Rope module finder did not elect a native resource"
            raise TypeError(message)
        return found

    @override
    def find_relative_module(
        self,
        modname: str,
        folder: Folder | p.Infra.RopeRoot,
        level: int,
    ) -> File | Folder | None:
        """Delegate relative resource election to its native SDK owner.

        Returns:
            The elected native resource, or no matching module in the folder.

        Raises:
            TypeError: The elected resource is not a native file or folder.

        """
        native = cast("p.Infra.RopeProject", super())
        found = native.find_relative_module(
            modname,
            self._native_folder(folder),
            level,
        )
        if found is not None and not isinstance(found, File | Folder):
            message = "Rope relative finder did not elect a native resource"
            raise TypeError(message)
        return found

    @override
    def get_resource(self, resource_name: str) -> File | Folder:
        """Elect the native resource addressed by a project-relative name.

        Returns:
            The elected native file or folder resource.

        Raises:
            TypeError: The SDK elected a resource outside its native classes.

        """
        native = cast("p.Infra.RopeProject", super())
        found = native.get_resource(resource_name)
        if not isinstance(found, File | Folder):
            message = "Rope resource lookup did not elect a native resource"
            raise TypeError(message)
        return found

    @staticmethod
    @overload
    def _native_folder(folder: Folder | p.Infra.RopeRoot) -> Folder: ...

    @staticmethod
    @overload
    def _native_folder(folder: None) -> None: ...

    @staticmethod
    def _native_folder(folder: Folder | p.Infra.RopeRoot | None) -> Folder | None:
        """Validate the native folder once at the SDK adapter boundary.

        Returns:
            The supplied native folder or absent absolute-lookup context.

        Raises:
            TypeError: The supplied folder is not native.

        """
        if folder is not None and not isinstance(folder, Folder):
            message = "Rope module lookup requires a native folder"
            raise TypeError(message)
        return folder

    @contextmanager
    def frozen_layout(self) -> Generator[Self]:
        """Freeze the native source and Python path folders for one read-only pass.

        Yields:
            This project, its folder layout computed once for the pass.

        """
        source_folders = self.get_source_folders()
        python_path_folders = self.get_python_path_folders()
        self._frozen_folders = (source_folders, python_path_folders)
        try:
            yield self
        finally:
            self._frozen_folders = None

    @override
    def get_source_folders(self) -> list[File | Folder]:
        """Return declared import roots, frozen during a read-only pass.

        Package roots also expose their parent so their qualified name resolves.
        Unrelated workspace resources never participate in source discovery.

        Returns:
            Declared folders and the import roots of declared packages.

        """
        if self._frozen_folders is None:
            folders: list[File | Folder] = list(self._custom_source_folders)
            for folder in self._custom_source_folders:
                if not isinstance(folder, Folder):
                    continue
                native = cast("p.Infra.RopeRoot", folder)
                if (
                    native.has_child(c.Infra.INIT_PY)
                    and not native.get_child(c.Infra.INIT_PY).is_folder()
                    and native.parent not in folders
                    and isinstance(native.parent, Folder)
                ):
                    folders.append(native.parent)
            return folders
        return list(self._frozen_folders[0])

    @override
    def get_python_path_folders(self) -> list[File | Folder]:
        """Declared Python path folders, frozen during a read-only pass.

        Returns:
            The folders Rope's own contract returns.

        Raises:
            TypeError: The SDK published a non-native Python path folder.

        """
        if self._frozen_folders is None:
            if self._snapshot_python_path_folders is not None:
                return list(self._snapshot_python_path_folders)
            native = cast("p.Infra.RopeProject", super())
            folders: list[File | Folder] = []
            for folder in native.get_python_path_folders():
                if not isinstance(folder, File | Folder):
                    message = "Rope Python path published a non-native folder"
                    raise TypeError(message)
                folders.append(folder)
            return folders
        return list(self._frozen_folders[1])


__all__: list[str] = ["FlextInfraRopeNativeProject"]
