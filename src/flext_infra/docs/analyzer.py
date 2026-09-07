"""Documentation analyzer service for CRG-driven code analysis reports.

Invokes the optional AI Hub ``code-review-graph`` CLI as an external subprocess
(never imported as a library) to produce auto-generated risk-analysis pages
under ``docs/architecture/crg-reports/``.  Absence of the CRG binary is treated
as a skip, not a failure.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import TYPE_CHECKING, override

from flext_core import r
from flext_infra import c, m, t, u

from .base import FlextInfraDocServiceBase

if TYPE_CHECKING:
    from flext_infra import p

_MAX_FINDINGS = 50
_MAX_COMMUNITIES = 20
_RAW_TRUNCATE = 50000


class FlextInfraDocAnalyzer(FlextInfraDocServiceBase):
    """Generate CRG-driven code-analysis reports as managed documentation.

    Runs ``code-review-graph`` subcommands (dead-code, architecture,
    large-functions) against the workspace and renders the results into
    auto-generated markdown pages.  Each report carries a generation header
    and a managed TOC so downstream docs phases (fix, build, audit) treat
    them uniformly.
    """

    _runner: p.Cli.CommandRunner = u.PrivateAttr(default_factory=u.Cli)

    def analyze(
        self, repository_root: Path, *, apply: bool = False
    ) -> p.Result[t.SequenceOf[m.Infra.DocsPhaseReport]]:
        """Run CRG analysis and emit report pages under docs/architecture/crg-reports."""
        return self._run_analysis(repository_root, apply=apply)

    @override
    def execute(self) -> p.Result[bool]:
        """Execute the configured CRG analysis flow."""
        return self._propagate_phase_outcome(
            "analyze",
            self.analyze(
                repository_root=self.repository_root, apply=self.apply_changes
            ),
            failure_predicate=lambda report: not report.passed,
        )

    def _run_analysis(
        self, repository_root: Path, *, apply: bool
    ) -> p.Result[t.SequenceOf[m.Infra.DocsPhaseReport]]:
        """Locate CRG, execute analysis subcommands, and write report pages."""
        crg_binary = shutil.which(c.Infra.CRG)
        if crg_binary is None:
            report = m.Infra.DocsPhaseReport(
                phase="analyze",
                scope=c.Infra.RK_ROOT,
                result=c.Infra.ResultStatus.OK,
                message="CRG binary not found; analysis skipped",
                passed=True,
                source="code-review-graph",
            )
            return r[t.SequenceOf[m.Infra.DocsPhaseReport]].ok((report,))
        report_dir = (
            repository_root / c.Infra.DIR_DOCS / c.Infra.DIR_CRG_REPORTS
        )
        if apply:
            report_dir.mkdir(parents=True, exist_ok=True)
        analyses: tuple[tuple[str, str, tuple[str, ...]], ...] = (
            ("dead-code", "Dead Code", ("dead-code", "--kind", "Class", "--json")),
            (
                "architecture",
                "Architecture Risk",
                ("architecture", "--detail-level", "standard"),
            ),
            (
                "large-functions",
                "Large Functions",
                ("large-functions", "--kind", "Function", "--min-lines", "100"),
            ),
        )
        items: list[m.Infra.DocsPhaseItemModel] = []
        for name, label, subcommand in analyses:
            page = self._build_report(
                crg_binary, repository_root, name, label, subcommand
            )
            if page is None:
                continue
            if apply:
                self._write_report(report_dir, name, page)
            items.append(
                m.Infra.DocsPhaseItemModel(
                    phase="analyze",
                    path=f"docs/{c.Infra.DIR_CRG_REPORTS}/{name}.md",
                    written=apply,
                )
            )
        report = m.Infra.DocsPhaseReport(
            phase="analyze",
            scope=c.Infra.RK_ROOT,
            result=c.Infra.ResultStatus.OK,
            message=f"generated {len(items)} CRG report(s)",
            applied=apply,
            generated=len(items),
            items=tuple(items),
            source="code-review-graph",
            passed=True,
        )
        return r[t.SequenceOf[m.Infra.DocsPhaseReport]].ok((report,))

    def _invoke_crg(
        self, binary: str, repo: Path, subcommand: tuple[str, ...]
    ) -> p.Cli.CommandOutput | None:
        """Run a CRG subcommand and return the captured output, or ``None`` on failure."""
        completed = self._runner.run_raw(
            [binary, *subcommand, "--repo", str(repo)],
            cwd=str(repo),
            timeout=120,
        )
        if completed.failure:
            self.logger.warning(
                "crg_run_failed",
                subcommand=subcommand[0],
                error=completed.error or "",
            )
            return None
        output = completed.value
        if not u.Cli.process_succeeded(output.outcome):
            self.logger.warning(
                "crg_analysis_failed",
                subcommand=subcommand[0],
                rc=output.outcome.raw_return_code,
            )
            return None
        return output

    def _build_report(
        self,
        binary: str,
        repo: Path,
        name: str,
        label: str,
        subcommand: tuple[str, ...],
    ) -> str | None:
        """Build one report page from CRG subcommand output."""
        output = self._invoke_crg(binary, repo, subcommand)
        if output is None:
            return None
        body = self._format_output(name, output.stdout)
        page = self._render_page(name, label, body)
        toc_updated, _ = u.Infra.update_toc(page)
        return toc_updated

    def _format_output(self, name: str, raw: str) -> str:
        """Render CRG subcommand output as structured markdown with a raw block.

        CRG subcommands emit JSON by default.  We parse known shapes and render
        concise summaries; the full JSON is always preserved in a collapsible
        raw block so no information is lost.
        """
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return raw.rstrip()
        lines: list[str] = []
        if isinstance(data, list):
            lines.extend(["## Summary", "", f"**Total items: {len(data)}**", ""])
            lines.extend(["## Findings", ""])
            lines.extend(self._format_list_item(name, item) for item in data[:_MAX_FINDINGS])
            if len(data) > _MAX_FINDINGS:
                lines.append(f"- ... and {len(data) - _MAX_FINDINGS} more")
            lines.append("")
        elif isinstance(data, dict):
            for key in ("summary", "context_savings", "total_found", "min_lines"):
                if key in data:
                    lines.extend([f"## {key.replace('_', ' ').title()}", "", str(data[key]), ""])
            if "warnings" in data and isinstance(data["warnings"], list):
                lines.extend(["## Architecture Warnings", ""])
                lines.extend(f"- {w!s}" for w in data["warnings"])
                lines.append("")
            if "communities" in data and isinstance(data["communities"], list):
                lines.extend(["## Top Communities", ""])
                for cmt in data["communities"][:_MAX_COMMUNITIES]:
                    cname = cmt.get("name", "unknown")
                    csize = cmt.get("size", 0)
                    lines.append(f"- {cname} ({csize} nodes)")
                if len(data["communities"]) > _MAX_COMMUNITIES:
                    lines.append(f"- ... and {len(data['communities']) - _MAX_COMMUNITIES} more")
                lines.append("")
            if "results" in data and isinstance(data["results"], list):
                lines.extend(["## Results", ""])
                lines.extend(
                    self._format_list_item(name, item) for item in data["results"][:_MAX_FINDINGS]
                )
                if len(data["results"]) > _MAX_FINDINGS:
                    lines.append(f"- ... and {len(data['results']) - _MAX_FINDINGS} more")
                lines.append("")
        lines.extend(["## Raw Output", "", "<details>", "", "```json"])
        raw_text = raw.rstrip()
        if len(raw_text) > _RAW_TRUNCATE:
            lines.extend([raw_text[:_RAW_TRUNCATE], f"\n\n... (truncated, {len(raw_text) - _RAW_TRUNCATE} chars omitted)"])
        else:
            lines.append(raw_text)
        lines.extend(["```", "", "</details>"])
        return "\n".join(lines)

    @staticmethod
    def _format_list_item(_name: str, item: object) -> str:
        """Format a single list item from JSON output into a markdown bullet."""
        if isinstance(item, dict):
            nm = item.get("name", "")
            fn = item.get("file", "") or item.get("file_path", "")
            ln = item.get("line", "")
            if nm and fn:
                return f"- {nm} (`{fn}`{f':{ln}' if ln else ''})"
            return f"- {json.dumps(item)}"
        return f"- {item}"

    def _render_page(self, name: str, label: str, body: str) -> str:
        """Wrap CRG output into a managed markdown page with auto-generated header."""
        lines = [
            f"<!-- AUTO-GENERATED — DO NOT EDIT MANUALLY. Source: code-review-graph → docs/{c.Infra.DIR_CRG_REPORTS}/{name}.md -->",
            "<!-- Run `make docs APPLY=Y` to regenerate. -->",
            "",
            f"# CRG {label}",
            "",
            "<!-- TOC START -->",
            "<!-- TOC END -->",
            "",
            body,
            "",
        ]
        return "\n".join(lines)

    def _write_report(self, report_dir: Path, name: str, content: str) -> None:
        """Write one report page to the report directory."""
        target = report_dir / f"{name}.md"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding=c.Cli.ENCODING_DEFAULT)
        self.logger.info("crg_report_written", path=str(target))


__all__: list[str] = ["FlextInfraDocAnalyzer"]
