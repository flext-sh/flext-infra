"""Workspace mode detection service.

Detects whether a project runs in standalone or workspace mode by inspecting
parent repository origin URL. Migrated from scripts/mode.py.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import override
from urllib.parse import urlparse

from flext_infra import c, m, r, u
from flext_infra.base import s

# Canonical alias -- single source of truth lives in workspace constants
FlextInfraWorkspaceMode = c.Infra.WorkspaceMode


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
        return name.removesuffix(c.Infra.Git.DIR)

    def detect(self, project_root: Path) -> r[c.Infra.WorkspaceMode]:
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
                    return r[c.Infra.WorkspaceMode].ok(
                        FlextInfraWorkspaceMode.WORKSPACE,
                    )
            parent = resolved_project_root.parent
            git_marker = parent / c.Infra.Git.DIR
            if not git_marker.exists():
                u.Infra.info(
                    "Running in standalone mode (no parent workspace detected)"
                )
                return r[c.Infra.WorkspaceMode].ok(FlextInfraWorkspaceMode.STANDALONE)
            result = u.Infra.git_run(
                ["config", "--get", "remote.origin.url"],
                cwd=parent,
            )
            if result.is_failure:
                u.Infra.info("Running in standalone mode (unable to detect workspace)")
                return r[c.Infra.WorkspaceMode].ok(FlextInfraWorkspaceMode.STANDALONE)
            origin = result.value.strip()
            if not origin:
                u.Infra.info("Running in standalone mode (no remote origin found)")
                return r[c.Infra.WorkspaceMode].ok(FlextInfraWorkspaceMode.STANDALONE)
            repo_name = self._repo_name_from_url(origin)
            mode = (
                FlextInfraWorkspaceMode.WORKSPACE
                if repo_name == c.Infra.Packages.ROOT
                else FlextInfraWorkspaceMode.STANDALONE
            )
            if mode == FlextInfraWorkspaceMode.STANDALONE:
                u.Infra.info(f"Running in standalone mode (parent repo: {repo_name})")
            return r[c.Infra.WorkspaceMode].ok(mode)
        except (OSError, RuntimeError, TypeError, ValueError) as exc:
            u.Infra.info(f"Running in standalone mode (detection error: {exc})")
            return r[c.Infra.WorkspaceMode].fail(f"Detection failed: {exc}")

    def _resolved_workspace_root(self) -> Path:
        """Return the validated workspace root from the command context."""
        raw = getattr(self, "workspace_root", None)
        if isinstance(raw, Path):
            return raw.resolve()
        if isinstance(raw, str) and raw.strip():
            return Path(raw).resolve()
        return Path.cwd().resolve()

    @override
    def execute(self) -> r[c.Infra.WorkspaceMode]:
        """Execute the workspace detection flow."""
        return self.detect(self._resolved_workspace_root())

    @classmethod
    @override
    def execute_command(
        cls,
        params: s[c.Infra.WorkspaceMode] | m.Infra.WorkspaceDetectInput,
    ) -> r[c.Infra.WorkspaceMode]:
        """Normalize workspace CLI input into the canonical detector model."""
        if isinstance(params, m.Infra.WorkspaceDetectInput):
            service = cls.model_validate({
                "workspace_root": params.workspace_path,
                "apply_changes": params.apply,
            })
            return service.execute()
        return params.execute()


__all__ = ["FlextInfraWorkspaceDetector", "FlextInfraWorkspaceMode"]
