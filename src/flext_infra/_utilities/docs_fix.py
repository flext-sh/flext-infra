"""Fix helpers for docs services."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_cli import u
from flext_infra._utilities.docs import FlextInfraUtilitiesDocs
from flext_infra.constants import c
from flext_infra.models import m
from flext_infra.typings import t

if TYPE_CHECKING:
    from pathlib import Path

    from flext_infra.protocols import p


class FlextInfraUtilitiesDocsFix:
    """Reusable fix helpers exposed through ``u.Infra``."""

    @staticmethod
    def docs_maybe_fix_link(md_file: Path, raw_link: str) -> str | None:
        """Return a corrected link target when a simple ``.md`` fix is possible."""
        result: str | None = None
        if not raw_link.startswith(("http://", "https://", "mailto:", "tel:", "#")):
            base = raw_link.split("#", maxsplit=1)[0]
            if (
                base
                and not (md_file.parent / base).exists()
                and not base.endswith(".md")
            ):
                md_candidate = md_file.parent / f"{base}.md"
                if md_candidate.exists():
                    result = f"{base}.md{raw_link[len(base) :]}"
        return result

    @staticmethod
    def docs_process_markdown_file(
        md_file: Path, *, apply: bool
    ) -> m.Infra.DocsPhaseItemModel:
        """Fix one markdown file and return the phase item summary."""
        original = md_file.read_text(
            encoding=c.Cli.ENCODING_DEFAULT, errors=c.Infra.IGNORE
        )
        link_count = 0

        def replace_link(match: t.Infra.RegexMatch) -> str:
            """Replace link."""
            nonlocal link_count
            text, link = match.groups()
            fixed = FlextInfraUtilitiesDocsFix.docs_maybe_fix_link(md_file, link)
            if fixed is None:
                original_match: str = match.group(0)
                return original_match
            link_count += 1
            return f"[{text}]({fixed})"

        updated = c.Infra.MARKDOWN_LINK_RE.sub(replace_link, original)
        updated, toc_changed = FlextInfraUtilitiesDocs.update_toc(updated)
        if apply and (link_count > 0 or toc_changed > 0) and updated != original:
            _ = md_file.write_text(updated, encoding=c.Cli.ENCODING_DEFAULT)
        return m.Infra.DocsPhaseItemModel(
            phase="fix", file=md_file.as_posix(), links=link_count, toc=toc_changed
        )

    @staticmethod
    def docs_write_fix_reports(
        scope: m.Infra.DocScope,
        *,
        items: t.SequenceOf[m.Infra.DocsPhaseItemModel],
        apply: bool,
    ) -> p.Result[None]:
        """Persist the standard fix summary and markdown report."""
        changes_payload: t.JsonList = [
            {c.Infra.RK_FILE: item.file, "links": item.links, "toc": item.toc}
            for item in items
        ]
        summary_payload = t.Cli.JSON_MAPPING_ADAPTER.validate_python({
            c.Infra.RK_SUMMARY: {
                c.Infra.RK_SCOPE: scope.name,
                "changed_files": len(items),
                "apply": apply,
            },
            "changes": changes_payload,
        })
        return FlextInfraUtilitiesDocs.write_report_pair(
            scope.report_dir,
            stem="fix",
            summary=summary_payload,
            markdown=[
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


__all__: list[str] = ["FlextInfraUtilitiesDocsFix"]
