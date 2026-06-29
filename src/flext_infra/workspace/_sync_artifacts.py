"""Workspace artifact sync steps — extracted concern of FlextInfraSyncService."""

from __future__ import annotations

from pathlib import Path

from flext_infra import c, m, p, r, t, u
from flext_infra.workspace.base import FlextInfraWorkspaceGeneratorBase
from flext_infra.workspace.project_makefile import FlextInfraProjectMakefileUpdater
from flext_infra.workspace.workspace_makefile import (
    FlextInfraWorkspaceMakefileGenerator,
)


class FlextInfraWorkspaceSyncArtifactsMixin(FlextInfraWorkspaceGeneratorBase):
    """Per-artifact sync steps (base.mk, Makefile, .gitignore) under the lock.

    Composed into FlextInfraSyncService via MRO; each step is idempotent
    (SHA256 / exact-line compare) and surfaces generator/IO failures as r.fail.
    Inherits the generator field + ``_get_generator`` from the workspace base.
    """

    def _sync_makefile_if_needed(
        self,
        resolved: Path,
        effective_root: Path | None,
    ) -> p.Result[int]:
        """Sync workspace or project Makefile and surface generator failures."""
        is_workspace_root = self._is_workspace_root(resolved, effective_root)
        if is_workspace_root:
            workspace_makefile_result = FlextInfraWorkspaceMakefileGenerator().generate(
                resolved
            )
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
    ) -> p.Result[bool]:
        """Sync the generated section of a project Makefile from pyproject.toml."""
        return FlextInfraProjectMakefileUpdater().update(
            workspace_root,
            canonical_root=canonical_root,
        )

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
    ) -> p.Result[bool]:
        """Idempotently append missing .gitignore entries (exact-line match).

        Never removes or reorders existing entries; returns True iff changed.
        """
        gitignore = workspace_root / c.Infra.GITIGNORE
        existing_result = self._gitignore_existing_patterns(gitignore)
        if existing_result.failure:
            return r[bool].fail(existing_result.error or ".gitignore read failed")
        missing = [p for p in required if p not in existing_result.value]
        if not missing:
            return r[bool].ok(False)
        return self._append_gitignore_entries(gitignore, missing)

    def _gitignore_existing_patterns(
        self,
        gitignore: Path,
    ) -> p.Result[frozenset[str]]:
        """Read existing non-empty .gitignore patterns."""
        if not gitignore.exists():
            return r[frozenset[str]].ok(frozenset())
        read = u.Cli.files_read_text(gitignore)
        if read.failure:
            return r[frozenset[str]].fail(read.error or ".gitignore read failed")
        return r[frozenset[str]].ok(
            frozenset(line.strip() for line in read.value.splitlines() if line.strip())
        )

    def _append_gitignore_entries(
        self,
        gitignore: Path,
        missing: t.StrSequence,
    ) -> p.Result[bool]:
        """Append missing generated .gitignore entries."""
        try:
            with gitignore.open("a", encoding=c.Cli.ENCODING_DEFAULT) as handle:
                _ = handle.write(
                    "\n# --- workspace-sync: required ignores (auto-managed) ---\n",
                )
                for pattern in missing:
                    _ = handle.write(f"{pattern}\n")
            return r[bool].ok(True)
        except OSError as exc:
            return r[bool].fail_op(".gitignore update", exc)

    def _sync_pre_commit_config(
        self,
        workspace_root: Path,
    ) -> p.Result[bool]:
        """Sync the workspace pre-commit config from the canonical SSOT."""
        target_path = workspace_root / ".pre-commit-config.yaml"
        content: str = c.Infra.PRE_COMMIT_CONFIG
        content_hash = u.Cli.sha256_content(content)
        if target_path.exists():
            existing_hash = u.Cli.sha256_file(target_path)
            if content_hash == existing_hash:
                return r[bool].ok(False)
        return u.Cli.atomic_write_text_file(target_path, content)

    @staticmethod
    def _is_flext_infra_root(workspace_root: Path) -> bool:
        """Return True when the path is the flext-infra project root."""
        return (workspace_root / "src" / "flext_infra" / "__init__.py").is_file()

    def _sync_basemk(
        self,
        workspace_root: Path,
        settings: m.Infra.BaseMkConfig | None,
        *,
        canonical_root: Path | None = None,
    ) -> p.Result[bool]:
        """Sync base.mk for workspace root and subprojects.

        The canonical ``base.mk`` now lives only in ``flext-infra``; other
        projects include it via the generated Makefile bootstrap.
        """
        _ = canonical_root
        generator = self._get_generator()
        gen_result = generator.generate_basemk(settings)
        if gen_result.failure:
            return r[bool].fail(gen_result.error or "base.mk generation failed")
        content: str = gen_result.value
        target_path = workspace_root / c.Infra.BASE_MK
        if not self._is_flext_infra_root(workspace_root):
            return r[bool].ok(False)
        content_hash = u.Cli.sha256_content(content)
        if target_path.exists():
            existing_hash = u.Cli.sha256_file(target_path)
            if content_hash == existing_hash:
                return r[bool].ok(False)
        return u.Cli.atomic_write_text_file(target_path, content)


__all__: list[str] = ["FlextInfraWorkspaceSyncArtifactsMixin"]
