"""Documentation shared utilities for the u.Infra MRO chain."""

from __future__ import annotations

import re
from collections.abc import (
    Callable,
    MutableSequence,
    Sequence,
)
from pathlib import Path

from flext_cli import u

from flext_infra import (
    FlextInfraUtilitiesBase,
    FlextInfraUtilitiesDocsScope,
    FlextInfraUtilitiesPatterns,
    c,
    m,
    p,
    r,
    t,
)


class FlextInfraUtilitiesDocs:
    """Documentation-related utility methods exposed via u.Infra."""

    @staticmethod
    def _selected_project_names(
        workspace_root: Path,
        projects: t.StrSequence | None,
    ) -> list[str]:
        """Return normalized project filters for docs-scoped operations."""
        _ = workspace_root
        return list(FlextInfraUtilitiesBase.normalize_sequence_values(projects) or ())

    @staticmethod
    def _doc_scope(
        *,
        name: str,
        path: Path,
        output_dir: str,
        project_class: str,
        package_name: str,
    ) -> m.Infra.DocScope:
        """Build one canonical docs scope model."""
        resolved = path.resolve()
        return m.Infra.DocScope(
            name=name,
            path=resolved,
            report_dir=(resolved / output_dir).resolve(),
            project_class=project_class,
            package_name=package_name,
        )

    @staticmethod
    def build_scopes(
        workspace_root: Path,
        projects: t.StrSequence | None,
        output_dir: str,
    ) -> p.Result[Sequence[m.Infra.DocScope]]:
        """Build DocScope objects for workspace root and each selected project."""
        try:
            resolved_root = workspace_root.resolve()
            if FlextInfraUtilitiesDocsScope.is_governed_project(
                resolved_root.name,
                resolved_root.parent,
            ):
                payload = FlextInfraUtilitiesDocsScope.project_payload(resolved_root)
                docs_meta = FlextInfraUtilitiesDocsScope.docs_meta_from_payload(payload)
                return r[Sequence[m.Infra.DocScope]].ok(
                    [
                        FlextInfraUtilitiesDocs._doc_scope(
                            name=resolved_root.name,
                            path=resolved_root,
                            output_dir=output_dir,
                            project_class=FlextInfraUtilitiesDocsScope.classify_project_from_meta(
                                resolved_root.name,
                                docs_meta,
                            ),
                            package_name=FlextInfraUtilitiesDocsScope.package_name_from_payload(
                                resolved_root,
                                payload,
                                docs_meta,
                            ),
                        )
                    ],
                )
            scopes: MutableSequence[m.Infra.DocScope] = [
                FlextInfraUtilitiesDocs._doc_scope(
                    name=c.Infra.RK_ROOT,
                    path=resolved_root,
                    output_dir=output_dir,
                    project_class="root",
                    package_name="",
                )
            ]
            discovered_result = FlextInfraUtilitiesDocsScope.discover_projects(
                resolved_root,
            )
            if discovered_result.failure:
                return r[Sequence[m.Infra.DocScope]].fail(
                    discovered_result.error or "project discovery failed",
                )
            discovered = discovered_result.value
            selected_names = FlextInfraUtilitiesDocs._selected_project_names(
                resolved_root,
                projects,
            )
            if selected_names:
                project_by_name: dict[str, m.Infra.ProjectInfo] = {}
                for project in discovered:
                    project_by_name.setdefault(project.name, project)
                    project_by_name.setdefault(project.path.name, project)
                for name in selected_names:
                    selected = project_by_name.get(name)
                    if selected is not None:
                        scopes.append(
                            FlextInfraUtilitiesDocs._doc_scope(
                                name=selected.name,
                                path=selected.path,
                                output_dir=output_dir,
                                project_class=selected.project_class,
                                package_name=selected.package_name,
                            )
                        )
                        continue
                    project_root = (resolved_root / name).resolve()
                    if not project_root.is_dir():
                        continue
                    if not (project_root / c.Infra.PYPROJECT_FILENAME).is_file():
                        continue
                    payload = FlextInfraUtilitiesDocsScope.project_payload(
                        project_root,
                    )
                    docs_meta = FlextInfraUtilitiesDocsScope.docs_meta_from_payload(
                        payload,
                    )
                    scopes.append(
                        FlextInfraUtilitiesDocs._doc_scope(
                            name=name,
                            path=project_root,
                            output_dir=output_dir,
                            project_class=FlextInfraUtilitiesDocsScope.classify_project_from_meta(
                                name,
                                docs_meta,
                            ),
                            package_name=FlextInfraUtilitiesDocsScope.package_name_from_payload(
                                project_root,
                                payload,
                                docs_meta,
                            ),
                        )
                    )
                return r[Sequence[m.Infra.DocScope]].ok(scopes)
            for project in discovered:
                scopes.append(
                    FlextInfraUtilitiesDocs._doc_scope(
                        name=project.name,
                        path=project.path,
                        output_dir=output_dir,
                        project_class=project.project_class,
                        package_name=project.package_name,
                    )
                )
            return r[Sequence[m.Infra.DocScope]].ok(scopes)
        except (OSError, TypeError, ValueError) as exc:
            return r[Sequence[m.Infra.DocScope]].fail(
                f"scope resolution failed: {exc}",
            )

    @staticmethod
    def iter_markdown_files(workspace_root: Path) -> Sequence[Path]:
        """Recursively collect markdown files under the docs scope."""
        docs_root = workspace_root / c.Infra.DIR_DOCS
        search_root = docs_root if docs_root.is_dir() else workspace_root
        return sorted(
            path
            for path in search_root.rglob("*.md")
            if not any(
                part in c.Infra.DOC_EXCLUDED_DIRS or part.startswith(".")
                for part in path.parts
            )
        )

    @staticmethod
    def iter_scope_markdown_files(
        scope: m.Infra.DocScope,
    ) -> Sequence[Path]:
        """Collect markdown files governed by one docs scope."""
        scope_root = scope.path
        files = FlextInfraUtilitiesDocs.iter_markdown_files(scope_root)
        if scope.name == c.Infra.RK_ROOT:
            return [
                path
                for path in files
                if not FlextInfraUtilitiesDocsScope.is_excluded_doc_path(
                    scope_root,
                    path.relative_to(scope_root / c.Infra.DIR_DOCS)
                    if path.is_relative_to(scope_root / c.Infra.DIR_DOCS)
                    else path.relative_to(scope_root),
                )
            ]
        docs_root = scope_root / c.Infra.DIR_DOCS
        return [
            path
            for path in files
            if not (
                path.is_relative_to(docs_root)
                and FlextInfraUtilitiesDocsScope.is_excluded_doc_path(
                    scope_root,
                    path.relative_to(docs_root),
                )
            )
        ]

    @staticmethod
    def write_markdown(path: Path, lines: t.StrSequence) -> p.Result[bool]:
        """Write markdown lines to path, creating parent dirs as needed."""
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            u.write_file(
                path,
                "\n".join(lines).rstrip() + "\n",
                encoding=c.Infra.ENCODING_DEFAULT,
            )
            return r[bool].ok(True)
        except OSError as exc:
            return r[bool].fail(f"markdown write error: {exc}")

    @staticmethod
    def anchorize(text: str) -> str:
        """Convert a heading title to a GitHub-compatible anchor slug."""
        value = u.norm_str(text, case="lower")
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
        return f"{c.Infra.TOC_START}\n" + "\n".join(items) + f"\n{c.Infra.TOC_END}"

    @staticmethod
    def update_toc(content: str) -> t.Infra.StrIntPair:
        """Insert or replace the TOC in content, returning (updated, changed)."""
        toc = FlextInfraUtilitiesDocs.build_toc(content)
        if c.Infra.TOC_START in content and c.Infra.TOC_END in content:
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
        projects: t.StrSequence | None,
        output_dir: str,
        handler: Callable[
            [m.Infra.DocScope],
            m.Infra.DocsPhaseReport,
        ],
    ) -> p.Result[Sequence[m.Infra.DocsPhaseReport]]:
        """Build scopes and run handler on each, collecting reports."""
        scopes_result = FlextInfraUtilitiesDocs.build_scopes(
            workspace_root=workspace_root,
            projects=projects,
            output_dir=output_dir,
        )
        if scopes_result.failure:
            return r[Sequence[m.Infra.DocsPhaseReport]].fail(
                scopes_result.error or "scope error",
            )
        return r[Sequence[m.Infra.DocsPhaseReport]].ok(
            [handler(scope) for scope in scopes_result.value],
        )


__all__: list[str] = ["FlextInfraUtilitiesDocs"]
