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
from pathlib import Path
from types import MappingProxyType
from typing import Self, override

from rope.base.exceptions import ResourceNotFoundError
from rope.base.project import NoProject, Project
from rope.base.resourceobserver import ChangeIndicator
from rope.base.resources import File, Folder

from flext_infra import c, p, t


class FlextInfraRopeProject(Project):
    """Rope project with the upstream self-warning initializer repaired."""

    # Import roots are declared by FLEXT; a read-only analysis pass also
    # freezes their resource identities and the external Python path.
    _frozen_folders: tuple[list[File | Folder], list[File | Folder]] | None = None
    _snapshot_files: SnapshotFiles | None = None
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
        resource: t.Infra.RopeResource,
        force_errors: bool = False,
    ) -> t.Infra.RopePyModule:
        """Declared Python module owned by one project resource.

        Returns:
            The resulting ``t.Infra.RopePyModule``.

        """
        return super().get_pymodule(resource, force_errors=force_errors)

    @override
    def find_module(
        self,
        modname: str,
        folder: p.Infra.RopeRoot | None = None,
    ) -> t.Infra.RopeResource | None:
        """Declared resolution of one module name to its resource.

        Returns:
            The resulting ``t.Infra.RopeResource | None``.

        """
        return super().find_module(modname, folder)

    class SnapshotFiles:
        """Closed, read-only input inventory for a semantic planning project.

        Deliberately exposes no filesystem mutation operations. Missing inputs
        are errors, never an invitation to consult a newer disk version.
        """

        def __init__(
            self,
            root: Path,
            sources: Mapping[Path, bytes],
            source_folders: t.SequenceOf[str],
        ) -> None:
            self._root = root.resolve()
            self._sources = MappingProxyType({
                path.resolve(): content for path, content in sources.items()
            })
            if any(not path.is_relative_to(self._root) for path in self._sources):
                msg = "Rope snapshot source is outside its project root"
                raise ValueError(msg)
            directories = {self._root}
            for path in (
                *self._sources,
                *(self._root / folder for folder in source_folders),
            ):
                resolved = path.resolve()
                if not resolved.is_relative_to(self._root):
                    msg = "Rope snapshot folder is outside its project root"
                    raise ValueError(msg)
                directories.update(
                    parent
                    for parent in (resolved, *resolved.parents)
                    if parent.is_relative_to(self._root) and parent not in self._sources
                )
            self._directories = frozenset(directories)

        @staticmethod
        def realpath(path: str) -> str:
            """Return the canonical identity Rope uses for snapshot paths."""
            return str(Path(path).expanduser().resolve())

        def exists(self, path: str) -> bool:
            """Report only files and folders captured by this snapshot."""
            resolved = Path(path).resolve()
            return resolved in self._sources or resolved in self._directories

        def isfile(self, path: str) -> bool:
            """Recognize only captured source files."""
            return Path(path).resolve() in self._sources

        def isdir(self, path: str) -> bool:
            """Recognize only declared or captured parent folders."""
            return Path(path).resolve() in self._directories

        def listdir(self, path: str) -> list[str]:
            """Enumerate captured direct children without consulting live disk."""
            directory = Path(path).resolve()
            if directory not in self._directories:
                msg = f"Rope snapshot folder is absent: {path}"
                raise FileNotFoundError(msg)
            return sorted({
                child.name
                for child in (*self._sources, *self._directories)
                if child.parent == directory
            })

        def read(self, path: str) -> bytes:
            """Read the exact captured source, including proposed edits.

            Returns:
                The resulting ``bytes``.

            """
            return self._sources[Path(self.realpath(path))]

        def contains_file(self, path: str) -> bool:
            """Recognize a declared snapshot file, including absent destinations."""
            return Path(self.realpath(path)) in self._sources

        def contains_directory(self, path: str) -> bool:
            """Recognize directories implied by the closed source inventory."""
            return Path(self.realpath(path)) in self._directories

        isfile = contains_file
        isdir = contains_directory

        def exists(self, path: str) -> bool:
            """Recognize only files and directories belonging to this snapshot.

            Returns:
                Whether the captured resource exists.

            """
            return self.contains_file(path) or self.contains_directory(path)

        def listdir(self, path: str) -> list[str]:
            """List the captured children of one declared snapshot directory.

            Returns:
                Direct child names in deterministic order.

            Raises:
                ResourceNotFoundError: If the directory is outside the snapshot.

            """
            if not self.contains_directory(path):
                msg = f"Resource <{path}> is absent from the closed snapshot"
                raise ResourceNotFoundError(msg)
            return [child.name for child in self.children(path)]

        def children(self, path: str) -> tuple[Path, ...]:
            """Read direct children from the same closed inventory."""
            return self._children.get(Path(self.realpath(path)), ())

    class SnapshotChangeIndicator(ChangeIndicator):
        """Observe captured content and directory membership by native equality."""

        def __init__(self, files: FlextInfraRopeProject.SnapshotFiles) -> None:
            self._files = files

        @override
        def get_indicator(self, resource: File | Folder) -> bytes | tuple[Path, ...]:
            """Return actual snapshot state instead of live filesystem metadata."""
            path = resource.real_path
            if self._files.contains_file(path):
                return self._files.read(path)
            if self._files.contains_directory(path):
                return self._files.children(path)
            msg = f"Resource <{resource.path}> is absent from the closed snapshot"
            raise ResourceNotFoundError(
                msg,
            )

    class SnapshotFile(File):
        """Native Rope file whose existence is the authenticated source inventory."""

        def __init__(
            self,
            project: Project | NoProject,
            path: str,
            files: FlextInfraRopeProject.SnapshotFiles,
        ) -> None:
            super().__init__(project, path)
            self._files = files

        @override
        def exists(self) -> bool:
            return self._files.contains_file(self.real_path)

    class SnapshotFolder(Folder):
        """Native Rope folder backed by captured and declared directory identities."""

        def __init__(
            self,
            project: Project | NoProject,
            path: str,
            files: FlextInfraRopeProject.SnapshotFiles,
        ) -> None:
            super().__init__(project, path)
            self._files = files

        @override
        def exists(self) -> bool:
            return self._files.contains_directory(self.real_path)

        @override
        def get_children(self) -> list[File | Folder]:
            return [
                child
                for path in self._files.children(self.real_path)
                if not self.project.is_ignored(
                    child := self.get_child(path.name),
                )
            ]

    class SnapshotExternalProject(NoProject):
        """Native external resource identities backed by the same closed inputs."""

        def __init__(self, files: FlextInfraRopeProject.SnapshotFiles) -> None:
            super().__init__(fscommands=files)
            self._files = files

        @override
        def get_resource(self, resource_name: str) -> File | Folder:
            path = self._get_resource_path(resource_name)
            if self._files.contains_file(path):
                return self.get_file(path)
            if self._files.contains_directory(path):
                return self.get_folder(path)
            msg = f"Resource <{resource_name}> is absent from the closed snapshot"
            raise ResourceNotFoundError(
                msg,
            )

        @override
        def get_file(self, path: str) -> File:
            return FlextInfraRopeProject.SnapshotFile(
                self,
                Path(path).resolve().as_posix(),
                self._files,
            )

        @override
        def get_folder(self, path: str) -> Folder:
            return FlextInfraRopeProject.SnapshotFolder(
                self,
                Path(path).resolve().as_posix(),
                self._files,
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
        external = cls.SnapshotExternalProject(files)
        project = cls(
            root,
            fscommands=cls.SnapshotFiles(Path(root), sources, source_folders),
            ropefolder=None,
            save_objectdb=False,
            save_history=False,
            ignored_resources=list(ignored_resources),
            source_folders=source_folders,
        )
        project._snapshot_files = files
        project._snapshot_python_path_folders = [
            external.get_folder(path) for path in python_path_folders
        ]
        project._custom_source_folders = [
            project.get_resource(path) for path in source_folders
        ]
        return project

    @override
    def get_resource(self, resource_name: str) -> File | Folder:
        """Expose authenticated virtual resources without materializing files."""
        if self._snapshot_files is not None:
            path = self._get_resource_path(resource_name)
            if self._snapshot_files.contains_file(path):
                return self.get_file(resource_name)
            if self._snapshot_files.contains_directory(path):
                return self.get_folder(resource_name)
            msg = f"Resource <{resource_name}> is absent from the closed snapshot"
            raise ResourceNotFoundError(
                msg,
            )
        return super().get_resource(resource_name)

    @override
    def get_file(self, path: str) -> File:
        """Keep file identities and existence consistent across native SDK lookups."""
        if self._snapshot_files is not None:
            return self.SnapshotFile(self, path, self._snapshot_files)
        return super().get_file(path)

    @override
    def get_folder(self, path: str) -> Folder:
        """Keep folder identities and children consistent with the closed inventory."""
        if self._snapshot_files is not None:
            return self.SnapshotFolder(self, path, self._snapshot_files)
        return super().get_folder(path)

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
            self.pycore.observer.timekeeper = self.SnapshotChangeIndicator(
                self.fscommands
            )

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
