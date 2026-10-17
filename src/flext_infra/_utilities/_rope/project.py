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
from contextlib import AbstractContextManager, closing, contextmanager, nullcontext
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
    _source_election: p.Infra.RopeProjectElection | None = None

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
        module = super().get_module(name, self._native_folder(folder))
        if not isinstance(module, BuiltinModule | PyModule | PyPackage):
            message = "Rope lookup did not return a native semantic module"
            raise TypeError(message)
        return module

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
        return super().get_relative_module(name, self._native_folder(folder), level)

    @override
    def find_module(
        self,
        modname: str,
        folder: p.Infra.RopeRoot | Folder | None = None,
    ) -> File | Folder | None:
        """Admit the resource elected by Rope's native module finder.

        Returns:
            The native module resource, or no matching module.

        """
        return super().find_module(modname, self._native_folder(folder))

    @override
    def find_relative_module(
        self,
        modname: str,
        folder: Folder | p.Infra.RopeRoot | None,
        level: int,
    ) -> File | Folder | None:
        """Delegate relative resource election to its native SDK owner.

        Returns:
            The elected native resource, or no resource without relative context.

        """
        return super().find_relative_module(modname, self._native_folder(folder), level)

    @staticmethod
    def _native_folder(folder: Folder | p.Infra.RopeRoot | None) -> Folder | None:
        """Validate the native folder once at the SDK adapter boundary.

        Returns:
            The supplied native folder or absent relative context.

        Raises:
            TypeError: The supplied folder is not native.

        """
        if folder is not None and not isinstance(folder, Folder):
            message = "Rope module lookup requires a native folder"
            raise TypeError(message)
        return folder

    class SnapshotFiles:
        """Closed, read-only input inventory for a semantic planning project.

        Deliberately exposes no filesystem mutation operations. Missing
        repository inputs are errors, never an invitation to consult a newer
        disk version. The elected interpreter paths (stdlib and installed
        distributions) are ambient runtime, not repository state: they stay
        readable read-only so semantic analysis resolves their identities
        without importing them into the closed snapshot.
        """

        def __init__(
            self,
            sources: Mapping[Path, bytes],
            directories: t.SequenceOf[Path],
            *,
            ambient_roots: t.SequenceOf[Path] = (),
        ) -> None:
            self._ambient_roots = tuple(
                Path(self.realpath(str(root))) for root in ambient_roots
            )
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

        def _ambient_identity(self, path: str) -> Path | None:
            """Return the real path when it belongs to an ambient interpreter root.

            Returns:
                The normalized real path inside one ambient root, or ``None``
                for repository-scoped paths the closed inventory owns.

            """
            resolved = Path(self.realpath(path))
            if any(
                root == resolved or root in resolved.parents
                for root in self._ambient_roots
            ):
                return resolved
            return None

        def exists(self, path: str) -> bool:
            """Report captured resources and readable ambient interpreter paths.

            Args:
                path: The path to check for existence within the snapshot.

            Returns:
                Whether the specified path exists within the snapshot.

            """
            resolved = Path(self.realpath(path))
            if resolved in self._sources or resolved in self._directories:
                return True
            ambient = self._ambient_identity(path)
            return ambient is not None and ambient.exists()

        def isfile(self, path: str) -> bool:
            """Recognize captured source files and ambient interpreter files.

            Args:
                path: The path to check for being a file.

            Returns:
                Whether the specified path is a captured source file.

            """
            resolved = Path(self.realpath(path))
            if resolved in self._sources:
                return True
            ambient = self._ambient_identity(path)
            return ambient is not None and ambient.is_file()

        def isdir(self, path: str) -> bool:
            """Recognize captured folders and ambient interpreter folders.

            Args:
                path: The path to check for being a directory.

            Returns:
                Whether the specified path is a captured or ambient folder.

            """
            resolved = Path(self.realpath(path))
            if resolved in self._directories:
                return True
            ambient = self._ambient_identity(path)
            return ambient is not None and ambient.is_dir()

        def listdir(self, path: str) -> list[str]:
            """Enumerate captured children, then ambient interpreter children.

            Args:
                path: The path to enumerate direct children for.

            Returns:
                A sorted list of direct child names captured in the snapshot.

            Raises:
                FileNotFoundError: If the specified directory is neither
                  captured in the snapshot nor ambient interpreter state.

            """
            directory = Path(self.realpath(path))
            if directory in self._directories:
                return [child.name for child in self._children[directory]]
            ambient = self._ambient_identity(path)
            if ambient is not None and ambient.is_dir():
                return sorted(item.name for item in ambient.iterdir())
            msg = f"Rope snapshot folder is absent: {path}"
            raise FileNotFoundError(msg)

        def read(self, path: str) -> bytes:
            """Read the exact captured source, then ambient interpreter bytes.

            Args:
                path: The path to the captured source file to read.

            Returns:
                The resulting ``bytes``.

            Raises:
                FileNotFoundError: If the path is neither captured nor
                  ambient interpreter state.

            """
            source = Path(self.realpath(path))
            if source in self._sources:
                return self._sources[source]
            ambient = self._ambient_identity(path)
            if ambient is not None and ambient.is_file():
                return ambient.read_bytes()
            msg = f"Rope snapshot source is absent: {path}"
            raise FileNotFoundError(msg)

        def children(self, path: str) -> tuple[Path, ...]:
            """Read direct children from the same closed inventory.

            Args:
                path: The path to enumerate direct children for.

            Returns:
                A tuple of direct child paths captured in the snapshot.

            """
            return self._children[Path(self.realpath(path))]

    class SourceConsumption:
        """Accumulate original receipts for one native consumer, not a set delta."""

        def __init__(self) -> None:
            self._states: tuple[m.Cli.AtomicFileState, ...] = ()
            self._directories: tuple[m.Cli.AtomicDirectoryInventory, ...] = ()
            self._topology: tuple[m.Cli.AtomicDirectoryChainPlan, ...] = ()
            self._receipt: m.Infra.CodegenPhaseAnalysis | None = None

        def record(
            self,
            states: tuple[m.Cli.AtomicFileState, ...] = (),
            directories: tuple[m.Cli.AtomicDirectoryInventory, ...] = (),
            topology: tuple[m.Cli.AtomicDirectoryChainPlan, ...] = (),
        ) -> None:
            """Merge exact observations while retaining their original identities."""
            if self._receipt is not None:
                msg = "Rope source consumption is already sealed"
                raise ValueError(msg)
            self._states = m.Infra.CodemodBindingSnapshot(
                states=(*self._states, *states),
            ).states
            self._directories, self._topology = (
                u.Cli.atomic_merge_directory_query_receipts(
                    (*self._directories, *directories),
                    (*self._topology, *topology),
                )
            )

        def seal(self) -> m.Infra.CodegenPhaseAnalysis:
            """Freeze the receipt only after the consumer has left its scope."""
            self._receipt = m.Infra.CodegenPhaseAnalysis(
                phase=c.Infra.CodegenStagedFilePhase.LAZY_INIT,
                files=(),
                inputs=self._states,
                source_directories=self._directories,
                source_query_topology=self._topology,
            )
            return self._receipt

        def receipt(self) -> m.Infra.CodegenPhaseAnalysis:
            """Require a complete receipt; an active or failed scope is not evidence."""
            if self._receipt is None:
                msg = "Rope source consumption has no completed receipt"
                raise ValueError(msg)
            return self._receipt

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
            self.epoch_failure: BaseException | None = None
            self._structural_queries = 0
            self._capturing = 0
            self._scopes: list[FlextInfraRopeProject.SourceConsumption] = []
            self._receipts: list[m.Infra.CodegenPhaseAnalysis] = []
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
            self._effects = {plan.path: plan for plan in declared_files}
            self._retired = frozenset(
                plan.path for plan in declared_files if plan.desired_content is None
            )
            proposed = {
                path: source.encode(c.DEFAULT_ENCODING)
                for path, source in sources.items()
            }
            for plan in declared_files:
                if plan.desired_content is not None:
                    supplied = proposed.get(plan.path)
                    if supplied is not None and supplied != plan.desired_content:
                        msg = f"Rope proposed source disagrees with its declared effect: {plan.path}"
                        raise ValueError(msg)
                    proposed[plan.path] = plan.desired_content
            self._sources = MappingProxyType(proposed)
            if self._retired.intersection(self._sources):
                msg = "Rope retired source has competing proposed bytes"
                raise ValueError(msg)
            for path in self._sources:
                original = self._originals.get(path)
                if path not in self._declared_paths and (
                    original is None or original.content is None
                ):
                    msg = f"Rope proposed source lacks its original input: {path}"
                    raise ValueError(msg)
            self._overlay = FlextInfraRopeProject.SnapshotFiles(self._sources, ())

        @contextmanager
        def capture(self) -> Generator[None]:
            """Pin originals before planning without claiming they were consumed."""
            self._capturing += 1
            try:
                yield
            finally:
                self._capturing -= 1

        @contextmanager
        def selection(self) -> Generator[None]:
            """Elect paths without treating an overlay's unread payload as consumed."""
            self._structural_queries += 1
            try:
                yield
            finally:
                self._structural_queries -= 1

        @contextmanager
        def consumption(self) -> Generator[p.Infra.RopeSourceConsumption]:
            """Record every read/query, including repeats and nested consumers."""
            scope = FlextInfraRopeProject.SourceConsumption()
            self._scopes.append(scope)
            try:
                yield scope
                self._receipts.append(scope.seal())
            finally:
                self._scopes.remove(scope)

        def replay(self, receipt: m.Infra.CodegenPhaseAnalysis) -> None:
            """Replay only evidence minted by this authenticated original epoch."""
            if not any(issued is receipt for issued in self._receipts):
                msg = "Rope source receipt does not belong to this original epoch"
                raise ValueError(msg)
            if not self._scopes:
                msg = "Rope source replay requires an active consumer"
                raise ValueError(msg)
            self._record(
                receipt.inputs,
                receipt.source_directories,
                receipt.source_query_topology,
            )

        def _record(
            self,
            states: tuple[m.Cli.AtomicFileState, ...] = (),
            directories: tuple[m.Cli.AtomicDirectoryInventory, ...] = (),
            topology: tuple[m.Cli.AtomicDirectoryChainPlan, ...] = (),
        ) -> None:
            """Attribute the exact event to every enclosing consumer."""
            if self._capturing:
                return
            for scope in self._scopes:
                scope.record(states, directories, topology)

        def _consume_effect(self, path: Path) -> None:
            """Attribute a declared overlay effect's original proof to its consumer."""
            if self._capturing:
                return
            plan = self._effects.get(path)
            if plan is None:
                return
            states = (
                *plan.source_states,
                *(
                    (plan.before,)
                    if isinstance(plan.before, m.Cli.AtomicFileState)
                    else ()
                ),
            )
            for original in states:
                if self.source_state(original.path, required=False) != original:
                    msg = f"Rope overlay effect has conflicting original input: {original.path}"
                    raise ValueError(msg)
            chains = (
                *plan.source_query_topology,
                *(
                    (plan.before,)
                    if isinstance(plan.before, m.Cli.AtomicDirectoryChainPlan)
                    else ()
                ),
            )
            directories, topology = u.Cli.atomic_merge_directory_query_receipts(
                (*self.directories(), *plan.source_directories),
                (*self.topology(), *chains),
            )
            self._inventories.update((item.root.path, item) for item in directories)
            self._topology.update((item.target, item) for item in topology)
            self._record(directories=plan.source_directories, topology=chains)

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
                if not self._capturing:
                    self._inventories[directory] = inventory.model_copy(update={"membership_queried": True})
                self._record(
                    directories=(
                        inventory.model_copy(
                            update={"queries": (), "membership_queried": True},
                        ),
                    ),
                )
            else:
                if not self._capturing:
                    self._topology[directory] = self._topology[directory].model_copy(update={"membership_queried": True})
                self._record(
                    topology=(
                        self._topology[directory].model_copy(
                            update={"queries": (), "membership_queried": True},
                        ),
                    ),
                )
            if self._overlay.isdir(path):
                physical_names = frozenset(names)
                for child in self._overlay.children(path):
                    if (
                        child.name not in physical_names
                        and not (self._structural_queries or self._capturing)
                    ):
                        self._observe_overlay(str(child))
                    names.append(child.name)
            elif inventory is None:
                raise FileNotFoundError(
                    ENOENT, "Rope source directory was observed absent", path
                )
            for retired in self._retired:
                if retired.parent == directory and not (self._structural_queries or self._capturing):
                    self._consume_effect(retired)
            return sorted(
                name for name in set(names) if directory / name not in self._retired
            )

        @staticmethod
        def require_value[ValueT](result: p.Result[ValueT]) -> ValueT:
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
                self._topology[directory] = self.require_value(
                    u.Cli.atomic_plan_directory_chain(directory)
                )
            witness = self._topology[directory]
            self._record(
                topology=(
                    witness.model_copy(
                        update={"queries": (), "membership_queried": False},
                    ),
                ),
            )
            return witness

        def _inventory(self, directory: Path) -> m.Cli.AtomicDirectoryInventory | None:
            """Pin the physical parent used by this native election.

            Returns:
                The original parent inventory, or None for an absent parent.

            """
            if self._directory_chain(directory).directories:
                return None
            if directory not in self._inventories:
                self._inventories[directory] = self.require_value(
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
            elif not candidate.is_relative_to(self._root):
                # Ambient interpreter trees and foreign ancestry end the
                # repository's authenticated scope: their membership is a
                # plain native fact, never an atomic inventory input, so the
                # election walk can ascend past mount boundaries without
                # inventorying hosts' ancestor directories.
                observed = {
                    "exists": candidate.exists,
                    "isfile": candidate.is_file,
                    "isdir": candidate.is_dir,
                }[predicate]()
            else:
                if self._query(str(candidate.parent), "exists") and not self._query(
                    str(candidate.parent),
                    "isdir",
                ):
                    return False
                inventory = self._inventory(candidate.parent)
                if inventory is None:
                    witness = self._topology[candidate.parent]
                    if not self._capturing:
                        self._topology[candidate.parent] = witness.model_copy(update={
                            "queries": tuple(sorted({*witness.queries, (candidate.name, predicate)})),
                        })
                    self._record(
                        topology=(
                            witness.model_copy(
                                update={
                                    "queries": ((candidate.name, predicate),),
                                    "membership_queried": False,
                                }
                            ),
                        ),
                    )
                    observed = False
                else:
                    observed = u.Cli.atomic_directory_query_value(inventory, candidate.name, predicate)
                    inventory = inventory.model_copy(update={
                        "queries": tuple(sorted({*inventory.queries, (candidate.name, predicate)})),
                    })
                    if not self._capturing:
                        self._inventories[candidate.parent] = inventory
                    self._record(directories=(inventory.model_copy(update={
                        "queries": ((candidate.name, predicate),), "membership_queried": False,
                    }),))
            if not (self._structural_queries or self._capturing):
                self._consume_effect(candidate)
            if candidate in self._retired:
                return False
            if candidate in self._sources:
                if not observed and not (self._structural_queries or self._capturing):
                    self._observe_overlay(path)
                return predicate != "isdir"
            if self._overlay.isdir(path):
                if not observed and not (self._structural_queries or self._capturing):
                    self._observe_overlay(path)
                return predicate != "isfile"
            original = self._originals.get(candidate)
            if original is not None:
                expected = original.content is not None and predicate != "isdir"
                if expected != observed:
                    self.source_state(candidate, required=False)
                return expected
            return observed

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
            state = self.source_state(
                source,
                required=source not in self._declared_paths,
            )
            self._consume_effect(source)
            if source in self._retired:
                msg = f"Rope source is explicitly retired: {source}"
                raise FileNotFoundError(msg)
            proposed = self._sources.get(source)
            if proposed is not None:
                return proposed
            if state.content is None:
                msg = f"Rope required source is absent: {source}"
                raise FileNotFoundError(msg)
            return state.content

        def source_state(
            self, source: Path, *, required: bool = True
        ) -> m.Cli.AtomicFileState:
            """Read or replay the original state, including an explicit absence."""
            state = self._consumed.get(source)
            if state is None:
                state = self._originals.get(source)
                if state is None:
                    state = self.require_value(
                        u.Cli.atomic_read_binary_file_state(
                            source,
                            required=required,
                        )
                    )
                    self._originals = MappingProxyType({**self._originals, source: state})
                if not self._capturing:
                    self._verify_declarations(source, check_current=False)
                    self._consumed[source] = state
            self._record(states=(state,))
            if required and state.content is None:
                msg = f"Rope required source is absent: {source}"
                raise FileNotFoundError(msg)
            return state

        def states(self) -> tuple[m.Cli.AtomicFileState, ...]:
            """Expose original physical receipts for the shared dependent group.

            Returns:
                Original physical receipts for the shared dependent group.

            """
            return tuple(self._consumed.values())

        def verify(self) -> None:
            """Reprove original inputs and absence witnesses without replacing them."""
            self.require_value(u.Cli.atomic_verify_binary_file_states(self.states()))
            self.require_value(
                u.Cli.atomic_verify_directory_queries(
                    self.directories(), self.topology()
                )
            )
            for path in self._consumed:
                self._verify_declarations(path)

        def _verify_declarations(self, path: Path, *, check_current: bool = True) -> None:
            """Use the existing owner for every consumed virtual birth witness.

            Args:
                path: The path to the consumed virtual birth witness to verify.

            Raises:
                ValueError: If the proposed source disagrees with its declaration.

            """
            for plan in self._declared:
                if plan.path != path:
                    continue
                if self._sources.get(path) != plan.desired_content:
                    msg = f"Rope proposed source disagrees with its declaration: {path}"
                    raise ValueError(msg)
                if check_current:
                    FlextInfraUtilitiesRopeRuntimeModuleQueries.snapshot_destination(plan.project, plan)

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
        election: p.Infra.RopeProjectElection,
    ) -> Self:
        """Construct a fresh Rope identity graph without persistent state.

        The snapshot applies its typed election's scan-ignore policy, so ignored
        tool resources never enter the closed source inventory.

        Args:
            root: The snapshot root directory.
            sources: The closed source inventory Rope may read.
            election: The exact native import roots, extension modules and
                scan-ignore policy sharing the closed source inventory.

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
                *(Path(root) / path for path in election.source_folders),
                *(Path(path) for path in election.python_path_folders),
            ),
            ambient_roots=tuple(Path(path) for path in election.python_path_folders),
        )
        return cls._from_files(root, files, election)

    @classmethod
    def _from_files(
        cls,
        root: str,
        files: (
            FlextInfraRopeProject.SnapshotFiles | FlextInfraRopeProject.AtomicReadFiles
        ),
        election: p.Infra.RopeProjectElection,
    ) -> Self:
        """Compose the native project and external resolver over one read owner.

        Returns:
            The project sharing authenticated local and external reads.

        """
        external = NoProject(fscommands=files)
        external.prefs.extension_modules = list(election.extension_modules)
        project = cls(
            root,
            fscommands=files,
            external_project=external,
            ropefolder=None,
            save_objectdb=False,
            save_history=False,
            ignored_resources=list(election.ignored_resources),
            extension_modules=list(election.extension_modules),
            source_folders=list(election.source_folders),
        )
        project._snapshot_python_path_folders = [
            external.get_folder(path) for path in election.python_path_folders
        ]
        with (
            files.selection()
            if isinstance(files, cls.AtomicReadFiles)
            else nullcontext()
        ):
            project._custom_source_folders = [
                project.get_resource(path) for path in election.source_folders
            ]
        project._source_election = m.Infra.RopeProjectElection(
            source_folders=tuple(election.source_folders),
            ignored_resources=tuple(election.ignored_resources),
            extension_modules=tuple(election.extension_modules),
            python_path_folders=tuple(election.python_path_folders),
        )
        return project

    @classmethod
    def from_atomic_reads(
        cls,
        live: p.Infra.RopeProject,
        source_states: tuple[m.Cli.AtomicFileState, ...],
        *,
        election: p.Infra.RopeProjectElection,
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
        return cls._from_files(live.root.real_path, files, election)

    @contextmanager
    def source_consumer(self, *, consumer_root: Path | None = None) -> Generator[Self]:
        """Isolate native semantic caches while sharing the original read authority.

        Yields:
            A fresh native graph with the same originals, election and receipt issuer.

        Raises:
            TypeError: The project has no authenticated original read authority.

        """
        if (
            not isinstance(self.fscommands, self.AtomicReadFiles)
            or self._source_election is None
        ):
            msg = "Rope source consumer requires an authenticated original election"
            raise TypeError(msg)
        election = self._source_election
        if consumer_root is not None:
            root = Path(self.root.real_path)
            preferred = tuple(
                folder
                for folder in election.source_folders
                if (root / folder).is_relative_to(consumer_root)
            )
            if not preferred:
                msg = f"Rope consumer has no originally elected source folder: {consumer_root}"
                raise ValueError(msg)
            election = m.Infra.RopeProjectElection(
                source_folders=(
                    *preferred,
                    *(
                        folder
                        for folder in election.source_folders
                        if folder not in preferred
                    ),
                ),
                ignored_resources=election.ignored_resources,
                extension_modules=election.extension_modules,
                python_path_folders=election.python_path_folders,
            )
        with closing(
            type(self)._from_files(
                self.root.real_path,
                self.fscommands,
                election,
            ),
        ) as consumer:
            yield consumer

    @property
    def authenticated_sources(self) -> bool:
        """Whether all source operations share an authenticated original epoch."""
        return isinstance(self.fscommands, self.AtomicReadFiles)

    @property
    def source_epoch_failure(self) -> BaseException | None:
        """Expose only the original exception raised by the global epoch verifier."""
        return (
            self.fscommands.epoch_failure
            if isinstance(self.fscommands, self.AtomicReadFiles)
            else None
        )

    def source_consumption(
        self,
    ) -> AbstractContextManager[p.Infra.RopeSourceConsumption]:
        """Open an exact native consumption scope, rejecting unbound projects."""
        if not isinstance(self.fscommands, self.AtomicReadFiles):
            msg = "Rope project does not own authenticated live reads"
            raise TypeError(msg)
        return self.fscommands.consumption()

    def source_selection(self) -> AbstractContextManager[None]:
        """Scope native structural election; actual reads still record full proofs."""
        if not isinstance(self.fscommands, self.AtomicReadFiles):
            msg = "Rope project does not own authenticated live reads"
            raise TypeError(msg)
        return self.fscommands.selection()

    def source_capture(self) -> AbstractContextManager[None]:
        """Pin potential originals once without claiming prefetch was consumption."""
        if not isinstance(self.fscommands, self.AtomicReadFiles):
            msg = "Rope project does not own authenticated live reads"
            raise TypeError(msg)
        return self.fscommands.capture()

    def replay_source_consumption(self, receipt: m.Infra.CodegenPhaseAnalysis) -> None:
        """Attribute an authentic cached result's original dependencies."""
        if not isinstance(self.fscommands, self.AtomicReadFiles):
            msg = "Rope project does not own authenticated live reads"
            raise TypeError(msg)
        self.fscommands.replay(receipt)

    def source_state(
        self, path: Path, *, required: bool = True
    ) -> m.Cli.AtomicFileState:
        """Use the authenticated resource owner for direct source decisions."""
        if not isinstance(self.fscommands, self.AtomicReadFiles):
            msg = "Rope project does not own authenticated live reads"
            raise TypeError(msg)
        return self.fscommands.source_state(path, required=required)

    def source_query(
        self, path: Path, predicate: Literal["exists", "isfile", "isdir"]
    ) -> bool:
        """Elect a direct path through the original native query owner."""
        if not isinstance(self.fscommands, self.AtomicReadFiles):
            msg = "Rope project does not own authenticated live reads"
            raise TypeError(msg)
        return self.fscommands._query(str(path), predicate)

    def source_children(self, path: Path) -> tuple[Path, ...]:
        """Enumerate original native membership with its exact query receipt."""
        if not isinstance(self.fscommands, self.AtomicReadFiles):
            msg = "Rope project does not own authenticated live reads"
            raise TypeError(msg)
        return self.fscommands.children(str(path))

    def source_text(self, path: Path) -> str:
        """Read local or external planning text through the same original authority."""
        if not isinstance(self.fscommands, self.AtomicReadFiles):
            msg = "Rope project does not own authenticated live reads"
            raise TypeError(msg)
        return self.fscommands.read(str(path)).decode(c.DEFAULT_ENCODING)

    def source_walk(self, path: Path) -> Generator[tuple[Path, list[str], list[str]]]:
        """Provide Path.walk's pruning contract over original native membership."""
        pending = [path]
        while pending:
            directory = pending.pop()
            directories: list[str] = []
            files: list[str] = []
            for child in self.source_children(directory):
                if self.source_query(child, "isdir"):
                    directories.append(child.name)
                else:
                    files.append(child.name)
            yield directory, directories, files
            pending.extend(directory / name for name in reversed(directories))

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
        try:
            self.fscommands.verify()
            if self.fscommands.epoch_failure is not None:
                raise self.fscommands.epoch_failure
        except (OSError, *c.EXC_BROAD_RUNTIME) as exc:
            if self.fscommands.epoch_failure is None:
                self.fscommands.epoch_failure = exc
                raise
            if self.fscommands.epoch_failure is exc:
                raise
            raise self.fscommands.epoch_failure from exc

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
        """Initialize the native core and captured resource observations."""
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
