"""Per-project text-file migration (base.mk, .gitignore, Makefile) — extracted.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core import r
from flext_infra import c, p, t, u
from flext_infra.basemk.renderer import FlextInfraBaseMkTemplateRenderer
from flext_infra.workspace.environment import FlextInfraWorkspaceEnvironment

if TYPE_CHECKING:
    from pathlib import Path

    from flext_infra.basemk.generator import FlextInfraBaseMkGenerator


class FlextInfraProjectMigratorArtifactsMixin:
    """Migrate base.mk / .gitignore / Makefile for one project.

    Composed into FlextInfraProjectMigrator via inheritance; borrows
    ``_get_generator`` (workspace-generator base) via MRO.
    """

    if TYPE_CHECKING:

        def _get_generator(self) -> FlextInfraBaseMkGenerator: ...

    @staticmethod
    def _action_text(action: str, *, dry_run: bool) -> str:
        """Return the action text, prefixed for dry-run mode."""
        return f"[DRY-RUN] {action}" if dry_run else action

    @staticmethod
    def _no_change_result(message: str, *, dry_run: bool) -> p.Result[str]:
        """Return a no-op result: dry-run shows message, normal returns empty."""
        if dry_run:
            return r[str].ok(f"[DRY-RUN] {message}")
        return r[str].ok("")

    @staticmethod
    def _is_flext_infra_root(project_root: Path) -> bool:
        """Return True when the path is the flext-infra project root."""
        return (project_root / "src" / "flext_infra" / "__init__.py").is_file()

    def _migrate_basemk(self, project_root: Path, *, dry_run: bool) -> p.Result[str]:
        """Migrate basemk.

        The canonical base.mk now lives only in flext-infra. Other projects
        must not keep a local copy.

        Returns:
            ``r.ok`` with a human-readable action description, or ``r.fail``
            when generation, read, or write fails.
        """
        target = project_root / c.Infra.BASE_MK
        is_canonical = self._is_flext_infra_root(project_root)

        if not is_canonical:
            if not target.exists():
                return self._no_change_result(
                    "no local base.mk to remove", dry_run=dry_run
                )
            if not dry_run:
                try:
                    target.unlink()
                except OSError as exc:
                    return r[str].fail_op("base.mk removal", exc)
            return r[str].ok(
                self._action_text("removed obsolete local base.mk", dry_run=dry_run)
            )

        generator = self._get_generator()
        generated = generator.generate_basemk()
        if generated.failure:
            return r[str].fail(generated.error or "base.mk generation failed")
        generated_text: str = generated.value
        current = ""
        if target.exists():
            read = u.Cli.files_read_text(target)
            if read.failure:
                return r[str].fail(f"base.mk read failed: {read.error}")
            current = read.value
        if u.Cli.sha256_content(current) == u.Cli.sha256_content(generated_text):
            return self._no_change_result(
                "canonical base.mk already up-to-date", dry_run=dry_run
            )
        if not dry_run:
            try:
                u.write_file(target, generated_text, encoding=c.Cli.ENCODING_DEFAULT)
            except OSError as exc:
                return r[str].fail_op("base.mk update", exc)
        return r[str].ok(
            self._action_text(
                "canonical base.mk regenerated via BaseMkGenerator", dry_run=dry_run
            )
        )

    def _migrate_gitignore(self, project_root: Path, *, dry_run: bool) -> p.Result[str]:
        """Migrate gitignore."""
        gitignore_path = project_root / c.Infra.GITIGNORE
        existing_lines: t.StrSequence = list[str]()
        if gitignore_path.exists():
            read = u.Cli.files_read_text(gitignore_path)
            if read.failure:
                return r[str].fail(f".gitignore read failed: {read.error}")
            existing_lines = read.value.splitlines()
        filtered = [
            line
            for line in existing_lines
            if line.strip() not in c.Infra.GITIGNORE_REMOVE_EXACT
        ]
        existing_patterns = {line.strip() for line in filtered if line.strip()}
        missing = [
            pattern
            for pattern in c.Infra.REQUIRED_GITIGNORE_ENTRIES
            if pattern not in existing_patterns
        ]
        if not missing and len(filtered) == len(existing_lines):
            return self._no_change_result(
                ".gitignore already normalized", dry_run=dry_run
            )
        next_lines = list(filtered)
        if missing:
            if next_lines and next_lines[-1].strip():
                next_lines.append("")
            next_lines.append(
                "# --- workspace-migrate: required ignores (auto-managed) ---"
            )
            next_lines.extend(missing)
        if not dry_run:
            body = "\n".join(next_lines).rstrip("\n") + "\n"
            try:
                u.write_file(gitignore_path, body, encoding=c.Cli.ENCODING_DEFAULT)
            except OSError as exc:
                return r[str].fail_op(".gitignore update", exc)
        return r[str].ok(
            self._action_text(
                ".gitignore cleaned from scripts/ and normalized", dry_run=dry_run
            )
        )

    def _migrate_makefile(self, project_root: Path, *, dry_run: bool) -> p.Result[str]:
        """Migrate makefile."""
        makefile_path = project_root / c.Infra.MAKEFILE_FILENAME
        if not makefile_path.exists():
            return self._no_change_result("Makefile not found", dry_run=dry_run)
        read = u.Cli.files_read_text(makefile_path)
        if read.failure:
            return r[str].fail(f"Makefile read failed: {read.error}")
        original = read.value
        updated = original
        for before, after in c.Infra.MAKEFILE_REPLACEMENTS:
            updated = updated.replace(before, after)
        include_result = self._apply_bootstrap_include(updated)
        if include_result.failure:
            return r[str].fail(
                include_result.error or "Makefile bootstrap include render failed"
            )
        updated = include_result.value
        if updated == original:
            return self._no_change_result("Makefile already migrated", dry_run=dry_run)
        if not dry_run:
            try:
                u.write_file(makefile_path, updated, encoding=c.Cli.ENCODING_DEFAULT)
            except OSError as exc:
                return r[str].fail_op("Makefile update", exc)
        return r[str].ok(
            self._action_text("Makefile migrated to bootstrap include", dry_run=dry_run)
        )

    def _migrate_environment_files(
        self, project_root: Path, *, dry_run: bool
    ) -> p.Result[str]:
        """Migrate generated direnv and mise environment files."""
        result = FlextInfraWorkspaceEnvironment.sync_environment_files(
            project_root, apply=not dry_run
        )
        if result.failure:
            return r[str].fail(result.error or "workspace environment sync failed")
        if result.value:
            return r[str].ok(
                self._action_text(
                    "workspace environment files normalized", dry_run=dry_run
                )
            )
        return self._no_change_result(
            "workspace environment files already normalized", dry_run=dry_run
        )

    def _apply_bootstrap_include(self, content: str) -> p.Result[str]:
        """Apply bootstrap include."""
        if c.Infra.MAKEFILE_INCLUDE_OLD not in content:
            return r[str].ok(content)
        bootstrap_result = FlextInfraBaseMkTemplateRenderer.render_bootstrap_include()
        if bootstrap_result.failure:
            return r[str].fail(
                bootstrap_result.error or "Makefile bootstrap include render failed"
            )
        return r[str].ok(
            content.replace(c.Infra.MAKEFILE_INCLUDE_OLD, bootstrap_result.value)
        )


__all__: list[str] = ["FlextInfraProjectMigratorArtifactsMixin"]
