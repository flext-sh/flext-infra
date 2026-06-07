"""Migrate projects to unified FLEXT infrastructure."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, override

from flext_infra import (
    FlextInfraBaseMkTemplateEngine,
    c,
    m,
    p,
    r,
    s,
    t,
    u,
)
from flext_infra.workspace.base import FlextInfraWorkspaceGeneratorBase


class FlextInfraProjectMigrator(
    s[t.SequenceOf[m.Infra.MigrationResult]],
    FlextInfraWorkspaceGeneratorBase,
):
    """Migrate projects to standardized base.mk, Makefile, and pyproject structure."""

    discovery: Annotated[
        p.Infra.Discovery | None,
        m.Field(exclude=True, description="Optional custom discovery service"),
    ] = None

    @staticmethod
    def _action_text(action: str, *, dry_run: bool) -> str:
        """Action text."""
        return f"[DRY-RUN] {action}" if dry_run else action

    @staticmethod
    def _no_change_result(message: str, *, dry_run: bool) -> p.Result[str]:
        """Return a no-op result: dry-run shows message, normal returns empty."""
        if dry_run:
            return r[str].ok(f"[DRY-RUN] {message}")
        return r[str].ok("")

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
    def execute(self) -> p.Result[t.SequenceOf[m.Infra.MigrationResult]]:
        """Execute the workspace migration flow."""
        dry_run = self.dry_run or not self.apply_changes
        result = self.migrate(
            workspace_root=self.workspace_root,
            dry_run=dry_run,
        )
        if result.failure:
            return result
        migrations: t.SequenceOf[m.Infra.MigrationResult] = result.value
        for migration in migrations:
            u.Cli.info(f"{migration.project}:")
            for change in migration.changes:
                u.Cli.info(f"  + {change}")
            for error in migration.errors:
                u.Cli.error(f"  ! {error}")
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
    ) -> p.Result[t.SequenceOf[m.Infra.MigrationResult]]:
        """Build migration results for all discovered projects in a workspace."""
        resolved_root = workspace_root.resolve()
        if not resolved_root.exists():
            return r[t.SequenceOf[m.Infra.MigrationResult]].fail(
                f"workspace root does not exist: {resolved_root}",
            )
        discovery = self.discovery
        projects_result = (
            discovery.discover_projects(resolved_root)
            if discovery is not None
            else u.Infra.discover_projects(resolved_root)
        )
        if projects_result.failure:
            return r[t.SequenceOf[m.Infra.MigrationResult]].fail(
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
            )
            for project in projects
        ]
        return r[t.SequenceOf[m.Infra.MigrationResult]].ok(migrations)

    def _migrate_basemk(
        self,
        project_root: Path,
        *,
        dry_run: bool,
    ) -> p.Result[str]:
        """Migrate basemk."""
        target = project_root / c.Infra.BASE_MK
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
                "base.mk already up-to-date",
                dry_run=dry_run,
            )
        if not dry_run:
            try:
                u.write_file(target, generated_text, encoding=c.Cli.ENCODING_DEFAULT)
            except OSError as exc:
                return r[str].fail_op("base.mk update", exc)
        return r[str].ok(
            self._action_text(
                "base.mk regenerated via BaseMkGenerator",
                dry_run=dry_run,
            ),
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
                ".gitignore already normalized",
                dry_run=dry_run,
            )
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
                u.write_file(gitignore_path, body, encoding=c.Cli.ENCODING_DEFAULT)
            except OSError as exc:
                return r[str].fail_op(".gitignore update", exc)
        return r[str].ok(
            self._action_text(
                ".gitignore cleaned from scripts/ and normalized",
                dry_run=dry_run,
            ),
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
                include_result.error or "Makefile bootstrap include render failed",
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
            self._action_text(
                "Makefile migrated to bootstrap include",
                dry_run=dry_run,
            ),
        )

    def _apply_bootstrap_include(self, content: str) -> p.Result[str]:
        """Apply bootstrap include."""
        if c.Infra.MAKEFILE_INCLUDE_OLD not in content:
            return r[str].ok(content)
        bootstrap_result = FlextInfraBaseMkTemplateEngine.render_bootstrap_include()
        if bootstrap_result.failure:
            return r[str].fail(
                bootstrap_result.error or "Makefile bootstrap include render failed",
            )
        return r[str].ok(
            content.replace(
                c.Infra.MAKEFILE_INCLUDE_OLD,
                bootstrap_result.value,
            ),
        )

    def _migrate_project(
        self,
        *,
        project: p.Infra.ProjectInfo,
        dry_run: bool,
    ) -> m.Infra.MigrationResult:
        """Migrate project."""
        changes: t.MutableSequenceOf[str] = []
        errors: t.MutableSequenceOf[str] = []
        for step_result in (
            self._migrate_basemk(
                project.path,
                dry_run=dry_run,
            ),
            self._migrate_makefile(project.path, dry_run=dry_run),
            self._migrate_pyproject(
                project.path,
                project_name=project.name,
                dry_run=dry_run,
            ),
            self._migrate_gitignore(project.path, dry_run=dry_run),
        ):
            if step_result.failure:
                errors.append(step_result.error or "migration action failed")
            elif step_result.value:
                changes.append(step_result.value)
        if not changes and not errors:
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
        """Migrate pyproject."""
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
        if c.Infra.PKG_CORE in u.Infra.declared_dependency_names(document):
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
