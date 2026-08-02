"""Python version enforcement service for FLEXT workspace.

Ensures Python version constraints are consistent across all workspace projects.
Creates ``.python-version`` files and verifies ``requires-python`` in each
project's ``pyproject.toml``.

Runtime version checking is handled automatically by
``flext_core_guard`` (imported on ``from flext_core import …``).
This service only manages the static ``.python-version`` files used by
pyenv / asdf / mise for interpreter selection.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, override

from flext_infra import c, config, m, r, s, u

if TYPE_CHECKING:
    from flext_infra import p

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
        bool, m.Field(description="Only validate Python version constraints")
    ] = False
    verbose: Annotated[
        bool, m.Field(description="Emit detailed per-project validation logs")
    ] = False

    @override
    def execute(
        self, *, check_only: bool | None = None, verbose: bool | None = None
    ) -> p.Result[int]:
        """Execute Python version enforcement; returns r[int] exit code."""
        if check_only is not None:
            self.check_only = check_only
        if verbose is not None:
            self.verbose = verbose
        root = self._resolve_workspace_root()
        required_version = config.Infra.codegen.toolchain.python_version
        discovered_projects = u.Infra.discover_projects(root)
        if discovered_projects.failure:
            return r[int].fail(
                discovered_projects.error or "workspace project discovery failed"
            )
        projects = tuple(
            project.path
            for project in discovered_projects.value
            if (project.path / c.Infra.PYPROJECT_FILENAME).exists()
        )
        mode = "Checking" if self.check_only else "Enforcing"
        logger.info(
            "python_version_enforcement_started",
            mode=mode,
            required_version=required_version,
            project_count=len(projects),
        )
        root_result = self._ensure_python_version_file(root, required_version)
        if root_result.failure:
            logger.error(
                "python_version_enforcement_failed",
                reason="missing_enforcement",
                required_version=required_version,
            )
            return r[int].fail(root_result.error or "root enforcement failed")
        for project in projects:
            project_result = self._ensure_python_version_file(
                project, required_version
            )
            if project_result.failure:
                logger.error(
                    "python_version_enforcement_failed",
                    reason="missing_enforcement",
                    required_version=required_version,
                    project=project.name,
                )
                return r[int].fail(
                    project_result.error or f"project enforcement failed: {project}"
                )
        logger.info(
            "python_version_enforcement_completed",
            project_count=len(projects),
            required_version=required_version,
        )
        return r[int].ok(0)

    def _resolve_workspace_root(self) -> Path:
        """Prefer the validated CLI workspace when provided, otherwise auto-detect."""
        if "workspace_root" in self.model_fields_set:
            workspace_root: Path = self.workspace_root
            return workspace_root.resolve()
        return self._workspace_root_from_file(__file__)

    def _ensure_python_version_file(
        self, project: Path, required_version: str
    ) -> p.Result[bool]:
        """Validate project/runtime constraints and conform the selector file."""
        local_result = self._read_declared_version(project)
        if local_result.failure:
            return r[bool].fail(
                local_result.error or f"failed to read Python requirement: {project}"
            )
        local_version = local_result.value
        if local_version != required_version:
            if self.check_only:
                logger.error(
                    "python_version_pyproject_wrong",
                    local_version=local_version,
                    project=project.name,
                )
            else:
                logger.error(
                    "python_version_pyproject_mismatch",
                    local_version=local_version,
                    required_version=required_version,
                    project=project.name,
                )
                logger.error(
                    "python_version_manual_update_required",
                    project=project.name,
                    file=f"{project.name}/pyproject.toml",
                )
            return r[bool].fail(
                f"Python requirement mismatch for {project}: "
                f"expected {required_version}, found {local_version}"
            )
        runtime_version = f"{sys.version_info.major}.{sys.version_info.minor}"
        if runtime_version != required_version:
            logger.error(
                "python_runtime_version_mismatch",
                runtime_version=runtime_version,
                required_version=required_version,
                project=project.name,
            )
            return r[bool].fail(
                f"Python runtime mismatch: expected {required_version}, "
                f"found {runtime_version}"
            )
        conformed = self._conform_python_version_file(project, required_version)
        if conformed.failure:
            return r[bool].fail(
                conformed.error or f"failed to conform Python version: {project}"
            )
        if self.verbose:
            logger.info(
                "python_version_validated",
                required_version=required_version,
                project=project.name,
            )
        return r[bool].ok(True)

    def _conform_python_version_file(
        self, project: Path, required_version: str
    ) -> p.Result[bool]:
        """Write ``.python-version`` from the full SSOT major.minor selector.

        In check-only mode a missing/stale file is a validation failure; in
        apply mode the file is created/rewritten so pyenv/asdf/mise select the
        interpreter that matches the workspace SSOT.
        """
        version_file = project / c.Infra.PYTHON_VERSION_FILENAME
        desired = f"{required_version}\n"
        current = ""
        if version_file.is_file():
            read_result = u.Cli.files_read_text(version_file)
            if read_result.failure:
                return r[bool].fail(
                    read_result.error or f"failed to read {version_file}"
                )
            current = read_result.value
        if current == desired:
            return r[bool].ok(True)
        if self.check_only:
            logger.error(
                "python_version_file_out_of_sync",
                project=project.name,
                file=c.Infra.PYTHON_VERSION_FILENAME,
            )
            return r[bool].fail(
                f"{version_file} is out of sync; expected {desired.strip()}"
            )
        write_result = u.Cli.files_write_text(version_file, desired)
        if write_result.failure:
            logger.error(
                "python_version_file_write_failed",
                project=project.name,
                error=write_result.error,
            )
            return r[bool].fail(
                write_result.error or f"failed to write {version_file}"
            )
        logger.info(
            "python_version_file_conformed",
            project=project.name,
            version=desired.strip(),
        )
        return r[bool].ok(True)

    def _read_declared_version(self, workspace_root: Path) -> p.Result[str]:
        """Read one generated project major.minor without an SSOT fallback."""
        pyproject = workspace_root / c.Infra.PYPROJECT_FILENAME
        if not pyproject.is_file():
            return r[str].fail(f"missing project metadata: {pyproject}")
        content_result = u.Cli.files_read_text(pyproject)
        if content_result.failure:
            return r[str].fail(
                content_result.error or f"failed to read {pyproject}"
            )
        match = c.Infra.REQUIRES_PYTHON_RE.search(content_result.value)
        if match is None:
            return r[str].fail(f"requires-python is missing or invalid: {pyproject}")
        return r[str].ok(f"{match.group(1)}.{match.group(2)}")

    def _workspace_root_from_file(self, file: str | Path) -> Path:
        """Walk up from ``file`` to the first dir with .git+Makefile+pyproject.

        Raises RuntimeError when no such workspace root exists (fail-loud).
        """
        current = Path(file).resolve()
        if current.is_file():
            current = current.parent
        for parent in [current, *list(current.parents)]:
            markers = {
                c.Infra.GIT_DIR,
                c.Infra.MAKEFILE_FILENAME,
                c.Infra.PYPROJECT_FILENAME,
            }
            if all((parent / marker).exists() for marker in markers):
                return parent
        msg = f"workspace root not found from {file}"
        raise RuntimeError(msg)
