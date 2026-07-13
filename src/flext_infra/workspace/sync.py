"""Workspace sync service for base.mk generation and deployment.

Generates base.mk from templates and deploys to project roots with
SHA256-based idempotency and file locking.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import contextlib
import fcntl
from pathlib import Path
from typing import Annotated, override

from flext_core import r
from flext_infra import c, config, m, p, u
from flext_infra.base import s
from flext_infra.workspace._sync_artifacts import FlextInfraWorkspaceSyncArtifactsMixin


class FlextInfraSyncService(
    s[m.Infra.SyncResult], FlextInfraWorkspaceSyncArtifactsMixin
):
    """Infrastructure service for workspace base.mk synchronization.

    Generates a fresh base.mk via ``FlextInfraBaseMkGenerator``, compares its SHA256
    hash against the existing file, and writes only when content differs.
    All writes are protected by an ``fcntl`` file lock.

    """

    canonical_root: Annotated[
        Path | None, m.Field(description="Optional canonical root path")
    ] = None

    def _resolved_workspace_root(self) -> Path:
        """Return the validated workspace root from the command context."""
        resolved: Path = self.workspace_root.resolve()
        return resolved

    @override
    def execute(self) -> p.Result[m.Infra.SyncResult]:
        """Execute the workspace sync flow."""
        resolved = self._resolved_workspace_root()
        if not resolved.exists():
            return r[m.Infra.SyncResult].fail(
                f"workspace_root '{resolved}' does not exist"
            )

        lock_file = resolved / ".flext-sync.lock"
        try:
            with lock_file.open("w", encoding=c.Cli.ENCODING_DEFAULT) as handle:
                return self._execute_with_lock(resolved, handle.fileno())
        except OSError as exc:
            return r[m.Infra.SyncResult].fail(f"Could not open lock file: {exc}")

    def _execute_with_lock(
        self, resolved: Path, descriptor: int
    ) -> p.Result[m.Infra.SyncResult]:
        """Run sync while holding the workspace sync lock."""
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return self._sync_locked_content(
                resolved, settings=None, canonical_root=self.canonical_root
            )
        except OSError as exc:
            return r[m.Infra.SyncResult].fail_op("lock acquisition", exc)
        finally:
            with contextlib.suppress(OSError):
                fcntl.flock(descriptor, fcntl.LOCK_UN)

    def _sync_locked_content(
        self,
        resolved: Path,
        settings: m.Infra.BaseMkConfig | None,
        *,
        canonical_root: Path | None = None,
    ) -> p.Result[m.Infra.SyncResult]:
        """Execute all sync steps under the file lock."""
        changed = 0
        effective_root = canonical_root or self.canonical_root
        is_workspace_root = self._is_workspace_root(resolved, effective_root)
        apply = not self.effective_dry_run
        basemk_result = self._sync_basemk(
            resolved, settings, canonical_root=effective_root, apply=apply
        )
        if basemk_result.failure:
            return r[m.Infra.SyncResult].fail(
                basemk_result.error or "base.mk sync failed"
            )
        changed += 1 if basemk_result.value else 0
        gitignore_result = self._ensure_gitignore_entries(
            resolved,
            self._gitignore_entries(is_workspace_root=is_workspace_root),
            apply=apply,
        )
        if gitignore_result.failure:
            return r[m.Infra.SyncResult].fail(
                gitignore_result.error or ".gitignore sync failed"
            )
        changed += 1 if gitignore_result.value else 0
        env_result = self._sync_environment_files(resolved, apply=apply)
        if env_result.failure:
            return r[m.Infra.SyncResult].fail(
                env_result.error or "workspace environment sync failed"
            )
        changed += env_result.value
        vscode_result = self._sync_vscode_settings(resolved, apply=apply)
        if vscode_result.failure:
            return r[m.Infra.SyncResult].fail(
                vscode_result.error or "VS Code settings sync failed"
            )
        changed += 1 if vscode_result.value else 0
        if is_workspace_root:
            pre_commit_result = self._sync_pre_commit_config(resolved, apply=apply)
            if pre_commit_result.failure:
                return r[m.Infra.SyncResult].fail(
                    pre_commit_result.error or ".pre-commit-config.yaml sync failed"
                )
            changed += 1 if pre_commit_result.value else 0
        makefile_result = self._sync_makefile_if_needed(
            resolved, effective_root, apply=apply
        )
        if makefile_result.failure:
            return r[m.Infra.SyncResult].fail(
                makefile_result.error or "Makefile sync failed"
            )
        changed += makefile_result.value
        if is_workspace_root:
            child_sync_result = self._sync_workspace_children(
                resolved, canonical_root=effective_root or resolved
            )
            if child_sync_result.failure:
                return r[m.Infra.SyncResult].fail(
                    child_sync_result.error or "workspace child sync failed"
                )
            changed += child_sync_result.value
        return r[m.Infra.SyncResult].ok(
            m.Infra.SyncResult(files_changed=changed, source=resolved, target=resolved)
        )

    @staticmethod
    def _gitignore_entries(*, is_workspace_root: bool) -> tuple[str, ...]:
        """Return managed ignores and tracked resource-root declarations."""
        entries = list(c.Infra.REQUIRED_GITIGNORE_ENTRIES)
        if is_workspace_root:
            # mro-wkii.17.26 (codex): uv.lock is a versioned workspace input.
            entries.extend((
                "!.pre-commit-config.yaml",
                f"!/{c.Infra.UV_LOCK_FILENAME}",
            ))
        for resource in config.Infra.codegen.scaffold.resources:
            source = resource.source.as_posix().rstrip("/")
            entries.extend((f"!/{source}/", f"!/{source}/**"))
        # mro-wkii.17.26 (codex): re-ignore bytecode after tracked resource roots.
        entries.extend(("**/__pycache__/", "**/*.py[cod]"))
        entries.extend((
            "**/.env",
            "**/*.key",
            "**/*.pem",
            "**/credentials.json",
            "**/secrets.y*ml",
        ))
        return tuple(entries)

    def _sync_workspace_children(
        self, workspace_root: Path, *, canonical_root: Path
    ) -> p.Result[int]:
        """Synchronize all discovered child projects under the workspace root."""
        discovered = u.Infra.discover_projects(workspace_root, include_attached=True)
        if discovered.failure:
            return r[int].fail(discovered.error or "workspace discovery failed")
        changed = 0
        resolved_root = workspace_root.resolve()
        for project in discovered.value:
            project_path = project.path.resolve()
            if project_path == resolved_root:
                continue
            sync_result = self._sync_locked_content(
                project_path, settings=None, canonical_root=canonical_root
            )
            if sync_result.failure:
                project_error = sync_result.error or "project sync failed"
                return r[int].fail(f"{project.name}: {project_error}")
            changed += sync_result.value.files_changed
        return r[int].ok(changed)


if __name__ == "__main__":
    raise SystemExit(0)


__all__: list[str] = ["FlextInfraSyncService"]
