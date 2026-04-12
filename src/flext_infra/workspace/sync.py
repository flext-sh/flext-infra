"""Workspace sync service for base.mk generation and deployment.

Generates base.mk from templates and deploys to project roots with
SHA256-based idempotency and file locking.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import contextlib
from pathlib import Path
from typing import Annotated, override

from pydantic import Field

from flext_core import r
from flext_infra import (
    FlextInfraBaseMkGenerator,
    FlextInfraServiceBase,
    c,
    m,
    t,
    u,
)


class FlextInfraSyncService(FlextInfraServiceBase[m.Infra.SyncResult]):
    """Infrastructure service for workspace base.mk synchronization.

    Generates a fresh base.mk via ``FlextInfraBaseMkGenerator``, compares its SHA256
    hash against the existing file, and writes only when content differs.
    All writes are protected by an ``fcntl`` file lock.

    """

    generator: Annotated[
        FlextInfraBaseMkGenerator | None,
        Field(
            default=None, exclude=True, description="Optional custom generator service"
        ),
    ] = None
    canonical_root: Annotated[
        Path | None,
        Field(default=None, description="Optional canonical root path"),
    ] = None

    def _get_generator(self) -> FlextInfraBaseMkGenerator:
        """Return the configured generator."""
        return self.generator or FlextInfraBaseMkGenerator()

    def _resolved_workspace_root(self) -> Path:
        """Return the validated workspace root from the command context."""
        return self.workspace_root.resolve()

    @override
    def execute(self) -> r[m.Infra.SyncResult]:
        """Execute the workspace sync flow."""
        import fcntl

        resolved = self._resolved_workspace_root()
        if not resolved.exists():
            return r[m.Infra.SyncResult].fail(
                f"workspace_root '{resolved}' does not exist"
            )

        lock_file = resolved / ".flext-sync.lock"
        try:
            with lock_file.open("w", encoding=c.Infra.ENCODING_DEFAULT) as handle:
                try:
                    fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    return self._sync_locked_content(
                        resolved,
                        settings=None,
                        canonical_root=self.canonical_root,
                    )
                except OSError as exc:
                    return r[m.Infra.SyncResult].fail(f"lock acquisition failed: {exc}")
                finally:
                    with contextlib.suppress(OSError):
                        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        except OSError as exc:
            return r[m.Infra.SyncResult].fail(f"Could not open lock file: {exc}")

    def _sync_locked_content(
        self,
        resolved: Path,
        settings: m.Infra.BaseMkConfig | None,
        *,
        canonical_root: Path | None = None,
    ) -> r[m.Infra.SyncResult]:
        """Execute all sync steps under the file lock."""
        changed = 0
        effective_root = canonical_root or self.canonical_root
        basemk_result = self._sync_basemk(
            resolved,
            settings,
            canonical_root=effective_root,
        )
        if basemk_result.failure:
            return r[m.Infra.SyncResult].fail(
                basemk_result.error or "base.mk sync failed",
            )
        changed += 1 if basemk_result.value else 0
        gitignore_result = self._ensure_gitignore_entries(
            resolved,
            c.Infra.REQUIRED_GITIGNORE_ENTRIES,
        )
        if gitignore_result.failure:
            return r[m.Infra.SyncResult].fail(
                gitignore_result.error or ".gitignore sync failed",
            )
        changed += 1 if gitignore_result.value else 0
        makefile_result = self._sync_makefile_if_needed(
            resolved,
            effective_root,
        )
        if makefile_result.failure:
            return r[m.Infra.SyncResult].fail(
                makefile_result.error or "Makefile sync failed",
            )
        changed += makefile_result.value
        is_workspace_root = self._is_workspace_root(resolved, effective_root)
        if is_workspace_root:
            child_sync_result = self._sync_workspace_children(
                resolved,
                canonical_root=effective_root or resolved,
            )
            if child_sync_result.failure:
                return r[m.Infra.SyncResult].fail(
                    child_sync_result.error or "workspace child sync failed",
                )
            changed += child_sync_result.value
        return r[m.Infra.SyncResult].ok(
            m.Infra.SyncResult(
                files_changed=changed,
                source=resolved,
                target=resolved,
            ),
        )

    def _sync_workspace_children(
        self,
        workspace_root: Path,
        *,
        canonical_root: Path,
    ) -> r[int]:
        """Synchronize all discovered child projects under the workspace root."""
        discovered = u.Infra.discover_projects(workspace_root)
        if discovered.failure:
            return r[int].fail(discovered.error or "workspace discovery failed")
        changed = 0
        resolved_root = workspace_root.resolve()
        for project in discovered.value:
            project_path = project.path.resolve()
            if project_path == resolved_root:
                continue
            sync_result = self._sync_locked_content(
                project_path,
                settings=None,
                canonical_root=canonical_root,
            )
            if sync_result.failure:
                project_error = sync_result.error or "project sync failed"
                return r[int].fail(f"{project.name}: {project_error}")
            changed += sync_result.value.files_changed
        return r[int].ok(changed)

    def _sync_makefile_if_needed(
        self,
        resolved: Path,
        effective_root: Path | None,
    ) -> r[int]:
        """Sync workspace or project Makefile and surface generator failures."""
        is_workspace_root = self._is_workspace_root(resolved, effective_root)
        if is_workspace_root:
            workspace_makefile_result = self._sync_workspace_makefile(resolved)
            if workspace_makefile_result.failure:
                return r[int].fail(
                    workspace_makefile_result.error
                    or "workspace Makefile generation failed",
                )
            return r[int].ok(1 if workspace_makefile_result.value else 0)
        if (resolved / c.Infra.PYPROJECT_FILENAME).exists():
            makefile_result = self._sync_project_makefile(
                resolved,
                effective_root or resolved,
            )
            if makefile_result.failure:
                return r[int].fail(
                    makefile_result.error or "project Makefile generation failed",
                )
            return r[int].ok(1 if makefile_result.value else 0)
        return r[int].ok(0)

    @staticmethod
    def _sync_project_makefile(
        workspace_root: Path,
        canonical_root: Path,
    ) -> r[bool]:
        """Sync the generated section of a project Makefile from pyproject.toml."""
        from flext_infra import (
            FlextInfraProjectMakefileUpdater,
        )

        return FlextInfraProjectMakefileUpdater().update(
            workspace_root,
            canonical_root=canonical_root,
        )

    @staticmethod
    def _sync_workspace_makefile(workspace_root: Path) -> r[bool]:
        """Sync the workspace root Makefile from the canonical generator."""
        from flext_infra import (
            FlextInfraWorkspaceMakefileGenerator,
        )

        return FlextInfraWorkspaceMakefileGenerator().generate(workspace_root)

    @staticmethod
    def _is_workspace_root(
        workspace_root: Path,
        canonical_root: Path | None,
    ) -> bool:
        """Detect whether the sync target is the workspace root."""
        resolved_root = workspace_root.resolve()
        if canonical_root is not None:
            return resolved_root == canonical_root.resolve()
        if (resolved_root / c.Infra.GITMODULES).exists():
            return True
        discovered = u.Infra.discover_projects(resolved_root)
        if discovered.failure:
            return False
        return any(
            project.path.resolve() != resolved_root for project in discovered.value
        )

    def _ensure_gitignore_entries(
        self,
        workspace_root: Path,
        required: t.StrSequence,
    ) -> r[bool]:
        """Idempotently add missing .gitignore entries.

        Appends only entries not already present (exact line match).
        Never removes or reorders existing entries.

        Args:
            workspace_root: Root directory of the project.
            required: List of gitignore patterns that must be present.

        Returns:
            r with True if file was changed, False otherwise.

        """
        gitignore = workspace_root / c.Infra.GITIGNORE
        try:
            existing_lines: t.StrSequence = []
            if gitignore.exists():
                existing_lines = gitignore.read_text(
                    encoding=c.Infra.ENCODING_DEFAULT,
                ).splitlines()
            existing_patterns = {
                line.strip() for line in existing_lines if line.strip()
            }
            missing = [p for p in required if p not in existing_patterns]
            if not missing:
                return r[bool].ok(False)
            with gitignore.open("a", encoding=c.Infra.ENCODING_DEFAULT) as handle:
                _ = handle.write(
                    "\n# --- workspace-sync: required ignores (auto-managed) ---\n",
                )
                for pattern in missing:
                    _ = handle.write(f"{pattern}\n")
            return r[bool].ok(True)
        except OSError as exc:
            return r[bool].fail(f".gitignore update failed: {exc}")

    def _sync_basemk(
        self,
        workspace_root: Path,
        settings: m.Infra.BaseMkConfig | None,
        *,
        canonical_root: Path | None = None,
    ) -> r[bool]:
        """Sync base.mk for workspace root and subprojects.

        All projects receive a generated local ``base.mk`` so regeneration is
        fully deterministic from ``make gen`` without relying on deferred
        bootstrap.
        """
        _ = canonical_root
        generator = self._get_generator()
        gen_result = generator.generate_basemk(settings)
        if gen_result.failure:
            return r[bool].fail(gen_result.error or "base.mk generation failed")
        content: str = gen_result.value
        target_path = workspace_root / c.Infra.BASE_MK
        content_hash = u.Cli.sha256_content(content)
        if target_path.exists():
            existing_hash = u.Cli.sha256_file(target_path)
            if content_hash == existing_hash:
                return r[bool].ok(False)
        return u.Cli.atomic_write_text_file(target_path, content)


if __name__ == "__main__":
    raise SystemExit(0)


__all__ = ["FlextInfraSyncService"]
