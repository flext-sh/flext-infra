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
from errno import ENOENT
from os.path import normpath, realpath
from pathlib import Path
from types import MappingProxyType
from typing import Literal, Self, override

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
        return super().get_pymodule(resource, force_errors=force_errors)

    @override
    def get_module(
        self,
        name: str,
        folder: Folder | p.Infra.RopeRoot | None = None,
    ) -> t.Infra.RopeNativeSemanticModule:
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
    def get_relative_module(
        self,
        name: str,
        folder: Folder | p.Infra.RopeRoot,
        level: int,
    ) -> t.Infra.RopeNativeParsedModule:
        """Resolve a relative import from its native declaring resource.

        Returns:
            The original native package or source module.

        Raises:
            TypeError: The folder or module violates the native SDK boundary.

        """
        if not isinstance(folder, Folder):
            message = "Rope module lookup requires a native folder"
            raise TypeError(message)
        module = super().get_relative_module(name, folder, level)
        if not isinstance(module, PyModule | PyPackage):
            message = "Rope lookup did not return a native parsed module"
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
        return self._elect_module(
            self,
            modname,
            (
                *self.get_source_folders(),
                *self.get_python_path_folders(),
                *((folder,) if folder is not None else ()),
            ),
        )

    @staticmethod
    def _elect_module(
        finder: p.Infra.RopeModuleFinder,
        modname: str,
        roots: t.SequenceOf[File | Folder],
    ) -> File | Folder | None:
        """Elect a regular package or module before a namespace portion.

        Returns:
            The native module resource, or no matching module.

        Raises:
            TypeError: The SDK elected a resource that is neither file nor folder.

        """
        namespace: Folder | None = None
        for root in roots:
            if not isinstance(root, Folder):
                continue
            resource = finder.find_relative_module(modname, root, 1)
            if resource is None:
                continue
            if isinstance(resource, File):
                return resource
            if not isinstance(resource, Folder):
                message = "Rope module lookup elected a non-native resource"
                raise TypeError(message)
            if resource.has_child(c.Infra.INIT_PY):
                return resource
            module = f"{resource.name}{c.Infra.EXT_PYTHON}"
            if resource.parent.has_child(module):
                sibling = resource.parent.get_child(module)
                if isinstance(sibling, File):
                    return sibling
            if namespace is None:
                namespace = resource
        return namespace

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
            children: t.MutableMappingKV[Path, set[Path]] = {
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

        stat = staticmethod(FileSystemCommands.stat)

        @staticmethod
        def realpath(path: str) -> str:
            """Return the physical identity Rope's native filesystem commands use.

            Returns:
                The user-expanded, symlink-resolved absolute path.

            """
            return realpath(Path(path).expanduser())

        def __init__(
            self,
            root: Path,
            source_states: tuple[m.Cli.AtomicFileState, ...],
            sources: t.MappingKV[Path, str],
            declared_files: tuple[m.Infra.CodegenFilePlan, ...],
        ) -> None:
            self._root = root
            self._originals: t.MutableMappingKV[Path, m.Cli.AtomicFileState] = {}
            self._consumed: t.MutableMappingKV[Path, m.Cli.AtomicFileState] = {}
            self._inventories: t.MutableMappingKV[
                Path, m.Cli.AtomicDirectoryInventory
            ] = {}
            self._topology: t.MutableMappingKV[
                Path, m.Cli.AtomicDirectoryChainPlan
            ] = {}
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
                Whether the overlay or native filesystem contains the path.

            """
            return self._query(path, "exists")

        def isfile(self, path: str) -> bool:
            """Recognize planned source files and native physical files.

            Args:
                path: The path to check for being a file.

            Returns:
                Whether the path is a planned or native source file.

            """
            return self._query(path, "isfile")

        def isdir(self, path: str) -> bool:
            """Recognize declared virtual parents and native physical folders.

            Args:
                path: The path to check for being a directory.

            Returns:
                Whether the path is a declared virtual or native folder.

            """
            return self._query(path, "isdir")

        def listdir(self, path: str) -> list[str]:
            """Compose native direct children with declared planned children.

            Args:
                path: The path to list the children of.

            Returns:
                Sorted unique native and planned child names.

            Raises:
                FileNotFoundError: The directory is absent from both inventories.

            """
            directory = Path(path)
            inventory = self._inventory(directory)
            names: list[str] = (
                [] if inventory is None else [item.name for item in inventory.entries]
            )
            if inventory is not None:
                self._inventories[directory] = inventory.model_copy(
                    update={"membership_queried": True}
                )
            else:
                self._topology[directory] = self._topology[directory].model_copy(
                    update={"membership_queried": True}
                )
            if self._overlay.isdir(path):
                physical_names = frozenset(names)
                for child in self._overlay.children(path):
                    if child.name not in physical_names:
                        self._observe_overlay(str(child))
                    names.append(child.name)
            elif inventory is None:
                raise FileNotFoundError(
                    ENOENT, "Rope source directory was observed absent", path
                )
            return sorted(set(names))

        @staticmethod
        def _required_value[ValueT](result: p.Result[ValueT]) -> ValueT:
            """Preserve the original native cause at this read-only IO boundary.

            Returns:
                The successful native result value.

            Raises:
                ValueError: A failed result has no original exception.

            """
            if result.failure:
                cause = result.exception
                if cause is not None:
                    raise cause
                raise ValueError(result.error)
            return result.value

        def _directory_chain(self, directory: Path) -> m.Cli.AtomicDirectoryChainPlan:
            """Pin one declared directory's own physical ancestry and presence.

            Returns:
                The original physical ancestry witness.

            """
            if directory not in self._topology:
                self._topology[directory] = self._required_value(
                    u.Cli.atomic_plan_directory_chain(directory)
                )
            return self._topology[directory]

        def _inventory(self, directory: Path) -> m.Cli.AtomicDirectoryInventory | None:
            """Pin the physical parent used by this native election.

            Returns:
                The original parent inventory, or None for an absent parent.

            """
            if self._directory_chain(directory).directories:
                return None
            if directory not in self._inventories:
                self._inventories[directory] = self._required_value(
                    u.Cli.atomic_inventory_physical_directory(directory)
                )
            return self._inventories[directory]

        def _query(
            self, path: str, predicate: Literal["exists", "isfile", "isdir"]
        ) -> bool:
            """Retain both positive and negative native candidate observations.

            Returns:
                The predicate value authenticated by the native inventory.

            """
            candidate = Path(path)
            if candidate in {self._root, candidate.parent}:
                observed = (
                    not self._directory_chain(candidate).directories
                    and predicate != "isfile"
                )
            else:
                inventory = self._inventory(candidate.parent)
                if inventory is None:
                    witness = self._topology[candidate.parent]
                    self._topology[candidate.parent] = witness.model_copy(
                        update={
                            "queries": tuple(
                                sorted({*witness.queries, (candidate.name, predicate)})
                            )
                        }
                    )
                    observed = False
                else:
                    inventory = inventory.model_copy(
                        update={
                            "queries": tuple(
                                sorted({
                                    *inventory.queries,
                                    (candidate.name, predicate),
                                })
                            )
                        }
                    )
                    self._inventories[candidate.parent] = inventory
                    observed = u.Cli.atomic_directory_query_value(
                        inventory, candidate.name, predicate
                    )
            if observed:
                return True
            match predicate:
                case "exists":
                    proposed = self._overlay.exists(path)
                case "isfile":
                    proposed = self._overlay.isfile(path)
                case "isdir":
                    proposed = self._overlay.isdir(path)
            if proposed:
                self._observe_overlay(path)
            return proposed

        def _observe_overlay(self, path: str) -> None:
            """Bind the exact planned sources contributing a virtual resource."""
            if self._overlay.isfile(path):
                self.read(path)
                return
            for child in self._overlay.children(path):
                self._observe_overlay(str(child))

        def directories(self) -> tuple[m.Cli.AtomicDirectoryInventory, ...]:
            """Return the complete native inventories with consumed query selectors."""
            return tuple(self._inventories.values())

        def topology(self) -> tuple[m.Cli.AtomicDirectoryChainPlan, ...]:
            """Return original presence and ancestry witnesses for queried parents."""
            return tuple(self._topology.values())

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
                    state = self._required_value(
                        u.Cli.atomic_read_binary_file_state(
                            source,
                            required=source not in self._declared_paths,
                        )
                    )
                else:
                    self._required_value(
                        u.Cli.atomic_verify_binary_file_states((state,))
                    )
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
                Original physical receipts for the shared dependent group.

            """
            return tuple(self._consumed.values())

        def verify(self) -> None:
            """Reprove original inputs and absence witnesses without replacing them."""
            self._required_value(u.Cli.atomic_verify_binary_file_states(self.states()))
            self._required_value(
                u.Cli.atomic_verify_directory_queries(
                    self.directories(), self.topology()
                )
            )
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
                        plan.project,
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
        extension_modules: t.SequenceOf[str],
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
            extension_modules: Native modules elected by the original project.
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
            extension_modules=extension_modules,
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
        extension_modules: t.SequenceOf[str],
        python_path_folders: t.SequenceOf[str],
    ) -> Self:
        """Compose the native project and external resolver over one read owner.

        Returns:
            The project sharing authenticated local and external reads.

        """
        external = NoProject(fscommands=files)
        external.prefs.extension_modules = list(extension_modules)
        project = cls(
            root,
            fscommands=files,
            external_project=external,
            ropefolder=None,
            save_objectdb=False,
            save_history=False,
            ignored_resources=list(ignored_resources),
            extension_modules=list(extension_modules),
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
        live: p.Infra.RopeProject,
        source_states: tuple[m.Cli.AtomicFileState, ...],
        ignored_resources: t.SequenceOf[str] = (),
        *,
        source_folders: t.SequenceOf[str],
        sources: t.MappingKV[Path, str],
        declared_files: tuple[m.Infra.CodegenFilePlan, ...] = (),
    ) -> Self:
        """Use native module election with authenticated reads and planned sources.

        Returns:
            The project owning the original input epoch and proposed sources.

        """
        files = cls.AtomicReadFiles(
            Path(live.root.real_path),
            source_states,
            sources,
            declared_files,
        )
        return cls._from_files(
            live.root.real_path,
            files,
            source_folders=source_folders,
            ignored_resources=ignored_resources,
            extension_modules=sorted(live.get_pycore().extension_modules),
            python_path_folders=[
                folder.real_path
                for folder in live.get_python_path_folders()
                if folder.is_folder()
            ],
        )

    def consumed_source_states(self) -> tuple[m.Cli.AtomicFileState, ...]:
        """Return the actual-read closure, including native external providers.

        Returns:
            Original physical states consumed by the native graph.

        Raises:
            TypeError: The project does not own authenticated live reads.

        """
        if not isinstance(self.fscommands, self.AtomicReadFiles):
            msg = "Rope project does not own authenticated live reads"
            raise TypeError(msg)
        return self.fscommands.states()

    def consumed_source_directories(self) -> tuple[m.Cli.AtomicDirectoryInventory, ...]:
        """Return the native query receipts for this planning epoch.

        Returns:
            Original directory inventories consumed by native queries.

        Raises:
            TypeError: The project does not own authenticated live reads.

        """
        if not isinstance(self.fscommands, self.AtomicReadFiles):
            msg = "Rope project does not own authenticated live reads"
            raise TypeError(msg)
        return self.fscommands.directories()

    def consumed_source_topology(self) -> tuple[m.Cli.AtomicDirectoryChainPlan, ...]:
        """Return physical ancestry witnesses for consumed source queries.

        Returns:
            Original physical ancestry witnesses for queried parents.

        Raises:
            TypeError: The project does not own authenticated live reads.

        """
        if not isinstance(self.fscommands, self.AtomicReadFiles):
            msg = "Rope project does not own authenticated live reads"
            raise TypeError(msg)
        return self.fscommands.topology()

    def verify_source_states(self) -> None:
        """Verify the original input epoch after semantic planning.

        Raises:
            TypeError: The project does not own authenticated live reads.

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
