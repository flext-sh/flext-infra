"""Modernize workspace pyproject.toml files to standardized format."""

from __future__ import annotations

from collections.abc import (
    MutableMapping,
)
from pathlib import Path
from typing import Annotated, override

from flext_infra import (
    FlextInfraConsolidateGroupsPhase,
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
    FlextInfraProjectSelectionServiceBase,
    c,
    m,
    p,
    r,
    t,
    u,
)
from flext_infra.deps._modernizer_constraints import (
    FlextInfraPyprojectModernizerConstraintsMixin,
)
from flext_infra.deps._modernizer_payload import (
    FlextInfraPyprojectModernizerPayloadMixin,
)


class FlextInfraPyprojectModernizer(
    FlextInfraProjectSelectionServiceBase[bool],
    FlextInfraPyprojectModernizerConstraintsMixin,
    FlextInfraPyprojectModernizerPayloadMixin,
):
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
    rewrite_constraints: Annotated[
        bool,
        m.Field(
            alias="rewrite-constraints",
            description="Rewrite dependency constraints from uv.lock",
        ),
    ] = False
    constraint_policy: Annotated[
        c.Infra.DependencyConstraintPolicy,
        m.Field(
            alias="constraint-policy",
            description="Policy used when rewriting dependency constraints",
        ),
        m.BeforeValidator(
            lambda v: (
                c.Infra.DependencyConstraintPolicy(v.strip().lower())
                if isinstance(v, str)
                else v
            )
        ),
    ] = c.Infra.DependencyConstraintPolicy.FLOOR
    _tool_config: m.Infra.ToolConfigDocument = u.PrivateAttr()
    _paths_manager: FlextInfraExtraPathsManager | None = u.PrivateAttr(
        default_factory=lambda: None,
    )

    @override
    def model_post_init(self, __context: dict[str, p.AttributeProbe], /) -> None:
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
        read = u.Cli.files_read_text(path)
        if read.failure:
            return r[m.Infra.PyprojectDocumentState].fail(
                read.error or f"failed to read {path}",
            )
        original_rendered = read.value
        payload_source = u.Cli.toml_mapping_from_text(original_rendered)
        if payload_source is None:
            return r[m.Infra.PyprojectDocumentState].fail(f"invalid TOML: {path}")
        try:
            payload = t.Infra.MUTABLE_INFRA_MAPPING_ADAPTER.validate_python(
                payload_source,
            )
        except c.ValidationError as exc:
            return r[m.Infra.PyprojectDocumentState].fail_op(
                "TOML payload validation", exc
            )
        return r[m.Infra.PyprojectDocumentState].ok(
            m.Infra.PyprojectDocumentState.model_validate(
                {
                    "pyproject_path": path,
                    "original_rendered": original_rendered,
                    "payload": payload,
                },
            ),
        )

    def _process_document_state(
        self,
        state: m.Infra.PyprojectDocumentState,
        *,
        canonical_dev: t.StrSequence,
        dry_run: bool,
        skip_comments: bool,
        rewrite_constraints: bool = False,
        locked_versions: t.MappingKV[str, str] | None = None,
        internal_names: t.StrSequence = (),
        constraint_policy: c.Infra.DependencyConstraintPolicy = c.Infra.DependencyConstraintPolicy.FLOOR,
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
        changes: t.MutableSequenceOf[str] = []
        changes.extend(self._ensure_build_system_payload(payload))
        changes.extend(self._remove_empty_poetry_groups_payload(payload))
        if rewrite_constraints:
            changes.extend(
                self._rewrite_dependency_constraints_payload(
                    payload,
                    locked_versions=locked_versions or {},
                    internal_names=internal_names,
                    policy=constraint_policy,
                )
            )
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
        doc: t.Cli.TomlDocument = u.Cli.toml_document_from_mapping(payload)
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
            u.write_file(path, rendered, encoding=c.Cli.ENCODING_DEFAULT)
        return changes

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
            rewrite_constraints=False,
        )

    def run(self) -> int:
        """Run pyproject modernization for the workspace."""
        check_mode = self.audit or self.check_only
        dry_run = check_mode or self.effective_dry_run
        project_names = list(self.project_names or [])
        project_paths: t.SequenceOf[Path] | None = None
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
        files: t.SequenceOf[Path] = (
            [] if files_result.failure else sorted(files_result.unwrap())
        )
        root_state_result = self._read_document_state(
            self.root / c.Infra.PYPROJECT_FILENAME
        )
        if root_state_result.failure:
            return 2
        root_state = root_state_result.value
        canonical_dev: t.StrSequence = t.Infra.STR_SEQ_ADAPTER.validate_python(
            u.Infra.canonical_dev_dependencies_from_payload(root_state.payload),
        )
        locked_versions: t.MappingKV[str, str] = {}
        internal_names: t.StrSequence = ()
        if self.rewrite_constraints:
            lock_path = self.root / "uv.lock"
            locked_versions = u.Infra.locked_dependency_versions(lock_path)
            if not locked_versions:
                u.Cli.error(f"missing or invalid uv.lock at {lock_path}")
                return 2
            try:
                root_project_name = u.Infra.project_name_from_payload(
                    root_state.pyproject_path,
                    root_state.payload,
                )
            except c.EXC_TYPE_VALIDATION as exc:
                u.Cli.error(str(exc))
                return 2
            internal_names = tuple(
                sorted(
                    set(u.Infra.workspace_member_names(self.root)) | {root_project_name}
                )
            )
        violations: MutableMapping[str, t.StrSequence] = {}
        document_states: t.MutableSequenceOf[m.Infra.PyprojectDocumentState] = []
        invalid_paths: t.MutableSequenceOf[Path] = []
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
                    rewrite_constraints=self.rewrite_constraints,
                    locked_versions=locked_versions,
                    internal_names=internal_names,
                    constraint_policy=self.constraint_policy,
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
        document_states: t.SequenceOf[m.Infra.PyprojectDocumentState],
        *,
        invalid_paths: t.SequenceOf[Path] = (),
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
