"""Workspace mode detection service.

Detects whether a project runs in standalone or workspace mode by inspecting
parent repository origin URL. Migrated from scripts/mode.py.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING, override
from urllib.parse import urlparse

from flext_core import r
from flext_infra.base import s
from flext_infra.constants import c
from flext_infra.utilities import u

if TYPE_CHECKING:
    from pathlib import Path

    from flext_infra.protocols import p


class FlextInfraWorkspaceDetector(s[c.Infra.WorkspaceMode]):
    """Infrastructure service for detecting workspace mode.

    Inspects parent repository origin URL to determine if a project
    runs in workspace (flext) or standalone mode.

    """

    @staticmethod
    def _repo_name_from_url(url: str) -> str:
        """Extract repository name from Git URL.

        Args:
            url: Git repository URL (SSH or HTTPS).

        Returns:
            Repository name without .git suffix.

        """
        parsed = urlparse(url)
        path = parsed.path or url
        name = path.rsplit("/", 1)[-1]
        return name.removesuffix(c.Infra.GIT_DIR)

    def detect(self, project_root: Path) -> p.Result[c.Infra.WorkspaceMode]:
        """Detect workspace mode by inspecting parent repository origin URL.

        Args:
            project_root: Path to the project directory.

        Returns:
            r with c.Infra.WorkspaceMode.WORKSPACE if parent repo is 'flext',
            c.Infra.WorkspaceMode.STANDALONE otherwise.

        """
        result: p.Result[c.Infra.WorkspaceMode]
        try:
            mode = self._detect_mode(project_root)
            result = r[c.Infra.WorkspaceMode].ok(mode)
        except c.EXC_OS_RUNTIME_TYPE as exc:
            u.Cli.info(f"Running in standalone mode (detection error: {exc})")
            result = r[c.Infra.WorkspaceMode].fail_op("Detection", exc)
        return result

    def _detect_mode(self, project_root: Path) -> c.Infra.WorkspaceMode:
        """Resolve workspace mode without wrapping expected OS/runtime errors."""
        resolved_project_root = project_root.resolve()
        for candidate in (resolved_project_root, *resolved_project_root.parents):
            if (candidate / c.Infra.GITMODULES).exists():
                return c.Infra.WorkspaceMode.WORKSPACE
        return self._detect_parent_mode(resolved_project_root.parent)

    def _detect_parent_mode(self, parent: Path) -> c.Infra.WorkspaceMode:
        """Detect mode from parent repository metadata."""
        git_marker = parent / c.Infra.GIT_DIR
        if not git_marker.exists():
            u.Cli.info("Running in standalone mode (no parent workspace detected)")
            return c.Infra.WorkspaceMode.STANDALONE
        capture_result = u.Cli.capture(
            [c.Infra.GIT, "config", "--get", "remote.origin.url"],
            cwd=parent,
        )
        if capture_result.failure:
            u.Cli.info("Running in standalone mode (unable to detect workspace)")
            return c.Infra.WorkspaceMode.STANDALONE
        origin = capture_result.value.strip()
        if not origin:
            u.Cli.info("Running in standalone mode (no remote origin found)")
            return c.Infra.WorkspaceMode.STANDALONE
        repo_name = self._repo_name_from_url(origin)
        if repo_name == c.Infra.PKG_ROOT:
            return c.Infra.WorkspaceMode.WORKSPACE
        u.Cli.info(f"Running in standalone mode (parent repo: {repo_name})")
        return c.Infra.WorkspaceMode.STANDALONE

    @override
    def execute(self) -> p.Result[c.Infra.WorkspaceMode]:
        """Execute the workspace detection flow."""
        return self.detect(self.workspace_root)


__all__: list[str] = ["FlextInfraWorkspaceDetector"]
