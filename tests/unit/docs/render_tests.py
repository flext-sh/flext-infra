"""Behavior tests for managed mkdocs.yml rendering (exclude_docs / nav404)."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

import pathspec

from tests.models import m
from tests.utilities import u

if TYPE_CHECKING:
    from pathlib import Path


def _exclude_doc_patterns(rendered_yml: str) -> list[str]:
    """Extract native ``exclude_docs`` patterns from a rendered mkdocs.yml."""
    match = re.search(r"exclude_docs: \|\n((?: {2}\S.*\n)+)", rendered_yml)
    if match is None:
        return []
    return [line.strip() for line in match.group(1).splitlines() if line.strip()]


class TestsDocsRenderExcludeDocs:
    """nav404 regression: exclude_docs must keep nested section READMEs (mro-3o9s).

    MkDocs evaluates ``exclude_docs`` as gitignore-style patterns
    (``pathspec.GitIgnoreSpec``). A bare ``README.md`` drops every section
    README that generated index pages link to, producing 404s in the built
    site nav; the rooted ``/README.md`` excludes only the docs-dir root README.
    """

    def test_project_mkdocs_excludes_root_readme_only(self, tmp_path: Path) -> None:
        scope = m.Infra.DocScope(
            name="flext-demo",
            path=tmp_path,
            report_dir=tmp_path / ".reports/docs",
        )

        rendered = u.Infra.docs_project_mkdocs(scope, {}, [])

        patterns = _exclude_doc_patterns(rendered)
        assert "/README.md" in patterns
        spec = pathspec.gitignore.GitIgnoreSpec.from_lines(patterns)
        # The docs-dir root README (project mirror) stays excluded...
        assert spec.match_file("README.md")
        # ...while nested section READMEs linked by generated index pages survive.
        assert not spec.match_file("guides/README.md")
        assert not spec.match_file("api-reference/README.md")
