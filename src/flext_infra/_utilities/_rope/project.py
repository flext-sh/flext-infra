"""Rope project over the live tree with planned sources overlaid in memory.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import csv
import sys
from collections.abc import Generator, Mapping, Sequence
from contextlib import contextmanager
from functools import lru_cache
from importlib import metadata
from importlib.machinery import EXTENSION_SUFFIXES
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
from flext_infra._utilities._rope import (
    FlextInfraRopeNativeProject,
    FlextInfraUtilitiesRopeRuntime,
)


class FlextInfraRopeProject(FlextInfraRopeNativeProject):
    """Native Rope project whose reads see planned sources before the disk."""

    _source_view_lock: RLock

    @override
    @contextmanager
    def frozen_layout(self) -> Generator[Self]:
        """Keep alias queries within this read-only pass's native source epoch.

        Yields:
            This project with its native layout and lexical index bound together.

        """
        with (
            super().frozen_layout(),
            FlextInfraUtilitiesRopeRuntime.annotation_alias_context(),
        ):
            yield self

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
            plans: tuple[p.Infra.CodegenFilePlan, ...],
            *,
            observations: tuple[p.Cli.AtomicFileState, ...] | None = None,
            source_roots: tuple[Path, ...] = (),
            dependency_roots: tuple[Path, ...] = (),
            captures: tuple[
                dict[str, Path],
                dict[Path, p.Cli.AtomicFileState],
                dict[Path, set[str]],
                set[Path],
                bool,
            ]
            | None = None,
        ) -> None:
            """Pin captured reads before admitting declared source effects.

            ``None`` selects native first-read observation. An explicit tuple,
            including an empty tuple, selects a closed source observation.
            ``captures`` shares another view's first-read witnesses (see
            ``derive``); ``None`` starts an independent capture.

            """
            self._physical: dict[str, Path] = {}
            self._states: dict[Path, p.Cli.AtomicFileState] = {}
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
            self.plans: tuple[p.Infra.CodegenFilePlan, ...] = ()
            self.analysis: Mapping[Path, bytes] = {}
            if captures is not None:
                (
                    self._physical,
                    self._states,
                    self._observed_children,
                    self._observed_directories,
                    self._closed_observations,
                ) = captures
            for state in observations if observations is not None else ():
                self._record_observation(state)
            self.replace(plans)

        @property
        def captures(
            self,
        ) -> tuple[
            dict[str, Path],
            dict[Path, p.Cli.AtomicFileState],
            dict[Path, set[str]],
            set[Path],
            bool,
        ]:
            """The first-read witnesses a derived view shares by reference.

            Returns:
                Physical identities, captured states, observed membership and
                whether the observation is closed.

            """
            return (
                self._physical,
                self._states,
                self._observed_children,
                self._observed_directories,
                self._closed_observations,
            )

        def _record_observation(self, state: p.Cli.AtomicFileState) -> None:
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

        def bind_reads(
            self,
            *,
            observations: tuple[p.Cli.AtomicFileState, ...] | None,
            dependency_roots: tuple[str, ...],
        ) -> None:
            """Close captured reads, then pin the elected dependency roots.

            ``None`` keeps native first-read observation open; an explicit
            tuple, including an empty tuple, closes the source observation.

            """
            if observations is not None:
                for state in observations:
                    self._record_observation(state)
                self._closed_observations = True
            self._dependency_roots = tuple(
                self._resolved(folder) for folder in dependency_roots
            )
            self._elect_root_owners()

        def derive(self) -> FlextInfraRopeProject.OverlayFiles:
            """Open a plan-free view over this view's physical witnesses.

            The derived view shares the first-read captures, their directory
            membership and path identities, so every view of one authority
            reads the same bytes and a later disk edit remains a conflict in
            all of them. Planned effects stay private to each view.

            Returns:
                A distinct view without planned effects.

            """
            return type(self)(
                (),
                source_roots=self._source_roots,
                dependency_roots=self._dependency_roots,
                captures=self.captures,
            )

        def select_source_roots(self, roots: tuple[Path, ...]) -> None:
            """Use the native election's current source roots for captured reads."""
            self._source_roots = tuple(self._resolved(str(path)) for path in roots)
            self._elect_root_owners()

        def _elect_root_owners(self) -> None:
            """Elect the most specific source or dependency root per lookup."""
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
            return self._elected_source_owner(path)

        def source_owned(self, path: Path) -> bool:
            """Answer whether the project's elected source roots own a path.

            Dependency roots elected from the Python path are lookup roots
            only: a module they own is never an edit target of this project.

            Returns:
                Whether the most specific elected root is a source root.

            """
            return self._elected_source_owner(self._resolved(str(path)))

        def _elected_source_owner(self, path: Path) -> bool:
            """Elect the most specific source or dependency root for a physical path.

            Source ownership wins a tie, including editable paths also present
            on the Python path.

            Returns:
                Whether the electing root is a source root.

            """
            return next(
                (
                    source
                    for root, source in self._root_owners
                    if path.is_relative_to(root)
                ),
                False,
            )

        def replace(
            self,
            plans: tuple[p.Infra.CodegenFilePlan, ...],
            analysis: Mapping[Path, bytes] | None = None,
        ) -> tuple[tuple[Path, bool, bool], ...]:
            """Change only candidate deltas, retaining authenticated preimages.

            ``analysis`` binds read-only bytes over existing dependency files:
            native resolution reads them, but they never join ``plans`` and so
            never reach publication. ``None`` declares no analysis view.

            Returns:
                Changed source paths and their preceding/following existence.

            """
            views = self._analysis_views(analysis)
            selected = self._selected_plans(plans, views)
            for plan in selected.values():
                self._record_observation(plan.before)
            changed: list[tuple[Path, bool, bool]] = []
            for path in sorted(
                self._files.keys() | self._hidden | selected.keys() | views.keys()
            ):
                previous = (
                    self._files[path]
                    if path in self._files
                    else None
                    if path in self._hidden
                    else self._states[path].content
                )
                plan = selected.get(path)
                following = (
                    views[path]
                    if path in views
                    else self._states[path].content
                    if plan is None
                    else plan.desired_content
                )
                if previous != following:
                    changed.append((path, previous is not None, following is not None))
                self._overlay_path(
                    path,
                    following,
                    overlaid=plan is not None or path in views,
                    hidden=plan is not None and following is None,
                )
            self.plans = plans
            self.analysis = views
            return tuple(changed)

        def _overlay_path(
            self,
            path: Path,
            following: bytes | None,
            *,
            overlaid: bool,
            hidden: bool,
        ) -> None:
            """Apply one path's following bytes, membership and hidden state."""
            if path in self._files and (not overlaid or following is None):
                del self._files[path]
                self._remove_membership(path)
            if overlaid and following is not None:
                if path not in self._files:
                    self._add_membership(path)
                self._files[path] = following
            if hidden:
                self._hidden.add(path)
            else:
                self._hidden.discard(path)

        def _analysis_views(
            self, analysis: Mapping[Path, bytes] | None
        ) -> dict[Path, bytes]:
            """Admit read-only analysis bytes that shadow no owned source.

            Returns:
                The resolved analysis view of each supplied path.

            Raises:
                ValueError: An analysis view shadows an owned source.

            """
            views: dict[Path, bytes] = {}
            for supplied, content in (analysis or {}).items():
                path = self._resolved(str(supplied))
                if self._elected_source_owner(path):
                    msg = f"analysis view cannot shadow an owned source: {path}"
                    raise ValueError(msg)
                self.source_state(path)
                views[path] = content
            return views

        def _selected_plans(
            self,
            plans: tuple[p.Infra.CodegenFilePlan, ...],
            views: Mapping[Path, bytes],
        ) -> dict[Path, p.Infra.CodegenFilePlan]:
            """Select one consistent candidate plan per physical path.

            Returns:
                Each resolved path with its single declared plan.

            Raises:
                ValueError: A plan disagrees with a retained witness or another
                    plan for the same path, or an analysis view shadows it.

            """
            selected: dict[Path, p.Infra.CodegenFilePlan] = {}
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
                if path in views:
                    msg = f"analysis view shadows a declared plan: {path}"
                    raise ValueError(msg)
                selected[path] = plan
            return selected

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
        ) -> p.Cli.AtomicFileState:
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
    ) -> p.Cli.AtomicFileState:
        """Observe the source view's physical publication witness.

        Returns:
            The captured physical state for an overlay, or the live project state.

        """
        files = self.fscommands
        if isinstance(files, self.OverlayFiles):
            return files.source_state(path, required=required)
        return u.Cli.atomic_read_binary_file_state(path, required=required).unwrap()

    @property
    def source_plans(self) -> tuple[p.Infra.CodegenFilePlan, ...]:
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

    def source_owned(self, path: Path) -> bool:
        """Separate this project's own sources from its dependency lookup roots.

        A project reading the native tree elects the same owners from Rope's
        own folders: its root and source folders own, its Python-path
        folders are dependency lookup roots.

        Returns:
            Whether an elected source root, not a Python-path dependency
            root, owns the physical path.

        """
        files = self.fscommands
        if not isinstance(files, self.OverlayFiles):
            files = self.OverlayFiles(
                (),
                source_roots=(
                    Path(self.root.real_path),
                    *(Path(folder.real_path) for folder in self.get_source_folders()),
                ),
                dependency_roots=tuple(
                    Path(folder.real_path) for folder in self.get_python_path_folders()
                ),
            )
        return files.source_owned(path)

    @contextmanager
    def source_view(
        self,
        *,
        declared_files: tuple[p.Infra.CodegenFilePlan, ...] | None = (),
        additional_source_folders: tuple[str, ...] | None = (),
        analysis_files: Mapping[Path, str] | None = None,
    ) -> Generator[Self]:
        """Bind one candidate and restore the entry view without disk effects.

        Synchronous nested bindings retain their own entry view. Another thread
        cannot replace a candidate while its native objects are being consumed.
        Physical preimages stay unchanged across every logical view transition.
        ``None`` retains the entry plans or roots while acquiring the same
        barrier, so preparing a nested candidate cannot observe another thread.
        ``analysis_files`` binds read-only dependency sources that native
        resolution reads but publication never sees; ``None`` retains the
        entry analysis view.

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
        previous_analysis = files.analysis
        folders = tuple(self._custom_source_folders)
        frozen = self._frozen_folders
        try:
            self._set_source_view(
                previous if declared_files is None else declared_files,
                tuple(folder.path for folder in folders)
                if additional_source_folders is None
                else additional_source_folders,
                previous_analysis
                if analysis_files is None
                else {
                    path: source.encode(c.DEFAULT_ENCODING)
                    for path, source in analysis_files.items()
                },
            )
            with FlextInfraUtilitiesRopeRuntime.annotation_alias_context():
                yield self
        finally:
            primary = sys.exception()
            try:
                self._set_source_view(
                    previous,
                    tuple(folder.path for folder in folders),
                    previous_analysis,
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
        plans: tuple[p.Infra.CodegenFilePlan, ...],
        folders: tuple[str, ...],
        analysis: Mapping[Path, bytes] | None,
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
        changed = files.replace(plans, analysis)
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
        changed_epoch = changed_folders or any(
            before != after for _, before, after in changed
        )
        if changed_epoch:
            FlextInfraUtilitiesRopeRuntime.invalidate_annotation_alias_indices()
        self._notify_source_changes(changed, previous_directories)
        if changed_epoch:
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

    @staticmethod
    @lru_cache(maxsize=c.Infra.CONTENT_CACHE_MAXSIZE)
    def _distribution_extension_modules(
        state: tuple[tuple[str, int], ...],
    ) -> tuple[str, ...]:
        """Derive the compiled modules the installed distributions declare.

        Rope sees a compiled module only through its ``extension_modules``
        preference. Each distribution on the Python path declares its files
        in its own metadata; a file carrying an interpreter extension suffix
        is a compiled module, named by its folder-relative dotted path. The
        key is each folder with its modification time, so an install or
        removal is a new key, never a stale election.

        Returns:
            The dotted compiled-module names in deterministic order.

        """
        suffixes = sorted(EXTENSION_SUFFIXES, key=len, reverse=True)
        names: set[str] = set()
        for distribution in metadata.distributions(
            path=[folder for folder, _ in state]
        ):
            record = distribution.read_text("RECORD")
            if record is not None and not any(suffix in record for suffix in suffixes):
                continue
            declared = (
                (row[0] for row in csv.reader(record.splitlines()))
                if record is not None
                else (file.as_posix() for file in distribution.files or ())
            )
            for spelled in declared:
                suffix = next(
                    (item for item in suffixes if spelled.endswith(item)), None
                )
                if suffix is None:
                    continue
                parts = spelled.removesuffix(suffix).split("/")
                if all(part.isidentifier() for part in parts) and (
                    distribution.locate_file(spelled).exists()
                ):
                    names.add(".".join(parts))
        return tuple(sorted(names))

    def __init__(
        self,
        projectroot: str | PathLike[str],
        fscommands: p.Infra.RopeProjectFiles | None = None,
        external_project: p.Infra.RopeResourceOwner | None = None,
        **prefs: bool | Sequence[str],
    ) -> None:
        """Initialize the native project over its filesystem view.

        Args:
            projectroot: The root directory of the existing project.
            fscommands: The filesystem view, or ``None`` for the live tree.
            external_project: Resource owner for external Python modules.
            prefs: Native project preferences.

        Raises:
            ValueError: The root is absent or the constructor changed its view.
            TypeError: The ``python_path`` preference is not a folder sequence.

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
            python_path = prefs.get("python_path", ())
            if isinstance(python_path, bool):
                message = "Rope python_path preference must be a folder sequence"
                raise TypeError(message)
            # Rope's own lookup order: preference folders, then ``sys.path``.
            folders = tuple(
                folder
                for entry in (*python_path, *sys.path)
                if (folder := Path(entry).resolve()).is_dir()
            )
            prefs["extension_modules"] = tuple(
                sorted({
                    *(
                        name
                        for name in tuple(sys.modules)
                        if name.partition(".")[0] in sys.stdlib_module_names
                        and (module := sys.modules.get(name)) is not None
                        and module.__spec__ is not None
                        and module.__spec__.origin in {"built-in", "frozen"}
                    ),
                    *FlextInfraRopeProject._distribution_extension_modules(
                        tuple(
                            dict.fromkeys(
                                (str(folder), folder.stat().st_mtime_ns)
                                for folder in folders
                            )
                        )
                    ),
                })
            )
        initializer: p.Infra.RopeProjectInitializer = Project.__dict__["__init__"]
        # FLEXT supplies every preference; the checkout's pyproject is planned
        # data under repair, never a Rope configuration source.
        initializer(
            self,
            root,
            fscommands=fscommands,
            # FLEXT keeps no Rope state: Rope's documented ``None`` folder
            # disables every data file, so no repository root receives one.
            ropefolder=None,
            external_project=external_project,
            config_files=False,
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
        declared_files: tuple[p.Infra.CodegenFilePlan, ...] = (),
        observations: tuple[p.Cli.AtomicFileState, ...] | None = None,
        additional_source_folders: tuple[str, ...] = (),
    ) -> Self:
        """Bind authenticated reads to an overlaid view of ``live``'s tree.

        ``additional_source_folders`` elect live or virtual import roots inside
        the project. Live roots retain their native directory identity; a
        virtual root must hold declared planned content.
        ``observations`` retain read authority independently of publication
        policy; observing a stub does not declare a stub file effect.
        Every call opens a distinct project, so two snapshots of one ``live``
        project are independent views and closing one never closes ``live``.
        A ``live`` project initialized over this class's overlay lends the
        snapshot its captured physical witnesses, so preference election and
        candidate reads share their first reads; a ``live`` project reading
        the native tree contributes only its root and election.

        Returns:
            A new overlaid project reading the bound candidate; the caller owns
            closing it.

        """
        root = Path(live.root.real_path)
        cls._validate_source_folders(root, additional_source_folders, declared_files)
        files = (
            live.fscommands.derive()
            if isinstance(live.fscommands, cls.OverlayFiles)
            else cls.OverlayFiles(
                (),
                source_roots=(
                    root,
                    *(root / folder for folder in election.source_folders),
                    *(root / folder for folder in additional_source_folders),
                ),
                dependency_roots=tuple(
                    Path(folder) for folder in election.python_path_folders
                ),
            )
        )
        snapshot = cls(
            root,
            fscommands=files,
            save_objectdb=False,
            save_history=False,
            ignored_resources=list(election.ignored_resources),
            extension_modules=list(election.extension_modules),
            source_folders=list(election.source_folders),
        )
        return snapshot.bind_atomic_reads(
            election=election,
            declared_files=declared_files,
            observations=observations,
            additional_source_folders=additional_source_folders,
        )

    def bind_atomic_reads(
        self,
        *,
        election: p.Infra.RopeProjectElection,
        declared_files: tuple[p.Infra.CodegenFilePlan, ...] = (),
        observations: tuple[p.Cli.AtomicFileState, ...] | None = None,
        additional_source_folders: tuple[str, ...] = (),
    ) -> Self:
        """Bind authenticated reads to this overlaid native analysis project.

        Returns:
            This project, core and observers reading the bound candidate.

        Raises:
            TypeError: Native initialization did not retain its source owner.

        """
        files = self.fscommands
        if not isinstance(files, self.OverlayFiles):
            message = "atomic source binding requires its original overlaid project"
            raise TypeError(message)
        root = Path(self.root.real_path)
        self._validate_source_folders(root, additional_source_folders, declared_files)
        files.bind_reads(
            observations=observations,
            dependency_roots=tuple(election.python_path_folders),
        )
        selected = m.Infra.RopeProjectElection(
            preferred_import_style=election.preferred_import_style,
            source_folders=tuple(
                sorted({*election.source_folders, *additional_source_folders})
            ),
            ignored_resources=tuple(election.ignored_resources),
            extension_modules=tuple(election.extension_modules),
            python_path_folders=tuple(election.python_path_folders),
        )
        external = NoProject(fscommands=files)
        external.prefs.extension_modules = list(selected.extension_modules)
        self.external_project = external
        self._snapshot_python_path_folders = [
            self._native_folder(external.get_folder(path))
            for path in selected.python_path_folders
        ]
        preferences = self.get_prefs()
        preferences.imports.preferred_import_style = selected.preferred_import_style
        preferences.set("ignored_resources", value=list(selected.ignored_resources))
        preferences.set("extension_modules", value=list(selected.extension_modules))
        preferences.set("source_folders", value=list(selected.source_folders))
        self._source_election = selected
        self._set_source_view(declared_files, (), None)
        return self

    @staticmethod
    def _validate_source_folders(
        root: Path,
        folders: tuple[str, ...],
        plans: tuple[p.Infra.CodegenFilePlan, ...],
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
