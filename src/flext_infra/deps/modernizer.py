"""Modernize workspace pyproject.toml files to standardized format."""

from __future__ import annotations

from collections.abc import (
    MutableMapping,
    MutableSequence,
    Sequence,
)
from pathlib import Path
from typing import Annotated, override

from tomlkit.items import AoT, Table

from flext_infra import (
    FlextInfraConsolidateGroupsPhase,
    FlextInfraDepsProjectServiceBase,
    FlextInfraEnsureCoverageConfigPhase,
    FlextInfraEnsureFormattingToolingPhase,
    FlextInfraEnsureMypyConfigPhase,
    FlextInfraEnsureNamespaceToolingPhase,
    FlextInfraEnsurePydanticMypyConfigPhase,
    FlextInfraEnsurePyreflyConfigPhase,
    FlextInfraEnsurePyrightConfigPhase,
    FlextInfraEnsurePytestConfigPhase,
    FlextInfraEnsureRuffConfigPhase,
    FlextInfraExtraPathsManager,
    FlextInfraInjectCommentsPhase,
    FlextInfraProjectClassifier,
    FlextInfraUtilitiesIteration,
    c,
    m,
    p,
    r,
    t,
    u,
)


class FlextInfraPyprojectModernizer(FlextInfraDepsProjectServiceBase):
    """Modernize all workspace pyproject.toml files."""

    audit: Annotated[
        bool,
        m.Field(False, description="Audit pyproject changes without writing"),
    ] = False
    skip_check: Annotated[
        bool,
        m.Field(alias="skip-check", description="Skip post-write validation"),
    ] = False
    skip_comments: Annotated[
        bool,
        m.Field(alias="skip-comments", description="Skip managed comment updates"),
    ] = False
    _tool_config: m.Infra.ToolConfigDocument = u.PrivateAttr()
    _paths_manager: FlextInfraExtraPathsManager | None = u.PrivateAttr(
        default_factory=lambda: None,
    )

    @override
    def model_post_init(self, __context: object, /) -> None:
        """Initialize pyproject modernization collaborators after validation."""
        tool_config_result = u.Infra.load_tool_config()
        if tool_config_result.failure:
            msg = tool_config_result.error or "failed to load deps tool settings"
            raise ValueError(msg)
        self._tool_config = tool_config_result.value

    @property
    def paths_manager(self) -> FlextInfraExtraPathsManager:
        """Create the extra-paths manager only when a phase actually needs it."""
        if self._paths_manager is None:
            self._paths_manager = FlextInfraExtraPathsManager(
                workspace=self.root,
            )
        return self._paths_manager

    def _classify_project(
        self,
        project_dir: Path,
        *,
        payload: t.Infra.ContainerDict | None = None,
    ) -> p.Result[str]:
        """Classify project kind for pyright/coverage settings selection."""
        kind = (
            FlextInfraProjectClassifier(
                project_dir,
                pyproject_payload=payload,
            )
            .classify()
            .project_kind
        )
        return r[str].ok(kind)

    def _read_document_state(
        self, path: Path
    ) -> p.Result[m.Infra.PyprojectDocumentState]:
        """Read one pyproject once and keep one validated plain payload state."""
        try:
            original_rendered = path.read_text(encoding=c.Infra.ENCODING_DEFAULT)
        except OSError:
            return r[m.Infra.PyprojectDocumentState].fail(f"failed to read {path}")
        payload_source = u.Cli.toml_mapping_from_text(original_rendered)
        if payload_source is None:
            return r[m.Infra.PyprojectDocumentState].fail(f"invalid TOML: {path}")
        try:
            payload = t.Cli.JSON_MAPPING_ADAPTER.validate_python(payload_source)
        except c.ValidationError as exc:
            return r[m.Infra.PyprojectDocumentState].fail(
                f"TOML payload validation failed: {exc}",
            )
        return r[m.Infra.PyprojectDocumentState].ok(
            m.Infra.PyprojectDocumentState(
                pyproject_path=path,
                original_rendered=original_rendered,
                payload={str(key): value for key, value in payload.items()},
            ),
        )

    def _process_document_state(
        self,
        state: m.Infra.PyprojectDocumentState,
        *,
        canonical_dev: t.StrSequence,
        dry_run: bool,
        skip_comments: bool,
    ) -> t.StrSequence:
        """Process one parsed pyproject state and collect changes."""
        path = state.pyproject_path
        original_rendered = state.original_rendered
        payload = state.payload
        is_root = path.parent.resolve() == self.root.resolve()
        project_kind = "core"
        if not is_root:
            kind_result = self._classify_project(path.parent, payload=payload)
            if kind_result.success:
                project_kind = kind_result.value
        changes: MutableSequence[str] = []
        changes.extend(self._ensure_build_system_payload(payload))
        changes.extend(self._remove_empty_poetry_groups_payload(payload))
        changes.extend(
            FlextInfraConsolidateGroupsPhase().apply_payload(payload, canonical_dev),
        )
        changes.extend(
            FlextInfraEnsurePytestConfigPhase(self._tool_config).apply_payload(payload),
        )
        changes.extend(
            FlextInfraEnsurePyreflyConfigPhase(self._tool_config).apply_payload(
                payload,
                is_root=is_root,
                project_dir=path.parent,
                paths_manager=self.paths_manager,
            ),
        )
        changes.extend(
            FlextInfraEnsureMypyConfigPhase(self._tool_config).apply_payload(payload),
        )
        changes.extend(
            FlextInfraEnsurePydanticMypyConfigPhase(self._tool_config).apply_payload(
                payload
            ),
        )
        changes.extend(
            FlextInfraEnsureFormattingToolingPhase(self._tool_config).apply_payload(
                payload
            ),
        )
        changes.extend(
            FlextInfraEnsureNamespaceToolingPhase().apply_payload(payload, path=path),
        )
        changes.extend(
            FlextInfraEnsureRuffConfigPhase(self._tool_config).apply_payload(
                payload,
                path=path,
            ),
        )
        changes.extend(
            FlextInfraEnsurePyrightConfigPhase(self._tool_config).apply_payload(
                payload,
                is_root=is_root,
                workspace_root=self.root,
                project_dir=path.parent,
                project_kind=project_kind,
                paths_manager=self.paths_manager,
            ),
        )
        changes.extend(
            FlextInfraEnsureCoverageConfigPhase(self._tool_config).apply_payload(
                payload,
                project_kind=project_kind,
            ),
        )
        changes.extend(
            self.paths_manager.sync_payload(
                payload,
                project_dir=path.parent,
                is_root=is_root,
            ),
        )
        doc = u.Cli.toml_document_from_mapping(payload)
        self._reorder_document_inplace(doc)
        state.payload = payload
        rendered = doc.as_string()
        if not skip_comments:
            rendered, comment_changes = FlextInfraInjectCommentsPhase().apply(rendered)
            changes.extend(comment_changes)
        normalized_original = original_rendered.rstrip() + "\n"
        normalized_rendered = rendered.rstrip() + "\n"
        if normalized_rendered == normalized_original:
            return []
        if not dry_run:
            u.write_file(path, rendered, encoding=c.Infra.ENCODING_DEFAULT)
        return changes

    def _ensure_build_system_payload(
        self,
        payload: MutableMapping[str, t.Cli.JsonValue],
    ) -> t.StrSequence:
        """Ensure canonical build-system backend/requirements in one plain payload."""
        changes: MutableSequence[str] = []
        build_system_existing = payload.get("build-system", None)
        build_system = u.Cli.toml_mapping_ensure_table(payload, "build-system")
        if not isinstance(build_system_existing, dict):
            changes.append("created [build-system]")
        expected_backend = "hatchling.build"
        current_backend = u.norm_str(str(build_system.get("build-backend", "")))
        if current_backend != expected_backend:
            build_system["build-backend"] = expected_backend
            changes.append("build-system.build-backend set to hatchling.build")
        expected_requires = ["hatchling"]
        requires_value = build_system.get("requires", None)
        current_requires: list[str] = []
        if isinstance(requires_value, str | int | float | bool) or (
            isinstance(requires_value, Sequence)
            and not isinstance(
                requires_value,
                str | bytes,
            )
        ):
            current_requires = sorted(u.Cli.toml_as_string_list(requires_value))
        if current_requires != expected_requires:
            build_system["requires"] = list(expected_requires)
            changes.append("build-system.requires set to ['hatchling']")
        metadata_table = u.Cli.toml_mapping_ensure_path(
            payload,
            (c.Infra.TOOL, "hatch", "metadata"),
        )
        current_allow = metadata_table.get("allow-direct-references", None) is True
        if not current_allow:
            metadata_table["allow-direct-references"] = True
            changes.append("tool.hatch.metadata.allow-direct-references set to true")
        return changes

    @staticmethod
    def _remove_empty_poetry_groups_payload(
        payload: MutableMapping[str, t.Cli.JsonValue],
    ) -> t.StrSequence:
        """Remove empty Poetry group tables from one normalized payload."""
        poetry_groups = u.Cli.toml_mapping_path(
            payload,
            (c.Infra.TOOL, c.Infra.POETRY, c.Infra.GROUP),
        )
        if poetry_groups is None:
            return []
        empty_groups: MutableSequence[str] = []
        for name, group_value in poetry_groups.items():
            group_table = (
                group_value
                if isinstance(group_value, dict)
                else u.Cli.toml_mapping_child(poetry_groups, name)
            )
            if group_table is None:
                continue
            deps_item = u.Cli.toml_mapping_child(group_table, c.Infra.DEPENDENCIES)
            if deps_item is not None and not deps_item:
                empty_groups.append(name)
        changes: MutableSequence[str] = []
        for name in empty_groups:
            del poetry_groups[name]
            changes.append(f"removed empty poetry group '{name}'")
        if poetry_groups:
            return changes
        poetry_table = u.Cli.toml_mapping_path(payload, (c.Infra.TOOL, c.Infra.POETRY))
        if poetry_table is None or c.Infra.GROUP not in poetry_table:
            return changes
        del poetry_table[c.Infra.GROUP]
        changes.append("removed empty poetry group container")
        return changes

    @staticmethod
    def _ordered_keys(
        keys: t.StrSequence,
        *,
        preferred_first: t.StrSequence | None = None,
    ) -> t.StrSequence:
        """Return keys with optional preferred-first order then alphabetical."""
        preferred = list(preferred_first or [])
        key_set = set(keys)
        ordered: MutableSequence[str] = [key for key in preferred if key in key_set]
        remaining = sorted(key for key in keys if key not in set(ordered))
        ordered.extend(remaining)
        return ordered

    @classmethod
    def _reorder_table_inplace(
        cls,
        table: t.Infra.TomlTable,
        *,
        preferred_first: t.StrSequence | None = None,
        table_key: str | None = None,
    ) -> None:
        """Reorder table keys in-place recursively (tables/AoT items)."""
        if table_key == "per-file-ignores":
            return
        original_keys = [str(key) for key in table]
        ordered_keys = cls._ordered_keys(
            original_keys,
            preferred_first=preferred_first,
        )
        if ordered_keys == original_keys:
            for key in ordered_keys:
                value = table[key]
                if isinstance(value, Table):
                    cls._reorder_table_inplace(value, table_key=key)
                elif isinstance(value, AoT):
                    for entry in value.body:
                        cls._reorder_table_inplace(entry, table_key=key)
            return
        items: MutableMapping[str, t.Infra.TomlItem] = {
            key: table[key] for key in original_keys
        }
        for key in original_keys:
            del table[key]
        for key in ordered_keys:
            value = items[key]
            if isinstance(value, Table):
                cls._reorder_table_inplace(value, table_key=key)
            elif isinstance(value, AoT):
                for entry in value.body:
                    cls._reorder_table_inplace(entry, table_key=key)
            table[key] = value

    @classmethod
    def _reorder_document_inplace(cls, doc: t.Infra.TomlDocument) -> None:
        """Apply deterministic ordering for top-level groups and nested tables."""
        root_keys = [str(key) for key in doc]
        ordered_root = cls._ordered_keys(
            root_keys,
            preferred_first=("build-system", "dependency-groups", "project", "tool"),
        )
        if ordered_root != root_keys:
            root_items: MutableMapping[
                str, t.Infra.TomlItem | t.Infra.TomlContainer
            ] = {key: doc[key] for key in root_keys}
            for key in root_keys:
                del doc[key]
            for key in ordered_root:
                doc[key] = root_items[key]
        tool_child = u.Cli.toml_table_child(doc, "tool")
        if tool_child is not None:
            cls._reorder_table_inplace(tool_child, table_key="tool")
        for key in ordered_root:
            if key == "tool":
                continue
            value = doc[key]
            if isinstance(value, Table):
                cls._reorder_table_inplace(value, table_key=key)
            elif isinstance(value, AoT):
                for entry in value.body:
                    cls._reorder_table_inplace(entry, table_key=key)

    def process_file(
        self,
        path: Path,
        *,
        canonical_dev: t.StrSequence,
        dry_run: bool,
        skip_comments: bool,
    ) -> t.StrSequence:
        """Process one pyproject.toml file and collect changes."""
        document_state_result = self._read_document_state(path)
        if document_state_result.failure:
            return ["invalid TOML"]
        return self._process_document_state(
            document_state_result.value,
            canonical_dev=canonical_dev,
            dry_run=dry_run,
            skip_comments=skip_comments,
        )

    def run(self) -> int:
        """Run pyproject modernization for the workspace."""
        check_mode = bool(self.audit or self.check_only)
        dry_run = bool(check_mode or self.effective_dry_run)
        project_names = list(self.project_names or [])
        project_paths: Sequence[Path] | None = None
        if project_names:
            selected_projects = u.Infra.resolve_projects(self.root, project_names)
            if selected_projects.failure:
                u.Cli.error(
                    selected_projects.error or "failed to resolve selected projects",
                )
                return 2
            project_paths = [project.path for project in selected_projects.value]
        files_result = u.Infra.find_all_pyproject_files(
            self.root,
            skip_dirs=c.Infra.SKIP_DIRS,
            project_paths=project_paths,
        )
        files: Sequence[Path] = (
            [] if files_result.failure else sorted(files_result.unwrap())
        )
        root_state_result = self._read_document_state(
            self.root / c.Infra.PYPROJECT_FILENAME
        )
        if root_state_result.failure:
            return 2
        root_state = root_state_result.value
        canonical_dev: t.StrSequence = t.Infra.STR_SEQ_ADAPTER.validate_python(
            FlextInfraUtilitiesIteration.canonical_dev_dependencies_from_payload(
                root_state.payload
            ),
        )
        violations: MutableMapping[str, t.StrSequence] = {}
        document_states: MutableSequence[m.Infra.PyprojectDocumentState] = []
        invalid_paths: MutableSequence[Path] = []
        total = 0
        for file_path in files:
            document_state_result = (
                r[m.Infra.PyprojectDocumentState].ok(root_state)
                if file_path.resolve() == root_state.pyproject_path.resolve()
                else self._read_document_state(file_path)
            )
            if document_state_result.failure:
                invalid_paths.append(file_path)
                changes = ["invalid TOML"]
            else:
                document_state = document_state_result.value
                document_states.append(document_state)
                changes = self._process_document_state(
                    document_state,
                    canonical_dev=canonical_dev,
                    dry_run=dry_run,
                    skip_comments=self.skip_comments,
                )
            if not changes:
                continue
            rel = str(file_path.relative_to(self.root))
            violations[rel] = changes
            total += len(changes)
        if violations:
            for rel_path, changes in violations.items():
                u.Cli.info(f"{rel_path}:")
                for change in changes:
                    u.Cli.info(f"  - {change}")
            u.Cli.info(
                f"Total: {total} change(s) across {len(violations)} file(s)",
            )
            if dry_run:
                u.Cli.info("(dry-run — no files modified)")
        if check_mode and total > 0:
            return 1
        if not dry_run and (not self.skip_check):
            return self._run_build_check(
                document_states,
                invalid_paths=invalid_paths,
            )
        return 0

    @override
    def execute(self) -> p.Result[bool]:
        """Execute pyproject modernization for the configured workspace."""
        exit_code = self.run()
        if exit_code != 0:
            return r[bool].fail("pyproject modernization failed")
        return r[bool].ok(True)

    def _run_build_check(
        self,
        document_states: Sequence[m.Infra.PyprojectDocumentState],
        *,
        invalid_paths: Sequence[Path] = (),
    ) -> int:
        """Validate pyproject.toml files have hatchling build backend."""
        has_warning = False
        for invalid_path in invalid_paths:
            u.Cli.info(f"{invalid_path}: invalid TOML")
            has_warning = True
        for document_state in document_states:
            path = document_state.pyproject_path
            build_sys = u.Cli.toml_mapping_child(document_state.payload, "build-system")
            if build_sys is None:
                u.Cli.info(f"{path}: missing [build-system]")
                has_warning = True
                continue
            backend = u.norm_str(str(build_sys.get("build-backend", "")))
            if backend != "hatchling.build":
                u.Cli.info(f"{path}: expected hatchling.build, got {backend}")
                has_warning = True
        return 1 if has_warning else 0


__all__: list[str] = ["FlextInfraPyprojectModernizer"]
