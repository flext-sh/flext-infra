"""Document-state processing mixin for pyproject modernization."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING

from flext_core import r
from flext_infra.constants import c
from flext_infra.deps.extra_paths import FlextInfraExtraPathsManager
from flext_infra.deps.phases.consolidate_groups import FlextInfraConsolidateGroupsPhase
from flext_infra.deps.phases.ensure_coverage import FlextInfraEnsureCoverageConfigPhase
from flext_infra.deps.phases.ensure_formatting import (
    FlextInfraEnsureFormattingToolingPhase,
)
from flext_infra.deps.phases.ensure_mypy import FlextInfraEnsureMypyConfigPhase
from flext_infra.deps.phases.ensure_namespace import (
    FlextInfraEnsureNamespaceToolingPhase,
)
from flext_infra.deps.phases.ensure_pydantic_mypy import (
    FlextInfraEnsurePydanticMypyConfigPhase,
)
from flext_infra.deps.phases.ensure_pyrefly import FlextInfraEnsurePyreflyConfigPhase
from flext_infra.deps.phases.ensure_pyright import FlextInfraEnsurePyrightConfigPhase
from flext_infra.deps.phases.ensure_pytest import FlextInfraEnsurePytestConfigPhase
from flext_infra.deps.phases.ensure_ruff import FlextInfraEnsureRuffConfigPhase
from flext_infra.deps.phases.inject_comments import FlextInfraInjectCommentsPhase
from flext_infra.models import m
from flext_infra.protocols import p
from flext_infra.refactor.project_classifier import FlextInfraProjectClassifier
from flext_infra.typings import t
from flext_infra.utilities import u


class FlextInfraPyprojectModernizerDocumentMixin:
    """Read, classify, and process one parsed pyproject document state."""

    if TYPE_CHECKING:
        # Members provided by sibling mixins / the facade at runtime via MRO.
        _tool_config: m.Infra.ToolConfigDocument
        _rewrite_dependency_constraints_payload: Callable[..., t.StrSequence]

        @property
        def root(self) -> Path: ...

        @property
        def paths_manager(self) -> FlextInfraExtraPathsManager: ...

        def _ensure_build_system_payload(
            self,
            payload: t.MutableJsonMapping,
        ) -> t.StrSequence: ...

        def _remove_empty_poetry_groups_payload(
            self,
            payload: t.MutableJsonMapping,
        ) -> t.StrSequence: ...

        def _reorder_document_inplace(
            self,
            doc: t.Cli.TomlDocument,
        ) -> None: ...

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

    def _format_rendered_pyproject(
        self,
        path: Path,
        rendered: str,
    ) -> p.Result[str]:
        """Format rendered pyproject TOML with the workspace Taplo contract."""
        cmd = [
            "taplo",
            "format",
            "-",
            "--stdin-filepath",
            str(path),
        ]
        config_path = self.root / ".taplo.toml"
        if config_path.is_file():
            cmd.extend(["--config", str(config_path)])
        format_result = u.Cli.run_raw(
            cmd,
            cwd=self.root,
            input_data=rendered.encode(c.Cli.ENCODING_DEFAULT),
        )
        if format_result.failure:
            return r[str].fail(format_result.error or "taplo format failed")
        output = format_result.value
        if output.exit_code != 0:
            detail = (output.stderr or output.stdout).strip()
            return r[str].fail(f"taplo format failed ({output.exit_code}): {detail}")
        return r[str].ok(output.stdout)

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
        formatted_result = self._format_rendered_pyproject(path, rendered)
        if formatted_result.failure:
            return [formatted_result.error or "taplo format failed"]
        rendered = formatted_result.value
        normalized_original = original_rendered.rstrip() + "\n"
        normalized_rendered = rendered.rstrip() + "\n"
        if normalized_rendered == normalized_original:
            return []
        if not dry_run:
            u.write_file(path, rendered, encoding=c.Cli.ENCODING_DEFAULT)
        return changes


__all__: list[str] = ["FlextInfraPyprojectModernizerDocumentMixin"]
