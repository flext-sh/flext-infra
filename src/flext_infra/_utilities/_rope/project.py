"""Rope project over the live tree with planned sources overlaid in memory.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from collections.abc import Generator, Sequence
from contextlib import contextmanager
from os import PathLike
from os.path import realpath
from pathlib import Path
from threading import RLock
from typing import Literal, Self, cast, override

from flext_cli import u
from rope.base.exceptions import ResourceNotFoundError
from rope.base.project import NoProject, Project
from rope.base.resourceobserver import ChangeIndicator
from rope.base.resources import File, Folder

from flext_infra import c, config, m, p
from flext_infra._utilities._rope.native_project import FlextInfraRopeNativeProject
from flext_infra._utilities._rope.rope_runtime import FlextInfraUtilitiesRopeRuntime


class FlextInfraRopeProject(FlextInfraRopeNativeProject):
    """Native Rope project whose reads see planned sources before the disk."""

    _source_view_lock: RLock

    class OverlayFiles:
        """Read-only filesystem view: planned bytes overlay authenticated captures.

        A planned ``None`` hides a live file; directories holding planned
        files exist even before publication creates them. Rope providers and
        source planning reuse the same first-read bytes and physical witness;
        a later disk edit remains a publication conflict.
        """

        _source_roots: tuple[Path, ...]
        _root_owners: tuple[tuple[Path, bool], ...]

        def __init__(
            self,
            plans: tuple[m.Infra.CodegenFilePlan, ...],
            *,
            observations: tuple[m.Cli.AtomicFileState, ...] | None = None,
            source_roots: tuple[Path, ...] = (),
            dependency_roots: tuple[Path, ...] = (),
        ) -> None:
            """Pin captured reads before admitting declared source effects.

            ``None`` selects native first-read observation. An explicit tuple,
            including an empty tuple, selects a closed source observation.

            """
            self._physical: dict[str, Path] = {}
            self._states: dict[Path, m.Cli.AtomicFileState] = {}
            self._files: dict[Path, bytes] = {}
            self._hidden: set[Path] = set()
            self._directories: set[Path] = set()
            self._planned_children: dict[Path, set[str]] = {}
            self._observed_children: dict[Path, set[str]] = {}
            self._observed_directories: set[Path] = set()
            self._closed_observations = False
            self._dependency_roots = tuple(
                self._resolved(str(path)) for path in dependency_roots
            )
            self.select_source_roots(source_roots)
            self._closed_observations = observations is not None
            self.plans: tuple[m.Infra.CodegenFilePlan, ...] = ()
            for state in observations if observations is not None else ():
                self._record_observation(state)
            self.replace(plans)

        def _record_observation(self, state: m.Cli.AtomicFileState) -> None:
            """Retain one witness and its original filesystem membership.

            Raises:
                ValueError: A physical path already has another captured witness.

            """
            path = self._resolved(str(state.path))
            for parent in path.parents:
                self._physical.setdefault(str(parent), parent)
            previous = self._states.get(path)
            if previous is not None:
                if previous != state:
                    message = f"source observations disagree for physical path: {path}"
                    raise ValueError(message)
                return
            self._states[path] = state
            if state.content is not None:
                self._observed_directories.update(path.parents)
                for child in (path, *path.parents):
                    if child.parent != child:
                        self._observed_children.setdefault(child.parent, set()).add(
                            child.name
                        )

        def select_source_roots(self, roots: tuple[Path, ...]) -> None:
            """Use the native election's current source roots for captured reads."""
            self._source_roots = tuple(self._resolved(str(path)) for path in roots)
            owners = dict.fromkeys(self._dependency_roots, False)
            owners.update(dict.fromkeys(self._source_roots, True))
            self._root_owners = tuple(
                sorted(
                    owners.items(), key=lambda item: len(item[0].parts), reverse=True
                )
            )

        def source_member(self, path: Path) -> bool:
            """Keep source traversal separate from native SDK lookup roots.

            Returns:
                Whether the path belongs to or leads to an elected source root.

            """
            if not self._closed_observations:
                return True
            resolved = self._resolved(str(path))
            return self._captured_source(resolved) or any(
                root.is_relative_to(resolved) for root in self._source_roots
            )

        @property
        def directory_membership(self) -> frozenset[Path]:
            """The captured and planned directories visible to native observers.

            Returns:
                The logical directory identities of this view.

            """
            return frozenset(self._observed_directories | self._directories)

        def captured_directory(self, path: str) -> bool:
            """Read directory membership from observations and declared effects.

            Returns:
                Whether the view already owns this directory independently of disk.

            """
            resolved = self._resolved(path)
            return (
                resolved in self._directories
                or resolved in self._observed_directories
                or (self._captured_source(resolved) and resolved in self._source_roots)
            )

        def _captured_source(self, path: Path) -> bool:
            """Distinguish captured sources from explicitly elected SDK roots.

            The most specific elected root owns a lookup. Source ownership wins
            a tie, including editable paths also present on the Python path.

            Returns:
                Whether the lookup belongs to the closed source observation.

            """
            if not self._closed_observations:
                return False
            return next(
                (
                    source
                    for root, source in self._root_owners
                    if path.is_relative_to(root)
                ),
                False,
            )

        def replace(
            self, plans: tuple[m.Infra.CodegenFilePlan, ...]
        ) -> tuple[tuple[Path, bool, bool], ...]:
            """Change only candidate deltas, retaining authenticated preimages.

            Returns:
                Changed source paths and their preceding/following existence.

            Raises:
                ValueError: A candidate disagrees with a retained witness or
                    contains conflicting declarations for one physical path.

            """
            selected: dict[Path, m.Infra.CodegenFilePlan] = {}
            for plan in plans:
                path = self._resolved(str(plan.path))
                previous = selected.get(path)
                observed = self._states.get(path)
                conflicting_plan = previous is not None and (
                    previous.before != plan.before
                    or previous.desired_content != plan.desired_content
                    or previous.desired_mode != plan.desired_mode
                )
                if conflicting_plan or (
                    observed is not None and observed != plan.before
                ):
                    msg = f"candidate source conflicts with captured state: {path}"
                    raise ValueError(msg)
                selected[path] = plan
            for plan in selected.values():
                self._record_observation(plan.before)
            changed: list[tuple[Path, bool, bool]] = []
            for path in sorted(self._files.keys() | self._hidden | selected.keys()):
                previous = (
                    self._files[path]
                    if path in self._files
                    else None
                    if path in self._hidden
                    else self._states[path].content
                )
                plan = selected.get(path)
                following = (
                    self._states[path].content if plan is None else plan.desired_content
                )
                if previous != following:
                    changed.append((path, previous is not None, following is not None))
                if path in self._files and (plan is None or following is None):
                    del self._files[path]
                    self._remove_membership(path)
                if plan is not None and following is not None:
                    if path not in self._files:
                        self._add_membership(path)
                    self._files[path] = following
                if plan is not None and following is None:
                    self._hidden.add(path)
                else:
                    self._hidden.discard(path)
            self.plans = plans
            return tuple(changed)

        def _add_membership(self, path: Path) -> None:
            """Add only the candidate path's ancestor membership."""
            self._directories.update(path.parents)
            for child in (path, *path.parents):
                if child.parent != child:
                    self._planned_children.setdefault(child.parent, set()).add(
                        child.name
                    )

        def _remove_membership(self, path: Path) -> None:
            """Retire only ancestor entries no other candidate source uses."""
            for child in (path, *path.parents):
                parent = child.parent
                if parent == child:
                    break
                children = self._planned_children[parent]
                children.remove(child.name)
                if children:
                    break
                del self._planned_children[parent]
                self._directories.discard(parent)

        def realpath(self, path: str) -> str:
            """Return the physical absolute identity of a path.

            Returns:
                The resolved path.

            """
            return str(self._resolved(path))

        def _resolved(self, path: str) -> Path:
            """Resolve one path once for the lifetime of this read-only view.

            Returns:
                The physical path identity.

            """
            physical = self._physical.get(path)
            if physical is None:
                logical = Path(path)
                if self._closed_observations:
                    for parent in logical.parents:
                        pinned = self._physical.get(str(parent))
                        if pinned is None:
                            continue
                        candidate = pinned / logical.relative_to(parent)
                        if self._captured_source(candidate):
                            physical = candidate
                        break
                if physical is None:
                    physical = Path(realpath(path))
                self._physical[path] = physical
            return physical

        def exists(self, path: str) -> bool:
            """Report planned, planned-parent and visible live paths.

            Returns:
                Whether the path exists in the overlaid view.

            """
            return self.isfile(path) or self.isdir(path)

        def isfile(self, path: str) -> bool:
            """Report captured and planned files, or native dependency files.

            Returns:
                Whether the path is a file in the overlaid view.

            """
            resolved = self._resolved(path)
            if resolved in self._files:
                return True
            if resolved in self._states:
                return (
                    resolved not in self._hidden
                    and self._states[resolved].content is not None
                )
            if self._captured_source(resolved):
                return False
            return resolved not in self._hidden and resolved.is_file()

        def isdir(self, path: str) -> bool:
            """Report observed parents, planned directories or native dependencies.

            Returns:
                Whether the path is a directory in the overlaid view.

            """
            resolved = self._resolved(path)
            if self.captured_directory(path):
                return True
            if (
                resolved in self._states
                or resolved in self._files
                or resolved in self._hidden
            ):
                return False
            if self._captured_source(resolved):
                return resolved in self._source_roots
            return resolved.is_dir()

        def listdir(self, path: str) -> list[str]:
            """List captured or SDK-owned children plus explicit planned effects.

            Returns:
                The sorted child names.

            """
            resolved = self._resolved(path)
            names = set(self._observed_children.get(resolved, ()))
            if not self._captured_source(resolved):
                names.update(
                    child.name
                    for child in (resolved.iterdir() if resolved.is_dir() else ())
                )
            names.update(self._planned_children.get(resolved, ()))
            visible: set[str] = set()
            for name in names:
                child = resolved / name
                if child in self._hidden:
                    continue
                state = self._states.get(child)
                if (
                    state is not None
                    and state.content is None
                    and child not in self._files
                    and child not in self._directories
                    and child not in self._observed_directories
                ):
                    continue
                visible.add(name)
            return sorted(visible)

        def read(self, path: str) -> bytes:
            """Read planned bytes, else the first authenticated physical capture.

            Returns:
                The file bytes.

            Raises:
                FileNotFoundError: The path is hidden by a planned deletion.

            """
            resolved = self._resolved(path)
            if resolved in self._files:
                return self._files[resolved]
            if resolved in self._hidden:
                raise FileNotFoundError(path)
            content = self.source_state(resolved).content
            if content is None:
                raise FileNotFoundError(path)
            return content

        def source_state(
            self, path: Path, *, required: bool = True
        ) -> m.Cli.AtomicFileState:
            """Retain the physical witness shared by source reads and publication.

            Returns:
                The first observed physical state, including declared plan inputs.

            Raises:
                FileNotFoundError: A required source was absent in this view.
                ValueError: An unobserved source is requested or appeared on disk.

            """
            resolved = self._resolved(str(path))
            if resolved not in self._states:
                if required and self._captured_source(resolved):
                    message = f"source is outside the captured observation: {resolved}"
                    raise ValueError(message)
                state = u.Cli.atomic_read_binary_file_state(
                    resolved, required=required
                ).unwrap()
                if self._captured_source(resolved) and state.content is not None:
                    message = (
                        f"uncaptured source appeared in the source scope: {resolved}"
                    )
                    raise ValueError(message)
                self._record_observation(state)
            observed = self._states[resolved]
            if required and observed.content is None:
                raise FileNotFoundError(path)
            return observed

        def children(self, path: str) -> tuple[Path, ...]:
            """Return the direct child paths of a directory.

            Returns:
                The child paths in lexical order.

            """
            return tuple(Path(path) / name for name in self.listdir(path))

    class OverlayChangeIndicator(ChangeIndicator):
        """Observe overlaid content instead of live filesystem metadata."""

        def __init__(self, files: FlextInfraRopeProject.OverlayFiles) -> None:
            self._files = files

        @override
        def get_indicator(
            self,
            resource: File | Folder,
        ) -> tuple[bool, bytes | tuple[Path, ...]]:
            """Return the overlaid bytes or membership of a resource.

            Returns:
                The file-kind flag and its bytes or directory membership.

            Raises:
                ResourceNotFoundError: The resource is absent from the view.

            """
            path = resource.real_path
            if self._files.isfile(path):
                return True, self._files.read(path)
            if self._files.isdir(path):
                return False, self._files.children(path)
            msg = f"Resource <{resource.path}> is absent from the overlaid view"
            raise ResourceNotFoundError(msg)

    def source_state(
        self, path: Path, *, required: bool = True
    ) -> m.Cli.AtomicFileState:
        """Observe the source view's physical publication witness.

        Returns:
            The captured physical state for an overlay, or the live project state.

        """
        files = self.fscommands
        if isinstance(files, self.OverlayFiles):
            return files.source_state(path, required=required)
        return u.Cli.atomic_read_binary_file_state(path, required=required).unwrap()

    @property
    def source_plans(self) -> tuple[m.Infra.CodegenFilePlan, ...]:
        """Expose the current candidate without copying its original witnesses.

        Returns:
            The plans owned by the active source view.

        Raises:
            TypeError: The project does not own an authenticated overlay.

        """
        files = self.fscommands
        if not isinstance(files, self.OverlayFiles):
            msg = "source plans require an authenticated source overlay"
            raise TypeError(msg)
        return files.plans

    @contextmanager
    def source_view(
        self,
        *,
        declared_files: tuple[m.Infra.CodegenFilePlan, ...] | None = (),
        additional_source_folders: tuple[str, ...] | None = (),
    ) -> Generator[Self]:
        """Bind one candidate and restore the entry view without disk effects.

        Synchronous nested bindings retain their own entry view. Another thread
        cannot replace a candidate while its native objects are being consumed.
        Physical preimages stay unchanged across every logical view transition.
        ``None`` retains the entry plans or roots while acquiring the same
        barrier, so preparing a nested candidate cannot observe another thread.

        Yields:
            This same native project reading the bound candidate.

        Raises:
            TypeError: The project lacks its authenticated overlay.
            RuntimeError: Another thread owns the active source view.

        """
        files = self.fscommands
        if not isinstance(files, self.OverlayFiles):
            msg = "candidate binding requires an authenticated source overlay"
            raise TypeError(msg)
        if not self._source_view_lock.acquire(blocking=False):
            msg = "another thread owns this native source view"
            raise RuntimeError(msg)
        previous = files.plans
        folders = tuple(self._custom_source_folders)
        frozen = self._frozen_folders
        try:
            self._set_source_view(
                previous if declared_files is None else declared_files,
                tuple(folder.path for folder in folders)
                if additional_source_folders is None
                else additional_source_folders,
            )
            yield self
        finally:
            primary = sys.exception()
            try:
                self._set_source_view(
                    previous, tuple(folder.path for folder in folders)
                )
                self._custom_source_folders = list(folders)
                self._frozen_folders = frozen
            except BaseException as restore_failure:
                if primary is None or (
                    isinstance(primary, SystemExit)
                    and (primary.code is None or primary.code == 0)
                ):
                    raise
                primary.add_note(
                    f"candidate source restoration failed: {restore_failure!r}"
                )
            finally:
                self._source_view_lock.release()

    def _set_source_view(
        self,
        plans: tuple[m.Infra.CodegenFilePlan, ...],
        folders: tuple[str, ...],
    ) -> None:
        """Evolve source deltas before notifying native resource observers.

        Raises:
            TypeError: The project has no authenticated source overlay.
            ValueError: The project has no declared source election.

        """
        files = self.fscommands
        if not isinstance(files, self.OverlayFiles):
            msg = "candidate transition requires an authenticated source overlay"
            raise TypeError(msg)
        election = self._source_election
        if election is None:
            msg = "candidate transition requires its declared source election"
            raise ValueError(msg)
        root = Path(self.root.real_path)
        self._validate_source_folders(root, folders, plans)
        previous_directories = files.directory_membership
        changed = files.replace(plans)
        selected = tuple(sorted({*election.source_folders, *folders}))
        files.select_source_roots((root, *(root / folder for folder in selected)))
        changed_folders = selected != tuple(
            folder.path for folder in self._custom_source_folders
        )
        self._custom_source_folders = [self.get_folder(path) for path in selected]
        if self._frozen_folders is not None:
            python_paths = self._frozen_folders[1]
            self._frozen_folders = None
            self._frozen_folders = (self.get_source_folders(), python_paths)
        self._notify_source_changes(changed, previous_directories)
        if changed_folders or any(before != after for _, before, after in changed):
            self._refresh_source_finders()
            # Roots and membership change this project's resolver epoch even
            # when no cached resource changed. Native imported-module and MRO
            # conclusions belong to that epoch; retaining their ASTs is safe,
            # retaining those conclusions is not. Relative lookups need this
            # too, although they are absent from the absolute finder memo.
            FlextInfraUtilitiesRopeRuntime.project_core(
                self
            ).module_cache.forget_all_data()

    def _source_resource(self, path: Path, *, folder: bool) -> File | Folder:
        """Elect local or external resources through this overlay's owners.

        Returns:
            The native resource, including absent candidate resources.

        Raises:
            TypeError: The external resolver lost its authenticated owner.

        """
        root = Path(self.root.real_path)
        if path.is_relative_to(root):
            relative = "" if path == root else path.relative_to(root).as_posix()
            resource = self.get_folder(relative) if folder else self.get_file(relative)
        else:
            external = self.external_project
            if not isinstance(external, NoProject):
                msg = "candidate resource has no authenticated external resolver"
                raise TypeError(msg)
            resolver = cast("p.Infra.RopeExternalResourceOwner", external)
            resource = (
                resolver.get_folder(str(path))
                if folder
                else resolver.get_file(str(path))
            )
        if not isinstance(resource, File | Folder):
            msg = "candidate resolver returned a non-resource"
            raise TypeError(msg)
        return resource

    def _notify_source_changes(
        self,
        changed: tuple[tuple[Path, bool, bool], ...],
        previous_directories: frozenset[Path],
    ) -> None:
        """Report candidate membership and content changes through native APIs.

        Raises:
            TypeError: The overlaid view lacks an authenticated source overlay,
                or a resolver returned a non-resource.

        """
        files = self.fscommands
        if not isinstance(files, self.OverlayFiles):
            msg = "candidate notifications require an authenticated source overlay"
            raise TypeError(msg)
        current_directories = files.directory_membership
        removed = {
            path
            for path in previous_directories - current_directories
            if not path.is_dir()
        }
        removed_roots = tuple(
            sorted(path for path in removed if path.parent not in removed)
        )
        created = sorted(
            (
                path
                for path in current_directories - previous_directories
                if not path.is_dir()
            ),
            key=lambda path: len(path.parts),
        )
        for observer in self.observers:
            for path in removed_roots:
                observer.resource_removed(self._source_resource(path, folder=True))
            for path in created:
                observer.resource_created(self._source_resource(path, folder=True))
            for path, before, after in changed:
                if any(path.is_relative_to(parent) for parent in removed_roots):
                    continue
                resource = self._source_resource(path, folder=False)
                if not after:
                    observer.resource_removed(resource)
                elif not before:
                    observer.resource_created(resource)
                else:
                    observer.resource_changed(resource)

    def _refresh_source_finders(self) -> None:
        """Re-elect memoized native lookups after membership or root changes.

        No parsed-module cache is cleared. Negative lookups are reconsidered
        through Rope's own resolver, and unchanged resource elections remain.

        Raises:
            TypeError: The native resolver returns a non-resource.

        """
        memo = self._frozen_modules
        if memo is None:
            return
        for name, folder_name in tuple(memo):
            folder: Folder | None = None
            if folder_name is not None:
                path = Path(folder_name)
                resource = self._source_resource(
                    path if path.is_absolute() else Path(self.root.real_path) / path,
                    folder=True,
                )
                if not isinstance(resource, Folder):
                    msg = "module lookup context is not a native folder"
                    raise TypeError(msg)
                folder = resource
            memo[name, folder_name] = self.find_module_native(name, folder)

    def source_query(
        self, path: Path, predicate: Literal["exists", "isfile", "isdir"]
    ) -> bool:
        """Query the overlaid view.

        Returns:
            Whether the predicate holds for the path.

        """
        files = self.fscommands
        return {
            "exists": files.exists,
            "isfile": files.isfile,
            "isdir": files.isdir,
        }[predicate](str(path))

    def source_children(self, path: Path) -> tuple[Path, ...]:
        """Enumerate the direct children of a directory in the overlaid view.

        Returns:
            The child paths in lexical order.

        """
        files = self.fscommands
        return tuple(path / name for name in files.listdir(str(path)))

    def source_text(self, path: Path) -> str:
        """Read decoded source text from the overlaid view.

        Returns:
            The decoded text.

        """
        return self.source_bytes(path).decode(c.DEFAULT_ENCODING)

    def source_bytes(self, path: Path) -> bytes:
        """Read source bytes from the overlaid view.

        Returns:
            The source bytes.

        """
        files = self.fscommands
        return files.read(str(path))

    def source_walk(self, path: Path) -> Generator[tuple[Path, list[str], list[str]]]:
        """Walk the overlaid view top-down, keeping aliases as candidates.

        Python-named aliases stay files; elsewhere an alias is a directory
        candidate, except unrelated top-level aliases of a project lookup
        anchor, which stay files.

        Yields:
            ``(directory, directories, files)`` tuples in traversal order.

        """
        lookup_anchor = path not in {
            path / root for root in config.Infra.source_scan.roots
        } and (
            path == Path(self.root.real_path)
            or self.source_query(path / c.PYPROJECT_FILENAME, "isfile")
        )
        source_names = frozenset(
            Path(root).parts[0]
            for root in config.Infra.source_scan.roots
            if Path(root).parts
        )
        files_view = self.fscommands
        source_traversal = isinstance(files_view, self.OverlayFiles) and (
            files_view.source_member(path)
        )
        pending = [path]
        while pending:
            directory = pending.pop()
            directories: list[str] = []
            files: list[str] = []
            for child in self.source_children(directory):
                if (
                    isinstance(files_view, self.OverlayFiles)
                    and source_traversal
                    and not files_view.source_member(child)
                ):
                    continue
                if isinstance(files_view, self.OverlayFiles) and (
                    files_view.captured_directory(str(child))
                ):
                    directories.append(child.name)
                elif child.is_symlink():
                    if child.suffix in c.Infra.PYTHON_SOURCE_SUFFIXES or (
                        directory == path
                        and lookup_anchor
                        and child.name not in source_names
                    ):
                        files.append(child.name)
                    else:
                        directories.append(child.name)
                elif self.source_query(child, "isdir"):
                    directories.append(child.name)
                else:
                    files.append(child.name)
            yield directory, directories, files
            pending.extend(directory / name for name in reversed(directories))

    _source_election: p.Infra.RopeProjectElection | None = None

    def __init__(
        self,
        projectroot: str | PathLike[str],
        fscommands: p.Infra.RopeProjectFiles | None = None,
        ropefolder: str | None = ".ropeproject",
        external_project: p.Infra.RopeResourceOwner | None = None,
        **prefs: bool | Sequence[str],
    ) -> None:
        """Initialize the native project over its filesystem view.

        Args:
            projectroot: The root directory of the existing project.
            fscommands: The filesystem view, or ``None`` for the live tree.
            ropefolder: Native state folder, or ``None`` for a read-only view.
            external_project: Resource owner for external Python modules.
            prefs: Native project preferences.

        Raises:
            ValueError: The root is absent or the constructor changed its view.

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
            message = f"Rope constructor changed its filesystem view: {root}"
            raise ValueError(message)

    @classmethod
    def from_atomic_reads(
        cls,
        live: p.Infra.RopeProject,
        *,
        election: p.Infra.RopeProjectElection,
        declared_files: tuple[m.Infra.CodegenFilePlan, ...] = (),
        observations: tuple[m.Cli.AtomicFileState, ...] | None = None,
        additional_source_folders: tuple[str, ...] = (),
    ) -> Self:
        """Bind authenticated reads to the existing native analysis project.

        ``additional_source_folders`` elect live or virtual import roots inside
        the project. Live roots retain their native directory identity; a
        virtual root must hold declared planned content.
        ``observations`` retain read authority independently of publication
        policy; observing a stub does not declare a stub file effect.
        The caller injects this class's overlay before native initialization,
        so preference election and candidate reads share their first witnesses.

        Returns:
            The same project, core and observers reading the bound candidate.

        Raises:
            TypeError: Native initialization did not retain its source owner.

        """
        if not isinstance(live, cls) or not isinstance(
            live.fscommands, cls.OverlayFiles
        ):
            message = "atomic source binding requires its original overlaid project"
            raise TypeError(message)
        root = Path(live.root.real_path)
        cls._validate_source_folders(root, additional_source_folders, declared_files)
        files = live.fscommands
        if observations is not None:
            for state in observations:
                files._record_observation(state)
            files._closed_observations = True
        files._dependency_roots = tuple(
            files._resolved(folder) for folder in election.python_path_folders
        )
        selected = m.Infra.RopeProjectElection(
            source_folders=tuple(
                sorted({*election.source_folders, *additional_source_folders})
            ),
            ignored_resources=tuple(election.ignored_resources),
            extension_modules=tuple(election.extension_modules),
            python_path_folders=tuple(election.python_path_folders),
        )
        external = NoProject(fscommands=files)
        external.prefs.extension_modules = list(selected.extension_modules)
        if not isinstance(external, p.Infra.RopeExternalResourceOwner):
            message = "native external resolver lost its resource factory contract"
            raise TypeError(message)
        live.external_project = external
        live._snapshot_python_path_folders = [
            live._native_folder(external.get_folder(path))
            for path in selected.python_path_folders
        ]
        preferences = live.get_prefs()
        if not isinstance(preferences, p.Infra.RopePreferences):
            message = "native source project lost its preference update contract"
            raise TypeError(message)
        preferences.set("ignored_resources", list(selected.ignored_resources))
        preferences.set("extension_modules", list(selected.extension_modules))
        preferences.set("source_folders", list(selected.source_folders))
        live._ropefolder_name = None
        live._source_election = selected
        live._set_source_view(declared_files, ())
        return live

    @staticmethod
    def _validate_source_folders(
        root: Path,
        folders: tuple[str, ...],
        plans: tuple[m.Infra.CodegenFilePlan, ...],
    ) -> None:
        """Reject roots without physical or proposed source membership.

        Raises:
            ValueError: A source root escapes the project or has no candidate file.

        """
        for entry in folders:
            relative = Path(entry)
            folder = "" if relative.as_posix() == "." else relative.as_posix()
            candidate = root / relative
            if (
                folder != (relative.as_posix() if relative.parts else "")
                or relative.is_absolute()
                or ".." in relative.parts
                or (
                    not candidate.is_dir()
                    and not any(
                        plan.desired_content is not None
                        and plan.path.is_relative_to(candidate)
                        for plan in plans
                    )
                )
            ):
                msg = f"Rope virtual source root lacks a planned file: {folder}"
                raise ValueError(msg)

    @override
    def _init_other_parts(self) -> None:
        """Initialize the native core and its overlaid resource observations."""
        super()._init_other_parts()
        self._source_view_lock = RLock()
        if isinstance(self.fscommands, self.OverlayFiles):
            core = FlextInfraUtilitiesRopeRuntime.project_core(self)
            core.observer.timekeeper = self.OverlayChangeIndicator(self.fscommands)


__all__: list[str] = ["FlextInfraRopeProject"]
