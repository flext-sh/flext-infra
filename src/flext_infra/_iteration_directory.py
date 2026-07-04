"""Directory-scoped Python file iteration mixin.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import fnmatch
from typing import TYPE_CHECKING

from flext_infra._iteration_canonical import FlextInfraUtilitiesIterationCanonical
from flext_infra._utilities.git_scope import FlextInfraUtilitiesGitScope
from flext_infra.constants import c

if TYPE_CHECKING:
    from pathlib import Path

    from flext_infra.typings import t


class FlextInfraUtilitiesIterationDirectory:
    """Static helpers for iterating Python files within a single directory tree."""

    @staticmethod
    def iter_directory_python_files(
        directory: Path,
        *,
        pattern: str | None = None,
        skip_pycache: bool = True,
    ) -> t.SequenceOf[Path]:
        """Iterate Python files in a single directory tree.

        Scoped to one directory (project src, subdirectory, etc.) — unlike
        ``iter_python_files`` which discovers across the whole workspace.

        Args:
            directory: Root directory to scan.
            pattern: Glob pattern (defaults to ``*.py``).
            skip_pycache: Exclude ``__pycache__`` paths (default True).

        Returns:
            Sorted list of matching file paths. Empty list if directory
            does not exist.

        """
        if not directory.is_dir():
            return []
        effective_pattern = pattern or c.Infra.EXT_PYTHON_GLOB
        tracked_files = FlextInfraUtilitiesGitScope.git_tracked_scope_paths(directory)
        files = (
            sorted(directory.rglob(effective_pattern))
            if tracked_files is None
            else [
                file_path
                for file_path in tracked_files
                if fnmatch.fnmatch(
                    file_path.relative_to(directory).as_posix(),
                    effective_pattern,
                )
            ]
        )
        ignored_parts = (
            c.Infra.ITERATION_EXCLUDED_PARTS
            if skip_pycache
            else c.Infra.ITERATION_EXCLUDED_PARTS - {c.Infra.DUNDER_PYCACHE}
        )
        return [
            file_path
            for file_path in files
            if FlextInfraUtilitiesIterationCanonical.matches_canonical_python_file(
                file_path,
            )
            if not FlextInfraUtilitiesIterationCanonical.is_ignored_python_path(
                file_path,
                ignored_parts=ignored_parts,
            )
        ]


__all__: list[str] = ["FlextInfraUtilitiesIterationDirectory"]
