"""Directory-scoped Python file iteration utility facet.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra import c, config
from flext_infra._utilities._git import FlextInfraUtilitiesGitScopeMixin

if TYPE_CHECKING:
    from pathlib import Path

    from flext_infra import t


class FlextInfraUtilitiesIterationDirectory(FlextInfraUtilitiesGitScopeMixin):
    """Static helpers for iterating Python files within a single directory tree."""

    @staticmethod
    def source_scan_ignored_path(root: Path, file_path: Path) -> bool:
        """Return whether ``file_path`` lies in a source-scan-ignored tree.

        The names are the codegen artifact SSOT (``source_scan_ignored``):
        environments such as the checkout-local ``.venv`` and ``site-packages``,
        tool caches, generated sources and archives such as ``legado``. Only the
        parts below ``root`` are judged, so an ancestor directory of the
        checkout that happens to carry one of those names never hides it.
        Paths are compared as given: callers pass a ``file_path`` under
        ``root`` in the same (resolved or unresolved) form; any other path is
        a caller defect that ``relative_to`` reports.

        Returns:
            Whether ``file_path`` lies in a source-scan-ignored tree.

        """
        return not frozenset(config.Infra.codegen.source_scan_ignored).isdisjoint(
            file_path.relative_to(root).parts,
        )

    @classmethod
    def iter_directory_python_files(cls, directory: Path) -> t.SequenceOf[Path]:
        """Iterate production Python files in one configured source tree.

        Scoped to one directory (project src, subdirectory, etc.) — unlike
        ``iter_python_files`` which discovers across the whole workspace.

        Args:
            directory: Root directory to scan.

        Returns:
            Sorted list of matching file paths. Empty list if directory
            does not exist.

        """
        resolved_directory = directory.resolve()
        if not resolved_directory.is_dir():
            return []
        tracked_files = FlextInfraUtilitiesGitScopeMixin.git_tracked_scope_paths(
            resolved_directory,
        )
        files = (
            sorted(resolved_directory.rglob(c.Infra.EXT_PYTHON_GLOB))
            if tracked_files is None
            else [
                file_path
                for file_path in tracked_files
                if file_path.suffixes == [c.Infra.EXT_PYTHON]
            ]
        )
        return [
            file_path
            for file_path in files
            if file_path.is_file()
            and file_path.suffixes == [c.Infra.EXT_PYTHON]
            and not cls.source_scan_ignored_path(resolved_directory, file_path)
        ]


__all__: list[str] = ["FlextInfraUtilitiesIterationDirectory"]
