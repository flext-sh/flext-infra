"""Dependency path sync utilities exposed through ``u.Infra``."""

from __future__ import annotations

from pathlib import Path

from flext_cli import u
from flext_core import FlextLogger
from flext_infra import (
    FlextInfraDependencyPathSyncRewrite,
    FlextInfraUtilitiesCli,
    FlextInfraUtilitiesCliDispatch,
    FlextInfraUtilitiesDocsScope,
    c,
    t,
)


class FlextInfraUtilitiesDependencyPathSync(
    FlextInfraDependencyPathSyncRewrite,
):
    """Rewrite internal FLEXT dependency paths for workspace or standalone mode."""

    _log = FlextLogger.create_module_logger(__name__)
    discover_projects = staticmethod(FlextInfraUtilitiesDocsScope.discover_projects)

    @staticmethod
    def detect_mode(project_root: Path) -> str:
        """Detect workspace or standalone mode from project structure."""
        for candidate in (project_root, *project_root.parents):
            if (candidate / c.Infra.Files.GITMODULES).exists():
                return c.Infra.ReportKeys.WORKSPACE
        return "standalone"

    def execute(self, *, cli: FlextInfraUtilitiesCli.CliArgs, mode: str) -> int:
        """Execute path synchronization for the given CLI arguments."""
        workspace_root = cli.workspace
        dry_run = cli.dry_run
        selected_projects: t.StrSequence = cli.project_names() or []

        if mode == "auto":
            mode = self.detect_mode(workspace_root)

        total_changes = 0
        internal_names: t.Infra.StrSet = set()
        root_pyproject = workspace_root / c.Infra.Files.PYPROJECT_FILENAME

        if root_pyproject.exists():
            root_data_result = u.Cli.toml_read_document(root_pyproject)
            if root_data_result.is_success:
                root_data: t.Cli.TomlDocument = root_data_result.value
                root_project = u.Cli.toml_get_item(root_data, c.Infra.PROJECT)
                root_mapping = u.Cli.toml_as_mapping(
                    u.Cli.toml_unwrap_item(root_project),
                )
                root_name = (
                    root_mapping.get(c.Infra.NAME)
                    if root_mapping is not None
                    else None
                )
                if isinstance(root_name, str) and root_name:
                    internal_names.add(root_name)

        discover_result = FlextInfraUtilitiesDocsScope.discover_projects(
            workspace_root,
        )
        if discover_result.is_failure:
            discovery_error = discover_result.error or "sync_dep_paths_discovery_failed"
            self._log.error(
                "sync_dep_paths_discovery_failed",
                root=str(workspace_root),
                error_detail=discovery_error,
            )
            return 1

        projects_list = discover_result.value
        all_project_dirs = [project.path for project in projects_list]
        workspace_members = sorted(
            str(project.path.relative_to(workspace_root))
            for project in projects_list
            if project.workspace_role == c.Infra.WorkspaceProjectRole.WORKSPACE_MEMBER
        )
        if selected_projects:
            project_dirs = [workspace_root / project for project in selected_projects]
        else:
            project_dirs = all_project_dirs

        for project_dir in all_project_dirs:
            pyproject = project_dir / c.Infra.Files.PYPROJECT_FILENAME
            if not pyproject.exists():
                continue
            data_result = u.Cli.toml_read_document(pyproject)
            if data_result.is_failure:
                project_error = data_result.error or "sync_dep_paths_project_invalid"
                self._log.error(
                    "sync_dep_paths_project_invalid",
                    pyproject=str(pyproject),
                    error_detail=project_error,
                )
                return 1
            project_data: t.Cli.TomlDocument = data_result.value
            project_obj = u.Cli.toml_get_item(project_data, c.Infra.PROJECT)
            project_mapping = u.Cli.toml_as_mapping(
                u.Cli.toml_unwrap_item(project_obj),
            )
            if project_mapping is None:
                continue
            project_name = project_mapping.get(c.Infra.NAME)
            if isinstance(project_name, str) and project_name:
                internal_names.add(project_name)

        if not selected_projects and root_pyproject.exists():
            changes_result = self.rewrite_dep_paths(
                root_pyproject,
                mode=mode,
                internal_names=internal_names,
                workspace_members=workspace_members,
                is_root=True,
                dry_run=dry_run,
            )
            if changes_result.is_failure:
                root_error = changes_result.error or "sync_dep_paths_root_failed"
                self._log.error(
                    "sync_dep_paths_root_failed",
                    pyproject=str(root_pyproject),
                    error_detail=root_error,
                )
                return 1
            changes: t.StrSequence = changes_result.value
            if changes:
                prefix = "[DRY-RUN] " if dry_run else ""
                _ = self._log.info(f"{prefix}{root_pyproject}:")
                for change in changes:
                    _ = self._log.info(change)
                total_changes += len(changes)

        for project_dir in sorted(project_dirs):
            pyproject = project_dir / c.Infra.Files.PYPROJECT_FILENAME
            if not pyproject.exists():
                continue
            changes_result = self.rewrite_dep_paths(
                pyproject,
                mode=mode,
                internal_names=internal_names,
                workspace_members=workspace_members,
                is_root=False,
                dry_run=dry_run,
            )
            if changes_result.is_failure:
                project_error = changes_result.error or "sync_dep_paths_project_failed"
                self._log.error(
                    "sync_dep_paths_project_failed",
                    pyproject=str(pyproject),
                    error_detail=project_error,
                )
                return 1
            project_changes: t.StrSequence = changes_result.value
            if project_changes:
                prefix = "[DRY-RUN] " if dry_run else ""
                _ = self._log.info(f"{prefix}{pyproject}:")
                for change in project_changes:
                    _ = self._log.info(change)
                total_changes += len(project_changes)

        if total_changes > 0:
            action = "would change" if dry_run else "changed"
            _ = self._log.info(f"[sync-dep-paths] {action} {total_changes} path(s).")
        return 0

    @classmethod
    def run_cli(cls, argv: t.StrSequence | None = None) -> int:
        """Execute path synchronization for the canonical deps CLI."""
        parser = FlextInfraUtilitiesCli.create_parser(
            "flext-infra deps path-sync",
            "Rewrite internal FLEXT dependency paths for workspace/standalone mode.",
            flags=FlextInfraUtilitiesCli.SharedFlags(
                include_apply=True,
                include_project=True,
            ),
        )
        _ = parser.add_argument(
            "--mode",
            choices=["workspace", "standalone", "auto"],
            default="auto",
            help="Target mode (default: auto-detect)",
        )
        args = parser.parse_args([] if argv is None else list(argv))
        cli = FlextInfraUtilitiesCli.resolve(args)
        return cls().execute(
            cli=cli,
            mode=args.mode,
        )

    @classmethod
    def main(cls, argv: t.StrSequence | None = None) -> int:
        """Legacy entrypoint routed through the canonical deps CLI."""
        return FlextInfraUtilitiesCliDispatch.run_command(
            "deps",
            "path-sync",
            argv,
        )


__all__ = ["FlextInfraUtilitiesDependencyPathSync"]
