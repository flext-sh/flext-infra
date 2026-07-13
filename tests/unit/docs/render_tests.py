"""Behavior tests for managed mkdocs.yml rendering (exclude_docs / nav404)."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from tests import m
from tests import u
from flext_tests import tm

if TYPE_CHECKING:
    from pathlib import Path


class TestsDocsRenderExcludeDocs:
    """nav404 regression: exclude_docs must keep nested section READMEs (mro-3o9s).

    MkDocs evaluates ``exclude_docs`` as gitignore-style patterns
    (``pathspec.GitIgnoreSpec``). A bare ``README.md`` drops every section
    README that generated index pages link to, producing 404s in the built
    site nav; the rooted ``/README.md`` excludes only the docs-dir root README.
    """

    def test_project_mkdocs_excludes_root_readme_only(self, tmp_path: Path) -> None:
        scope = m.Infra.DocScope(
            name="flext-demo", path=tmp_path, report_dir=tmp_path / ".reports/docs"
        )

        rendered = u.Infra.docs_project_mkdocs(scope, {}, [])

        # mro-i6nq.10: Validate the rendered public artifact through pathspec's
        # documented text-stream boundary, without an ad-hoc extraction helper.
        match = re.search(r"exclude_docs: \|\n((?: {2}\S.*\n)+)", rendered)
        tm.that(match, none=False)
        patterns = tuple(
            line.strip() for line in match.group(1).splitlines() if line.strip()
        )
        # The rooted pattern excludes only the docs-dir root README; a bare
        # README.md would also hide every nested section README from MkDocs.
        tm.that(patterns, has="/README.md")
        tm.that(patterns, lacks="README.md")
