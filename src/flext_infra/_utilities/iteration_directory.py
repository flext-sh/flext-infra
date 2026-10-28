"""Directory-scoped Python file iteration utility facet.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)

from collections.abc import Sequence
from typing import TYPE_CHECKING

from flext_infra import c, config
from flext_infra._utilities import FlextInfraUtilitiesGit
from flext_infra._utilities._git import FlextInfraUtilitiesGitScope

if TYPE_CHECKING:
    from pathlib import Path


class FlextInfraUtilitiesIterationDirectory(
    FlextInfraUtilitiesGit,
):
    """Static helpers for iterating Python files within a single directory tree."""

    @classmethod
    def source_scan_ignored_path(cls, root: Path, file_path: Path) -> bool:
        """Return whether ``file_path`` lies in a source-scan-ignored tree.

        The names are the codegen artifact SSOT (``source_scan_ignored``):
        environments such as the checkout-local ``.venv`` and ``site-packages``,
        tool caches and archives such as ``legado``. Generation ownership alone
        never excludes executable sources. Only the
        parts below ``root`` are judged, so an ancestor directory of the
        checkout that happens to carry one of those names never hides it.
        Paths are compared as given: callers pass a ``file_path`` under
        ``root`` in the same (resolved or unresolved) form; any other path is
        a caller defect that ``relative_to`` reports.

        Returns:
            Whether ``file_path`` lies in a source-scan-ignored tree.

        """
        relative = file_path.relative_to(root)
        return not frozenset(config.Infra.codegen.source_scan_ignored).isdisjoint(
            relative.parts,
        )

    @classmethod
    def iter_directory_python_files(
        cls, directory: Path, *, repository_root: Path
    ) -> Sequence[Path]:
        """Iterate owned Python files in one configured source tree.

        Scoped to one directory (project src, subdirectory, etc.) — unlike
        ``iter_python_files`` which discovers across the whole workspace.
        Unpublished, nonignored sources participate before Git staging.
        Fixture materialization roots do not exclude their Python files.

        Args:
            directory: Root directory to scan.
            repository_root: Declared project owner of the selected directory.

        Returns:
            Sorted list of matching file paths. Empty list if directory
            does not exist.

        """
        resolved_directory = directory.resolve()
        resolved_root = repository_root.resolve()
        if not resolved_directory.is_dir():
            return []
        source_files = FlextInfraUtilitiesGitScope.git_source_scope_paths(
            resolved_directory,
        )
        files = (
            sorted(resolved_directory.rglob(c.Infra.EXT_PYTHON_GLOB))
            if source_files is None
            else [
                file_path
                for file_path in source_files
                if file_path.suffixes == [c.Infra.EXT_PYTHON]
            ]
        )
        return [
            file_path
            for file_path in files
            if file_path.is_file()
            and file_path.suffixes == [c.Infra.EXT_PYTHON]
            and not cls.source_scan_ignored_path(resolved_root, file_path)
        ]


__all__: list[str] = ["FlextInfraUtilitiesIterationDirectory"]
