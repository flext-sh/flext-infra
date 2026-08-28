"""Docs scope construction helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core import r
from flext_infra._utilities.base import FlextInfraUtilitiesBase
from flext_infra._utilities.docs_scope import FlextInfraUtilitiesDocsScope
from flext_infra.constants import c
from flext_infra.models import m
from flext_infra.typings import t

if TYPE_CHECKING:
    from pathlib import Path

    from flext_infra.protocols import p


class FlextInfraUtilitiesDocsScopeBuildMixin:
    """Build canonical DocScope models for docs commands."""

    @staticmethod
    def _selected_project_names(
        workspace_root: Path, projects: t.StrSequence | None
    ) -> list[str]:
        """Return normalized project filters for docs-scoped operations."""
        _ = workspace_root
        return list(FlextInfraUtilitiesBase.normalize_sequence_values(projects) or ())

    @staticmethod
    def _root_scope(workspace_root: Path, output_dir: Path | str) -> m.Infra.DocScope:
        """Build the report scope owned by the explicitly supplied root."""
        return m.Infra.DocScope(
            name=c.Infra.RK_ROOT,
            path=workspace_root,
            report_dir=(workspace_root / output_dir).resolve(),
            project_class="root",
            package_name="",
        )

    @staticmethod
    def _project_scope(
        project: m.Infra.ProjectInfo, output_dir: Path | str
    ) -> m.Infra.DocScope:
        """Build one scope from a canonical explicit project descriptor."""
        resolved = project.path.resolve()
        return m.Infra.DocScope(
            name=project.name,
            path=resolved,
            report_dir=(resolved / output_dir).resolve(),
            project_class=project.project_class,
            package_name=project.package_name,
        )

    @staticmethod
    def _governed_scope(project_root: Path, output_dir: Path | str) -> m.Infra.DocScope:
        """Build the local repository scope from its declared metadata."""
        payload = FlextInfraUtilitiesDocsScope.project_payload(project_root)
        docs_meta = FlextInfraUtilitiesDocsScope.docs_meta_from_payload(payload)
        project_name = FlextInfraUtilitiesDocsScope.project_name_from_payload(
            project_root, payload
        )
        return m.Infra.DocScope(
            name=project_name,
            path=project_root,
            report_dir=(project_root / output_dir).resolve(),
            project_class=FlextInfraUtilitiesDocsScope.classify_project_from_meta(
                project_name, docs_meta
            ),
            package_name=FlextInfraUtilitiesDocsScope.package_name_from_payload(
                project_root, payload, docs_meta
            ),
        )

    @staticmethod
    def build_scopes(
        workspace_root: Path, projects: t.StrSequence | None, output_dir: Path | str
    ) -> p.Result[t.SequenceOf[m.Infra.DocScope]]:
        """Build DocScope objects for workspace root and selected projects."""
        try:
            scopes = FlextInfraUtilitiesDocsScopeBuildMixin._build_scopes_unchecked(
                workspace_root, projects, output_dir
            )
        except c.EXC_OS_TYPE_VALUE as exc:
            return r[t.SequenceOf[m.Infra.DocScope]].fail_op("scope resolution", exc)
        return r[t.SequenceOf[m.Infra.DocScope]].ok(scopes)

    @staticmethod
    def _build_scopes_unchecked(
        workspace_root: Path, projects: t.StrSequence | None, output_dir: Path | str
    ) -> t.SequenceOf[m.Infra.DocScope]:
        """Build docs scopes without exception wrapping."""
        resolved_root = workspace_root.resolve()
        selected_names = FlextInfraUtilitiesDocsScopeBuildMixin._selected_project_names(
            resolved_root, projects
        )
        if selected_names:
            selected = FlextInfraUtilitiesDocsScope.resolve_projects(
                resolved_root, selected_names
            )
            if selected.failure:
                raise ValueError(selected.error or "project resolution failed")
            return (
                FlextInfraUtilitiesDocsScopeBuildMixin._root_scope(
                    resolved_root, output_dir
                ),
                *(
                    FlextInfraUtilitiesDocsScopeBuildMixin._project_scope(
                        project, output_dir
                    )
                    for project in selected.value
                ),
            )
        project_state = FlextInfraUtilitiesDocsScope.project_state(resolved_root)
        enabled = project_state.docs_meta.get("enabled", True)
        is_enabled = enabled if isinstance(enabled, bool) else True
        if (resolved_root / c.Infra.PYPROJECT_FILENAME).is_file() and is_enabled:
            return (
                FlextInfraUtilitiesDocsScopeBuildMixin._governed_scope(
                    resolved_root, output_dir
                ),
            )
        return (
            FlextInfraUtilitiesDocsScopeBuildMixin._root_scope(
                resolved_root, output_dir
            ),
        )


__all__: list[str] = ["FlextInfraUtilitiesDocsScopeBuildMixin"]
