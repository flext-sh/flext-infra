"""``make fix`` moves the MkDocs list blocks rumdl reports without a repair.

The documents are scenario data under ``tests/fixtures/markdown-mkdocs-list-indent``
modeled on the consumer findings: under the MkDocs flavor rumdl reports MD007 for
a bullet nested at an ordered item's CommonMark column and MD077 for loose item
content below the MkDocs column, and withholds both fixes. The gate, rumdl and
the generated configuration are the real lane tools.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from flext_infra import config
from flext_infra.gates import FlextInfraGatesMarkdown
from tests import c, m, tm, u

if TYPE_CHECKING:
    from pathlib import Path

    from tests import p


class TestsFlextInfraMarkdownMkdocsListIndent:
    """Public repair contract of the MkDocs list indentation."""

    SCENARIO: ClassVar[str] = "markdown-mkdocs-list-indent"
    # The generated .rumdl.toml renders this typed SSOT, MkDocs flavor for docs/.
    CANONICAL_MARKDOWN_CONFIG: ClassVar[str] = u.Infra.markdown_native_configuration(
        config.Infra.tooling.tools.markdown,
        config.Infra.codegen.markdown_exclude_globs,
    )

    @classmethod
    def _project(
        cls,
        fixture_tree: p.Tests.FixtureTree,
        tmp_path: Path,
        case: str,
    ) -> Path:
        """Materialize one case's documents as a committed project.

        Returns:
            The project root holding the case's ``before`` documents.

        """
        project_dir = u.Tests.mk_project(
            tmp_path,
            f"markdown-{case}",
            markdown_config=cls.CANONICAL_MARKDOWN_CONFIG,
        )
        fixture_tree(f"{cls.SCENARIO}/{case}/before", destination=project_dir)
        u.Tests.initialize_git_repo(project_dir)
        return project_dir

    @staticmethod
    def _fix(tmp_path: Path, project_dir: Path) -> p.Infra.GateExecution:
        """Run the markdown gate's repair once.

        Returns:
            The repair's execution.

        """
        context = m.Infra.GateContext(
            repository_root=tmp_path,
            reports_dir=tmp_path,
            apply_fixes=True,
        )
        return FlextInfraGatesMarkdown(tmp_path).fix(project_dir, context)

    @classmethod
    def _expected(
        cls,
        fixture_tree: p.Tests.FixtureTree,
        tmp_path: Path,
        case: str,
        document: str,
    ) -> str:
        """Read one case's repaired document.

        Returns:
            The ``after`` text of ``document``.

        """
        expected = fixture_tree(
            f"{cls.SCENARIO}/{case}/after", destination=tmp_path / "expected"
        )
        return (expected / document).read_text(encoding=c.DEFAULT_ENCODING)

    def test_fix_moves_each_reported_block_to_the_mkdocs_column(
        self,
        fixture_tree: p.Tests.FixtureTree,
        tmp_path: Path,
    ) -> None:
        """Nested lists, paragraphs, fences and quotes reach the 4-space column.

        Lines rumdl does not report stay byte for byte: tight continuation,
        the two-digit marker already at its column, the bullet child at its
        configured indent and the fenced example outside every list.
        """
        project_dir = self._project(fixture_tree, tmp_path, "repaired")

        result = self._fix(tmp_path, project_dir)

        tm.ok(result.result.passed)
        tm.that(
            (project_dir / "docs" / "guide.md").read_text(encoding=c.DEFAULT_ENCODING),
            eq=self._expected(fixture_tree, tmp_path, "repaired", "docs/guide.md"),
        )
        _ = u.Tests.check_gate_asserting(
            FlextInfraGatesMarkdown,
            tmp_path,
            project_dir,
            passed=True,
            issues_len=0,
        )

    def test_fix_is_idempotent(
        self,
        fixture_tree: p.Tests.FixtureTree,
        tmp_path: Path,
    ) -> None:
        """A repaired document is a fixed point of the next repair."""
        project_dir = self._project(fixture_tree, tmp_path, "repaired")
        guide = project_dir / "docs" / "guide.md"
        _ = self._fix(tmp_path, project_dir)
        repaired = guide.read_bytes()

        again = self._fix(tmp_path, project_dir)

        tm.ok(again.result.passed)
        tm.that(guide.read_bytes(), eq=repaired)

    def test_standard_flavor_markdown_keeps_its_commonmark_columns(
        self,
        fixture_tree: p.Tests.FixtureTree,
        tmp_path: Path,
    ) -> None:
        """Outside the MkDocs flavor the CommonMark content column is the contract."""
        project_dir = self._project(fixture_tree, tmp_path, "repaired")
        authored = (project_dir / "docs" / "guide.md").read_text(
            encoding=c.DEFAULT_ENCODING
        )
        readme = project_dir / "README.md"
        readme.write_text(authored, encoding=c.DEFAULT_ENCODING)
        u.Tests.initialize_git_repo(project_dir)

        _ = self._fix(tmp_path, project_dir)

        tm.that(readme.read_text(encoding=c.DEFAULT_ENCODING), eq=authored)

    def test_bullet_chain_moves_as_one_subtree(
        self,
        fixture_tree: p.Tests.FixtureTree,
        tmp_path: Path,
    ) -> None:
        """A bullet under a bullet keeps its parent; rumdl's verdict stays reported.

        rumdl 0.3.2 expects the second bullet level under an ordered item at
        four columns, where it would become its parent's sibling. The repair
        never flattens the chain: the level moves with its parent and the
        native finding remains the gate's verdict.
        """
        project_dir = self._project(fixture_tree, tmp_path, "bullet-chain")

        result = self._fix(tmp_path, project_dir)

        tm.that(
            (project_dir / "docs" / "chain.md").read_text(encoding=c.DEFAULT_ENCODING),
            eq=self._expected(fixture_tree, tmp_path, "bullet-chain", "docs/chain.md"),
        )
        tm.that(
            [(issue.code, issue.line) for issue in result.issues],
            eq=[("MD007", 5)],
        )
