"""Fix helpers for docs services."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from flext_cli import u
from flext_infra import FlextInfraUtilitiesDocs, FlextInfraUtilitiesPatterns, c, m, t


class FlextInfraUtilitiesDocsFix(u.Cli):
    """Reusable fix helpers exposed through ``u.Infra``."""

    @staticmethod
    def docs_maybe_fix_link(md_file: Path, raw_link: str) -> str | None:
        """Return a corrected link target when a simple ``.md`` fix is possible."""
        if raw_link.startswith(("http://", "https://", "mailto:", "tel:", "#")):
            return None
        base = raw_link.split("#", maxsplit=1)[0]
        if not base:
            return None
        if (md_file.parent / base).exists():
            return None
        if base.endswith(".md"):
            return None
        md_candidate = md_file.parent / f"{base}.md"
        if not md_candidate.exists():
            return None
        return f"{base}.md{raw_link[len(base) :]}"

    @staticmethod
    def docs_update_toc(content: str) -> t.Infra.StrIntPair:
        """Insert or replace the standard docs TOC."""
        return FlextInfraUtilitiesDocs.update_toc(content)

    @staticmethod
    def docs_process_markdown_file(
        md_file: Path,
        *,
        apply: bool,
    ) -> m.Infra.DocsPhaseItemModel:
        """Fix one markdown file and return the phase item summary."""
        original = md_file.read_text(
            encoding=c.Infra.Encoding.DEFAULT, errors=c.Infra.IGNORE
        )
        link_count = 0

        def replace_link(match: t.Infra.RegexMatch) -> str:
            nonlocal link_count
            text, link = match.groups()
            fixed = FlextInfraUtilitiesDocsFix.docs_maybe_fix_link(md_file, link)
            if fixed is None:
                return match.group(0)
            link_count += 1
            return f"[{text}]({fixed})"

        updated = FlextInfraUtilitiesPatterns.MARKDOWN_LINK_RE.sub(
            replace_link,
            original,
        )
        updated, toc_changed = FlextInfraUtilitiesDocsFix.docs_update_toc(updated)
        if apply and (link_count > 0 or toc_changed > 0) and updated != original:
            _ = md_file.write_text(updated, encoding=c.Infra.Encoding.DEFAULT)
        return m.Infra.DocsPhaseItemModel(
            phase="fix",
            file=md_file.as_posix(),
            links=link_count,
            toc=toc_changed,
        )

    @staticmethod
    def docs_write_fix_reports(
        scope: m.Infra.DocScope,
        *,
        items: Sequence[m.Infra.DocsPhaseItemModel],
        apply: bool,
    ) -> None:
        """Persist the standard fix summary and markdown report."""
        _ = FlextInfraUtilitiesDocsFix.json_write(
            scope.report_dir / "fix-summary.json",
            {
                c.Infra.ReportKeys.SUMMARY: {
                    c.Infra.ReportKeys.SCOPE: scope.name,
                    "changed_files": len(items),
                    "apply": apply,
                },
                "changes": [
                    {
                        c.Infra.ReportKeys.FILE: item.file,
                        "links": item.links,
                        "toc": item.toc,
                    }
                    for item in items
                ],
            },
        )
        _ = FlextInfraUtilitiesDocs.write_markdown(
            scope.report_dir / "fix-report.md",
            [
                "# Docs Fix Report",
                "",
                f"Scope: {scope.name}",
                f"Apply: {int(apply)}",
                f"Changed files: {len(items)}",
                "",
                "| file | link_fixes | toc_updates |",
                "|---|---:|---:|",
                *[f"| {item.file} | {item.links} | {item.toc} |" for item in items],
            ],
        )


__all__ = ["FlextInfraUtilitiesDocsFix"]
