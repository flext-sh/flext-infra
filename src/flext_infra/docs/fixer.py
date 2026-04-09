"""Documentation fixer service."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Annotated, override

from pydantic import Field

from flext_infra import c, m, r, s, t, u


class FlextInfraDocFixer(s[bool]):
    """Fix links and TOCs across governed FLEXT docs scopes."""

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

    def fix(
        self,
        workspace_root: Path,
        *,
        projects: Sequence[str] | None = None,
        output_dir: str = c.Infra.DEFAULT_DOCS_OUTPUT_DIR,
        apply: bool = False,
    ) -> r[Sequence[m.Infra.DocsPhaseReport]]:
        """Run documentation fixes across project scopes."""
        return u.Infra.run_scoped(
            workspace_root,
            projects=projects,
            output_dir=output_dir,
            handler=lambda scope: self._fix_scope(scope, apply=apply),
        )

    @override
    def execute(self) -> r[bool]:
        """Execute the configured docs fix flow."""
        result = self.fix(
            workspace_root=self.workspace_root,
            projects=self.selected_projects,
            output_dir=self.docs_output_dir,
            apply=self.apply_changes,
        )
        if result.is_failure:
            return r[bool].fail(result.error or "fix failed")
        return r[bool].ok(True)

    def _fix_scope(
        self,
        scope: m.Infra.DocScope,
        *,
        apply: bool,
    ) -> m.Infra.DocsPhaseReport:
        """Run TOC and link fixes on one scope and persist the reports."""
        collected: list[m.Infra.DocsPhaseItemModel] = []
        for md_file in u.Infra.iter_scope_markdown_files(scope):
            item = self._process_file(md_file, apply=apply)
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
        u.Infra.docs_write_fix_reports(scope, items=items, apply=apply)
        report = m.Infra.DocsPhaseReport(
            phase="fix",
            scope=scope.name,
            changed_files=len(items),
            applied=apply,
            items=items,
            result=c.Infra.Status.OK if apply or not items else c.Infra.Status.WARN,
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

    def _process_file(
        self,
        md_file: Path,
        *,
        apply: bool,
    ) -> m.Infra.DocsPhaseItemModel:
        """Delegate one-file markdown fixing to ``u.Infra``."""
        return u.Infra.docs_process_markdown_file(md_file, apply=apply)


__all__ = ["FlextInfraDocFixer"]
