"""Native Rope resource and module interface over declared import roots.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import importlib.machinery
import importlib.util
import os
import sys
import threading
from collections.abc import Generator, Sequence
from contextlib import contextmanager
from functools import cache
from pathlib import Path
from typing import ClassVar, Self, cast, overload, override

from rope.base.builtins import BuiltinModule
from rope.base.project import NoProject, Project
from rope.base.pycore import PyCore
from rope.base.resources import File, Folder, Resource

from flext_infra import c, p, t
from flext_infra._utilities import FlextInfraUtilitiesProjectDiscovery


class FlextInfraRopeNativeProject(Project):
    """Preserve native SDK identities behind the consumed project interface.

    Authenticated Python inventories elect source paths before native resource
    construction. Unrelated non-Python entries are not import inputs; selected
    Python aliases remain visible to the strict source-query boundary. Declared
    folders include project-root lookup anchors as well as source trees: lookup
    alone never selects non-Python root aliases. Dependency paths and added
    package-lookup parents do not enlarge the source election.
    Unbound SDK projects retain their SDK-owned inventory, including closed
    snapshots whose virtual modules need not exist on disk.
    """

    fscommands: p.Infra.RopeProjectFiles
    external_project: NoProject | None
    observers: list[p.Infra.RopeChangeObserver]
    _frozen_folders: tuple[list[File | Folder], list[File | Folder]] | None = None
    _frozen_modules: dict[tuple[str, str | None], File | Folder | None] | None = None
    _snapshot_python_path_folders: list[File | Folder] | None = None
    _custom_source_folders: list[File | Folder]
    _dependency_universe: bool = False
    _dependency_election: (
        tuple[
            tuple[int, int],
            tuple[int, tuple[str, ...], tuple[str, ...]] | None,
        ]
        | None
    ) = None
    _dependency_projects: ClassVar[
        dict[tuple[int, tuple[str, ...], tuple[str, ...]], FlextInfraRopeNativeProject]
    ] = {}

    class DependencyCore(PyCore):
        """Native core that parses installed modules once per process.

        Installed modules resolve only against the declared Python path, so a
        project whose sources shadow none of them reads the same native
        modules every other such project reads. Those modules belong to one
        process-wide dependency project per interpreter thread and election;
        a project with analysis views or shadowing sources keeps its own.
        """

        project: FlextInfraRopeNativeProject

        @override
        def resource_to_pyobject(
            self,
            resource: Resource,
            force_errors: bool = False,
        ) -> t.Infra.RopeNativeParsedModule:
            """Read installed modules from the shared dependency project.

            Returns:
                The shared installed module, or this project's own module.

            """
            universe = self.project.dependency_universe(resource)
            if universe is None:
                return super().resource_to_pyobject(resource, force_errors)
            owner = universe.external_project
            if owner is None:
                msg = "shared dependency project lost its external resolver"
                raise TypeError(msg)
            path = resource.real_path
            return universe.pycore.resource_to_pyobject(
                owner.get_folder(path) if resource.is_folder() else owner.get_file(path),
                force_errors,
            )

    @property
    @override
    def pycore(self) -> PyCore:
        """Native core reading installed modules once per process.

        Returns:
            This project's native core.

        """
        core = self.__dict__.get("_pycore")
        if not isinstance(core, PyCore):
            core = self.DependencyCore(self)
            self.__dict__["_pycore"] = core
        return core

    def dependency_universe(self, resource: Resource) -> FlextInfraRopeNativeProject | None:
        """Elect the shared dependency project that owns an installed module.

        Returns:
            The shared dependency project, or None when this project owns it.

        """
        if self._dependency_universe or resource.project is self:
            return None
        key = self._dependency_key()
        if key is None or not any(
            Path(resource.real_path).is_relative_to(folder) for folder in key[1]
        ):
            return None
        universe = FlextInfraRopeNativeProject._dependency_projects.get(key)
        if universe is None:
            universe = FlextInfraRopeNativeProject(
                key[1][0],
                ropefolder=None,
                config_files=False,
                save_objectdb=False,
                save_history=False,
                extension_modules=list(key[2]),
            )
            universe._dependency_universe = True
            universe._custom_source_folders = []
            external = NoProject()
            external.prefs.extension_modules = list(key[2])
            universe.external_project = external
            universe._snapshot_python_path_folders = [
                external.get_folder(folder) for folder in key[1]
            ]
            FlextInfraRopeNativeProject._dependency_projects[key] = universe
        return universe

    def _dependency_key(
        self,
    ) -> tuple[int, tuple[str, ...], tuple[str, ...]] | None:
        """Elect this epoch's shared installed view when no source shadows it.

        Returns:
            The thread, ordered installed folders and extension modules, or
            None when a source shadows an installed module.

        """
        epoch = (
            self.pycore.module_cache.data_epoch,
            id(self._snapshot_python_path_folders),
        )
        election = self._dependency_election
        if election is not None and election[0] == epoch:
            return election[1]
        root = Path(self.root.real_path)
        folders = tuple(
            dict.fromkeys(
                folder.real_path
                for folder in self.get_python_path_folders()
                if isinstance(folder, Folder)
                and not Path(folder.real_path).is_relative_to(root)
            )
        )
        sources = {
            child.name.removesuffix(c.Infra.EXT_PYTHON)
            for folder in self.get_source_folders()
            if isinstance(folder, Folder)
            for child in folder.get_children()
        }
        installed = {
            name.removesuffix(c.Infra.EXT_PYTHON)
            for folder in folders
            for name in FlextInfraRopeNativeProject._folder_names(folder)
        }
        key = (
            None
            if not folders or sources & installed
            else (
                threading.get_ident(),
                folders,
                tuple(sorted(self.prefs.get("extension_modules", ()))),
            )
        )
        self._dependency_election = (epoch, key)
        return key

    @staticmethod
    @cache
    def _folder_names(folder: str) -> frozenset[str]:
        """List one installed folder's entries once per process.

        Returns:
            The entry names of the installed folder.

        """
        return frozenset(os.listdir(folder)) if Path(folder).is_dir() else frozenset()

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

        Candidate syntax failures propagate unchanged from the native lookup.

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
        folder: Folder | p.Infra.RopeRoot | p.Infra.RopeResource | None = None,
    ) -> t.Infra.RopeNativeSemanticModule:
        """Resolve the native semantic module elected by the SDK.

        Candidate syntax failures propagate unchanged from the native lookup.

        Returns:
            The original native builtin, package, or source module.

        """
        native = cast("p.Infra.RopeProject", super())
        if self.find_module(name, folder) is None and (
            name.partition(".")[0] in sys.stdlib_module_names
        ):
            # Per-repository resolution law: the interpreter's import system
            # elects stdlib modules only. Governed member modules resolve
            # through this project's own index — never through the shared
            # environment, where divergent member libraries would leak in.
            spec = importlib.util.find_spec(name)
            if spec is not None and isinstance(
                spec.loader, importlib.machinery.ExtensionFileLoader
            ):
                return BuiltinModule(name, self.pycore)
        return native.get_module(name, self._native_folder(folder))

    @override
    def get_relative_module(
        self,
        name: str,
        folder: Folder | p.Infra.RopeRoot | None,
        level: int,
    ) -> t.Infra.RopeNativeParsedModule:
        """Resolve a relative import from its native declaring resource.

        Returns:
            The original native package or source module.

        """
        native = cast("p.Infra.RopeProject", super())
        origin = self._native_folder(folder) or self._native_folder(self.root)
        return native.get_relative_module(name, origin, level)

    @override
    def find_module(
        self,
        modname: str,
        folder: p.Infra.RopeRoot | p.Infra.RopeResource | Folder | None = None,
    ) -> File | Folder | None:
        """Admit the resource elected by Rope's native module finder.

        Returns:
            The native module resource, or no matching module.

        """
        # The folder layout is fixed for a read-only pass, so each lookup's
        # election is fixed too: answer it once instead of rescanning folders.
        memo = self._frozen_modules
        key = (modname, None if folder is None else folder.path)
        if memo is not None and key in memo:
            return memo[key]
        found = self.find_module_native(modname, folder)
        if memo is not None:
            memo[key] = found
        return found

    def find_module_native(
        self,
        modname: str,
        folder: p.Infra.RopeRoot | p.Infra.RopeResource | Folder | None = None,
    ) -> File | Folder | None:
        """Elect through Rope's own finder without consulting the freeze memo.

        Refresh paths reuse this entry after membership changes invalidated
        memoized elections, so a stale memo must never answer them.

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
        folder: Folder | p.Infra.RopeRoot | None,
        level: int,
    ) -> File | Folder | None:
        """Delegate relative resource election to its native SDK owner.

        Returns:
            The elected native resource, or no matching module in the folder.

        Raises:
            TypeError: The elected resource is not a native file or folder.

        """
        native = cast("p.Infra.RopeProject", super())
        origin = self._native_folder(folder) or self._native_folder(self.root)
        found = native.find_relative_module(modname, origin, level)
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

    @override
    def get_file(self, path: str) -> File:
        """Elect the native file addressed by a project-relative path.

        The file may not exist on disk; the overlay decides its visibility.

        Returns:
            The native file resource.

        Raises:
            TypeError: The SDK elected a resource outside its native classes.

        """
        native = cast("p.Infra.RopeProject", super())
        found = native.get_file(path)
        if not isinstance(found, File):
            message = "Rope file lookup did not elect a native file"
            raise TypeError(message)
        return found

    @override
    def get_folder(self, path: str) -> Folder:
        """Elect the native folder addressed by a project-relative path.

        The folder may not exist on disk; the overlay decides its visibility.

        Returns:
            The native folder resource.

        Raises:
            TypeError: The SDK elected a resource outside its native classes.

        """
        native = cast("p.Infra.RopeProject", super())
        found = native.get_folder(path)
        if not isinstance(found, Folder):
            message = "Rope folder lookup did not elect a native folder"
            raise TypeError(message)
        return found

    @override
    def get_python_files(self) -> list[File]:
        """Elect scoped Python inputs before constructing native file resources.

        Returns:
            Native files in the declared source scope or closed SDK inventory.

        Raises:
            TypeError: A selected Python resource is not a native file.

        """
        project = cast("p.Infra.RopeProject", self)
        resources: Sequence[p.Infra.RopeResource]
        root = Path(self.root.real_path)
        paths = {
            path
            for folder in self._custom_source_folders
            if isinstance(folder, Folder)
            for path in FlextInfraUtilitiesProjectDiscovery.discover_python_files(
                Path(folder.real_path),
                workspace_excluded_top_dirs=frozenset(),
                source_project=project,
            )
            if path.suffix == c.Infra.EXT_PYTHON
        }
        resources = tuple(
            project.get_resource(path.relative_to(root).as_posix())
            for path in sorted(paths)
        )
        files: list[File] = []
        for resource in resources:
            if not isinstance(resource, File):
                message = "Rope Python inventory did not elect a native file"
                raise TypeError(message)
            files.append(resource)
        return files

    @staticmethod
    @overload
    def _native_folder(
        folder: Folder | p.Infra.RopeRoot | p.Infra.RopeResource,
    ) -> Folder: ...

    @staticmethod
    @overload
    def _native_folder(folder: None) -> None: ...

    @staticmethod
    def _native_folder(
        folder: Folder | p.Infra.RopeRoot | p.Infra.RopeResource | None,
    ) -> Folder | None:
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

        Module lookups made during the pass are answered once each, since the
        layout they search cannot change while it is frozen.

        Yields:
            This project, its folder layout computed once for the pass.

        """
        source_folders = self.get_source_folders()
        python_path_folders = self.get_python_path_folders()
        self._frozen_folders = (source_folders, python_path_folders)
        self._frozen_modules = {}
        try:
            yield self
        finally:
            self._frozen_folders = None
            self._frozen_modules = None

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
