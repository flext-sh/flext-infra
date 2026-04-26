"""Documentation fixer service."""

from __future__ import annotations

from collections.abc import (
    Sequence,
)
from pathlib import Path
from typing import override

from flext_infra import (
    c,
    m,
    p,
    t,
    u,
)
from flext_infra.docs.base import FlextInfraDocServiceBase


class FlextInfraDocFixer(FlextInfraDocServiceBase):
    """Fix links and TOCs across governed FLEXT docs scopes."""

    def fix(
        self,
        workspace_root: Path,
        *,
        projects: t.StrSequence | None = None,
        output_dir: Path | str | None = None,
        apply: bool = False,
    ) -> p.Result[Sequence[m.Infra.DocsPhaseReport]]:
        """Run documentation fixes across project scopes."""
        return self.run_scoped_docs(
            workspace_root,
            projects=projects,
            output_dir=output_dir,
            handler=lambda scope: self._fix_scope(scope, apply=apply),
        )

    @override
    def execute(self) -> p.Result[bool]:
        """Execute the configured docs fix flow."""
        return self._propagate_phase_outcome(
            "fix",
            self.fix(
                workspace_root=self.workspace_root,
                projects=self.selected_projects,
                output_dir=self.output_dir,
                apply=self.apply_changes,
            ),
        )

    def _fix_scope(
        self,
        scope: m.Infra.DocScope,
        *,
        apply: bool,
    ) -> m.Infra.DocsPhaseReport:
        """Run TOC and link fixes on one scope and persist the reports."""
        collected: list[m.Infra.DocsPhaseItemModel] = []
        for md_file in u.Infra.iter_scope_markdown_files(scope):
            item = u.Infra.docs_process_markdown_file(
                md_file,
                apply=apply,
            )
            if item.links or item.toc:
                collected.append(
                    m.Infra.DocsPhaseItemModel(
                        phase="fix",
                        file=md_file.relative_to(scope.path).as_posix(),
                        links=item.links,
                        toc=item.toc,
                    ),
                )
        items = tuple(collected)
        u.Infra.docs_write_fix_reports(
            scope,
            items=items,
            apply=apply,
        )
        report = m.Infra.DocsPhaseReport(
            phase="fix",
            scope=scope.name,
            changed_files=len(items),
            applied=apply,
            items=items,
            result=(
                c.Infra.ResultStatus.OK
                if apply or not items
                else c.Infra.ResultStatus.WARN
            ),
            reason=f"changes:{len(items)}",
            passed=apply or not items,
        )
        self.logger.info(
            "docs_fix_scope_completed",
            project=scope.name,
            phase="fix",
            result=report.result,
            reason=report.reason,
        )
        return report


__all__: list[str] = ["FlextInfraDocFixer"]
