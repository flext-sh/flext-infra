"""Immutable source-bundle preparation for the documentation generator."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from flext_core import r
from flext_infra import c, m, t, u
from flext_infra._utilities.docs_generate import FlextInfraUtilitiesDocsGenerate

if TYPE_CHECKING:
    from flext_infra import p

type _DocsScopeArtifacts = tuple[
    m.Infra.DocScope,
    tuple[t.Triple[Path, Path, str | None], ...],
]


class FlextInfraDocGeneratorBundleMixin:
    """Freeze one render and every authenticated input before planning."""

    @staticmethod
    def _is_collocated_workspace_project(
        scope: m.Infra.DocScope, *, workspace_root: Path
    ) -> bool:
        """Return whether a project scope shares the aggregate root path."""
        return scope.name != c.Infra.RK_ROOT and scope.path == workspace_root

    @staticmethod
    def _validate_scope_targets(
        scopes: t.SequenceOf[m.Infra.DocScope], output_dir: Path
    ) -> p.Result[bool]:
        """Require builders to preserve each lexical scope and report target."""
        for scope in scopes:
            expected = scope.path / output_dir
            if scope.report_dir != expected:
                return r[bool].fail(
                    "docs report directory is aliased or escaped: "
                    f"expected {expected}, observed {scope.report_dir}"
                )
        return r[bool].ok(True)

    @classmethod
    def _prepare_request(
        cls, request: m.Infra.DocsGenerateRequest
    ) -> p.Result[m.Infra.DocsGenerationBundle]:
        """Render and source-verify one canonical docs artifact inventory."""
        if request.apply:
            return r[m.Infra.DocsGenerationBundle].fail(
                "docs publication is owned by codegen conform; "
                "the generation transaction must publish plan_files()"
            )
        roots = u.Infra.docs_workspace_roots(request.workspace_root)
        if roots.failure:
            return r[m.Infra.DocsGenerationBundle].from_failure(roots)
        workspace_root = roots.value[0]
        selected_names = u.Infra.normalize_sequence_values(request.projects) or ()
        selected_roots: list[Path] = []
        for name in selected_names:
            selector = Path(name)
            if selector.is_absolute() or ".." in selector.parts:
                return r[m.Infra.DocsGenerationBundle].fail(
                    f"docs project selector escapes workspace: {name}"
                )
            selected_roots.append(workspace_root / selector)
        output_dir = u.Cli.resolve_optional_path(
            request.output_dir, default=Path(c.Infra.DEFAULT_DOCS_OUTPUT_DIR)
        )
        source_paths = u.Infra.docs_source_paths(workspace_root, tuple(selected_roots))
        if source_paths.failure:
            return r[m.Infra.DocsGenerationBundle].from_failure(source_paths)
        sources = u.Infra.docs_snapshot_sources(source_paths.value)
        if sources.failure:
            return r[m.Infra.DocsGenerationBundle].from_failure(sources)
        selected = u.Infra.build_scopes(workspace_root, request.projects, output_dir)
        if selected.failure:
            return r[m.Infra.DocsGenerationBundle].from_failure(selected)
        selected_targets = cls._validate_scope_targets(selected.value, output_dir)
        if selected_targets.failure:
            return r[m.Infra.DocsGenerationBundle].from_failure(selected_targets)
        aggregate = u.Infra.build_scopes(workspace_root, None, output_dir)
        if aggregate.failure:
            return r[m.Infra.DocsGenerationBundle].from_failure(aggregate)
        aggregate_targets = cls._validate_scope_targets(aggregate.value, output_dir)
        if aggregate_targets.failure:
            return r[m.Infra.DocsGenerationBundle].from_failure(aggregate_targets)
        rendered: list[_DocsScopeArtifacts] = []
        for scope in selected.value:
            if cls._is_collocated_workspace_project(
                scope, workspace_root=workspace_root
            ):
                rendered.append((scope, ()))
                continue
            artifacts = u.Infra.docs_scope_artifacts(
                scope, workspace_root=workspace_root, aggregate_scopes=aggregate.value
            )
            if artifacts.failure:
                return r[m.Infra.DocsGenerationBundle].from_failure(artifacts)
            rendered.append((scope, artifacts.value))
        normalized = u.Infra.docs_normalize_artifacts(
            tuple(artifact for _scope, artifacts in rendered for artifact in artifacts)
        )
        if normalized.failure:
            return r[m.Infra.DocsGenerationBundle].from_failure(normalized)
        normalized_scopes: list[m.Infra.DocsScopeArtifacts] = []
        offset = 0
        for scope, scope_artifacts in rendered:
            size = len(scope_artifacts)
            normalized_artifacts: list[m.Infra.DocsRenderedArtifact] = []
            for project, target, content in normalized.value[offset : offset + size]:
                if project != scope.path:
                    return r[m.Infra.DocsGenerationBundle].fail(
                        f"docs artifact owner differs from scope: {target}"
                    )
                normalized_content = content
                if normalized_content is not None and target.suffix == ".md":
                    normalized_content = c.Infra.FENCE_NOTEST_RE.sub(
                        r"```\1", normalized_content
                    )
                    normalized_content = u.Infra.docs_update_toc(normalized_content)[0]
                normalized_artifacts.append(
                    m.Infra.DocsRenderedArtifact(
                        relative_path=target.relative_to(project),
                        desired_content=(
                            None
                            if normalized_content is None
                            else normalized_content.encode(c.Cli.ENCODING_DEFAULT)
                        ),
                        desired_mode=0o644 if normalized_content is not None else None,
                    )
                )
            normalized_scopes.append(
                m.Infra.DocsScopeArtifacts(
                    scope=scope, artifacts=tuple(normalized_artifacts)
                )
            )
            offset += size
        scope_roots = tuple(scoped.scope.path for scoped in normalized_scopes)
        stable = FlextInfraUtilitiesDocsGenerate.docs_verify_sources(
            workspace_root, sources.value, extra_roots=scope_roots
        )
        if stable.failure:
            return r[m.Infra.DocsGenerationBundle].from_failure(stable)
        try:
            bundle = m.Infra.DocsGenerationBundle(
                scopes=tuple(normalized_scopes), source_states=sources.value
            )
        except c.ValidationError as exc:
            return r[m.Infra.DocsGenerationBundle].fail_op(
                "docs generation bundle validation", exc
            )
        return r[m.Infra.DocsGenerationBundle].ok(bundle)


__all__: list[str] = ["FlextInfraDocGeneratorBundleMixin"]
