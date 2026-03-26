"""Documentation shared utilities for the u.Infra MRO chain."""

from __future__ import annotations

import re
from collections.abc import Callable, MutableSequence, Sequence
from pathlib import Path

from flext_core import r

from flext_infra import (
    FlextInfraUtilitiesDiscovery,
    FlextInfraUtilitiesPatterns,
    FlextInfraUtilitiesTemplates,
    c,
    m,
    t,
)


class FlextInfraUtilitiesDocs:
    """Documentation-related utility methods exposed via u.Infra."""

    @staticmethod
    def _selected_project_names(
        workspace_root: Path,
        project: str | None,
        projects: str | None,
    ) -> t.StrSequence:
        """Resolve CLI project flags to a concrete name list."""
        if project:
            return [project]
        if projects:
            requested = [part.strip() for part in projects.split(",") if part.strip()]
            if len(requested) == 1 and " " in requested[0]:
                requested = [
                    part.strip() for part in requested[0].split(" ") if part.strip()
                ]
            return requested
        result: r[Sequence[m.Infra.ProjectInfo]] = (
            FlextInfraUtilitiesDiscovery.discover_projects(workspace_root)
        )
        return result.fold(
            on_failure=lambda _: [],
            on_success=lambda v: [p.name for p in v],
        )

    @staticmethod
    def build_scopes(
        workspace_root: Path,
        project: str | None,
        projects: str | None,
        output_dir: str,
    ) -> r[Sequence[m.Infra.DocScope]]:
        """Build DocScope objects for workspace root and each selected project."""
        try:
            scopes: MutableSequence[m.Infra.DocScope] = [
                m.Infra.DocScope(
                    name=c.Infra.ReportKeys.ROOT,
                    path=workspace_root,
                    report_dir=(workspace_root / output_dir).resolve(),
                ),
            ]
            names = FlextInfraUtilitiesDocs._selected_project_names(
                workspace_root,
                project,
                projects,
            )
            for name in names:
                path = (workspace_root / name).resolve()
                if (
                    not path.exists()
                    or not (path / c.Infra.Files.PYPROJECT_FILENAME).exists()
                ):
                    continue
                scopes.append(
                    m.Infra.DocScope(
                        name=name,
                        path=path,
                        report_dir=(path / output_dir).resolve(),
                    ),
                )
            return r[Sequence[m.Infra.DocScope]].ok(scopes)
        except (OSError, TypeError, ValueError) as exc:
            return r[Sequence[m.Infra.DocScope]].fail(
                f"scope resolution failed: {exc}",
            )

    @staticmethod
    def iter_markdown_files(workspace_root: Path) -> Sequence[Path]:
        """Recursively collect markdown files under the docs scope."""
        docs_root = workspace_root / c.Infra.Directories.DOCS
        search_root = docs_root if docs_root.is_dir() else workspace_root
        return sorted(
            path
            for path in search_root.rglob("*.md")
            if not any(
                part in c.Infra.Excluded.DOC_EXCLUDED_DIRS or part.startswith(".")
                for part in path.parts
            )
        )

    @staticmethod
    def write_markdown(path: Path, lines: t.StrSequence) -> r[bool]:
        """Write markdown lines to path, creating parent dirs as needed."""
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            _ = path.write_text(
                "\n".join(lines).rstrip() + "\n",
                encoding=c.Infra.Encoding.DEFAULT,
            )
            return r[bool].ok(True)
        except OSError as exc:
            return r[bool].fail(f"markdown write error: {exc}")

    @staticmethod
    def anchorize(text: str) -> str:
        """Convert a heading title to a GitHub-compatible anchor slug."""
        value = text.strip().lower()
        value = re.sub(r"[^a-z0-9\s-]", "", value)
        value = re.sub(r"\s+", "-", value)
        return re.sub(r"-+", "-", value).strip("-")

    @staticmethod
    def build_toc(content: str) -> str:
        """Generate a TOC block from ## and ### headings in content."""
        items: MutableSequence[str] = []
        for level, title in FlextInfraUtilitiesPatterns.HEADING_H2_H3_RE.findall(
            content
        ):
            anchor = FlextInfraUtilitiesDocs.anchorize(title)
            if not anchor:
                continue
            indent = "  " if level == "###" else ""
            items.append(f"{indent}- [{title}](#{anchor})")
        if not items:
            items = ["- No sections found"]
        return (
            f"{FlextInfraUtilitiesTemplates.TOC_START}\n"
            + "\n".join(items)
            + f"\n{FlextInfraUtilitiesTemplates.TOC_END}"
        )

    @staticmethod
    def update_toc(content: str) -> t.Infra.StrIntPair:
        """Insert or replace the TOC in content, returning (updated, changed)."""
        toc = FlextInfraUtilitiesDocs.build_toc(content)
        if (
            FlextInfraUtilitiesTemplates.TOC_START in content
            and FlextInfraUtilitiesTemplates.TOC_END in content
        ):
            updated = re.sub(
                r"<!-- TOC START -->.*?<!-- TOC END -->",
                toc,
                content,
                count=1,
                flags=re.DOTALL,
            )
            return (updated, int(updated != content))
        lines = content.splitlines()
        if lines and lines[0].startswith("# "):
            insert_at = 1
            while insert_at < len(lines) and (not lines[insert_at].strip()):
                insert_at += 1
            lines.insert(insert_at, "")
            lines.insert(insert_at + 1, toc)
            lines.insert(insert_at + 2, "")
            return ("\n".join(lines) + ("\n" if content.endswith("\n") else ""), 1)
        return (toc + "\n\n" + content, 1)

    @staticmethod
    def run_scoped(
        workspace_root: Path,
        *,
        project: str | None,
        projects: str | None,
        output_dir: str,
        handler: Callable[[m.Infra.DocScope], m.Infra.DocsPhaseReport],
    ) -> r[Sequence[m.Infra.DocsPhaseReport]]:
        """Build scopes and run handler on each, collecting reports."""
        scopes_result = FlextInfraUtilitiesDocs.build_scopes(
            workspace_root=workspace_root,
            project=project,
            projects=projects,
            output_dir=output_dir,
        )
        if scopes_result.is_failure:
            return r[Sequence[m.Infra.DocsPhaseReport]].fail(
                scopes_result.error or "scope error",
            )
        return r[Sequence[m.Infra.DocsPhaseReport]].ok(
            [handler(scope) for scope in scopes_result.value],
        )


__all__ = ["FlextInfraUtilitiesDocs"]
