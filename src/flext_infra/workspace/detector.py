"""Workspace mode detection service.

Detects whether a project runs in standalone or workspace mode by inspecting
parent repository origin URL. Migrated from scripts/mode.py.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from enum import StrEnum, unique
from pathlib import Path
from typing import override
from urllib.parse import urlparse

from flext_infra import c, r, s, u


@unique
class FlextInfraWorkspaceMode(StrEnum):
    """Workspace execution mode enumeration."""

    WORKSPACE = "workspace"
    STANDALONE = "standalone"


class FlextInfraWorkspaceDetector(s[FlextInfraWorkspaceMode]):
    """Infrastructure service for detecting workspace mode.

    Inspects parent repository origin URL to determine if a project
    runs in workspace (flext) or standalone mode.

    """

    def __init__(self) -> None:
        """Initialize the workspace detector."""
        super().__init__()

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
        return name.removesuffix(c.Infra.Git.DIR)

    def detect(self, project_root: Path) -> r[FlextInfraWorkspaceMode]:
        """Detect workspace mode by inspecting parent repository origin URL.

        Args:
            project_root: Path to the project directory.

        Returns:
            r with FlextInfraWorkspaceMode.WORKSPACE if parent repo is 'flext',
            FlextInfraWorkspaceMode.STANDALONE otherwise.

        """
        try:
            resolved_project_root = project_root.resolve()
            for candidate in (resolved_project_root, *resolved_project_root.parents):
                if (candidate / c.Infra.Files.GITMODULES).exists():
                    return r[FlextInfraWorkspaceMode].ok(
                        FlextInfraWorkspaceMode.WORKSPACE,
                    )
            parent = resolved_project_root.parent
            git_marker = parent / c.Infra.Git.DIR
            if not git_marker.exists():
                u.Infra.info(
                    "Running in standalone mode (no parent workspace detected)"
                )
                return r[FlextInfraWorkspaceMode].ok(FlextInfraWorkspaceMode.STANDALONE)
            result = u.Infra.git_run(
                ["config", "--get", "remote.origin.url"],
                cwd=parent,
            )
            if result.is_failure:
                u.Infra.info("Running in standalone mode (unable to detect workspace)")
                return r[FlextInfraWorkspaceMode].ok(FlextInfraWorkspaceMode.STANDALONE)
            origin = result.value.strip()
            if not origin:
                u.Infra.info("Running in standalone mode (no remote origin found)")
                return r[FlextInfraWorkspaceMode].ok(FlextInfraWorkspaceMode.STANDALONE)
            repo_name = self._repo_name_from_url(origin)
            mode = (
                FlextInfraWorkspaceMode.WORKSPACE
                if repo_name == c.Infra.Packages.ROOT
                else FlextInfraWorkspaceMode.STANDALONE
            )
            if mode == FlextInfraWorkspaceMode.STANDALONE:
                u.Infra.info(f"Running in standalone mode (parent repo: {repo_name})")
            return r[FlextInfraWorkspaceMode].ok(mode)
        except (OSError, RuntimeError, TypeError, ValueError) as exc:
            u.Infra.info(f"Running in standalone mode (detection error: {exc})")
            return r[FlextInfraWorkspaceMode].fail(f"Detection failed: {exc}")

    @override
    def execute(self) -> r[FlextInfraWorkspaceMode]:
        """Not used; call detect() directly instead."""
        return r[FlextInfraWorkspaceMode].fail("Use detect() method directly")


__all__ = ["FlextInfraWorkspaceDetector", "FlextInfraWorkspaceMode"]
