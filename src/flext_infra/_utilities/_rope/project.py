"""Rope project over the live tree with planned sources overlaid in memory.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from collections.abc import Generator, Mapping
from os import PathLike
from os.path import realpath
from pathlib import Path
from typing import Literal, Protocol, Self, cast, override

from flext_cli import u
from rope.base.exceptions import ResourceNotFoundError
from rope.base.project import NoProject, Project
from rope.base.resourceobserver import ChangeIndicator
from rope.base.resources import File, Folder

from flext_infra import c, config, m, p, t
from flext_infra._utilities._rope import FlextInfraRopeNativeProject
from flext_infra._utilities.rope_runtime import FlextInfraUtilitiesRopeRuntime


class FlextInfraRopeProject(FlextInfraRopeNativeProject):
    """Native Rope project whose reads see planned sources before the disk."""

    class OverlayFiles:
        """Read-only filesystem view: planned bytes overlay the live tree.

        A planned ``None`` hides a live file; directories holding planned
        files exist even before publication creates them.
        """

        def __init__(self, overlay: Mapping[Path, bytes | None]) -> None:
            self._physical: dict[str, Path] = {}
            self._files = {
                Path(realpath(path)): content
                for path, content in overlay.items()
                if content is not None
            }
            self._hidden = frozenset(
                Path(realpath(path))
                for path, content in overlay.items()
                if content is None
            )
            self._directories = frozenset(
                parent for path in self._files for parent in path.parents
            )
            # Every planned path's ancestors are planned directories, so the
            # first component below any directory is one of its direct planned
            # children: index them once instead of scanning per listing.
            children: dict[Path, set[str]] = {}
            for planned in (*self._files, *self._directories):
                if planned.parent != planned:
                    children.setdefault(planned.parent, set()).add(planned.name)
            self._planned_children: Mapping[Path, frozenset[str]] = {
                parent: frozenset(names) for parent, names in children.items()
            }

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
            """Report planned files and visible live files.

            Returns:
                Whether the path is a file in the overlaid view.

            """
            resolved = self._resolved(path)
            if resolved in self._files:
                return True
            return resolved not in self._hidden and resolved.is_file()

        def isdir(self, path: str) -> bool:
            """Report planned parents and live directories.

            Returns:
                Whether the path is a directory in the overlaid view.

            """
            resolved = self._resolved(path)
            return resolved in self._directories or resolved.is_dir()

        def listdir(self, path: str) -> list[str]:
            """List live entries plus planned children, minus hidden files.

            Returns:
                The sorted child names.

            """
            resolved = self._resolved(path)
            names = {
                child.name
                for child in (resolved.iterdir() if resolved.is_dir() else ())
                if child not in self._hidden
            }
            names.update(self._planned_children.get(resolved, ()))
            return sorted(names)

        def read(self, path: str) -> bytes:
            """Read planned bytes, else the live file.

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
            return resolved.read_bytes()

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
        ) -> t.Pair[bool, bytes | tuple[Path, ...]]:
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

    @staticmethod
    def source_state(path: Path, *, required: bool = True) -> m.Cli.AtomicFileState:
        """Observe the live destination state used as a publication guard.

        Returns:
            The live physical state of the file.

        """
        return u.Cli.atomic_read_binary_file_state(path, required=required).unwrap()

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
        pending = [path]
        while pending:
            directory = pending.pop()
            directories: list[str] = []
            files: list[str] = []
            for child in self.source_children(directory):
                if child.is_symlink():
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
        **prefs: bool | t.StrSequence,
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
        additional_source_folders: tuple[str, ...] = (),
    ) -> Self:
        """Build a read-only project over ``live``'s tree with planned sources.

        ``additional_source_folders`` elect live or virtual import roots inside
        the project. Live roots retain their native directory identity; a
        virtual root must hold declared planned content.

        Returns:
            The project reading planned sources before the live tree.

        Raises:
            ValueError: A virtual root is noncanonical or holds no planned file.

        """
        root = Path(live.root.real_path)
        for folder in additional_source_folders:
            relative = Path(folder)
            candidate = root / relative
            if (
                folder != (relative.as_posix() if relative.parts else "")
                or relative.is_absolute()
                or ".." in relative.parts
                or (
                    not live.source_query(candidate, "isdir")
                    and not any(
                        plan.desired_content is not None
                        and plan.path.is_relative_to(candidate)
                        for plan in declared_files
                    )
                )
            ):
                msg = f"Rope virtual source root lacks a planned file: {folder}"
                raise ValueError(msg)
        files = cls.OverlayFiles({
            plan.path: plan.desired_content for plan in declared_files
        })
        return cls._from_files(
            str(root),
            files,
            m.Infra.RopeProjectElection(
                source_folders=tuple(
                    sorted({*election.source_folders, *additional_source_folders})
                ),
                ignored_resources=tuple(election.ignored_resources),
                extension_modules=tuple(election.extension_modules),
                python_path_folders=tuple(election.python_path_folders),
            ),
        )

    @classmethod
    def _from_files(
        cls,
        root: str,
        files: FlextInfraRopeProject.OverlayFiles,
        election: p.Infra.RopeProjectElection,
    ) -> Self:
        """Compose the native project and external resolver over one view.

        Returns:
            The project sharing one view for local and external reads.

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

    @override
    def _init_other_parts(self) -> None:
        """Initialize the native core and its overlaid resource observations."""
        super()._init_other_parts()
        if isinstance(self.fscommands, self.OverlayFiles):
            core = FlextInfraUtilitiesRopeRuntime.project_core(self)
            core.observer.timekeeper = self.OverlayChangeIndicator(self.fscommands)


__all__: list[str] = ["FlextInfraRopeProject"]
