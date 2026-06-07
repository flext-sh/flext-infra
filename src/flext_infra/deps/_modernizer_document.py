"""Document-state processing mixin for pyproject modernization."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING

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
    c,
    m,
    p,
    r,
    t,
    u,
)


class FlextInfraPyprojectModernizerDocumentMixin:
    """Read, classify, and process one parsed pyproject document state."""

    if TYPE_CHECKING:
        # Members provided by sibling mixins / the facade at runtime via MRO.
        type _Change = Callable[[t.MutableJsonMapping], t.StrSequence]
        root: Path
        _tool_config: m.Infra.ToolConfigDocument
        paths_manager: FlextInfraExtraPathsManager
        _ensure_build_system_payload: _Change
        _remove_empty_poetry_groups_payload: _Change
        _rewrite_dependency_constraints_payload: Callable[..., t.StrSequence]
        _reorder_document_inplace: Callable[[t.Cli.TomlDocument], None]

    def _classify_project(
        self,
        project_dir: Path,
        *,
        payload: t.Infra.ContainerDict | None = None,
    ) -> p.Result[str]:
        """Classify project kind for pyright/coverage settings selection."""
        classifier = FlextInfraProjectClassifier(project_dir, pyproject_payload=payload)
        return r[str].ok(classifier.classify().project_kind)

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


__all__: list[str] = ["FlextInfraPyprojectModernizerDocumentMixin"]
