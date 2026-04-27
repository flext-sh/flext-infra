"""Dependency path sync utilities exposed through ``u.Infra``."""

from __future__ import annotations

from collections.abc import (
    MutableMapping,
    MutableSequence,
)
from pathlib import Path

from flext_cli import u
from flext_infra import (
    FlextInfraModelsDeps,
    FlextInfraUtilitiesDocsScope,
    FlextInfraUtilitiesIteration,
    c,
    m,
    p,
    r,
    t,
)


class FlextInfraUtilitiesDependencyPathSync:
    """Rewrite internal FLEXT dependency paths for workspace or standalone mode."""

    _log = u.fetch_logger(__name__)
    discover_projects = staticmethod(FlextInfraUtilitiesDocsScope.discover_projects)

    def _rewrite_pep621(
        self,
        payload: MutableMapping[str, t.JsonValue],
        *,
        internal_names: t.Infra.StrSet,
    ) -> t.Pair[t.StrSequence, t.Infra.StrSet]:
        project_section = u.Cli.toml_mapping_child(payload, c.Infra.PROJECT)
        if project_section is None:
            return ([], set())
        raw_deps = u.Cli.json_as_sequence(
            project_section.get(c.Infra.DEPENDENCIES, None),
        )
        if not raw_deps:
            return ([], set())
        try:
            deps = t.Infra.STR_SEQ_ADAPTER.validate_python(raw_deps, strict=True)
        except c.ValidationError:
            return ([], set())
        changes: MutableSequence[str] = []
        updated_deps: MutableSequence[str] = []
        internal_deps: t.Infra.StrSet = set()
        for item in deps:
            requirement_part, _, marker_part = item.partition(";")
            dep_name = FlextInfraUtilitiesIteration.dep_name(requirement_part)
            if not dep_name or dep_name not in internal_names:
                updated_deps.append(item)
                continue
            internal_deps.add(dep_name)
            new_entry = item
            if " @ " in requirement_part:
                new_entry = dep_name
                if marker_part:
                    new_entry = f"{dep_name} ;{marker_part}"
            updated_deps.append(new_entry)
            if item != new_entry:
                changes.append(f"  PEP621: {item} -> {new_entry}")
        if changes:
            updated_dependencies: list[t.JsonValue] = list(updated_deps)
            u.Cli.toml_mapping_ensure_table(payload, c.Infra.PROJECT)[
                c.Infra.DEPENDENCIES
            ] = updated_dependencies
        return (changes, internal_deps)

    def _rewrite_uv_sources(
        self,
        payload: MutableMapping[str, t.JsonValue],
        *,
        is_root: bool,
        mode: c.Infra.PathSyncMode,
        internal_names: t.Infra.StrSet,
        internal_deps: t.Infra.StrSet,
        workspace_members: t.StrSequence,
    ) -> t.StrSequence:
        expected_names: t.Infra.StrSet = (
            set(workspace_members)
            if is_root and mode == c.Infra.PathSyncMode.WORKSPACE
            else set(internal_deps)
        )
        if not expected_names:
            return []
        changes: MutableSequence[str] = []
        tool_section = u.Cli.toml_mapping_ensure_table(payload, c.Infra.TOOL)
        uv_section = u.Cli.toml_mapping_ensure_table(tool_section, "uv")
        sources = u.Cli.toml_mapping_ensure_table(uv_section, "sources")
        for source_key in [str(key) for key in sources]:
            if source_key in internal_names and source_key not in expected_names:
                del sources[source_key]
                changes.append(f"  uv.sources: removed stale source {source_key}")
        for dep_name in sorted(expected_names):
            expected = (
                {"workspace": True}
                if mode == c.Infra.PathSyncMode.WORKSPACE
                else {
                    "path": f"{c.Infra.FLEXT_DEPS_DIR}/{dep_name}",
                    "editable": True,
                }
            )
            if u.Cli.toml_mapping_sync_mapping_table(
                sources,
                dep_name,
                expected,
                sort_keys=True,
            ):
                changes.append(f"  uv.sources: synced source for {dep_name}")
        return changes

    def _rewrite_uv_workspace(
        self,
        payload: MutableMapping[str, t.JsonValue],
        *,
        is_root: bool,
        members: t.StrSequence,
    ) -> t.StrSequence:
        if not is_root:
            return []
        changes: MutableSequence[str] = []
        tool_section = u.Cli.toml_mapping_ensure_table(payload, c.Infra.TOOL)
        uv_section = u.Cli.toml_mapping_ensure_table(tool_section, "uv")
        workspace_section = u.Cli.toml_mapping_ensure_table(uv_section, "workspace")
        expected_members = sorted(set(members))
        if u.Cli.toml_mapping_sync_string_list(
            workspace_section,
            "members",
            expected_members,
        ):
            changes.append("  uv.workspace: members synchronized")
        return changes

    @classmethod
    def _rewrite_poetry(
        cls,
        payload: MutableMapping[str, t.JsonValue],
        *,
        is_root: bool,
        mode: c.Infra.PathSyncMode,
    ) -> t.StrSequence:
        tool_section = u.Cli.toml_mapping_child(payload, c.Infra.TOOL)
        if tool_section is None:
            return []
        poetry_section = u.Cli.toml_mapping_child(tool_section, c.Infra.POETRY)
        if poetry_section is None:
            return []
        deps_view = u.Cli.toml_mapping_child(poetry_section, c.Infra.DEPENDENCIES)
        if deps_view is None:
            return []
        deps = u.Cli.toml_mapping_ensure_path(
            payload,
            (c.Infra.TOOL, c.Infra.POETRY, c.Infra.DEPENDENCIES),
        )
        changes: MutableSequence[str] = []
        for dep_key_raw in list(deps_view):
            value = u.Cli.toml_mapping_child(deps, dep_key_raw)
            if value is None:
                continue
            raw_path = value.get(c.Infra.PATH, None)
            if not isinstance(raw_path, str) or not raw_path.strip():
                continue
            dep_name = FlextInfraUtilitiesIteration.dep_name(raw_path)
            if not dep_name:
                continue
            new_path = f"{c.Infra.FLEXT_DEPS_DIR}/{dep_name}"
            if mode == c.Infra.PathSyncMode.WORKSPACE:
                new_path = dep_name if is_root else f"../{dep_name}"
            if raw_path == new_path:
                continue
            changes.append(
                f"  Poetry: {dep_key_raw}.path = {raw_path!r} -> {new_path!r}",
            )
            u.Cli.toml_mapping_ensure_table(deps, dep_key_raw)[c.Infra.PATH] = new_path
        return changes

    def _read_document_state(
        self,
        path: Path,
    ) -> p.Result[m.Infra.PyprojectDocumentState]:
        """Read one pyproject into a validated plain payload state."""
        try:
            original_rendered = path.read_text(encoding=c.Cli.ENCODING_DEFAULT)
        except OSError:
            return r[m.Infra.PyprojectDocumentState].fail(
                f"failed to read TOML: {path}"
            )
        payload_source = u.Cli.toml_mapping_from_text(original_rendered)
        if payload_source is None:
            return r[m.Infra.PyprojectDocumentState].fail(f"TOML parse failed: {path}")
        return r[m.Infra.PyprojectDocumentState].ok(
            m.Infra.PyprojectDocumentState(
                pyproject_path=path,
                original_rendered=original_rendered,
                payload={key: payload_source[key] for key in payload_source},
            )
        )

    def rewrite_dep_paths(
        self,
        pyproject_path: Path,
        *,
        command: FlextInfraModelsDeps.PathSyncCommand,
        internal_names: t.Infra.StrSet,
        workspace_members: t.StrSequence,
    ) -> p.Result[t.StrSequence]:
        """Rewrite PEP 621 and Poetry dependency paths."""
        mode = command.mode
        is_root = pyproject_path.resolve() == (
            command.workspace_path / c.Infra.PYPROJECT_FILENAME
        )
        state_result = self._read_document_state(pyproject_path)
        if state_result.failure:
            return r[t.StrSequence].fail(
                state_result.error or "failed to read TOML document",
            )
        state = state_result.value
        payload = state.payload
        pep_changes, internal_deps = self._rewrite_pep621(
            payload,
            internal_names=internal_names,
        )
        changes: MutableSequence[str] = list(pep_changes)
        changes += list(
            self._rewrite_uv_sources(
                payload,
                is_root=is_root,
                mode=mode,
                internal_names=internal_names,
                internal_deps=internal_deps,
                workspace_members=workspace_members,
            )
        )
        changes += list(
            self._rewrite_uv_workspace(
                payload,
                is_root=is_root,
                members=workspace_members,
            )
        )
        changes += list(self._rewrite_poetry(payload, is_root=is_root, mode=mode))
        if changes and (not command.dry_run):
            write_result = u.Cli.toml_write_mapping(pyproject_path, state.payload)
            if write_result.failure:
                return r[t.StrSequence].fail(
                    write_result.error or "failed to write TOML",
                )
        return r[t.StrSequence].ok(changes)

    @staticmethod
    def detect_mode(project_root: Path) -> c.Infra.PathSyncMode:
        """Detect workspace or standalone mode from project structure."""
        for candidate in (project_root, *project_root.parents):
            if (candidate / c.Infra.GITMODULES).exists():
                return c.Infra.PathSyncMode.WORKSPACE
        return c.Infra.PathSyncMode.STANDALONE

    @classmethod
    def execute_command(
        cls,
        params: FlextInfraModelsDeps.PathSyncCommand,
    ) -> p.Result[bool]:
        """Execute dependency path synchronization from the canonical CLI payload."""
        exit_code = cls().execute(params)
        if exit_code != 0:
            return r[bool].fail("dependency path sync failed")
        return r[bool].ok(True)

    def execute(self, params: FlextInfraModelsDeps.PathSyncCommand) -> int:
        """Execute dependency path synchronization for one canonical command payload."""
        workspace_root = params.workspace_path
        dry_run = params.dry_run
        selected_projects: t.StrSequence = list(params.project_names or [])
        mode = params.mode

        if mode == c.Infra.PathSyncMode.AUTO:
            mode = self.detect_mode(workspace_root)
        effective_command = params.model_copy(update={"mode": mode})

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
        discovered_member_paths: t.Infra.StrSet = {
            str(project.path.relative_to(workspace_root))
            for project in projects_list
            if project.path.is_relative_to(workspace_root)
        }
        configured_members = tuple(
            FlextInfraUtilitiesIteration.workspace_member_names(workspace_root)
        )
        invalid_members = [
            member
            for member in configured_members
            if (workspace_root / member).exists()
            and (workspace_root / member / c.Infra.PYPROJECT_FILENAME).exists()
            and member not in discovered_member_paths
        ]
        if invalid_members:
            member_text = ", ".join(sorted(invalid_members))
            self._log.error(
                "sync_dep_paths_invalid_workspace_members",
                root=str(workspace_root),
                members=member_text,
            )
            return 1
        total_changes = 0
        internal_names: t.Infra.StrSet = {
            project.name for project in projects_list if project.name
        }
        if root_pyproject.exists():
            root_payload: t.Infra.ContainerDict
            try:
                root_payload = FlextInfraUtilitiesDocsScope.project_payload(
                    workspace_root,
                )
            except (TypeError, ValueError):
                root_payload = {}
            project_section = root_payload.get(c.Infra.PROJECT)
            if isinstance(project_section, dict):
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
                command=effective_command,
                internal_names=internal_names,
                workspace_members=workspace_members,
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
                command=effective_command,
                internal_names=internal_names,
                workspace_members=workspace_members,
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


__all__: list[str] = ["FlextInfraUtilitiesDependencyPathSync"]
