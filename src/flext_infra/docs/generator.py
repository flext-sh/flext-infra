"""Documentation generator service driven by code, exports, and docstrings."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Annotated, override

from pydantic import Field

from flext_infra import c, m, p, r, s, t, u


class FlextInfraDocGenerator(s[bool]):
    """Generate managed docs artifacts from package exports and docstrings."""

    selected_projects: Annotated[
        t.StrSequence | None,
        Field(
            default=None,
            alias="projects",
            description="Selected projects",
        ),
    ] = None
    docs_output_dir: Annotated[
        str,
        Field(
            default=c.Infra.DEFAULT_DOCS_OUTPUT_DIR,
            alias="output_dir",
            description="Docs output dir",
        ),
    ] = c.Infra.DEFAULT_DOCS_OUTPUT_DIR

    def generate(
        self,
        workspace_root: Path,
        *,
        projects: t.StrSequence | None = None,
        output_dir: str = c.Infra.DEFAULT_DOCS_OUTPUT_DIR,
        apply: bool = False,
    ) -> p.Result[Sequence[m.Infra.DocsPhaseReport]]:
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
    def execute(self) -> p.Result[bool]:
        """Execute the configured docs generation flow."""
        result = self.generate(
            workspace_root=self.workspace_root,
            projects=self.selected_projects,
            output_dir=self.docs_output_dir,
            apply=self.apply_changes,
        )
        if result.failure:
            return r[bool].fail(result.error or "generate failed")
        return r[bool].ok(True)

    def _generate_scope(
        self,
        scope: m.Infra.DocScope,
        *,
        apply: bool,
        workspace_root: Path,
        projects: t.StrSequence | None = None,
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


__all__: list[str] = ["FlextInfraDocGenerator"]
