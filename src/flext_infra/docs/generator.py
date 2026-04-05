"""Documentation generator service driven by code, exports, and docstrings."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Annotated, override

from pydantic import Field

from flext_core import r
from flext_infra import c, m, t, u
from flext_infra.base import s


class FlextInfraDocGenerator(s[bool]):
    """Generate managed docs artifacts from package exports and docstrings."""

    selected_projects: Annotated[
        t.StrSequence | None,
        Field(default=None, description="Selected projects", exclude=True),
    ] = None
    docs_output_dir: Annotated[
        str,
        Field(
            default=c.Infra.DEFAULT_DOCS_OUTPUT_DIR,
            description="Docs output dir",
            exclude=True,
        ),
    ] = c.Infra.DEFAULT_DOCS_OUTPUT_DIR

    def generate(
        self,
        workspace_root: Path,
        *,
        projects: Sequence[str] | None = None,
        output_dir: str = c.Infra.DEFAULT_DOCS_OUTPUT_DIR,
        apply: bool = False,
    ) -> r[Sequence[m.Infra.DocsPhaseReport]]:
        """Generate docs across the workspace root and governed FLEXT projects."""
        return u.Infra.run_scoped(
            workspace_root,
            projects=projects,
            output_dir=output_dir,
            handler=lambda scope: self._generate_scope(
                scope,
                apply=apply,
                workspace_root=workspace_root,
                projects=projects,
            ),
        )

    @override
    def execute(self) -> r[bool]:
        """Execute the configured docs generation flow."""
        result = self.generate(
            workspace_root=self.workspace_root,
            projects=self.selected_projects,
            output_dir=self.docs_output_dir,
            apply=self.apply_changes,
        )
        if result.is_failure:
            return r[bool].fail(result.error or "generate failed")
        return r[bool].ok(True)

    @override
    def execute_command(self, params: m.Infra.DocsGenerateInput) -> r[bool]:
        """CLI handler that normalizes input into the canonical service model."""
        service = type(self)(
            workspace=params.workspace_path,
            apply=params.apply,
            selected_projects=params.project_names,
            docs_output_dir=params.output_dir,
        )
        return service.execute()

    def _generate_scope(
        self,
        scope: m.Infra.DocScope,
        *,
        apply: bool,
        workspace_root: Path,
        projects: Sequence[str] | None = None,
    ) -> m.Infra.DocsPhaseReport:
        """Generate one scope via ``u.Infra`` and log the result."""
        report = u.Infra.docs_generate_scope(
            scope,
            apply=apply,
            workspace_root=workspace_root,
            projects=projects,
        )
        self.logger.info(
            "docs_generate_scope_completed",
            project=scope.name,
            phase="generate",
            result=report.result,
            reason=report.reason,
        )
        return report

    def _generate_root_docs(
        self,
        scope: m.Infra.DocScope,
        *,
        apply: bool,
    ) -> Sequence[m.Infra.GeneratedFile]:
        """Delegate root docs generation to ``u.Infra``."""
        return u.Infra.docs_root_generated_files(scope.path, apply=apply)

    def _generate_project_guides(
        self,
        scope: m.Infra.DocScope,
        *,
        workspace_root: Path,
        apply: bool,
    ) -> Sequence[m.Infra.GeneratedFile]:
        """Delegate project guide generation to ``u.Infra``."""
        return u.Infra.docs_project_guides_files(
            scope,
            workspace_root=workspace_root,
            apply=apply,
        )

    def _generate_project_mkdocs(
        self,
        scope: m.Infra.DocScope,
        *,
        apply: bool,
    ) -> Sequence[m.Infra.GeneratedFile]:
        """Delegate project mkdocs generation to ``u.Infra``."""
        return u.Infra.docs_project_mkdocs_files(scope, apply=apply)

    def _project_guide_content(
        self,
        content: str,
        project_name: str,
        guide_name: str,
    ) -> str:
        """Delegate guide content normalization to ``u.Infra``."""
        return u.Infra.docs_project_guide_content(
            content,
            project_name,
            guide_name,
        )

    def _sanitize_internal_anchor_links(self, content: str) -> str:
        """Delegate markdown link sanitization to ``u.Infra``."""
        return u.Infra.docs_sanitize_internal_anchor_links(content)

    def _update_toc(self, content: str) -> str:
        """Delegate TOC updates to ``u.Infra`` and return updated content only."""
        updated, _ = u.Infra.docs_update_toc(content)
        return updated

    def _write_if_needed(
        self,
        path: Path,
        content: str,
        *,
        apply: bool,
    ) -> m.Infra.GeneratedFile:
        """Delegate conditional writes to ``u.Infra``."""
        return u.Infra.docs_write_if_needed(path, content, apply=apply)

    def _project_files(
        self,
        scope: m.Infra.DocScope,
        *,
        apply: bool,
    ) -> Sequence[m.Infra.GeneratedFile]:
        """Return generated project files via ``u.Infra``."""
        return u.Infra.docs_project_generated_files(scope, apply=apply)

    def _root_files(
        self,
        workspace_root: Path,
        *,
        apply: bool,
    ) -> Sequence[m.Infra.GeneratedFile]:
        """Return generated root files via ``u.Infra``."""
        return u.Infra.docs_root_generated_files(workspace_root, apply=apply)


__all__ = ["FlextInfraDocGenerator"]
