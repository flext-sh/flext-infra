"""Rewrite internal FLEXT dependency paths for workspace or standalone mode.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from collections.abc import Sequence
from pathlib import Path

from flext_core import FlextLogger
from flext_infra import FlextInfraDependencyPathSyncRewrite, c, m, t, u


class FlextInfraDependencyPathSync(FlextInfraDependencyPathSyncRewrite):
    """Rewrite internal FLEXT dependency paths for workspace or standalone mode."""

    ROOT = u.Infra.resolve_workspace_root(__file__)
    _log = FlextLogger.create_module_logger(__name__)

    def __init__(self) -> None:
        """Initialize the dependency path sync service with TOML service."""
        self._root = self.ROOT

    def set_workspace_root(self, workspace_root: Path) -> None:
        """Configure workspace root for path resolution."""
        self._root = workspace_root

    def _info(self, message: str) -> None:
        """Emit informational progress through the module logger."""
        _ = self._log.info(message)

    def _workspace_members(
        self,
        projects_list: Sequence[m.Infra.ProjectInfo],
    ) -> t.StrSequence:
        """Return canonical uv workspace members for the root pyproject."""
        return sorted(
            str(project.path.relative_to(self._root))
            for project in projects_list
            if (project.workspace_role == c.Infra.WorkspaceProjectRole.WORKSPACE_MEMBER)
        )

    @staticmethod
    def detect_mode(project_root: Path) -> str:
        """Detect workspace or standalone mode from project structure."""
        for candidate in (project_root, *project_root.parents):
            if (candidate / c.Infra.Files.GITMODULES).exists():
                return c.Infra.ReportKeys.WORKSPACE
        return "standalone"

    def run(self, *, cli: u.Infra.CliArgs, mode: str) -> int:
        """Execute path synchronization for the given CLI arguments."""
        self.set_workspace_root(cli.workspace)
        dry_run = cli.dry_run
        selected_projects: t.StrSequence = cli.project_names() or []

        if mode == "auto":
            mode = self.detect_mode(self._root)

        total_changes = 0
        internal_names: t.Infra.StrSet = set()
        root_pyproject = self._root / c.Infra.Files.PYPROJECT_FILENAME

        if root_pyproject.exists():
            root_data_result = u.Cli.toml_read_document(root_pyproject)
            if root_data_result.is_success:
                root_data: t.Cli.TomlDocument = root_data_result.value
                root_project = u.Cli.toml_get_item(root_data, c.Infra.PROJECT)
                root_mapping = u.Cli.toml_as_mapping(
                    u.Cli.toml_unwrap_item(root_project),
                )
                if root_mapping is not None:
                    root_name = self._mapping_str_value(root_mapping, c.Infra.NAME)
                    if root_name is not None:
                        internal_names.add(root_name)

        discover_result = u.Infra.discover_projects(self._root)
        if discover_result.is_failure:
            discovery_error = discover_result.error or "sync_dep_paths_discovery_failed"
            self._log.error(
                "sync_dep_paths_discovery_failed",
                root=str(self._root),
                error_detail=discovery_error,
            )
            return 1

        projects_list: Sequence[m.Infra.ProjectInfo] = discover_result.value
        all_project_dirs = [project.path for project in projects_list]
        workspace_members = self._workspace_members(projects_list)
        if selected_projects:
            project_dirs = [self._root / project for project in selected_projects]
        else:
            project_dirs = all_project_dirs

        for project_dir in all_project_dirs:
            pyproject = project_dir / c.Infra.Files.PYPROJECT_FILENAME
            if not pyproject.exists():
                continue
            data_result = u.Cli.toml_read_document(pyproject)
            if data_result.is_failure:
                continue
            project_data: t.Cli.TomlDocument = data_result.value
            project_obj = u.Cli.toml_get_item(project_data, c.Infra.PROJECT)
            project_mapping = u.Cli.toml_as_mapping(
                u.Cli.toml_unwrap_item(project_obj),
            )
            if project_mapping is None:
                continue
            project_name = self._mapping_str_value(project_mapping, c.Infra.NAME)
            if project_name is not None:
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
                self._info(f"{prefix}{root_pyproject}:")
                for change in changes:
                    self._info(change)
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
                self._info(f"{prefix}{pyproject}:")
                for change in project_changes:
                    self._info(change)
                total_changes += len(project_changes)

        if total_changes > 0:
            action = "would change" if dry_run else "changed"
            self._info(f"[sync-dep-paths] {action} {total_changes} path(s).")
        return 0

    @staticmethod
    def main(argv: t.StrSequence | None = None) -> int:
        """Entry point for path sync CLI."""
        parser = u.Infra.create_parser(
            "flext-infra deps path-sync",
            "Rewrite internal FLEXT dependency paths for workspace/standalone mode.",
            flags=u.Infra.SharedFlags(include_apply=True, include_project=True),
        )
        _ = parser.add_argument(
            "--mode",
            choices=["workspace", "standalone", "auto"],
            default="auto",
            help="Target mode (default: auto-detect)",
        )
        args = parser.parse_args(argv)
        cli = u.Infra.resolve(args)
        return FlextInfraDependencyPathSync().run(cli=cli, mode=args.mode)


main = FlextInfraDependencyPathSync.main


if __name__ == "__main__":
    sys.exit(FlextInfraDependencyPathSync.main())


__all__ = ["FlextInfraDependencyPathSync"]
