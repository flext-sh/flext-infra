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

from flext_cli import u
from rope.base.builtins import BuiltinModule
from rope.base.exceptions import ResourceNotFoundError
from rope.base.fscommands import FileSystemCommands
from rope.base.project import NoProject, Project
from rope.base.pyobjectsdef import PyModule, PyPackage
from rope.base.resourceobserver import ChangeIndicator
from rope.base.resources import File, Folder, Resource

from flext_infra import c, m, p, t
from flext_infra._utilities.rope_runtime_module_queries import (
    FlextInfraUtilitiesRopeRuntimeModuleQueries,
)


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
        """Resolve native resources without shadowing packages by namespaces.

        Rope's folder query accepts namespace portions before regular packages.
        Keep its resource and snapshot machinery, but elect a regular package
        or module before an otherwise matching namespace portion, as Python does.

        Returns:
            The native module resource, or no matching module.

        Raises:
            TypeError: The supplied folder is not a native Rope folder.

        """
        if folder is not None and not isinstance(folder, Folder):
            message = "Rope module lookup requires a native folder"
            raise TypeError(message)
        namespace: Folder | None = None
        roots = (
            *self.get_source_folders(),
            *self.get_python_path_folders(),
            *((folder,) if folder is not None else ()),
        )
        for root in roots:
            resource = super().find_relative_module(modname, root, 1)
            if resource is None:
                continue
            if isinstance(resource, File) or resource.has_child(c.Infra.INIT_PY):
                return resource
            module = f"{resource.name}{c.Infra.EXT_PYTHON}"
            if resource.parent.has_child(module):
                sibling = resource.parent.get_child(module)
                if isinstance(sibling, File):
                    return sibling
            if namespace is None:
                namespace = resource
        return namespace

    @override
    def validate(self, folder: Folder | p.Infra.RopeRoot | None = None) -> None:
        """Validate the selected native folder, or the complete project root.

        Raises:
            TypeError: The supplied folder is not a native Rope folder.

        """
        if folder is not None and not isinstance(folder, Folder):
            message = "Rope validation requires a native folder"
            raise TypeError(message)
        super().validate(self.root if folder is None else folder)

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

    class AtomicReadFiles:
        """Authenticate only sources actually read by the native semantic graph."""

        realpath = staticmethod(FileSystemCommands.realpath)
        stat = staticmethod(FileSystemCommands.stat)

        def __init__(
            self,
            root: Path,
            source_states: tuple[m.Cli.AtomicFileState, ...],
            sources: t.MappingKV[Path, str],
            declared_files: tuple[m.Infra.CodegenFilePlan, ...],
        ) -> None:
            self._root = root
            self._originals: dict[Path, m.Cli.AtomicFileState] = {}
            self._consumed: dict[Path, m.Cli.AtomicFileState] = {}
            for state in source_states:
                path = Path(state.path)
                previous = self._originals.get(path)
                if previous is not None and previous != state:
                    msg = f"Rope source has conflicting original states: {path}"
                    raise ValueError(msg)
                self._originals[path] = state
            self._declared = tuple(
                plan
                for plan in declared_files
                if isinstance(plan.before, m.Cli.AtomicDirectoryChainPlan)
                or plan.before.content is None
            )
            self._declared_paths = frozenset(plan.path for plan in self._declared)
            self._sources = MappingProxyType({
                path: source.encode(c.DEFAULT_ENCODING)
                for path, source in sources.items()
            })
            for path in self._sources:
                original = self._originals.get(path)
                if path not in self._declared_paths and (
                    original is None or original.content is None
                ):
                    msg = f"Rope proposed source lacks its original input: {path}"
                    raise ValueError(msg)
            self._overlay = FlextInfraRopeProject.SnapshotFiles(self._sources, ())

        def exists(self, path: str) -> bool:
            """Retain native election, including explicitly planned resources.

            Args:
                path: The path to check for existence.

            Returns:
                True if the path exists either in the overlay or the native file system; False otherwise.

            """
            return self._overlay.exists(path) or FileSystemCommands.exists(path)

        def isfile(self, path: str) -> bool:
            """Recognize planned source files and native physical files.

            Args:
                path: The path to check for being a file.

            Returns:
                True if the path is a planned source file or a native physical file; False otherwise.

            """
            return self._overlay.isfile(path) or FileSystemCommands.isfile(path)

        def isdir(self, path: str) -> bool:
            """Recognize declared virtual parents and native physical folders.

            Args:
                path: The path to check for being a directory.

            Returns:
                True if the path is a declared virtual parent or a native physical folder; False otherwise.

            """
            return self._overlay.isdir(path) or FileSystemCommands.isdir(path)

        def listdir(self, path: str) -> list[str]:
            """Compose native direct children with declared planned children.

            Args:
                path: The path to list the children of.

            Returns:
                A sorted list of unique child names from both the native file system and the declared planned children.

            """
            names = (
                FileSystemCommands.listdir(path)
                if FileSystemCommands.isdir(path)
                else []
            )
            if self._overlay.isdir(path):
                names.extend(self._overlay.listdir(path))
            elif not FileSystemCommands.isdir(path):
                return FileSystemCommands.listdir(path)
            return sorted(set(names))

        def children(self, path: str) -> tuple[Path, ...]:
            """Return native direct membership for the change observer."""
            return tuple(Path(path) / name for name in self.listdir(path))

        def read(self, path: str) -> bytes:
            """Return the same authenticated bytes recorded as consumed input.

            Args:
                path: The path to read the bytes from.

            Returns:
                The authenticated bytes for the given path.

            Raises:
                FileNotFoundError: If the required source is absent.

            """
            source = Path(path)
            state = self._consumed.get(source)
            if state is None:
                state = self._originals.get(source)
                if state is None:
                    state = u.Cli.atomic_read_binary_file_state(
                        source,
                        required=source not in self._declared_paths,
                    ).unwrap()
                else:
                    u.Cli.atomic_verify_binary_file_states((state,)).unwrap()
                self._verify_declarations(source)
                self._consumed[source] = state
            proposed = self._sources.get(source)
            if proposed is not None:
                return proposed
            if state.content is None:
                msg = f"Rope required source is absent: {source}"
                raise FileNotFoundError(msg)
            return state.content

        def states(self) -> tuple[m.Cli.AtomicFileState, ...]:
            """Expose original physical receipts for the shared dependent group.

            Returns:
                A tuple of atomic file states representing the original physical receipts for the shared dependent group.

            """
            return tuple(self._consumed.values())

        def verify(self) -> None:
            """Reprove original inputs and absence witnesses without replacing them."""
            u.Cli.atomic_verify_binary_file_states(self.states()).unwrap()
            for path in self._consumed:
                self._verify_declarations(path)

        def _verify_declarations(self, path: Path) -> None:
            """Use the existing owner for every consumed virtual birth witness.

            Args:
                path: The path to the consumed virtual birth witness to verify.

            Raises:
                ValueError: If the proposed source disagrees with its declaration.

            """
            for plan in self._declared:
                if plan.path != path:
                    continue
                _, content = (
                    FlextInfraUtilitiesRopeRuntimeModuleQueries.snapshot_destination(
                        self._root,
                        plan,
                    )
                )
                if self._sources.get(path) != content:
                    msg = f"Rope proposed source disagrees with its declaration: {path}"
                    raise ValueError(msg)

    class SnapshotChangeIndicator(ChangeIndicator):
        """Observe captured content and directory membership by native equality."""

        def __init__(
            self,
            files: (
                FlextInfraRopeProject.SnapshotFiles
                | FlextInfraRopeProject.AtomicReadFiles
            ),
        ) -> None:
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
            A native project of the requested snapshot owner.

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
        return cls._from_files(
            root,
            files,
            source_folders,
            ignored_resources=ignored_resources,
            python_path_folders=python_path_folders,
        )

    @classmethod
    def _from_files(
        cls,
        root: str,
        files: (
            FlextInfraRopeProject.SnapshotFiles | FlextInfraRopeProject.AtomicReadFiles
        ),
        source_folders: t.SequenceOf[str],
        *,
        ignored_resources: t.SequenceOf[str],
        python_path_folders: t.SequenceOf[str],
    ) -> Self:
        """Compose the native project and external resolver over one read owner.

        Returns:
            The resulting ``Self``.

        """
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

    @classmethod
    def from_atomic_reads(
        cls,
        root: str,
        source_states: tuple[m.Cli.AtomicFileState, ...],
        source_folders: t.SequenceOf[str],
        ignored_resources: t.SequenceOf[str] = (),
        *,
        sources: t.MappingKV[Path, str],
        python_path_folders: t.SequenceOf[str] = (),
        declared_files: tuple[m.Infra.CodegenFilePlan, ...] = (),
    ) -> Self:
        """Use native module election with authenticated reads and planned sources.

        Returns:
            The resulting ``Self``.

        """
        files = cls.AtomicReadFiles(
            Path(root),
            source_states,
            sources,
            declared_files,
        )
        return cls._from_files(
            root,
            files,
            source_folders=source_folders,
            ignored_resources=ignored_resources,
            python_path_folders=python_path_folders,
        )

    def consumed_source_states(self) -> tuple[m.Cli.AtomicFileState, ...]:
        """Return the actual-read closure, including native external providers.

        Raises:
            TypeError: If Rope project does not own authenticated live reads.

        """
        if not isinstance(self.fscommands, self.AtomicReadFiles):
            msg = "Rope project does not own authenticated live reads"
            raise TypeError(msg)
        return self.fscommands.states()

    def verify_source_states(self) -> None:
        """Verify the original input epoch after semantic planning.

        Raises:
            TypeError: If Rope project does not own authenticated live reads.

        """
        if not isinstance(self.fscommands, self.AtomicReadFiles):
            msg = "Rope project does not own authenticated live reads"
            raise TypeError(msg)
        self.fscommands.verify()

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
        if isinstance(self.fscommands, self.SnapshotFiles | self.AtomicReadFiles):
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
