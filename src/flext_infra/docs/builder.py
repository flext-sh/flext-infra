"""Documentation builder service."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Annotated, override

from pydantic import Field, PrivateAttr

from flext_core import r
from flext_infra import c, m, p, s, t, u


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
    _runner: p.Cli.CommandRunner = PrivateAttr(default_factory=u.Cli)

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

    @classmethod
    @override
    def execute_command(
        cls,
        params: s[bool] | m.Infra.DocsBuildInput,
    ) -> r[bool]:
        """Normalize docs CLI input into the canonical builder service model."""
        if isinstance(params, m.Infra.DocsBuildInput):
            service = cls.model_validate({
                "workspace_root": params.workspace_path,
                "apply_changes": params.apply,
                "selected_projects": params.project_names,
                "docs_output_dir": params.output_dir,
            })
            return service.execute()
        return params.execute()

    def _build_scope(self, scope: m.Infra.DocScope) -> m.Infra.DocsPhaseReport:
        """Build one scope via ``u.Infra`` and persist its reports."""
        report = u.Infra.docs_run_mkdocs(scope, runner=self._runner)
        u.Infra.docs_write_build_reports(scope, report)
        self.logger.info(
            "docs_build_scope_completed",
            project=scope.name,
            phase=c.Infra.Directories.BUILD,
            result=report.result,
            reason=report.reason,
        )
        return report


__all__ = ["FlextInfraDocBuilder"]
