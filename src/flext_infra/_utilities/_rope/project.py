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

from rope.base.project import Project
from rope.base.resources import File, Folder

from flext_infra import c, p, t


class FlextInfraRopeProject(Project):
    """Rope project with the upstream self-warning initializer repaired."""

    # Import roots are declared by FLEXT; a read-only analysis pass also
    # freezes their resource identities and the external Python path.
    _frozen_folders: tuple[list[File | Folder], list[File | Folder]] | None = None

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
            directories = {self._root, *self._root.parents}
            for path in self._sources:
                directories.update(path.parents)
            for folder in source_folders:
                path = self._root / folder
                resolved = path.resolve()
                if not resolved.is_relative_to(self._root):
                    msg = "Rope snapshot folder is outside its project root"
                    raise ValueError(msg)
                directories.update((resolved, *resolved.parents))
            self._directories = frozenset(directories)

        @staticmethod
        def realpath(path: str) -> str:
            """Return the canonical identity Rope uses for snapshot paths."""
            return str(Path(path).expanduser().resolve())

        def exists(self, path: str) -> bool:
            """Report only files and folders captured by this snapshot.

            Returns:
                The resulting ``bool``.

            """
            resolved = Path(path).resolve()
            return resolved in self._sources or resolved in self._directories

        def isfile(self, path: str) -> bool:
            """Recognize only captured source files.

            Returns:
                The resulting ``bool``.

            """
            return Path(path).resolve() in self._sources

        def isdir(self, path: str) -> bool:
            """Recognize only declared or captured parent folders.

            Returns:
                The resulting ``bool``.

            """
            return Path(path).resolve() in self._directories

        def listdir(self, path: str) -> list[str]:
            """Enumerate captured direct children without consulting live disk.

            Returns:
                The resulting ``list[str]``.

            Raises:
                FileNotFoundError: If Rope snapshot folder is absent.

            """
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
            return self._sources[Path(path).resolve()]

    @classmethod
    def from_snapshot(
        cls,
        root: str,
        sources: Mapping[Path, bytes],
        source_folders: t.SequenceOf[str],
        ignored_resources: t.SequenceOf[str] = (),
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

        Returns:
            The resulting ``Self``.

        Raises:
            ValueError: If Rope snapshot root must already exist.

        """
        if not Path(root).is_dir():
            msg = f"Rope snapshot root must already exist: {root}"
            raise ValueError(msg)
        return cls(
            root,
            fscommands=cls.SnapshotFiles(Path(root), sources, source_folders),
            ropefolder=None,
            save_objectdb=False,
            save_history=False,
            ignored_resources=list(ignored_resources),
            source_folders=source_folders,
        )

    @contextmanager
    def frozen_layout(self) -> Generator[Self]:
        """Declared freeze of the source and Python path folders for one read-only pass.

        Yields:
            This project, its folder layout computed once for the pass.

        """
        source_folders = self.get_source_folders()
        python_path_folders: list[File | Folder] = super().get_python_path_folders()
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
            folders: list[File | Folder] = super().get_python_path_folders()
            return folders
        return list(self._frozen_folders[1])

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
