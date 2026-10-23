"""Authenticated Rope project boundary over the installed native lifecycle.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from collections.abc import Generator, Mapping
from contextlib import AbstractContextManager, closing, contextmanager, nullcontext
from errno import ENOENT
from os import PathLike
from os.path import normpath, realpath, sep
from pathlib import Path
from types import MappingProxyType
from typing import Literal, Protocol, Self, cast, override

from flext_cli import u
from rope.base.exceptions import ResourceNotFoundError
from rope.base.fscommands import FileSystemCommands
from rope.base.project import NoProject, Project
from rope.base.resourceobserver import ChangeIndicator
from rope.base.resources import File, Folder

from flext_infra import c, config, m, p, t
from flext_infra._utilities import FlextInfraUtilitiesRopeRuntimeModuleQueries
from flext_infra._utilities._rope.native_project import FlextInfraRopeNativeProject


class FlextInfraRopeProject(FlextInfraRopeNativeProject):
    """Authenticated source epochs over the native Rope project interface.

    Source access reads ``fscommands`` and the snapshot owner classes only
    through the declared authenticated boundary.
    """

    @property
    def _authenticated_reads(self) -> FlextInfraRopeProject.AtomicReadFiles:
        """Require the authenticated original read owner of this project.

        Returns:
            The authenticated original read owner.

        Raises:
            TypeError: The project does not own authenticated live reads.

        """
        if not isinstance(self.fscommands, FlextInfraRopeProject.AtomicReadFiles):
            msg = "Rope project does not own authenticated live reads"
            raise TypeError(msg)
        return self.fscommands

    @property
    def authenticated_sources(self) -> bool:
        """Whether all source operations share an authenticated original epoch."""
        return isinstance(self.fscommands, FlextInfraRopeProject.AtomicReadFiles)

    def source_consumption(
        self,
    ) -> AbstractContextManager[p.Infra.RopeSourceConsumption]:
        """Open an exact native consumption scope, rejecting unbound projects.

        Returns:
            The native consumption scope context manager.

        """
        return self._authenticated_reads.consumption()

    def source_selection(self) -> AbstractContextManager[None]:
        """Scope native structural election; actual reads still record full proofs.

        Returns:
            The native structural election scope context manager.

        """
        return self._authenticated_reads.selection()

    def source_capture(self) -> AbstractContextManager[None]:
        """Pin potential originals once without claiming prefetch was consumption.

        Returns:
            The native capture scope context manager.

        """
        return self._authenticated_reads.capture()

    def replay_source_consumption(self, receipt: m.Infra.CodegenPhaseAnalysis) -> None:
        """Attribute an authentic cached result's original dependencies."""
        self._authenticated_reads.replay(receipt)

    def source_state(
        self, path: Path, *, required: bool = True
    ) -> m.Cli.AtomicFileState:
        """Use the authenticated resource owner for direct source decisions.

        Returns:
            The original physical state for the source.

        """
        return self._authenticated_reads.source_state(path, required=required)

    def source_query(
        self, path: Path, predicate: Literal["exists", "isfile", "isdir"]
    ) -> bool:
        """Query the declared snapshot or the authenticated physical read owner.

        Returns:
            Whether the owning source inventory's predicate holds for the path.

        """
        if isinstance(self.fscommands, FlextInfraRopeProject.SnapshotFiles):
            return {
                "exists": self.fscommands.exists,
                "isfile": self.fscommands.isfile,
                "isdir": self.fscommands.isdir,
            }[predicate](str(path))
        return self._authenticated_reads.query(str(path), predicate)

    def source_children(
        self, path: Path, *, follow_aliases: bool = True
    ) -> tuple[Path, ...]:
        """Enumerate original native membership with its exact query receipt.

        Returns:
            The original direct child paths.

        """
        return self._authenticated_reads.children(
            str(path),
            follow_aliases=follow_aliases,
        )

    def source_text(self, path: Path) -> str:
        """Read local or external planning text through the same original authority.

        Returns:
            The decoded planning text for the source.

        """
        return self.source_bytes(path).decode(c.DEFAULT_ENCODING)

    def source_bytes(self, path: Path) -> bytes:
        """Read selected payload bytes without changing their original receipts.

        Returns:
            The selected payload bytes.

        """
        if isinstance(self.fscommands, FlextInfraRopeProject.SnapshotFiles):
            return self.fscommands.read(str(path))
        return self._authenticated_reads.read(str(path))

    def source_walk(self, path: Path) -> Generator[tuple[Path, list[str], list[str]]]:
        """Provide prunable physical source traversal without following aliases.

        Yields:
            ``(directory, directories, files)`` tuples in traversal order.

        """
        pending = [path]
        while pending:
            directory = pending.pop()
            directories: list[str] = []
            files: list[str] = []
            for child in self.source_children(directory, follow_aliases=False):
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

        """
        return self._authenticated_reads.states()

    def consumed_source_directories(self) -> tuple[m.Cli.AtomicDirectoryInventory, ...]:
        """Return the native query receipts for this planning epoch.

        Returns:
            Original directory inventories consumed by native queries.

        """
        return self._authenticated_reads.receipt_directories()

    def consumed_source_topology(self) -> tuple[m.Cli.AtomicDirectoryChainPlan, ...]:
        """Return physical ancestry witnesses for consumed source queries.

        Returns:
            Original physical ancestry witnesses for queried parents.

        """
        return self._authenticated_reads.receipt_topology()

    def verify_source_states(
        self, receipt: m.Infra.CodegenPhaseAnalysis | None = None
    ) -> None:
        """Verify the complete epoch or one authentic original consumer receipt."""
        self._authenticated_reads.verify(receipt)

    _source_election: p.Infra.RopeProjectElection | None = None

    def __init__(
        self,
        projectroot: str | PathLike[str],
        fscommands: p.Infra.RopeProjectFiles | None = None,
        ropefolder: str | None = ".ropeproject",
        external_project: p.Infra.RopeResourceOwner | None = None,
        **prefs: bool | t.StrSequence,
    ) -> None:
        """Initialize the native project over its checked physical read owner.

        Args:
            projectroot: The root directory of the existing project.
            fscommands: The native or authenticated filesystem owner.
            ropefolder: Native state folder, or ``None`` for a read-only epoch.
            external_project: Resource owner for external Python modules.
            prefs: Native project preferences.

        Raises:
            ValueError: The root is absent or the constructor changed its owner.

        """
        root = (
            fscommands.realpath(str(projectroot))
            if fscommands is not None
            else realpath(projectroot)
        )
        directory_exists = (
            fscommands.isdir(root) if fscommands is not None else Path(root).is_dir()
        )
        if not directory_exists:
            message = f"Rope project root must already be a directory: {root}"
            raise ValueError(message)
        if "extension_modules" not in prefs:
            prefs["extension_modules"] = tuple(
                sorted(
                    name
                    for name in tuple(sys.modules)
                    if name.partition(".")[0] in sys.stdlib_module_names
                    and (module := sys.modules.get(name)) is not None
                    and module.__spec__ is not None
                    and module.__spec__.origin in {"built-in", "frozen"}
                )
            )
        initializer: p.Infra.RopeProjectInitializer = Project.__dict__["__init__"]
        initializer(
            self,
            root,
            fscommands=fscommands,
            ropefolder=ropefolder,
            external_project=external_project,
            **prefs,
        )
        if self.root.real_path != root or (
            fscommands is not None and self.fscommands is not fscommands
        ):
            message = f"Rope constructor changed its physical read owner: {root}"
            raise ValueError(message)

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
                self.realpath(str(root)) for root in ambient_roots
            )
            self._identities: t.MutableMappingKV[str, Path] = {}
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

        def _identity(self, path: str) -> Path:
            """Resolve one queried path once for this immutable snapshot.

            Returns:
                The lexical absolute identity of the queried path.

            """
            if path not in self._identities:
                self._identities[path] = Path(self.realpath(path))
            return self._identities[path]

        def _ambient_identity(self, resolved: Path) -> Path | None:
            """Return the real path when it belongs to an ambient interpreter root.

            Args:
                resolved: Already normalized path; avoids repeating ``realpath``.

            Returns:
                The normalized real path inside one ambient root, or ``None``
                for repository-scoped paths the closed inventory owns.

            """
            # Both sides are lexical absolute paths: a string prefix test is exact.
            text = str(resolved)
            if any(
                text == root or text.startswith(root + sep)
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
            resolved = self._identity(path)
            if resolved in self._sources or resolved in self._directories:
                return True
            ambient = self._ambient_identity(resolved)
            return ambient is not None and ambient.exists()

        def isfile(self, path: str) -> bool:
            """Recognize captured source files and ambient interpreter files.

            Args:
                path: The path to check for being a file.

            Returns:
                Whether the specified path is a captured source file.

            """
            resolved = self._identity(path)
            if resolved in self._sources:
                return True
            ambient = self._ambient_identity(resolved)
            return ambient is not None and ambient.is_file()

        def isdir(self, path: str) -> bool:
            """Recognize captured folders and ambient interpreter folders.

            Args:
                path: The path to check for being a directory.

            Returns:
                Whether the specified path is a captured or ambient folder.

            """
            resolved = self._identity(path)
            if resolved in self._directories:
                return True
            ambient = self._ambient_identity(resolved)
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
            directory = self._identity(path)
            if directory in self._directories:
                return [child.name for child in self._children[directory]]
            ambient = self._ambient_identity(directory)
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
            source = self._identity(path)
            if source in self._sources:
                return self._sources[source]
            ambient = self._ambient_identity(source)
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

            Raises:
                FileNotFoundError: If the path is neither captured nor
                  ambient interpreter state.

            """
            source = self._identity(path)
            if source in self._children:
                return self._children[source]
            ambient = self._ambient_identity(source)
            if ambient is not None and ambient.is_dir():
                return tuple(
                    ambient / item.name
                    for item in sorted(ambient.iterdir(), key=lambda item: item.name)
                )
            msg = f"Rope snapshot folder is absent: {path}"
            raise FileNotFoundError(msg)

    class SourceConsumption:
        """Accumulate original receipts for one native consumer, not a set delta."""

        def __init__(self) -> None:
            self._states: t.MutableMappingKV[int, m.Cli.AtomicFileState] = {}
            self._directories: t.MutableMappingKV[
                int, m.Cli.AtomicDirectoryInventory
            ] = {}
            self._topology: t.MutableMappingKV[int, m.Cli.AtomicDirectoryChainPlan] = {}
            self._effects: set[Path] = set()
            self._receipt: m.Infra.CodegenPhaseAnalysis | None = None

        def record(
            self,
            states: tuple[m.Cli.AtomicFileState, ...] = (),
            directories: tuple[m.Cli.AtomicDirectoryInventory, ...] = (),
            topology: tuple[m.Cli.AtomicDirectoryChainPlan, ...] = (),
            effects: tuple[Path, ...] = (),
        ) -> None:
            """Merge exact observations while retaining their original identities.

            Repeated references retain one original witness, not another copy.
            Distinct observations remain distinct and reach native conflict
            validation even when they concern the same path.

            Raises:
                ValueError: If the receipt is already sealed.

            """
            if self._receipt is not None:
                msg = "Rope source consumption is already sealed"
                raise ValueError(msg)
            self._states.update((id(state), state) for state in states)
            self._directories.update((id(item), item) for item in directories)
            self._topology.update((id(item), item) for item in topology)
            self._effects.update(effects)

        def _directory_observations(
            self,
        ) -> tuple[m.Cli.AtomicDirectoryInventory, ...]:
            """Union selectors only over the exact same original native tree.

            Returns:
                Observations retaining every distinct root and child inventory.

            """
            elected: t.MutableMappingKV[
                t.Pair[int, int], m.Cli.AtomicDirectoryInventory
            ] = {}
            queries: t.MutableMappingKV[
                t.Pair[int, int],
                set[t.Pair[str, Literal["exists", "isfile", "isdir"]]],
            ] = {}
            membership: set[t.Pair[int, int]] = set()
            membership_queries: t.MutableMappingKV[
                t.Pair[int, int], set[t.StrTuple]
            ] = {}
            for inventory in self._directories.values():
                key = (id(inventory.root), id(inventory.entries))
                if key not in elected:
                    elected[key] = inventory
                    queries[key] = set()
                    membership_queries[key] = set()
                for name, predicate in inventory.queries:
                    _ = u.Cli.atomic_directory_query_value(inventory, name, predicate)
                queries[key].update(inventory.queries)
                membership_queries[key].update(inventory.membership_queries)
                if inventory.membership_queried:
                    membership.add(key)
            return tuple(
                inventory.model_copy(
                    update={
                        "queries": tuple(sorted(queries[key])),
                        "membership_queried": key in membership,
                        "membership_queries": tuple(sorted(membership_queries[key])),
                    }
                )
                for key, inventory in elected.items()
            )

        def seal(
            self,
        ) -> t.Pair[m.Infra.CodegenPhaseAnalysis, tuple[Path, ...]]:
            """Freeze the receipt only after the consumer has left its scope.

            Returns:
                The sealed original consumption receipt.

            """
            directories, topology = u.Cli.atomic_merge_directory_query_receipts(
                self._directory_observations(),
                tuple(self._topology.values()),
            )
            self._receipt = m.Infra.CodegenPhaseAnalysis(
                phase=c.Infra.CodegenStagedFilePhase.LAZY_INIT,
                files=(),
                inputs=m.Infra.CodemodBindingSnapshot(
                    states=tuple(self._states.values()),
                ).states,
                source_directories=directories,
                source_query_topology=topology,
            )
            return self._receipt, tuple(sorted(self._effects))

        def receipt(self) -> m.Infra.CodegenPhaseAnalysis:
            """Require a complete receipt; an active or failed scope is not evidence.

            Returns:
                The sealed original consumption receipt.

            Raises:
                ValueError: If the receipt has not been sealed yet.

            """
            if self._receipt is None:
                msg = "Rope source consumption has no completed receipt"
                raise ValueError(msg)
            return self._receipt

    class AtomicReadFiles:
        """Authenticate only sources actually read by the native semantic graph.

        Authentication ends at the repository root: supplier and dependency
        sources outside it are read for inference and never authenticated.
        """

        stat = staticmethod(FileSystemCommands.stat)

        _declared: tuple[m.Infra.CodegenFilePlan, ...]
        _declared_paths: frozenset[Path]
        _effects: t.MappingKV[Path, m.Infra.CodegenFilePlan]
        _consumed_effects: set[Path]
        _retired: frozenset[Path]
        _sources: Mapping[Path, bytes]

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
            *,
            election: p.Infra.RopeProjectElection,
        ) -> None:
            self._root = root
            self._query_owners = tuple(
                sorted(
                    {
                        (root, True),
                        *((root / folder, True) for folder in election.source_folders),
                        *(
                            (Path(folder), False)
                            for folder in election.python_path_folders
                        ),
                    },
                    key=lambda item: (len(item[0].parts), item[1]),
                    reverse=True,
                )
            )
            self._managed_query_paths = frozenset(
                path
                for plan in declared_files
                for path in (plan.path, *plan.path.parents)
                if path.is_relative_to(root)
            )
            self._structural_queries = 0
            self._capturing = 0
            self._scopes: list[FlextInfraRopeProject.SourceConsumption] = []
            self._receipts: list[
                t.Pair[m.Infra.CodegenPhaseAnalysis, tuple[Path, ...]]
            ] = []
            self._originals: t.MutableMappingKV[Path, m.Cli.AtomicFileState] = {}
            self._consumed: t.MutableMappingKV[Path, m.Cli.AtomicFileState] = {}
            self._inventories: t.MutableMappingKV[
                Path, m.Cli.AtomicDirectoryInventory
            ] = {}
            self._topology: t.MutableMappingKV[
                Path, m.Cli.AtomicDirectoryChainPlan
            ] = {}
            self._imported_directories: t.MutableMappingKV[
                Path, m.Cli.AtomicDirectoryInventory
            ] = {}
            self._imported_topology: t.MutableMappingKV[
                Path, m.Cli.AtomicDirectoryChainPlan
            ] = {}
            self._register_original_states(source_states)
            self._adopt_declared_effects(declared_files)
            self._reconcile_proposed_sources(sources, declared_files)
            self._overlay = FlextInfraRopeProject.SnapshotFiles(self._sources, ())
            # Original-epoch membership facts are pinned at construction, so
            # each (path, predicate) observation is stable for this owner's
            # lifetime. Every access still attributes its original witnesses
            # to the current native consumption scopes, including cache hits.
            self._query_observations: t.MutableMappingKV[tuple[Path, str], bool] = {}
            self._query_witnesses: t.MutableMappingKV[
                tuple[Path, str],
                m.Cli.AtomicDirectoryInventory | m.Cli.AtomicDirectoryChainPlan,
            ] = {}
            self._consumed_queries: set[tuple[Path, str]] = set()
            self._observed_overlays: set[str] = set()

        def _register_original_states(
            self,
            source_states: tuple[m.Cli.AtomicFileState, ...],
        ) -> None:
            """Index the supplied original states or reject their conflicts.

            Raises:
                ValueError: If one path carries conflicting original states.

            """
            for state in source_states:
                path = Path(state.path)
                previous = self._originals.get(path)
                if previous is not None and previous != state:
                    msg = f"Rope source has conflicting original states: {path}"
                    raise ValueError(msg)
                self._originals[path] = state

        def _adopt_declared_effects(
            self,
            declared_files: tuple[m.Infra.CodegenFilePlan, ...],
        ) -> None:
            """Adopt the declared effects and their destination absence witnesses.

            Raises:
                ValueError: If an effect lacks its original destination
                  absence witness.

            """
            self._declared = tuple(
                plan
                for plan in declared_files
                if plan.desired_content is not None
                and (
                    isinstance(plan.before, m.Cli.AtomicDirectoryChainPlan)
                    or plan.before.content is None
                )
            )
            self._declared_paths = frozenset(plan.path for plan in self._declared)
            self._effects = {plan.path: plan for plan in declared_files}
            self._consumed_effects = set()
            for plan in declared_files:
                if isinstance(plan.before, m.Cli.AtomicDirectoryChainPlan):
                    if (
                        not plan.before.directories
                        or plan.before.target != plan.path.parent
                    ):
                        msg = (
                            "Rope effect lacks its original destination "
                            f"absence witness: {plan.path}"
                        )
                        raise ValueError(msg)
                    _, chains = u.Cli.atomic_merge_directory_query_receipts(
                        (),
                        (
                            *self._topology.values(),
                            plan.before.model_copy(
                                update={
                                    "queries": (),
                                    "membership_queried": False,
                                    "membership_queries": (),
                                }
                            ),
                        ),
                    )
                    self._topology.update((item.target, item) for item in chains)
            self._retired = frozenset(
                plan.path for plan in declared_files if plan.desired_content is None
            )

        def _reconcile_proposed_sources(
            self,
            sources: t.MappingKV[Path, str],
            declared_files: tuple[m.Infra.CodegenFilePlan, ...],
        ) -> None:
            """Freeze the proposed bytes after proving every original input.

            Raises:
                ValueError: If proposed sources disagree with their declared
                  effects or lack their original input.

            """
            proposed = {
                path: source.encode(c.DEFAULT_ENCODING)
                for path, source in sources.items()
            }
            for plan in declared_files:
                if plan.desired_content is not None:
                    supplied = proposed.get(plan.path)
                    if supplied is not None and supplied != plan.desired_content:
                        msg = (
                            "Rope proposed source disagrees with its "
                            f"declared effect: {plan.path}"
                        )
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
            """Record every read/query, including repeats and nested consumers.

            Yields:
                The consumption scope accumulating original receipts.

            """
            scope = FlextInfraRopeProject.SourceConsumption()
            self._scopes.append(scope)
            try:
                yield scope
                self._receipts.append(scope.seal())
            finally:
                self._scopes.remove(scope)

        def replay(self, receipt: m.Infra.CodegenPhaseAnalysis) -> None:
            """Replay only evidence minted by this authenticated original epoch.

            Raises:
                ValueError: If the receipt belongs to another original epoch
                  or no consumer scope is active.

            """
            issued = next((item for item in self._receipts if item[0] is receipt), None)
            if issued is None:
                msg = "Rope source receipt does not belong to this original epoch"
                raise ValueError(msg)
            if not self._scopes:
                msg = "Rope source replay requires an active consumer"
                raise ValueError(msg)
            self._record(
                receipt.inputs,
                receipt.source_directories,
                receipt.source_query_topology,
                issued[1],
            )

        def _record(
            self,
            states: tuple[m.Cli.AtomicFileState, ...] = (),
            directories: tuple[m.Cli.AtomicDirectoryInventory, ...] = (),
            topology: tuple[m.Cli.AtomicDirectoryChainPlan, ...] = (),
            effects: tuple[Path, ...] = (),
        ) -> None:
            """Attribute the exact event to every enclosing consumer."""
            if self._capturing:
                return
            for scope in self._scopes:
                scope.record(states, directories, topology, effects)

        def _consume_effect(self, path: Path) -> None:
            """Attribute a declared overlay effect's original proof to its consumer.

            Raises:
                ValueError: If a declared overlay effect lacks its original
                  input receipt.

            """
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
            chains = (
                *plan.source_query_topology,
                *(
                    (plan.before,)
                    if isinstance(plan.before, m.Cli.AtomicDirectoryChainPlan)
                    else ()
                ),
            )
            if path in self._consumed_effects:
                # Reuse the original plan receipt without repeating filesystem
                # verification; still attribute the declared effect to this
                # consumer so independent scopes retain their proof.
                self._record(
                    states=states,
                    directories=plan.source_directories,
                    topology=chains,
                    effects=(path,),
                )
                return
            self._consumed_effects.add(path)
            for original in states:
                if self.source_state(original.path, required=False) != original:
                    msg = (
                        "Rope overlay effect has conflicting "
                        f"original input: {original.path}"
                    )
                    raise ValueError(msg)
            directories, topology = u.Cli.atomic_merge_directory_query_receipts(
                (*self._imported_directories.values(), *plan.source_directories),
                (*self._imported_topology.values(), *chains),
            )
            self._imported_directories.update(
                (item.root.path, item) for item in directories
            )
            self._imported_topology.update((item.target, item) for item in topology)
            self._record(
                directories=plan.source_directories, topology=chains, effects=(path,)
            )

        def exists(self, path: str) -> bool:
            """Retain native election, including explicitly planned resources.

            Args:
                path: The path to check for existence.

            Returns:
                Whether the overlay or native filesystem contains the path.

            """
            return self.query(path, "exists")

        def isfile(self, path: str) -> bool:
            """Recognize planned source files and native physical files.

            Args:
                path: The path to check for being a file.

            Returns:
                Whether the path is a planned or native source file.

            """
            return self.query(path, "isfile")

        def isdir(self, path: str) -> bool:
            """Recognize declared virtual parents and native physical folders.

            Args:
                path: The path to check for being a directory.

            Returns:
                Whether the path is a declared virtual or native folder.

            """
            return self.query(path, "isdir")

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
            if not self._owns_query(directory):
                # Dependency membership is inference, not a project election.
                # Actual payload reads retain their immutable file receipts.
                return sorted(
                    child.name
                    for child in directory.iterdir()
                    if not self._is_generated_artifact(child)
                )
            inventory = self._inventory(directory)
            names: list[str] = (
                []
                if inventory is None
                else list(
                    u.Cli.atomic_directory_membership_value(
                        inventory, tuple(sorted(self._GENERATED_ARTIFACT_PARTS))
                    )
                )
            )
            self._record_membership(directory, inventory)
            if self._overlay.isdir(path):
                physical_names = frozenset(names)
                for child in self._overlay.children(path):
                    if child.name not in physical_names and not (
                        self._structural_queries or self._capturing
                    ):
                        self._observe_overlay(str(child))
                    names.append(child.name)
            elif inventory is None:
                raise FileNotFoundError(
                    ENOENT, "Rope source directory was observed absent", path
                )
            for retired in self._retired:
                if retired.parent == directory and not (
                    self._structural_queries or self._capturing
                ):
                    self._consume_effect(retired)
            return sorted(
                name
                for name in set(names)
                if directory / name not in self._retired
                and not self._is_generated_artifact(directory / name)
            )

        def _record_membership(
            self,
            directory: Path,
            inventory: m.Cli.AtomicDirectoryInventory | None,
        ) -> None:
            """Pin a listed folder's membership on its inventory or absence witness."""
            if inventory is not None:
                if not self._capturing:
                    self._inventories[directory] = inventory.model_copy(
                        update={
                            "membership_queries": (
                                tuple(sorted(self._GENERATED_ARTIFACT_PARTS)),
                            )
                        }
                    )
                self._record(
                    directories=(
                        inventory.model_copy(
                            update={
                                "queries": (),
                                "membership_queried": False,
                                "membership_queries": (
                                    tuple(sorted(self._GENERATED_ARTIFACT_PARTS)),
                                ),
                            },
                        ),
                    ),
                )
                return
            if not self._capturing:
                self._topology[directory] = self._topology[directory].model_copy(
                    update={
                        "membership_queries": (
                            tuple(sorted(self._GENERATED_ARTIFACT_PARTS)),
                        )
                    }
                )
            self._record(
                topology=(
                    self._topology[directory].model_copy(
                        update={
                            "queries": (),
                            "membership_queried": False,
                            "membership_queries": (
                                tuple(sorted(self._GENERATED_ARTIFACT_PARTS)),
                            ),
                        },
                    ),
                ),
            )

        def _directory_chain(self, directory: Path) -> m.Cli.AtomicDirectoryChainPlan:
            """Pin one declared directory's own physical ancestry and presence.

            Returns:
                The original physical ancestry witness.

            """
            if directory not in self._topology:
                self._topology[directory] = u.Cli.atomic_plan_directory_chain(
                    directory
                ).unwrap()
            witness = self._topology[directory]
            self._record(
                topology=(
                    witness.model_copy(
                        update={
                            "queries": (),
                            "membership_queried": False,
                            "membership_queries": (),
                        },
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
                self._inventories[directory] = (
                    u.Cli.atomic_inventory_physical_directory(directory).unwrap()
                )
            return self._inventories[directory]

        _GENERATED_ARTIFACT_PARTS = frozenset(config.Infra.codegen.source_scan_ignored)

        @classmethod
        def _is_generated_artifact(cls, candidate: Path) -> bool:
            """Recognize runtime byproduct paths outside the source epoch.

            Returns:
                Whether any path part names a generated cache artifact.

            """
            return bool(cls._GENERATED_ARTIFACT_PARTS.intersection(candidate.parts))

        def query(
            self, path: str, predicate: Literal["exists", "isfile", "isdir"]
        ) -> bool:
            """Retain both positive and negative native candidate observations.

            Returns:
                The predicate value authenticated by the native inventory.

            """
            candidate = Path(path)
            if self._is_generated_artifact(candidate):
                # Bytecode and tool caches are runtime byproducts, never
                # original sources: they answer from the plain filesystem and
                # stay outside the epoch inventory, so their appearance or
                # disappearance mid-run can never invalidate an epoch.
                return self._ambient_query(candidate, predicate)
            memo_key = (candidate, predicate)
            observed = self._query_observations.get(memo_key)
            if observed is None:
                if candidate == self._root:
                    observed = (
                        not self._directory_chain(candidate).directories
                        and predicate != "isfile"
                    )
                elif not self._owns_query(candidate):
                    observed = self._ambient_query(candidate, predicate)
                else:
                    observed = self._repository_query(candidate, predicate)
                self._query_observations[memo_key] = observed
            elif candidate == self._root:
                self._directory_chain(candidate)
            elif memo_key in self._query_witnesses:
                witness = self._query_witnesses[memo_key]
                if isinstance(witness, m.Cli.AtomicDirectoryInventory):
                    self._record(directories=(witness,))
                else:
                    self._record(topology=(witness,))
            if not self._capturing and memo_key in self._query_witnesses:
                self._consumed_queries.add(memo_key)
            return self._resolve_query_result(
                candidate, path, predicate, observed=observed
            )

        def _owns_query(self, candidate: Path) -> bool:
            """Elect declared source or managed ownership, not lexical containment.

            Returns:
                Whether the most specific declared owner is project source.

            """
            if candidate in self._managed_query_paths:
                return True
            return next(
                (
                    owned
                    for root, owned in self._query_owners
                    if candidate.is_relative_to(root)
                ),
                False,
            )

        @staticmethod
        def _ambient_query(
            candidate: Path,
            predicate: Literal["exists", "isfile", "isdir"],
        ) -> bool:
            """Read plain native membership outside the authenticated repository.

            Returns:
                The plain filesystem fact for the ambient candidate.

            """
            return {
                "exists": candidate.exists,
                "isfile": candidate.is_file,
                "isdir": candidate.is_dir,
            }[predicate]()

        def _repository_query(
            self,
            candidate: Path,
            predicate: Literal["exists", "isfile", "isdir"],
        ) -> bool:
            """Observe one repository candidate through its authenticated parent.

            Returns:
                The predicate value authenticated by the parent inventory or
                absence witness.

            Raises:
                NotADirectoryError: If native ancestry conflicts with a declared
                    directory.

            """
            parent = candidate.parent
            try:
                inventory = self._inventory(parent)
            except NotADirectoryError:
                if self.query(str(parent), "isdir"):
                    raise
                self._query_witnesses[candidate, predicate] = self._query_witnesses[
                    parent, "isdir"
                ]
                return False
            if inventory is None:
                self._record_parent_witness(candidate, predicate)
                return False
            return self._record_parent_inventory(candidate, predicate, inventory)

        def _record_parent_witness(
            self,
            candidate: Path,
            predicate: Literal["exists", "isfile", "isdir"],
        ) -> None:
            """Pin the queried selector on the parent's absence witness."""
            witness = self._topology[candidate.parent]
            selector = (candidate.name, predicate)
            if not self._capturing and selector not in witness.queries:
                self._topology[candidate.parent] = witness.model_copy(
                    update={"queries": tuple(sorted({*witness.queries, selector}))}
                )
            selection = witness.model_copy(
                update={
                    "queries": ((candidate.name, predicate),),
                    "membership_queried": False,
                    "membership_queries": (),
                },
            )
            self._query_witnesses[candidate, predicate] = selection
            self._record(topology=(selection,))

        def _record_parent_inventory(
            self,
            candidate: Path,
            predicate: Literal["exists", "isfile", "isdir"],
            inventory: m.Cli.AtomicDirectoryInventory,
        ) -> bool:
            """Pin the queried selector on the parent's physical inventory.

            Returns:
                The predicate value authenticated by the inventory.

            """
            observed = u.Cli.atomic_directory_query_value(
                inventory, candidate.name, predicate
            )
            selector = (candidate.name, predicate)
            if selector not in inventory.queries:
                inventory = inventory.model_copy(
                    update={"queries": tuple(sorted({*inventory.queries, selector}))}
                )
            if not self._capturing:
                self._inventories[candidate.parent] = inventory
            selection = inventory.model_copy(
                update={
                    "queries": ((candidate.name, predicate),),
                    "membership_queried": False,
                    "membership_queries": (),
                },
            )
            self._query_witnesses[candidate, predicate] = selection
            self._record(directories=(selection,))
            return observed

        def _resolve_query_result(
            self,
            candidate: Path,
            path: str,
            predicate: Literal["exists", "isfile", "isdir"],
            *,
            observed: bool,
        ) -> bool:
            """Reconcile the native observation with planned and original state.

            Returns:
                The final predicate value for the queried candidate.

            """
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
            if path in self._observed_overlays:
                return
            if self._overlay.isfile(path):
                self._observed_overlays.add(path)
                self.read(path)
                return
            self._observed_overlays.add(path)
            for child in self._overlay.children(path):
                self._observe_overlay(str(child))

        def _directory_receipts(self) -> tuple[m.Cli.AtomicDirectoryInventory, ...]:
            """Return the complete native inventories with consumed query selectors."""
            return tuple(self._inventories.values())

        def _topology_receipts(self) -> tuple[m.Cli.AtomicDirectoryChainPlan, ...]:
            """Return original presence and ancestry witnesses for queried parents."""
            return tuple(self._topology.values())

        def receipt_directories(self) -> tuple[m.Cli.AtomicDirectoryInventory, ...]:
            """Return this epoch's inventories plus imported planning receipts."""
            return u.Cli.atomic_merge_directory_query_receipts(
                (
                    *self._directory_receipts(),
                    *self._imported_directories.values(),
                    *(
                        witness
                        for key in sorted(self._consumed_queries)
                        if isinstance(
                            witness := self._query_witnesses[key],
                            m.Cli.AtomicDirectoryInventory,
                        )
                    ),
                ),
                (),
            )[0]

        def receipt_topology(self) -> tuple[m.Cli.AtomicDirectoryChainPlan, ...]:
            """Return this epoch's witnesses plus imported planning receipts."""
            return u.Cli.atomic_merge_directory_query_receipts(
                (),
                (
                    *self._topology_receipts(),
                    *self._imported_topology.values(),
                    *(
                        witness
                        for key in sorted(self._consumed_queries)
                        if isinstance(
                            witness := self._query_witnesses[key],
                            m.Cli.AtomicDirectoryChainPlan,
                        )
                    ),
                ),
            )[1]

        def children(
            self, path: str, *, follow_aliases: bool = True
        ) -> tuple[Path, ...]:
            """Return native direct membership for the change observer."""
            children = tuple(Path(path) / name for name in self.listdir(path))
            if follow_aliases:
                return children
            if not self._owns_query(Path(path)):
                return tuple(
                    child
                    for child in children
                    if not child.is_symlink() and (child.is_file() or child.is_dir())
                )
            inventory = self._inventory(Path(path))
            excluded: set[str] = (
                {
                    entry.name
                    for entry in inventory.entries
                    if entry.kind not in {"file", "directory"}
                }
                if inventory is not None
                else set()
            )
            return tuple(
                child
                for child in children
                if child.name not in excluded or child in self._effects
            )

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
            """Read or replay the original state, including an explicit absence.

            Returns:
                The original physical state for the source.

            Raises:
                FileNotFoundError: If a required source is absent or
                  explicitly retired.
                ValueError: If the source lacks its original parent absence
                  witness.

            """
            state = self._consumed.get(source)
            if state is None:
                state = self._original_state(source)
                if not self._capturing:
                    self._verify_declarations(source, check_current=False)
                    if state.parent_inode is not None:
                        self._consumed[source] = state
            if state.parent_inode is None:
                witness = self._directory_chain(source.parent)
                if not witness.directories:
                    msg = f"Rope source lacks its original parent absence: {source}"
                    raise ValueError(msg)
                self._record(topology=(witness,))
            else:
                self._record(states=(state,))
            declaration = self._effects.get(source)
            if declaration is not None:
                self._record(effects=(source,))
            if declaration is not None and isinstance(
                declaration.before, m.Cli.AtomicDirectoryChainPlan
            ):
                self._record(topology=(declaration.before,))
            if required and state.content is None:
                msg = f"Rope required source is absent: {source}"
                raise FileNotFoundError(msg)
            return state

        def _original_state(self, source: Path) -> m.Cli.AtomicFileState:
            """Pin one source's original state on first use, absence included.

            Returns:
                The original physical state for the source.

            """
            state = self._originals.get(source)
            if state is None:
                declaration = self._effects.get(source)
                # An original absent parent proves its declared file absent too.
                state = (
                    m.Cli.AtomicFileState(path=source)
                    if declaration is not None
                    and isinstance(declaration.before, m.Cli.AtomicDirectoryChainPlan)
                    else u.Cli.atomic_read_binary_file_state(
                        source, required=False
                    ).unwrap()
                )
                self._originals[source] = state
            return state

        def states(self) -> tuple[m.Cli.AtomicFileState, ...]:
            """Expose original physical receipts for the shared dependent group.

            Returns:
                Original physical receipts for the shared dependent group.

            """
            return tuple(self._consumed.values())

        def verify(self, receipt: m.Infra.CodegenPhaseAnalysis | None = None) -> None:
            """Reprove an issued scope, or all original inputs for direct consumers.

            Raises:
                ValueError: An original source or directory query changed.

            """
            if receipt is not None:
                with self.consumption() as scope:
                    self.replay(receipt)
                issued = scope.receipt()
                if not (
                    issued.inputs
                    or issued.source_directories
                    or issued.source_query_topology
                ):
                    self.verify()
                    return
                states = issued.inputs
                directories = issued.source_directories
                topology = issued.source_query_topology
                effects = self._receipts[-1][1]
            else:
                states = self.states()
                directories = self.receipt_directories()
                topology = self.receipt_topology()
                effects = tuple(self._consumed_effects)
            verified = u.Cli.atomic_verify_binary_file_states(
                states,
                nonsecret_source_paths=tuple(
                    Path(state.path)
                    for state in states
                    if Path(state.path).suffix in {".py", ".pyi"}
                ),
            )
            if verified.failure:
                if verified.exception is not None:
                    raise verified.exception
                raise ValueError(verified.error)
            verified = u.Cli.atomic_verify_directory_queries(
                directories,
                topology,
                publications=m.Cli.AtomicDirectoryQueryEffects(
                    membership_policy=tuple(
                        sorted(config.Infra.codegen.source_scan_ignored)
                    )
                ),
            )
            if verified.failure:
                if verified.exception is not None:
                    raise verified.exception
                raise ValueError(verified.error)
            for path in sorted({*(state.path for state in states), *effects}):
                self._verify_declarations(path)

        def _verify_declarations(
            self, path: Path, *, check_current: bool = True
        ) -> None:
            """Authenticate every consumed declared source effect at its owner.

            Args:
                path: The path of the consumed declared source effect.
                check_current: Whether the current source must still match
                  its declaration.

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
                    FlextInfraUtilitiesRopeRuntimeModuleQueries.snapshot_declared_effect(
                        plan.project, plan
                    )

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
                # Observer registration pins bytes; only semantic reads consume them.
                with (
                    self._files.capture()
                    if isinstance(self._files, FlextInfraRopeProject.AtomicReadFiles)
                    else nullcontext()
                ):
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

        class _NativeExternalFolders(Protocol):
            """Typed view of the external resolver's native folder factory."""

            def get_folder(self, path: str) -> Folder: ...

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
        external_folders = cast("_NativeExternalFolders", external)
        project._snapshot_python_path_folders = [
            external_folders.get_folder(path) for path in election.python_path_folders
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
            election=election,
        )
        return cls._from_files(live.root.real_path, files, election)

    @contextmanager
    def source_consumer(self, *, consumer_root: Path | None = None) -> Generator[Self]:
        """Isolate native semantic caches while sharing the original read authority.

        Yields:
            A fresh native graph with the same originals, election and receipt issuer.

        Raises:
            TypeError: The project has no authenticated original read authority.
            ValueError: The consumer root covers no originally elected
                source folder.

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
                msg = (
                    "Rope consumer has no originally elected "
                    f"source folder: {consumer_root}"
                )
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
            self._from_files(
                self.root.real_path,
                self.fscommands,
                election,
            ),
        ) as consumer:
            yield consumer

    @override
    def _init_other_parts(self) -> None:
        """Initialize the native core and captured resource observations."""
        super()._init_other_parts()
        if isinstance(self.fscommands, self.SnapshotFiles | self.AtomicReadFiles):
            core = cast("p.Infra.RopeProject", self).get_pycore()
            core.observer.timekeeper = self.SnapshotChangeIndicator(self.fscommands)


__all__: list[str] = ["FlextInfraRopeProject"]
