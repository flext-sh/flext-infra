"""Dependency path sync utilities exposed through ``u.Infra``."""

from __future__ import annotations

from collections.abc import MutableSequence
from pathlib import Path

from tomlkit.items import InlineTable, Table as TomlTable

from flext_cli import u
from flext_core import r
from flext_infra import (
    FlextInfraModelsDeps,
    FlextInfraUtilitiesDocsScope,
    FlextInfraUtilitiesTomlParse,
    c,
    t,
)


class FlextInfraUtilitiesDependencyPathSync(
    FlextInfraUtilitiesTomlParse,
):
    """Rewrite internal FLEXT dependency paths for workspace or standalone mode."""

    _log = u.fetch_logger(__name__)
    discover_projects = staticmethod(FlextInfraUtilitiesDocsScope.discover_projects)

    def _rewrite_pep621(
        self,
        doc: t.Cli.TomlDocument,
        *,
        internal_names: t.Infra.StrSet,
    ) -> t.Infra.Pair[t.StrSequence, t.Infra.StrSet]:
        project_section = u.Cli.toml_table_child(doc, c.Infra.PROJECT)
        if project_section is None:
            return ([], set())
        deps: t.StrSequence = u.Cli.toml_as_string_list(
            u.Cli.toml_item_child(project_section, c.Infra.DEPENDENCIES)
        )
        if not deps:
            return ([], set())
        changes: MutableSequence[str] = []
        updated_deps: MutableSequence[str] = []
        internal_deps: t.Infra.StrSet = set()
        for item in deps:
            requirement_part, _, marker_part = item.partition(";")
            dep_name = type(self).dep_name(requirement_part)
            if not dep_name or dep_name not in internal_names:
                updated_deps.append(item)
                continue
            internal_deps.add(dep_name)
            new_entry = (
                f"{dep_name} ;{marker_part}"
                if marker_part and " @ " in requirement_part
                else dep_name
                if " @ " in requirement_part
                else item
            )
            if item == new_entry:
                updated_deps.append(item)
                continue
            changes.append(f"  PEP621: {item} -> {new_entry}")
            updated_deps.append(new_entry)
        if changes:
            project_section[c.Infra.DEPENDENCIES] = updated_deps
        return (changes, internal_deps)

    def _rewrite_uv_sources(
        self,
        doc: t.Cli.TomlDocument,
        *,
        is_root: bool,
        mode: str,
        internal_names: t.Infra.StrSet,
        internal_deps: t.Infra.StrSet,
        workspace_members: t.StrSequence,
    ) -> t.StrSequence:
        expected_names: t.Infra.StrSet = (
            set(workspace_members)
            if is_root and mode == c.Infra.RK_WORKSPACE
            else set(internal_deps)
        )
        if not expected_names:
            return []
        changes: MutableSequence[str] = []
        tool_section = u.Cli.toml_ensure_table(doc, c.Infra.TOOL)
        uv_section = u.Cli.toml_ensure_table(tool_section, "uv")
        sources = u.Cli.toml_ensure_table(uv_section, "sources")
        for source_key in [str(key) for key in sources]:
            if source_key in internal_names and source_key not in expected_names:
                del sources[source_key]
                changes.append(f"  uv.sources: removed stale source {source_key}")
        for dep_name in sorted(expected_names):
            expected = (
                {"workspace": True}
                if mode == c.Infra.RK_WORKSPACE
                else {
                    "path": f"{c.Infra.FLEXT_DEPS_DIR}/{dep_name}",
                    "editable": True,
                }
            )
            current_table = u.Cli.toml_table_child(sources, dep_name)
            current_map: t.Infra.ContainerDict = (
                dict(current_table.unwrap()) if current_table is not None else {}
            )
            if current_map == expected:
                continue
            source_table = u.Cli.toml_table()
            for key in sorted(expected):
                source_table[key] = expected[key]
            sources[dep_name] = source_table
            changes.append(f"  uv.sources: synced source for {dep_name}")
        return changes

    def _rewrite_uv_workspace(
        self,
        doc: t.Cli.TomlDocument,
        *,
        is_root: bool,
        members: t.StrSequence,
    ) -> t.StrSequence:
        if not is_root:
            return []
        changes: MutableSequence[str] = []
        tool_section = u.Cli.toml_ensure_table(doc, c.Infra.TOOL)
        uv_section = u.Cli.toml_ensure_table(tool_section, "uv")
        workspace_section = u.Cli.toml_ensure_table(uv_section, "workspace")
        expected_members = sorted(set(members))
        current_members = u.Cli.toml_as_string_list(
            u.Cli.toml_item_child(workspace_section, "members")
        )
        if current_members != expected_members:
            workspace_section["members"] = u.Cli.toml_array(expected_members)
            changes.append("  uv.workspace: members synchronized")
        return changes

    @classmethod
    def _rewrite_poetry(
        cls,
        doc: t.Cli.TomlDocument,
        *,
        is_root: bool,
        mode: str,
    ) -> t.StrSequence:
        tool_section = u.Cli.toml_table_child(doc, c.Infra.TOOL)
        if tool_section is None:
            return []
        poetry_section = u.Cli.toml_table_child(tool_section, c.Infra.POETRY)
        if poetry_section is None:
            return []
        deps = u.Cli.toml_table_child(poetry_section, c.Infra.DEPENDENCIES)
        if deps is None:
            return []
        changes: MutableSequence[str] = []
        for dep_key_raw in deps:
            value = deps[dep_key_raw]
            if not isinstance(value, TomlTable | InlineTable):
                continue
            raw_path = value.get(c.Infra.PATH)
            if not isinstance(raw_path, str) or not raw_path.strip():
                continue
            dep_name = cls.dep_name(raw_path)
            if not dep_name:
                continue
            new_path = (
                dep_name
                if mode == c.Infra.RK_WORKSPACE and is_root
                else (
                    f"../{dep_name}"
                    if mode == c.Infra.RK_WORKSPACE
                    else f"{c.Infra.FLEXT_DEPS_DIR}/{dep_name}"
                )
            )
            if raw_path == new_path:
                continue
            changes.append(
                f"  Poetry: {dep_key_raw}.path = {raw_path!r} -> {new_path!r}",
            )
            value[c.Infra.PATH] = new_path
        return changes

    def rewrite_dep_paths(
        self,
        pyproject_path: Path,
        *,
        mode: str,
        internal_names: t.Infra.StrSet,
        workspace_members: t.StrSequence,
        is_root: bool = False,
        dry_run: bool = False,
    ) -> r[t.StrSequence]:
        """Rewrite PEP 621 and Poetry dependency paths."""
        doc_result = u.Cli.toml_read_document(pyproject_path)
        if doc_result.failure:
            return r[t.StrSequence].fail(
                doc_result.error or "failed to read TOML document",
            )
        doc = doc_result.value
        pep_changes, internal_deps = self._rewrite_pep621(
            doc,
            internal_names=internal_names,
        )
        changes: MutableSequence[str] = list(pep_changes)
        changes += list(
            self._rewrite_uv_sources(
                doc,
                is_root=is_root,
                mode=mode,
                internal_names=internal_names,
                internal_deps=internal_deps,
                workspace_members=workspace_members,
            )
        )
        changes += list(
            self._rewrite_uv_workspace(
                doc,
                is_root=is_root,
                members=workspace_members,
            )
        )
        changes += list(self._rewrite_poetry(doc, is_root=is_root, mode=mode))
        if changes and (not dry_run):
            write_result = u.Cli.toml_write_document(pyproject_path, doc)
            if write_result.failure:
                return r[t.StrSequence].fail(
                    write_result.error or "failed to write TOML",
                )
        return r[t.StrSequence].ok(changes)

    @staticmethod
    def detect_mode(project_root: Path) -> str:
        """Detect workspace or standalone mode from project structure."""
        for candidate in (project_root, *project_root.parents):
            if (candidate / c.Infra.GITMODULES).exists():
                return c.Infra.RK_WORKSPACE
        return "standalone"

    def execute(self, params: FlextInfraModelsDeps.PathSyncCommand) -> int:
        """Execute dependency path synchronization for one canonical command payload."""
        workspace_root = params.workspace_path
        dry_run = params.dry_run
        selected_projects: t.StrSequence = list(params.project_names or [])
        mode = params.mode

        if mode == "auto":
            mode = self.detect_mode(workspace_root)

        root_pyproject = workspace_root / c.Infra.PYPROJECT_FILENAME

        discover_result = FlextInfraUtilitiesDocsScope.discover_projects(
            workspace_root,
        )
        if discover_result.failure:
            discovery_error = discover_result.error or "sync_dep_paths_discovery_failed"
            self._log.error(
                "sync_dep_paths_discovery_failed",
                root=str(workspace_root),
                error_detail=discovery_error,
            )
            return 1

        projects_list = discover_result.value
        total_changes = 0
        internal_names: t.Infra.StrSet = {
            project.name for project in projects_list if project.name
        }
        if root_pyproject.exists():
            root_payload = FlextInfraUtilitiesDocsScope.pyproject_payload(
                workspace_root,
            )
            root_name = FlextInfraUtilitiesDocsScope.project_name_from_payload(
                workspace_root,
                root_payload,
            )
            if root_name:
                internal_names.add(root_name)
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

        if not selected_projects and root_pyproject.exists():
            changes_result = self.rewrite_dep_paths(
                root_pyproject,
                mode=mode,
                internal_names=internal_names,
                workspace_members=workspace_members,
                is_root=True,
                dry_run=dry_run,
            )
            if changes_result.failure:
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
            pyproject = project_dir / c.Infra.PYPROJECT_FILENAME
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
            if changes_result.failure:
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


__all__ = ["FlextInfraUtilitiesDependencyPathSync"]
