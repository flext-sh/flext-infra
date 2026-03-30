"""Workspace sync service for base.mk generation and deployment.

Generates base.mk from templates and deploys to project roots with
SHA256-based idempotency and file locking.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import fcntl
import hashlib
from pathlib import Path
from typing import override

from flext_infra import FlextInfraBaseMkGenerator, c, m, output, r, s, t, u


class FlextInfraSyncService(s[m.Infra.SyncResult]):
    """Infrastructure service for workspace base.mk synchronization.

    Generates a fresh base.mk via ``FlextInfraBaseMkGenerator``, compares its SHA256
    hash against the existing file, and writes only when content differs.
    All writes are protected by an ``fcntl`` file lock.

    """

    def __init__(
        self,
        generator: FlextInfraBaseMkGenerator | None = None,
        *,
        canonical_root: Path | None = None,
    ) -> None:
        """Initialize the sync service."""
        super().__init__()
        self._generator = generator or FlextInfraBaseMkGenerator()
        self._canonical_root = canonical_root

    @staticmethod
    def _atomic_write(target: Path, content: str) -> r[bool]:
        """Write content to target via atomic temp-file rename."""
        return u.Infra.atomic_write_file(target, content)

    @staticmethod
    def _sha256_content(content: str) -> str:
        """Compute SHA256 of string content."""
        return hashlib.sha256(content.encode(c.Infra.Encoding.DEFAULT)).hexdigest()

    @staticmethod
    def _sha256_file(path: Path) -> str:
        """Compute SHA256 of file on disk."""
        hasher = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    @override
    def execute(self) -> r[m.Infra.SyncResult]:
        """Not used; call sync() directly instead."""
        return r[m.Infra.SyncResult].fail("Use sync() method directly")

    def sync(
        self,
        _source: str | None = None,
        _target: str | None = None,
        *,
        workspace_root: Path | None = None,
        config: m.Infra.BaseMkConfig | None = None,
        canonical_root: Path | None = None,
    ) -> r[m.Infra.SyncResult]:
        """Synchronize base.mk and .gitignore for a project.

        Copies base.mk from canonical root when available, otherwise
        generates from template. Compares SHA256 hashes and writes only if
        changed. Also ensures required .gitignore entries exist.

        Args:
            workspace_root: Workspace root directory. Required.
            config: Optional base.mk generation configuration.
            canonical_root: Workspace root with canonical base.mk.

        Returns:
            r with SyncResult on success, error message on failure.

        """
        if workspace_root is None:
            return r[m.Infra.SyncResult].fail("workspace_root is required")
        resolved = workspace_root.resolve()
        if not resolved.is_dir():
            return r[m.Infra.SyncResult].fail(
                f"project root does not exist: {resolved}",
            )
        lock_path = resolved / ".sync.lock"
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with lock_path.open("w", encoding=c.Infra.Encoding.DEFAULT) as lock_handle:
                fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX)
                try:
                    return self._sync_locked_content(
                        resolved,
                        config,
                        canonical_root=canonical_root,
                    )
                finally:
                    fcntl.flock(lock_handle.fileno(), fcntl.LOCK_UN)
        except OSError as exc:
            return r[m.Infra.SyncResult].fail(
                f"sync lock acquisition failed: {exc}",
            )

    def _sync_locked_content(
        self,
        resolved: Path,
        config: m.Infra.BaseMkConfig | None,
        *,
        canonical_root: Path | None = None,
    ) -> r[m.Infra.SyncResult]:
        """Execute all sync steps under the file lock."""
        changed = 0
        effective_root = canonical_root or self._canonical_root
        basemk_result = self._sync_basemk(
            resolved,
            config,
            canonical_root=effective_root,
        )
        if basemk_result.is_failure:
            return r[m.Infra.SyncResult].fail(
                basemk_result.error or "base.mk sync failed",
            )
        changed += 1 if basemk_result.value else 0
        gitignore_result = self._ensure_gitignore_entries(
            resolved,
            c.Infra.REQUIRED_GITIGNORE_ENTRIES,
        )
        if gitignore_result.is_failure:
            return r[m.Infra.SyncResult].fail(
                gitignore_result.error or ".gitignore sync failed",
            )
        changed += 1 if gitignore_result.value else 0
        changed += self._sync_makefile_if_needed(resolved, effective_root)
        return r[m.Infra.SyncResult].ok(
            m.Infra.SyncResult(
                files_changed=changed,
                source=resolved,
                target=resolved,
            ),
        )

    def _sync_makefile_if_needed(
        self,
        resolved: Path,
        effective_root: Path | None,
    ) -> int:
        """Sync workspace or project Makefile as appropriate. Returns 1 if changed."""
        is_workspace_root = self._is_workspace_root(resolved, effective_root)
        if is_workspace_root:
            workspace_makefile_result = self._sync_workspace_makefile(resolved)
            if workspace_makefile_result.is_success and workspace_makefile_result.value:
                return 1
        elif (resolved / c.Infra.Files.PYPROJECT_FILENAME).exists():
            makefile_result = self._sync_project_makefile(
                resolved,
                effective_root or resolved,
            )
            if makefile_result.is_success and makefile_result.value:
                return 1
        return 0

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
        if canonical_root is not None and resolved_root == canonical_root.resolve():
            return True
        if (resolved_root / c.Infra.Files.GITMODULES).exists():
            return True
        discovered = u.Infra.discover_projects(resolved_root)
        if discovered.is_failure:
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
        gitignore = workspace_root / c.Infra.Files.GITIGNORE
        try:
            existing_lines: t.StrSequence = []
            if gitignore.exists():
                existing_lines = gitignore.read_text(
                    encoding=c.Infra.Encoding.DEFAULT,
                ).splitlines()
            existing_patterns = {
                line.strip() for line in existing_lines if line.strip()
            }
            missing = [p for p in required if p not in existing_patterns]
            if not missing:
                return r[bool].ok(False)
            with gitignore.open("a", encoding=c.Infra.Encoding.DEFAULT) as handle:
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
        config: m.Infra.BaseMkConfig | None,
        *,
        canonical_root: Path | None = None,
    ) -> r[bool]:
        """Sync base.mk for workspace root and subprojects.

        All projects receive a generated local ``base.mk`` so regeneration is
        fully deterministic from ``make gen`` without relying on deferred
        bootstrap.
        """
        _ = canonical_root
        gen_result = self._generator.generate_basemk(config)
        if gen_result.is_failure:
            return r[bool].fail(gen_result.error or "base.mk generation failed")
        content: str = gen_result.value
        target_path = workspace_root / c.Infra.Files.BASE_MK
        content_hash = self._sha256_content(content)
        if target_path.exists():
            existing_hash = self._sha256_file(target_path)
            if content_hash == existing_hash:
                return r[bool].ok(False)
        return self._atomic_write(target_path, content)

    @staticmethod
    def main() -> int:
        """CLI entry point for workspace sync."""
        parser = u.Infra.create_parser(
            "flext-infra workspace sync",
            "Workspace base.mk sync",
            include_apply=False,
        )
        _ = parser.add_argument(
            "--canonical-root",
            type=Path,
            default=None,
            help="Canonical workspace root",
        )
        args = parser.parse_args()
        cli = u.Infra.resolve(args)
        service = FlextInfraSyncService(
            canonical_root=getattr(args, "canonical_root", None),
        )
        result = service.sync(workspace_root=cli.workspace)
        if result.is_success:
            return 0
        output.error(result.error or "sync failed")
        return 1


main = FlextInfraSyncService.main


if __name__ == "__main__":
    raise SystemExit(FlextInfraSyncService.main())
__all__ = ["FlextInfraSyncService", "main"]
