"""Warning-free Rope project boundary.

Rope 1.14.0 and its current upstream branch decorate
``Project._init_source_folders`` as deprecated while still calling it
unconditionally from ``Project.__init__``.  A strict warnings-as-errors runtime
therefore cannot construct the documented public ``Project`` at all.  The
boundary below preserves Rope's initializer semantics without filtering the
warning or weakening the process warning policy.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Generator, Mapping
from contextlib import contextmanager
from os.path import normpath
from pathlib import Path
from types import MappingProxyType
from typing import Self, override

from rope.base.builtins import BuiltinModule
from rope.base.exceptions import ResourceNotFoundError
from rope.base.project import NoProject, Project
from rope.base.pyobjectsdef import PyModule, PyPackage
from rope.base.resourceobserver import ChangeIndicator
from rope.base.resources import File, Folder, Resource

from flext_infra import c, p, t


class FlextInfraRopeProject(Project):
    """Rope project with the upstream self-warning initializer repaired."""

    # Import roots are declared by FLEXT; a read-only analysis pass also
    # freezes their resource identities and the external Python path.
    _frozen_folders: tuple[list[File | Folder], list[File | Folder]] | None = None
    _snapshot_python_path_folders: list[File | Folder] | None = None

    @property
    @override
    def address(self) -> str:
        """Declared project root address.

        Returns:
            The resulting ``str``.

        """
        return super().address

    @property
    @override
    def root(self) -> p.Infra.RopeRoot:
        """Declared project root folder.

        Returns:
            The resulting ``p.Infra.RopeRoot``.

        """
        return super().root

    @override
    def get_pymodule(
        self,
        resource: Resource | p.Infra.RopeResource,
        force_errors: bool = False,
    ) -> PyModule | PyPackage:
        """Resolve a native resource while preserving the SDK return classes.

        Returns:
            The original native module or package.

        Raises:
            TypeError: The caller did not supply a native resource.

        """
        if not isinstance(resource, Resource):
            message = "Rope module lookup requires a native resource"
            raise TypeError(message)
        return super().get_pymodule(resource, force_errors=force_errors)

    @override
    def get_module(
        self,
        name: str,
        folder: Folder | p.Infra.RopeRoot | None = None,
    ) -> BuiltinModule | PyModule | PyPackage:
        """Resolve the native semantic module elected by the SDK.

        Returns:
            The original native builtin, package, or source module.

        Raises:
            TypeError: The folder or module violates the native SDK boundary.

        """
        if folder is not None and not isinstance(folder, Folder):
            message = "Rope module lookup requires a native folder"
            raise TypeError(message)
        module = super().get_module(name, folder)
        if not isinstance(module, BuiltinModule | PyModule | PyPackage):
            message = "Rope lookup did not return a native semantic module"
            raise TypeError(message)
        return module

    @override
    def find_module(
        self,
        modname: str,
        folder: p.Infra.RopeRoot | Folder | None = None,
    ) -> File | Folder | None:
        """Resolve through the SDK with an authenticated native folder.

        Returns:
            The native module resource, or no matching module.

        Raises:
            TypeError: The supplied folder is not a native Rope folder.

        """
        if folder is not None and not isinstance(folder, Folder):
            message = "Rope module lookup requires a native folder"
            raise TypeError(message)
        return super().find_module(modname, folder)

    class SnapshotFiles:
        """Closed, read-only input inventory for a semantic planning project.

        Deliberately exposes no filesystem mutation operations. Missing inputs
        are errors, never an invitation to consult a newer disk version.
        """

        def __init__(
            self,
            sources: Mapping[Path, bytes],
            directories: t.SequenceOf[Path],
        ) -> None:
            self._sources = MappingProxyType({
                Path(self.realpath(str(path))): content
                for path, content in sources.items()
            })
            self._directories = frozenset(
                parent
                for path in (
                    *(path.parent for path in self._sources),
                    *(Path(self.realpath(str(path))) for path in directories),
                )
                for parent in (path, *path.parents)
            )
            children: dict[Path, set[Path]] = {
                directory: set() for directory in self._directories
            }
            for path in (*self._sources, *self._directories):
                if path.parent in children and path != path.parent:
                    children[path.parent].add(path)
            self._children = MappingProxyType({
                directory: tuple(sorted(paths)) for directory, paths in children.items()
            })

        @staticmethod
        def realpath(path: str) -> str:
            """Return the lexical absolute identity of a captured path.

            Returns:
                The normalized path without consulting the live filesystem.

            """
            return normpath(str(Path(path).absolute()))

        def exists(self, path: str) -> bool:
            """Report only files and folders captured by this snapshot.

            Args:
                path: The path to check for existence within the snapshot.

            Returns:
                Whether the specified path exists within the snapshot.

            """
            resolved = Path(self.realpath(path))
            return resolved in self._sources or resolved in self._directories

        def isfile(self, path: str) -> bool:
            """Recognize only captured source files.

            Args:
                path: The path to check for being a captured source file.

            Returns:
                Whether the specified path is a captured source file.

            """
            return Path(self.realpath(path)) in self._sources

        def isdir(self, path: str) -> bool:
            """Recognize only declared or captured parent folders.

            Args:
                path: The path to check for being a declared or captured parent folder.

            Returns:
                Whether the specified path is a declared or captured parent folder.

            """
            return Path(self.realpath(path)) in self._directories

        def listdir(self, path: str) -> list[str]:
            """Enumerate captured direct children without consulting live disk.

            Args:
                path: The path to enumerate direct children for.

            Returns:
                A sorted list of direct child names captured in the snapshot.

            Raises:
                FileNotFoundError: If the specified directory is not captured in the
                  snapshot.

            """
            directory = Path(self.realpath(path))
            if directory not in self._directories:
                msg = f"Rope snapshot folder is absent: {path}"
                raise FileNotFoundError(msg)
            return [child.name for child in self._children[directory]]

        def read(self, path: str) -> bytes:
            """Read the exact captured source, including proposed edits.

            Args:
                path: The path to the captured source file to read.

            Returns:
                The resulting ``bytes``.

            """
            return self._sources[Path(self.realpath(path))]

        def children(self, path: str) -> tuple[Path, ...]:
            """Read direct children from the same closed inventory.

            Args:
                path: The path to enumerate direct children for.

            Returns:
                A tuple of direct child paths captured in the snapshot.

            """
            return self._children[Path(self.realpath(path))]

    class SnapshotChangeIndicator(ChangeIndicator):
        """Observe captured content and directory membership by native equality."""

        def __init__(self, files: FlextInfraRopeProject.SnapshotFiles) -> None:
            self._files = files

        @override
        def get_indicator(
            self,
            resource: File | Folder,
        ) -> t.Pair[bool, bytes | tuple[Path, ...]]:
            """Return actual snapshot state instead of live filesystem metadata.

            Args:
                resource: The file or folder resource to query.

            Returns:
                The file-kind flag and captured bytes or directory membership.

            Raises:
                ResourceNotFoundError: If the resource is not present in the snapshot.

            """
            path = resource.real_path
            if self._files.isfile(path):
                return True, self._files.read(path)
            if self._files.isdir(path):
                return False, self._files.children(path)
            msg = f"Resource <{resource.path}> is absent from the closed snapshot"
            raise ResourceNotFoundError(
                msg,
            )

    @classmethod
    def from_snapshot(
        cls,
        root: str,
        sources: Mapping[Path, bytes],
        source_folders: t.SequenceOf[str],
        ignored_resources: t.SequenceOf[str] = (),
        *,
        python_path_folders: t.SequenceOf[str] = (),
    ) -> Self:
        """Construct a fresh Rope identity graph without persistent state.

        Args:
            root: The snapshot root directory.
            sources: The closed source inventory Rope may read.
            source_folders: The declared importable source folders.
            ignored_resources: The scan-ignore SSOT patterns; without them
                Rope enumerates real disk files the closed inventory does not
                hold (tool hooks under ignored resources) and every such
                read dies in the snapshot mapping.
            python_path_folders: Authenticated native import roots whose resources
                must read the same captured inventory as project modules.

        Returns:
            The resulting ``Self``.

        Raises:
            ValueError: If Rope snapshot root must already exist.

        """
        if not Path(root).is_dir():
            msg = f"Rope snapshot root must already exist: {root}"
            raise ValueError(msg)
        files = cls.SnapshotFiles(
            sources,
            (
                Path(root),
                *(Path(root) / path for path in source_folders),
                *(Path(path) for path in python_path_folders),
            ),
        )
        external = NoProject(fscommands=files)
        project = cls(
            root,
            fscommands=files,
            external_project=external,
            ropefolder=None,
            save_objectdb=False,
            save_history=False,
            ignored_resources=list(ignored_resources),
            source_folders=source_folders,
        )
        project._snapshot_python_path_folders = [
            external.get_folder(path) for path in python_path_folders
        ]
        project._custom_source_folders = [
            project.get_resource(path) for path in source_folders
        ]
        return project

    @contextmanager
    def frozen_layout(self) -> Generator[Self]:
        """Declared freeze of the source and Python path folders for one read-only pass.

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
                if (
                    isinstance(folder, Folder)
                    and folder.has_child(c.Infra.INIT_PY)
                    and not folder.get_child(c.Infra.INIT_PY).is_folder()
                    and folder.parent not in folders
                ):
                    folders.append(folder.parent)
            return folders
        return list(self._frozen_folders[0])

    @override
    def get_python_path_folders(self) -> list[File | Folder]:
        """Declared Python path folders, frozen during a read-only pass.

        Returns:
            The folders Rope's own contract returns.

        """
        if self._frozen_folders is None:
            if self._snapshot_python_path_folders is not None:
                return list(self._snapshot_python_path_folders)
            folders: list[File | Folder] = super().get_python_path_folders()
            return folders
        return list(self._frozen_folders[1])

    @override
    def _init_other_parts(self) -> None:
        """Install captured change observations before initializing resources."""
        super()._init_other_parts()
        if isinstance(self.fscommands, self.SnapshotFiles):
            core = self.get_pycore()
            core.observer.timekeeper = self.SnapshotChangeIndicator(self.fscommands)

    @override
    def _init_source_folders(self) -> None:
        """Initialize configured source roots without Rope's warning wrapper.

        Raises:
            ValueError: If rope preference 'source_folders' is None; expected a list of
                source folder paths.

        """
        source_folders = self.prefs.get("source_folders", [])
        if source_folders is None:
            msg = (
                "rope preference 'source_folders' is None; "
                "expected a list of source folder paths"
            )
            raise ValueError(msg)
        for path in source_folders:
            self._custom_source_folders.append(self.get_resource(path))


__all__: list[str] = ["FlextInfraRopeProject"]
