"""Shared documentation behavior independent of the outer docs composition.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from urllib.parse import urlsplit

from flext_cli import u

from flext_infra import c, config, m, r, t
from flext_infra._utilities._docs import (
    FlextInfraUtilitiesDocsScope,
    FlextInfraUtilitiesDocsScopeBuild,
)

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from flext_infra import p


class FlextInfraUtilitiesDocsBase(FlextInfraUtilitiesDocsScopeBuild):
    """Share the documentation operations used by composed components."""

    @staticmethod
    def docs_url_scheme(target: str) -> str:
        """Read a documentation URL scheme, rejecting insecure web links."""
        normalized = u.norm_str(target, case="lower").lstrip("<")
        scheme = urlsplit(normalized).scheme
        if scheme == c.Infra.DOCS_INSECURE_WEB_SCHEME:
            msg = f"insecure documentation URL is prohibited; use HTTPS: {target}"
            raise ValueError(msg)
        return scheme

    @staticmethod
    def docs_is_secure_web_url(target: str) -> bool:
        """Identify HTTPS documentation links."""
        return (
            FlextInfraUtilitiesDocsBase.docs_url_scheme(target)
            == c.Infra.DOCS_SECURE_WEB_SCHEME
        )

    @staticmethod
    def docs_is_python_fence(fence: m.Cli.MarkdownFence) -> bool:
        """Select Python fences governed by executable documentation checks."""
        return (
            fence.language.startswith(c.Infra.MARKDOWN_CODE_LANGUAGE)
            and c.Infra.MARKDOWN_CODE_SKIP_MARKER not in fence.info
        )

    @staticmethod
    def docs_is_external(target: str) -> bool:
        """Identify documentation links with a permitted external scheme."""
        return (
            FlextInfraUtilitiesDocsBase.docs_url_scheme(target)
            in c.Infra.DOCS_EXTERNAL_SCHEMES
        )

    @staticmethod
    def iter_markdown_files(repository_root: Path) -> t.SequenceOf[Path]:
        """Collect Markdown files under the configured documentation scope."""
        docs_root = repository_root / c.Infra.DIR_DOCS
        search_root = docs_root if docs_root.is_dir() else repository_root
        return sorted(
            path
            for path in search_root.rglob("*.md")
            if not any(
                part in config.Infra.codegen.docs_excluded_dirs or part.startswith(".")
                for part in path.relative_to(search_root).parts
            )
        )

    @staticmethod
    def iter_scope_markdown_files(scope: m.Infra.DocScope) -> t.SequenceOf[Path]:
        """Collect the Markdown files governed by one documentation scope."""
        return FlextInfraUtilitiesDocsBase.docs_scope_markdown_paths(
            scope, FlextInfraUtilitiesDocsBase.iter_markdown_files(scope.path)
        )

    @staticmethod
    def docs_scope_markdown_paths(
        scope: m.Infra.DocScope,
        candidates: t.SequenceOf[Path],
    ) -> t.SequenceOf[Path]:
        """Apply scope policy to already captured candidate paths."""
        scope_root = scope.path
        docs_root = scope_root / c.Infra.DIR_DOCS
        search_root = docs_root if docs_root.is_dir() else scope_root
        files = tuple(
            path
            for path in candidates
            if path.suffix == ".md"
            and path.is_relative_to(search_root)
            and not any(
                part in config.Infra.codegen.docs_excluded_dirs or part.startswith(".")
                for part in path.relative_to(search_root).parts
            )
        )
        if scope.name == c.Infra.RK_ROOT:
            return [
                path
                for path in files
                if not FlextInfraUtilitiesDocsScope.excluded_doc_path(
                    scope_root,
                    path.relative_to(docs_root)
                    if path.is_relative_to(docs_root)
                    else path.relative_to(scope_root),
                )
            ]
        return [
            path
            for path in files
            if not (
                path.is_relative_to(docs_root)
                and FlextInfraUtilitiesDocsScope.excluded_doc_path(
                    scope_root, path.relative_to(docs_root)
                )
            )
        ]

    @staticmethod
    def write_markdown(path: Path, lines: t.StrSequence) -> p.Result[bool]:
        """Write Markdown through the SDK file owner."""
        path.parent.mkdir(parents=True, exist_ok=True)
        u.write_file(
            path, "\n".join(lines).rstrip() + "\n", encoding=c.DEFAULT_ENCODING
        )
        return r[bool].ok(value=True)

    @staticmethod
    def docs_write_phase_reports(
        scope: m.Infra.DocScope,
        *,
        phase: str,
        table: m.Cli.TableRenderRequest,
        apply: bool,
    ) -> None:
        """Persist the phase summary and its corresponding Markdown report."""
        payload = u.json_mapping_adapter().validate_python({
            c.Infra.RK_SUMMARY: {
                c.Infra.RK_SCOPE: scope.name,
                "changed_files": len(table.rows),
                "apply": apply,
            },
            "changes": [list(row) for row in table.rows],
        })
        u.Cli.json_write(scope.report_dir / f"{phase}-summary.json", payload).unwrap()
        FlextInfraUtilitiesDocsBase.write_markdown(
            scope.report_dir / f"{phase}-report.md",
            [
                f"# {table.title}",
                "",
                f"Scope: {scope.name}",
                f"Apply: {int(apply)}",
                f"Changed files: {len(table.rows)}",
                "",
                "| " + " | ".join(table.columns) + " |",
                "|---|" + "---:|" * (len(table.columns) - 1),
                *(" | ".join(row) + " |" for row in table.rows),
            ],
        ).unwrap()

    @staticmethod
    def docs_write_fmt_reports(
        scope: m.Infra.DocScope,
        *,
        items: t.SequenceOf[m.Infra.DocsPhaseItemModel],
        apply: bool,
    ) -> None:
        """Persist the standard documentation formatting reports."""
        FlextInfraUtilitiesDocsBase.docs_write_phase_reports(
            scope,
            phase="fmt",
            table=m.Cli.TableRenderRequest(
                title="Docs Format Report",
                columns=("file",),
                rows=tuple((item.file,) for item in items),
            ),
            apply=apply,
        )

    @staticmethod
    def run_scoped(
        repository_root: Path,
        *,
        projects: t.StrSequence | None,
        output_dir: Path | str,
        handler: Callable[[m.Infra.DocScope], m.Infra.DocsPhaseReport],
    ) -> p.Result[t.SequenceOf[m.Infra.DocsPhaseReport]]:
        """Run the selected handler over the elected documentation scopes."""
        return FlextInfraUtilitiesDocsScopeBuild.build_scopes(
            repository_root=repository_root,
            projects=projects,
            output_dir=output_dir,
        ).map(lambda scopes: [handler(scope) for scope in scopes])


__all__ = ["FlextInfraUtilitiesDocsBase"]
