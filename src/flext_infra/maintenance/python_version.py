"""Python version enforcement service for FLEXT workspace.

Ensures Python version constraints are consistent across all workspace projects.
Creates ``.python-version`` files and verifies ``requires-python`` in each
project's ``pyproject.toml``.

Runtime version checking is handled automatically by
``flext_core_guard`` (imported on ``from flext_core import …``).
This service only manages the static ``.python-version`` files used by
pyenv / asdf / mise for interpreter selection.

Usage::

    from flext_infra import (
        FlextInfraPythonVersionEnforcer,
    )

    service = FlextInfraPythonVersionEnforcer()
    result = service.execute(check_only=True, verbose=True)
    if result.success:
        logger.info("Python version check passed")

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Annotated, override

from pydantic import Field

from flext_infra import c, p, r, s, u

logger = u.fetch_logger(__name__)


class FlextInfraPythonVersionEnforcer(s[int]):
    """Service for enforcing Python version constraints across workspace.

    Validates that all projects have consistent Python version requirements
    and that the runtime matches the workspace requirement.

    Attributes:
        check_only: If True, only verify without making changes.
        verbose: If True, print detailed output for each project.

    """

    check_only: Annotated[
        bool,
        Field(default=False, description="Only validate Python version constraints"),
    ] = False
    verbose: Annotated[
        bool,
        Field(default=False, description="Emit detailed per-project validation logs"),
    ] = False

    @override
    def execute(
        self,
        *,
        check_only: bool | None = None,
        verbose: bool | None = None,
    ) -> p.Result[int]:
        """Execute Python version enforcement.

        Args:
            check_only: If True, only verify without making changes.
            verbose: If True, print detailed output.

        Returns:
            r[int]: Exit code (0 for success, 1 for failure).

        """
        if check_only is not None:
            self.check_only = check_only
        if verbose is not None:
            self.verbose = verbose
        root = self._resolve_workspace_root()
        required_minor = self._read_required_minor(root)
        discovered_projects = u.Infra.discover_projects(root)
        if discovered_projects.failure:
            projects: tuple[Path, ...] = ()
        else:
            projects = tuple(
                project.path
                for project in discovered_projects.unwrap()
                if (project.path / c.Infra.PYPROJECT_FILENAME).exists()
            )
        mode = "Checking" if self.check_only else "Enforcing"
        logger.info(
            "python_version_enforcement_started",
            mode=mode,
            required_minor=required_minor,
            project_count=len(projects),
        )
        if not self._ensure_python_version_file(root, required_minor):
            logger.error(
                "python_version_enforcement_failed",
                reason="missing_enforcement",
                required_minor=required_minor,
            )
            return r[int].fail("enforcement failed")
        for project in projects:
            if not self._ensure_python_version_file(project, required_minor):
                logger.error(
                    "python_version_enforcement_failed",
                    reason="missing_enforcement",
                    required_minor=required_minor,
                    project=project.name,
                )
                return r[int].fail("enforcement failed")
        logger.info(
            "python_version_enforcement_completed",
            project_count=len(projects),
            required_minor=required_minor,
        )
        return r[int].ok(0)

    def _resolve_workspace_root(self) -> Path:
        """Prefer the validated CLI workspace when provided, otherwise auto-detect."""
        if "workspace_root" in self.model_fields_set:
            return self.workspace_root.resolve()
        return self._workspace_root_from_file(__file__)

    def _ensure_python_version_file(self, project: Path, required_minor: int) -> bool:
        """Ensure pyproject.toml requires-python matches required minor version.

        Args:
            project: Path to project.
            required_minor: Required Python minor version.

        Returns:
            bool: True if validation passed, False otherwise.

        """
        local_minor = self._read_required_minor(project)
        if local_minor != required_minor:
            if self.check_only:
                logger.error(
                    "python_version_pyproject_wrong",
                    local_minor=local_minor,
                    project=project.name,
                )
            else:
                logger.error(
                    "python_version_pyproject_mismatch",
                    local_minor=local_minor,
                    required_minor=required_minor,
                    project=project.name,
                )
                logger.error(
                    "python_version_manual_update_required",
                    project=project.name,
                    file=f"{project.name}/pyproject.toml",
                )
            return False
        runtime_minor = sys.version_info.minor
        if runtime_minor != required_minor:
            logger.error(
                "python_runtime_minor_mismatch",
                runtime_minor=runtime_minor,
                required_minor=required_minor,
                project=project.name,
            )
            return False
        if self.verbose:
            logger.info(
                "python_version_validated",
                required_minor=required_minor,
                project=project.name,
            )
        return True

    def _read_required_minor(self, workspace_root: Path) -> int:
        """Read the required Python minor version from workspace pyproject.toml.

        Falls back to 13 if the field cannot be parsed.

        Args:
            workspace_root: Path to workspace root.

        Returns:
            int: Required Python minor version.

        """
        pyproject = workspace_root / c.Infra.PYPROJECT_FILENAME
        if not pyproject.is_file():
            return 13
        content = pyproject.read_text(encoding=c.Infra.ENCODING_DEFAULT)
        match = re.search(r'requires-python\s*=\s*"[>!=]*(\d+)\.(\d+)', content)
        if match is None:
            return 13
        return int(match.group(2))

    def _workspace_root_from_file(self, file: str | Path) -> Path:
        """Resolve workspace root by walking up from file location.

        Finds the first directory containing .git, Makefile, and pyproject.toml.

        Args:
            file: Path to a file (usually __file__).

        Returns:
            Absolute Path to the workspace root.

        Raises:
            RuntimeError: If workspace root cannot be found.

        """
        current = Path(file).resolve()
        if current.is_file():
            current = current.parent
        for parent in [current] + list(current.parents):
            markers = {
                c.Infra.GIT_DIR,
                c.Infra.MAKEFILE_FILENAME,
                c.Infra.PYPROJECT_FILENAME,
            }
            if all((parent / marker).exists() for marker in markers):
                return parent
        msg = f"workspace root not found from {file}"
        raise RuntimeError(msg)
