"""Documentation builder service."""

from __future__ import annotations

from collections.abc import (
    Sequence,
)
from pathlib import Path
from typing import Annotated, override

from flext_infra import FlextInfraProjectSelectionServiceBase, c, m, p, r, t, u


class FlextInfraDocBuilder(FlextInfraProjectSelectionServiceBase[bool]):
    """Build MkDocs sites for governed FLEXT scopes."""

    output_dir: Annotated[
        str,
        m.Field(description="Docs output dir"),
    ] = c.Infra.DEFAULT_DOCS_OUTPUT_DIR

    _runner: p.Cli.CommandRunner = u.PrivateAttr(default_factory=u.Cli)

    def build(
        self,
        workspace_root: Path,
        *,
        projects: t.StrSequence | None = None,
        output_dir: str = c.Infra.DEFAULT_DOCS_OUTPUT_DIR,
    ) -> p.Result[Sequence[m.Infra.DocsPhaseReport]]:
        """Build MkDocs sites across project scopes."""
        return self.run_scoped_docs(
            workspace_root,
            projects=projects,
            output_dir=output_dir,
            handler=self._build_scope,
        )

    @override
    def execute(self) -> p.Result[bool]:
        """Execute the configured docs build flow."""
        result = self.build(
            workspace_root=self.workspace_root,
            projects=self.selected_projects,
            output_dir=self.output_dir,
        )
        if result.failure:
            return r[bool].fail(result.error or "build failed")
        failures = sum(
            1 for report in result.value if report.result == c.Infra.ResultStatus.FAIL
        )
        if failures:
            return r[bool].fail(f"Build had {failures} failure(s)")
        return r[bool].ok(True)

    def _build_scope(self, scope: m.Infra.DocScope) -> m.Infra.DocsPhaseReport:
        """Build one scope via ``u.Infra`` and persist its reports."""
        report = u.Infra.docs_run_mkdocs(scope, runner=self._runner)
        u.Infra.docs_write_build_reports(scope, report)
        self.logger.info(
            "docs_build_scope_completed",
            project=scope.name,
            phase=c.Infra.DIR_BUILD,
            result=report.result,
            reason=report.reason,
        )
        return report


__all__: list[str] = ["FlextInfraDocBuilder"]
