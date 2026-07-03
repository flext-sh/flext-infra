"""Migrate projects to unified FLEXT infrastructure."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, override

from flext_infra import (
    c,
    m,
    p,
    r,
    s,
    t,
    u,
)
from flext_infra.workspace._migrator_artifacts import (
    FlextInfraProjectMigratorArtifactsMixin,
)
from flext_infra.workspace._migrator_pyproject import (
    FlextInfraProjectMigratorPyprojectMixin,
)
from flext_infra.workspace.base import FlextInfraWorkspaceGeneratorBase


class FlextInfraProjectMigrator(
    s[t.SequenceOf[m.Infra.MigrationResult]],
    FlextInfraWorkspaceGeneratorBase,
    FlextInfraProjectMigratorArtifactsMixin,
    FlextInfraProjectMigratorPyprojectMixin,
):
    """Migrate projects to standardized base.mk, Makefile, and pyproject structure."""

    discovery: Annotated[
        p.Infra.Discovery | None,
        m.Field(exclude=True, description="Optional custom discovery service"),
    ] = None

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
            self._migrate_environment_files(project.path, dry_run=dry_run),
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


__all__: list[str] = ["FlextInfraProjectMigrator"]
