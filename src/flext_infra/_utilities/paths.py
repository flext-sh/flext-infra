"""Path resolution utilities for workspace navigation.

Provides static utility methods for path resolution with r error handling,
replacing bare functions with a utility class.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import os
from pathlib import Path

from flext_core import r
from flext_infra import c


class FlextInfraUtilitiesPaths:
    """Utility class for workspace path resolution.

    Provides static methods for path resolution with r-wrapped error handling,
    replacing bare functions from ``scripts/libs/paths.py``.
    """

    @staticmethod
    def workspace_root(path: str | Path = ".") -> r[Path]:
        """Resolve and return the absolute path to the workspace root.

        Uses ``FLEXT_WORKSPACE_ROOT`` only when the caller keeps the default
        current-directory path. Explicit paths must be honored directly.

        Args:
            path: A starting path, defaults to the current directory.

        Returns:
            r[Path] with the resolved absolute path.

        """
        try:
            requested = Path(path)
            env_root = os.getenv("FLEXT_WORKSPACE_ROOT")
            uses_default_path = (str(path) in {"", "."}) or (requested == Path())
            if env_root and uses_default_path:
                candidate = Path(env_root).expanduser().resolve()
                if candidate.is_dir():
                    return r[Path].ok(candidate)
            resolved = requested.expanduser().resolve()
            return r[Path].ok(resolved)
        except (OSError, RuntimeError, TypeError, ValueError) as exc:
            return r[Path].fail(f"failed to resolve workspace root: {exc}")

    @staticmethod
    def resolve_workspace_root(file: str | Path) -> Path:
        """Resolve workspace root by walking up from file location to .gitmodules.

        This specific resolution pattern is used by orchestration services
        to identify the FLEXT workspace root.

        Args:
            file: Path to a file (usually __file__).

        Returns:
            Absolute path to workspace root.

        """
        here = Path(file).resolve()
        for candidate in here.parents:
            if (candidate / c.Infra.GITMODULES).exists():
                return candidate
        return here.parents[4]

    @staticmethod
    def resolve_workspace_root_or_cwd(workspace_root: Path | None = None) -> Path:
        """Resolve workspace root from an optional path, falling back to cwd.

        Args:
            workspace_root: Explicit workspace root, or None to auto-detect.

        Returns:
            Resolved absolute path to the workspace root.

        """
        if workspace_root is not None:
            return workspace_root.resolve()
        result = FlextInfraUtilitiesPaths.workspace_root()
        return result.unwrap_or(Path.cwd().resolve())


__all__: list[str] = ["FlextInfraUtilitiesPaths"]
