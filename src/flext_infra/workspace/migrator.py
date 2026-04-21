"""Migrate projects to unified FLEXT infrastructure."""

from __future__ import annotations

from collections.abc import (
    MutableSequence,
    Sequence,
)
from pathlib import Path
from typing import Annotated, override

from flext_infra import (
    FlextInfraBaseMkGenerator,
    FlextInfraBaseMkTemplateEngine,
    c,
    m,
    p,
    r,
    s,
    t,
    u,
)


class FlextInfraProjectMigrator(s[Sequence[m.Infra.MigrationResult]]):
    """Migrate projects to standardized base.mk, Makefile, and pyproject structure."""

    discovery: Annotated[
        p.Infra.Discovery | None,
        m.Field(exclude=True, description="Optional custom discovery service"),
    ] = None
    generator: Annotated[
        FlextInfraBaseMkGenerator | None,
        m.Field(exclude=True, description="Optional custom generator service"),
    ] = None

    def _get_discovery(self) -> p.Infra.Discovery | None:
        """Return the configured discovery service."""
        return self.discovery

    def _get_generator(self) -> FlextInfraBaseMkGenerator:
        """Return the configured generator."""
        return self.generator or FlextInfraBaseMkGenerator()

    @staticmethod
    def _action_text(action: str, *, dry_run: bool) -> str:
        return f"[DRY-RUN] {action}" if dry_run else action

    @staticmethod
    def _no_change_result(message: str, *, dry_run: bool) -> p.Result[str]:
        """Return a no-op result: dry-run shows message, normal returns empty."""
        if dry_run:
            return r[str].ok(f"[DRY-RUN] {message}")
        return r[str].ok("")

    @staticmethod
    def _append_result(
        result: p.Result[str],
        changes: MutableSequence[str],
        errors: MutableSequence[str],
    ) -> None:
        if result.failure:
            errors.append(result.error or "migration action failed")
            return
        val: str = result.value
        if val:
            changes.append(val)

    @staticmethod
    def _has_flext_core_dependency(document: t.Cli.TomlDocument) -> bool:
        return c.Infra.PKG_CORE in u.Infra.declared_dependency_names(document)

    @staticmethod
    def _workspace_root_project(
        workspace_root: Path,
    ) -> m.Infra.ProjectInfo | None:
        """Detect workspace root as a project if it has Makefile, pyproject.toml, and .git."""
        has_makefile = (workspace_root / c.Infra.MAKEFILE_FILENAME).is_file()
        has_pyproject = (workspace_root / c.Infra.PYPROJECT_FILENAME).is_file()
        has_git = (workspace_root / c.Infra.GIT_DIR).exists()
        if not (has_makefile and has_pyproject and has_git):
            return None
        return m.Infra.ProjectInfo(
            name=workspace_root.name,
            path=workspace_root,
            stack="python/workspace",
            has_tests=(workspace_root / c.Infra.DIR_TESTS).is_dir(),
            has_src=(workspace_root / c.Infra.DEFAULT_SRC_DIR).is_dir(),
        )

    @override
    def execute(self) -> p.Result[Sequence[m.Infra.MigrationResult]]:
        """Execute the workspace migration flow."""
        dry_run = self.dry_run or not self.apply_changes
        result = self.migrate(
            workspace_root=self.workspace_root,
            dry_run=dry_run,
        )
        if result.failure:
            return result
        migrations: Sequence[m.Infra.MigrationResult] = result.value
        failed_projects = 0
        for migration in migrations:
            u.Cli.info(f"{migration.project}:")
            for change in migration.changes:
                u.Cli.info(f"  + {change}")
            for error in migration.errors:
                u.Cli.error(f"  ! {error}")
            if migration.errors:
                failed_projects += 1
        total_changes = sum(len(migration.changes) for migration in migrations)
        total_errors = sum(len(migration.errors) for migration in migrations)
        u.Cli.info(
            f"Total: {total_changes} change(s), {total_errors} error(s) across {len(migrations)} project(s)"
        )
        if dry_run:
            u.Cli.info("(dry-run — no files modified)")
        return result

    def migrate(
        self,
        *,
        workspace_root: Path,
        dry_run: bool,
    ) -> p.Result[Sequence[m.Infra.MigrationResult]]:
        """Build migration results for all discovered projects in a workspace."""
        resolved_root = workspace_root.resolve()
        if not resolved_root.exists():
            return r[Sequence[m.Infra.MigrationResult]].fail(
                f"workspace root does not exist: {resolved_root}",
            )
        discovery = self._get_discovery()
        projects_result = (
            discovery.discover_projects(resolved_root)
            if discovery is not None
            else u.Infra.discover_projects(resolved_root)
        )
        if projects_result.failure:
            return r[Sequence[m.Infra.MigrationResult]].fail(
                projects_result.error or "workspace discovery failed",
            )
        projects_by_path: dict[Path, m.Infra.ProjectInfo] = {
            project.path.resolve(): project for project in projects_result.value
        }
        workspace_project = self._workspace_root_project(resolved_root)
        if workspace_project is not None:
            projects_by_path.setdefault(resolved_root, workspace_project)
        projects = [
            projects_by_path[path]
            for path in sorted(projects_by_path, key=lambda current: str(current))
        ]
        migrations = [
            self._migrate_project(
                project=project,
                dry_run=dry_run,
                workspace_root=resolved_root,
            )
            for project in projects
        ]
        return r[Sequence[m.Infra.MigrationResult]].ok(migrations)

    def _migrate_basemk(
        self,
        project_root: Path,
        *,
        dry_run: bool,
        is_workspace_root: bool = False,
    ) -> p.Result[str]:
        _ = is_workspace_root
        target = project_root / c.Infra.BASE_MK
        generator = self._get_generator()
        generated = generator.generate_basemk()
        if generated.failure:
            return r[str].fail(generated.error or "base.mk generation failed")
        generated_text: str = generated.value
        current = (
            target.read_text(encoding=c.Infra.ENCODING_DEFAULT)
            if target.exists()
            else ""
        )
        if u.Cli.sha256_content(current) == u.Cli.sha256_content(generated_text):
            if dry_run:
                return r[str].ok(
                    self._action_text("base.mk already up-to-date", dry_run=True),
                )
            return r[str].ok("")
        if not dry_run:
            try:
                u.write_file(target, generated_text, encoding=c.Infra.ENCODING_DEFAULT)
            except OSError as exc:
                return r[str].fail(f"base.mk update failed: {exc}")
        return r[str].ok(
            self._action_text(
                "base.mk regenerated via BaseMkGenerator",
                dry_run=dry_run,
            ),
        )

    def _migrate_gitignore(self, project_root: Path, *, dry_run: bool) -> p.Result[str]:
        gitignore_path = project_root / c.Infra.GITIGNORE
        try:
            existing_lines = (
                gitignore_path.read_text(encoding=c.Infra.ENCODING_DEFAULT).splitlines()
                if gitignore_path.exists()
                else list[str]()
            )
        except OSError as exc:
            return r[str].fail(f".gitignore read failed: {exc}")
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
            if dry_run:
                return r[str].ok(
                    self._action_text(".gitignore already normalized", dry_run=True),
                )
            return r[str].ok("")
        next_lines = list(filtered)
        if missing:
            if next_lines and next_lines[-1].strip():
                next_lines.append("")
            next_lines.append(
                "# --- workspace-migrate: required ignores (auto-managed) ---",
            )
            next_lines.extend(missing)
        if not dry_run:
            body = "\n".join(next_lines).rstrip("\n") + "\n"
            try:
                u.write_file(gitignore_path, body, encoding=c.Infra.ENCODING_DEFAULT)
            except OSError as exc:
                return r[str].fail(f".gitignore update failed: {exc}")
        return r[str].ok(
            self._action_text(
                ".gitignore cleaned from scripts/ and normalized",
                dry_run=dry_run,
            ),
        )

    def _migrate_makefile(self, project_root: Path, *, dry_run: bool) -> p.Result[str]:
        makefile_path = project_root / c.Infra.MAKEFILE_FILENAME
        if not makefile_path.exists():
            return self._no_change_result("Makefile not found", dry_run=dry_run)
        try:
            original = makefile_path.read_text(encoding=c.Infra.ENCODING_DEFAULT)
        except OSError as exc:
            return r[str].fail(f"Makefile read failed: {exc}")
        updated = original
        for before, after in c.Infra.MAKEFILE_REPLACEMENTS:
            updated = updated.replace(before, after)
        updated = self._apply_bootstrap_include(updated)
        if updated == original:
            return self._no_change_result("Makefile already migrated", dry_run=dry_run)
        if not dry_run:
            try:
                u.write_file(makefile_path, updated, encoding=c.Infra.ENCODING_DEFAULT)
            except OSError as exc:
                return r[str].fail(f"Makefile update failed: {exc}")
        return r[str].ok(
            self._action_text(
                "Makefile migrated to bootstrap include",
                dry_run=dry_run,
            ),
        )

    def _apply_bootstrap_include(self, content: str) -> str:
        if c.Infra.MAKEFILE_INCLUDE_OLD not in content:
            return content
        bootstrap_result = FlextInfraBaseMkTemplateEngine.render_bootstrap_include()
        if bootstrap_result.failure:
            return content
        return content.replace(
            c.Infra.MAKEFILE_INCLUDE_OLD,
            bootstrap_result.value,
        )

    def _migrate_project(
        self,
        *,
        project: p.Infra.ProjectInfo,
        dry_run: bool,
        workspace_root: Path,
    ) -> m.Infra.MigrationResult:
        is_root = project.path.resolve() == workspace_root.resolve()
        changes: MutableSequence[str] = []
        errors: MutableSequence[str] = []
        self._append_result(
            self._migrate_basemk(
                project.path,
                dry_run=dry_run,
                is_workspace_root=is_root,
            ),
            changes,
            errors,
        )
        self._append_result(
            self._migrate_makefile(project.path, dry_run=dry_run),
            changes,
            errors,
        )
        self._append_result(
            self._migrate_pyproject(
                project.path,
                project_name=project.name,
                dry_run=dry_run,
            ),
            changes,
            errors,
        )
        self._append_result(
            self._migrate_gitignore(project.path, dry_run=dry_run),
            changes,
            errors,
        )
        if not changes and (not errors):
            changes.append("no changes needed")
        return m.Infra.MigrationResult(
            project=project.name,
            changes=changes,
            errors=errors,
        )

    def _migrate_pyproject(
        self,
        project_root: Path,
        *,
        project_name: str,
        dry_run: bool,
    ) -> p.Result[str]:
        pyproject_path = project_root / c.Infra.PYPROJECT_FILENAME
        if not pyproject_path.exists():
            return self._no_change_result("pyproject.toml not found", dry_run=dry_run)
        if project_name == c.Infra.PKG_CORE:
            return self._no_change_result(
                "pyproject.toml dependency unchanged for flext-core",
                dry_run=dry_run,
            )
        document_result = u.Cli.toml_read_document(pyproject_path)
        if document_result.failure:
            return r[str].fail(
                document_result.error or "pyproject parse failed",
            )
        document: t.Cli.TomlDocument = document_result.value
        if self._has_flext_core_dependency(document):
            return self._no_change_result(
                "pyproject.toml already includes flext-core dependency",
                dry_run=dry_run,
            )
        return self._apply_flext_core_dependency(
            document, pyproject_path, dry_run=dry_run
        )

    def _apply_flext_core_dependency(
        self,
        document: t.Cli.TomlDocument,
        pyproject_path: Path,
        *,
        dry_run: bool,
    ) -> p.Result[str]:
        """Add flext-core dependency to the pyproject document and write if not dry-run."""
        project_table = u.Cli.toml_ensure_table(document, c.Infra.PROJECT)
        dependencies_item = u.Cli.toml_item_child(project_table, c.Infra.DEPENDENCIES)
        dependencies = list(
            u.Cli.toml_as_string_list(
                dependencies_item if dependencies_item is not None else [],
            ),
        )
        dependency_spec = c.Infra.PKG_CORE
        if dependency_spec not in dependencies:
            dependencies.append(dependency_spec)
        project_table[c.Infra.DEPENDENCIES] = dependencies
        if not dry_run:
            write_result = u.Cli.toml_write_document(pyproject_path, document)
            if write_result.failure:
                return r[str].fail(
                    write_result.error or "pyproject update failed",
                )
        return r[str].ok(
            self._action_text(
                "pyproject.toml adds flext-core dependency",
                dry_run=dry_run,
            ),
        )


__all__: list[str] = ["FlextInfraProjectMigrator"]
