"""Documentation generator service driven by code, exports, and docstrings."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Annotated, override

from pydantic import Field

from flext_core import r
from flext_infra import c, m, s, t, u


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

    @classmethod
    @override
    def execute_command(
        cls,
        params: s[bool] | m.Infra.DocsGenerateInput,
    ) -> r[bool]:
        """Normalize docs CLI input into the canonical generator service model."""
        if isinstance(params, m.Infra.DocsGenerateInput):
            service = cls.model_validate({
                "workspace_root": params.workspace_path,
                "apply_changes": params.apply,
                "selected_projects": params.project_names,
                "docs_output_dir": params.output_dir,
            })
            return service.execute()
        return params.execute()

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


__all__ = ["FlextInfraDocGenerator"]
