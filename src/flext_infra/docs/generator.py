"""Documentation generator service driven by code, exports, and docstrings."""

from __future__ import annotations

from collections.abc import (
    Sequence,
)
from typing import override

from flext_infra import (
    m,
    p,
    u,
)
from flext_infra.docs.base import FlextInfraDocServiceBase


class FlextInfraDocGenerator(FlextInfraDocServiceBase):
    """Generate managed docs artifacts from package exports and docstrings."""

    def generate(
        self,
        request: m.Infra.DocsGenerateRequest,
    ) -> p.Result[Sequence[m.Infra.DocsPhaseReport]]:
        """Generate docs across the workspace root and governed FLEXT projects."""
        return self.run_scoped_docs(
            request.workspace_root,
            projects=request.projects,
            output_dir=request.output_dir,
            handler=lambda scope: self._generate_scope(
                scope,
                request=request,
            ),
        )

    @override
    def execute(self) -> p.Result[bool]:
        """Execute the configured docs generation flow."""
        return self._propagate_phase_outcome(
            "generate",
            self.generate(
                m.Infra.DocsGenerateRequest(
                    workspace_root=self.workspace_root,
                    projects=self.selected_projects,
                    output_dir=self.output_dir,
                    apply=self.apply_changes,
                ),
            ),
        )

    def _generate_scope(
        self,
        scope: m.Infra.DocScope,
        *,
        request: m.Infra.DocsGenerateRequest,
    ) -> m.Infra.DocsPhaseReport:
        """Generate one scope via the docs generator utilities and log the result."""
        report = u.Infra.docs_generate_scope(
            scope,
            apply=request.apply,
            workspace_root=request.workspace_root,
            projects=request.projects,
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
