"""Documentation shared utilities for the u.Infra MRO chain."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_cli import u
from flext_core import r
from flext_infra._utilities._docs_scope_build import (
    FlextInfraUtilitiesDocsScopeBuildMixin,
)
from flext_infra._utilities.docs_contract import FlextInfraUtilitiesDocsContract
from flext_infra._utilities.docs_scope import FlextInfraUtilitiesDocsScope
from flext_infra._utilities.protected_edit import FlextInfraUtilitiesProtectedEdit
from flext_infra.constants import c
from flext_infra.models import m
from flext_infra.typings import t

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from flext_infra.protocols import p


class FlextInfraUtilitiesDocs(FlextInfraUtilitiesDocsScopeBuildMixin):
    """Documentation-related utility methods exposed via u.Infra."""

    @staticmethod
    def iter_markdown_files(workspace_root: Path) -> t.SequenceOf[Path]:
        """Recursively collect markdown files under the docs scope."""
        docs_root = workspace_root / c.Infra.DIR_DOCS
        search_root = docs_root if docs_root.is_dir() else workspace_root
        return sorted(
            path
            for path in search_root.rglob("*.md")
            if ".bak" not in path.name
            and not any(
                part in c.Infra.DOC_EXCLUDED_DIRS or part.startswith(".")
                for part in path.parts
            )
        )

    @staticmethod
    def iter_scope_markdown_files(scope: m.Infra.DocScope) -> t.SequenceOf[Path]:
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
                    scope_root, path.relative_to(docs_root)
                )
            )
        ]

    @staticmethod
    def write_markdown(path: Path, lines: t.StrSequence) -> p.Result[bool]:
        """Write markdown lines to path, creating parent dirs as needed."""
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            u.write_file(
                path, "\n".join(lines).rstrip() + "\n", encoding=c.Cli.ENCODING_DEFAULT
            )
            return r[bool].ok(True)
        except OSError as exc:
            return r[bool].fail(f"markdown write error: {exc}")

    @staticmethod
    def write_report_pair(
        report_dir: Path,
        *,
        stem: str,
        summary: t.JsonMapping,
        markdown: t.StrSequence,
    ) -> p.Result[None]:
        """Persist one JSON/Markdown report pair as one rollback-safe operation."""
        serialized = u.Cli.json_dumps(summary, indent=2)
        if serialized.failure:
            error = serialized.error
            if error is None:
                msg = "report summary serialization failed without an error"
                raise RuntimeError(msg)
            return r[None].fail(error)
        updates = {
            report_dir / f"{stem}-summary.json": serialized.value + "\n",
            report_dir / f"{stem}-report.md": "\n".join(markdown).rstrip() + "\n",
        }
        try:
            FlextInfraUtilitiesProtectedEdit.protected_source_writes(
                updates,
                request=m.Infra.ProtectedSourceWritesRequest(workspace=report_dir),
            )
        except (*c.EXC_OS_VALIDATION, UnicodeError) as exc:
            return r[None].fail_op("persist docs report pair", exc)
        return r[None].ok(None)

    @staticmethod
    def docs_persistence_failure(
        *,
        phase: str,
        scope: str,
        error: str | None,
        report: m.Infra.DocsPhaseReport | None = None,
    ) -> m.Infra.DocsPhaseReport:
        """Represent one exact report-persistence error in the phase result."""
        if error is None:
            msg = f"{phase} report persistence failed without an error"
            raise RuntimeError(msg)
        failure = {
            "result": c.Infra.ResultStatus.FAIL,
            "reason": error,
            "message": error,
            "passed": False,
        }
        if report is not None:
            return report.model_copy(update=failure)
        return m.Infra.DocsPhaseReport(
            phase=phase,
            scope=scope,
            result=c.Infra.ResultStatus.FAIL,
            reason=error,
            message=error,
            passed=False,
        )

    @staticmethod
    def anchorize(text: str) -> str:
        """Convert a heading title to a GitHub-compatible anchor slug."""
        return FlextInfraUtilitiesDocsContract.docs_anchorize(text)

    @staticmethod
    def build_toc(content: str) -> str:
        """Generate a TOC block from ## and ### headings in content."""
        return FlextInfraUtilitiesDocsContract.docs_build_toc(content)

    @staticmethod
    def update_toc(content: str) -> t.StrIntPair:
        """Insert or replace the TOC in content, returning (updated, changed)."""
        return FlextInfraUtilitiesDocsContract.docs_update_toc(content)

    @staticmethod
    def run_scoped(
        workspace_root: Path,
        *,
        projects: t.StrSequence | None,
        output_dir: Path | str,
        handler: Callable[[m.Infra.DocScope], m.Infra.DocsPhaseReport],
    ) -> p.Result[t.SequenceOf[m.Infra.DocsPhaseReport]]:
        """Build scopes and run handler on each, collecting reports."""
        scopes_result = FlextInfraUtilitiesDocs.build_scopes(
            workspace_root=workspace_root, projects=projects, output_dir=output_dir
        )
        if scopes_result.failure:
            return r[t.SequenceOf[m.Infra.DocsPhaseReport]].fail(
                scopes_result.error or "scope error"
            )
        return r[t.SequenceOf[m.Infra.DocsPhaseReport]].ok([
            handler(scope) for scope in scopes_result.value
        ])


__all__: list[str] = ["FlextInfraUtilitiesDocs"]
