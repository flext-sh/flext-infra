"""Synchronize pyright and mypy extraPaths from path dependencies."""

from __future__ import annotations

import sys
from collections.abc import MutableSequence, Sequence
from pathlib import Path

from flext_infra import (
    FlextInfraExtraPathsPyrefly,
    FlextInfraExtraPathsResolutionMixin,
    FlextInfraUtilitiesCliDispatch,
    FlextInfraUtilitiesDocsScope,
    FlextInfraUtilitiesPaths,
    c,
    m,
    r,
    t,
    u,
)


class FlextInfraExtraPathsManager(
    FlextInfraExtraPathsResolutionMixin,
    FlextInfraExtraPathsPyrefly,
):
    """Manager for synchronizing pyright and mypy extraPaths from path dependencies."""

    ROOT = FlextInfraUtilitiesPaths.resolve_workspace_root(__file__)

    def __init__(self, workspace_root: Path | None = None) -> None:
        """Initialize the extra paths manager with path resolver and TOML service."""
        super().__init__()
        self.root = workspace_root or self.ROOT
        tool_config_result = u.Infra.load_tool_config()
        if tool_config_result.is_failure:
            msg = tool_config_result.error or "failed to load deps tool config"
            raise ValueError(msg)
        self._tool_config: m.Infra.ToolConfigDocument = tool_config_result.value
        projects_result = FlextInfraUtilitiesDocsScope.discover_projects(self.root)
        self._workspace_project_names = (
            {project.name for project in projects_result.value}
            if projects_result.is_success
            else set()
        )

    def pyrefly_path_rules(self) -> m.Infra.PyreflyConfig.PathRulesConfig:
        """Expose pyrefly path rules through the public resolver contract."""
        return self._tool_config.tools.pyrefly.path_rules

    def pyright_extra_paths(
        self,
        *,
        project_dir: Path,
        is_root: bool,
    ) -> t.StrSequence:
        """Compute pyright extra paths for a project."""
        rules = self._tool_config.tools.pyright.path_rules
        source_root = (
            rules.source_dir
            if (project_dir / rules.source_dir).is_dir()
            else rules.project_root
        )
        configured_typings = (
            rules.root_typings_paths if is_root else rules.project_typings_paths
        )
        typings_paths = [
            relative_path
            for relative_path in configured_typings
            if (project_dir / relative_path).is_dir()
        ]
        return sorted({rules.project_root, source_root, *typings_paths})

    def _apply_paths_to_doc(
        self,
        doc: t.Cli.TomlDocument,
        *,
        project_dir: Path,
        is_root: bool,
    ) -> t.StrSequence:
        """Apply computed extra paths to an in-memory TOMLDocument.

        Returns list of change descriptions (empty if nothing changed).
        """
        expected = self.pyright_extra_paths(
            project_dir=project_dir,
            is_root=is_root,
        )
        tool_table = u.Cli.toml_get_table(doc, c.Infra.TOOL)
        if tool_table is None:
            return list[str]()
        pyright_table = u.Cli.toml_get_table(tool_table, c.Infra.PYRIGHT)
        if pyright_table is None:
            return list[str]()
        mypy_table = u.Cli.toml_get_table(tool_table, c.Infra.MYPY)
        changes: MutableSequence[str] = []
        current_pyright = u.Cli.toml_as_string_list(
            u.Cli.toml_get_item(pyright_table, "extraPaths")
        )
        if current_pyright != expected:
            pyright_table["extraPaths"] = expected
            changes.append("synchronized pyright extraPaths")
        if mypy_table is not None:
            current_mypy = u.Cli.toml_as_string_list(
                u.Cli.toml_get_item(mypy_table, "mypy_path")
            )
            if current_mypy != expected:
                mypy_table["mypy_path"] = expected
                tool_table[c.Infra.MYPY] = mypy_table
                changes.append("synchronized mypy mypy_path")
        if changes:
            tool_table[c.Infra.PYRIGHT] = pyright_table
            doc["tool"] = tool_table
        return changes

    def sync_one(
        self,
        pyproject_path: Path,
        *,
        dry_run: bool = False,
        is_root: bool = False,
    ) -> r[bool]:
        """Synchronize pyright and mypy paths for single pyproject.toml."""
        if not pyproject_path.exists():
            return r[bool].fail(f"pyproject not found: {pyproject_path}")
        doc_result = u.Cli.toml_read_document(pyproject_path)
        if doc_result.is_failure:
            return r[bool].fail(doc_result.error or f"failed to read {pyproject_path}")
        doc: t.Cli.TomlDocument = doc_result.value
        changes = self._apply_paths_to_doc(
            doc,
            project_dir=pyproject_path.parent,
            is_root=is_root,
        )
        if changes and (not dry_run):
            write_result = u.Cli.toml_write_document(pyproject_path, doc)
            if write_result.is_failure:
                return r[bool].fail(
                    write_result.error or f"failed to write {pyproject_path}",
                )
        return r[bool].ok(bool(changes))

    def sync_doc(
        self,
        doc: t.Cli.TomlDocument,
        *,
        project_dir: Path,
        is_root: bool = False,
    ) -> t.StrSequence:
        """Synchronize extra paths on an in-memory TOMLDocument.

        Used by FlextInfraEnsureExtraPathsPhase to modify the doc in-place
        without reading/writing to disk (avoiding overwrite by modernizer).

        Returns:
            List of change descriptions.

        """
        return self._apply_paths_to_doc(
            doc,
            project_dir=project_dir,
            is_root=is_root,
        )

    def sync_extra_paths(
        self,
        *,
        dry_run: bool = False,
        project_dirs: Sequence[Path] | None = None,
    ) -> r[int]:
        """Synchronize extraPaths and mypy_path across projects."""
        if project_dirs:
            for project_dir in project_dirs:
                pyproject = project_dir / c.Infra.Files.PYPROJECT_FILENAME
                sync_result = self.sync_one(
                    pyproject,
                    dry_run=dry_run,
                    is_root=project_dir == self.root,
                )
                if sync_result.is_failure:
                    return r[int].fail(
                        sync_result.error or f"sync failed for {pyproject}",
                    )
                if sync_result.value and (not dry_run):
                    u.Infra.info(f"Updated {pyproject}")
            return r[int].ok(0)
        pyproject = self.root / c.Infra.Files.PYPROJECT_FILENAME
        if not pyproject.exists():
            return r[int].fail(f"Missing {pyproject}")
        sync_result = self.sync_one(pyproject, dry_run=dry_run, is_root=True)
        if sync_result.is_failure:
            return r[int].fail(sync_result.error or f"sync failed for {pyproject}")
        if sync_result.value and (not dry_run):
            u.Infra.info("Updated extraPaths and mypy_path from path dependencies.")
        return r[int].ok(0)

    @staticmethod
    def run_cli(argv: t.StrSequence | None = None) -> int:
        """Execute extra paths synchronization for the canonical deps CLI."""
        parser = u.Infra.create_parser(
            "flext-infra deps extra-paths",
            "Synchronize pyright and mypy extraPaths from path dependencies",
            flags=u.Infra.SharedFlags(include_apply=True, include_project=True),
        )
        args = parser.parse_args([] if argv is None else list(argv))
        cli = u.Infra.resolve(args)
        manager = FlextInfraExtraPathsManager(workspace_root=cli.workspace)
        result = manager.sync_extra_paths(
            dry_run=cli.dry_run,
            project_dirs=cli.project_dirs(),
        )
        if result.is_success:
            return result.value
        u.Infra.error(result.error or "sync failed")
        return 1

    @staticmethod
    def main(argv: t.StrSequence | None = None) -> int:
        """Legacy entrypoint routed through the canonical deps CLI."""
        return FlextInfraUtilitiesCliDispatch.run_command(
            "deps",
            "extra-paths",
            argv,
        )


if __name__ == "__main__":
    sys.exit(FlextInfraExtraPathsManager.main())


__all__ = [
    "FlextInfraExtraPathsManager",
]
