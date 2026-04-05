"""Documentation builder service."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Annotated, override

from pydantic import Field, PrivateAttr

from flext_core import r
from flext_infra import c, m, p, t, u
from flext_infra.base import s


class FlextInfraDocBuilder(s[bool]):
    """Build MkDocs sites for governed FLEXT scopes."""

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
    _runner: p.Infra.CommandRunner = PrivateAttr(default_factory=u.Infra)

    def build(
        self,
        workspace_root: Path,
        *,
        projects: Sequence[str] | None = None,
        output_dir: str = c.Infra.DEFAULT_DOCS_OUTPUT_DIR,
    ) -> r[Sequence[m.Infra.DocsPhaseReport]]:
        """Build MkDocs sites across project scopes."""
        return u.Infra.run_scoped(
            workspace_root,
            projects=projects,
            output_dir=output_dir,
            handler=self._build_scope,
        )

    @override
    def execute(self) -> r[bool]:
        """Execute the configured docs build flow."""
        result = self.build(
            workspace_root=self.workspace_root,
            projects=self.selected_projects,
            output_dir=self.docs_output_dir,
        )
        if result.is_failure:
            return r[bool].fail(result.error or "build failed")
        failures = sum(
            1 for report in result.value if report.result == c.Infra.Status.FAIL
        )
        if failures:
            return r[bool].fail(f"Build had {failures} failure(s)")
        return r[bool].ok(True)

    @override
    def execute_command(self, params: m.Infra.DocsBuildInput) -> r[bool]:
        """CLI handler that normalizes input into the canonical service model."""
        service = type(self)(
            workspace=params.workspace_path,
            selected_projects=params.project_names,
            docs_output_dir=params.output_dir,
        )
        return service.execute()

    def _build_scope(self, scope: m.Infra.DocScope) -> m.Infra.DocsPhaseReport:
        """Build one scope via ``u.Infra`` and persist its reports."""
        report = self._run_mkdocs(scope)
        self._write_reports(scope, report)
        self.logger.info(
            "docs_build_scope_completed",
            project=scope.name,
            phase=c.Infra.Directories.BUILD,
            result=report.result,
            reason=report.reason,
        )
        return report

    def _run_mkdocs(self, scope: m.Infra.DocScope) -> m.Infra.DocsPhaseReport:
        """Delegate MkDocs execution to the docs utilities."""
        return u.Infra.docs_run_mkdocs(scope, runner=self._runner)

    def _write_reports(
        self,
        scope: m.Infra.DocScope,
        report: m.Infra.DocsPhaseReport,
    ) -> None:
        """Delegate build report persistence to the docs utilities."""
        u.Infra.docs_write_build_reports(scope, report)


__all__ = ["FlextInfraDocBuilder"]
