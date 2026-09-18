"""Public markdown-format (prettier) and markdown-code (embedded ruff) gates."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from flext_tests import tm

from flext_infra import c, m, t
from flext_infra.gates.markdown_code import FlextInfraMarkdownCodeGate
from flext_infra.gates.markdown_format import FlextInfraMarkdownFormatGate
from tests import TestsFlextInfraUtilities as u

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraMarkdownFormatAndCodeGates:
    """Declarative public-contract tests for the markdown formatting gates."""

    FORMATTED_MARKDOWN = "# Test\n"
    UNFORMATTED_MARKDOWN = "#    Test\n"
    FORMATTED = "# Test\n\n```python\nx = 1\n```\n"
    UNFORMATTED = "# Test\n\n```python\nx=1\n```\n"
    SYNTAX_BROKEN = "# Test\n\n```python\ndef broken(:\n    return 1\n```\n"
    NOTEST_PSEUDO = "# Test\n\n```python notest\nthis is @@@ not python\n```\n"

    def test_format_gate_reports_unformatted_markdown(self, tmp_path: Path) -> None:
        project_dir = u.Tests.mk_project(tmp_path, "markdown-format-project")
        (project_dir / "README.md").write_text(
            self.UNFORMATTED_MARKDOWN, encoding="utf-8"
        )

        result = u.Tests.check_gate_asserting(
            FlextInfraMarkdownFormatGate,
            tmp_path,
            project_dir,
            passed=False,
            issues_len=1,
        )

        tm.that(result.issues[0].code, eq=c.Infra.MARKDOWN_FORMAT)
        tm.that(result.issues[0].file, eq="README.md")

    def test_format_gate_skips_neutrally_without_markdown(self, tmp_path: Path) -> None:
        project_dir = u.Tests.mk_project(tmp_path, "markdown-format-empty")

        result = u.Tests.check_gate_asserting(
            FlextInfraMarkdownFormatGate,
            tmp_path,
            project_dir,
            passed=True,
            issues_len=0,
        )

        tm.that(result.result.passed, eq=True)

    def test_format_gate_fix_is_the_single_writer(self, tmp_path: Path) -> None:
        """`make fmt` drives prettier --write once and the tree reaches green."""
        project_dir = u.Tests.mk_project(tmp_path, "markdown-format-fix")
        readme = project_dir / "README.md"
        readme.write_text(self.UNFORMATTED_MARKDOWN, encoding="utf-8")
        u.Tests.initialize_git_repo(project_dir)
        context = m.Infra.GateContext(
            repository_root=tmp_path, reports_dir=tmp_path, apply_fixes=True
        )

        result = FlextInfraMarkdownFormatGate(tmp_path).fix(project_dir, context)

        tm.that(result.result.passed, eq=True)
        tm.that(readme.read_text(encoding="utf-8"), eq=self.FORMATTED_MARKDOWN)
        _ = u.Tests.check_gate_asserting(
            FlextInfraMarkdownFormatGate,
            tmp_path,
            project_dir,
            passed=True,
            issues_len=0,
        )

    def test_format_gate_fails_closed_without_provisioned_binary(
        self, tmp_path: Path
    ) -> None:
        """A missing mise-provisioned binary is a tool error, never a clean pass."""
        project_dir = u.Tests.mk_project(tmp_path, "markdown-format-no-binary")
        (project_dir / "README.md").write_text(self.FORMATTED, encoding="utf-8")
        empty_path = tmp_path / "empty-path"
        empty_path.mkdir()

        with tm.scope(env={"PATH": str(empty_path)}):
            result = u.Tests.run_gate_check(
                FlextInfraMarkdownFormatGate, tmp_path, project_dir
            )

        tm.that(result.result.passed, eq=False)
        tm.that(len(result.issues), eq=1)
        tm.that("make setup" in result.issues[0].message, eq=True)

    @pytest.mark.parametrize(
        ("markdown_text", "passed", "issues_len"),
        [(FORMATTED, True, 0), (NOTEST_PSEUDO, True, 0)],
    )
    def test_code_gate_clean_and_notest_blocks(
        self, *, tmp_path: Path, markdown_text: str, passed: bool, issues_len: int
    ) -> None:
        project_dir = u.Tests.mk_project(tmp_path, "markdown-code-clean")
        (project_dir / "README.md").write_text(markdown_text, encoding="utf-8")

        _ = u.Tests.check_gate_asserting(
            FlextInfraMarkdownCodeGate,
            tmp_path,
            project_dir,
            passed=passed,
            issues_len=issues_len,
        )

    def test_code_gate_reports_syntax_broken_block_at_origin(
        self, tmp_path: Path
    ) -> None:
        """Findings map back to the documentation file and block position."""
        project_dir = u.Tests.mk_project(tmp_path, "markdown-code-broken")
        (project_dir / "README.md").write_text(self.SYNTAX_BROKEN, encoding="utf-8")

        result = u.Tests.check_gate_asserting(
            FlextInfraMarkdownCodeGate,
            tmp_path,
            project_dir,
            passed=False,
            issues_len=2,
        )

        tm.that(result.issues[0].file, eq="README.md")
        tm.that(result.issues[0].line, eq=3)

    def test_code_gate_fix_splices_formatted_block_back(self, tmp_path: Path) -> None:
        """`make fix` formats fenced blocks whose round-trip recompiles cleanly."""
        project_dir = u.Tests.mk_project(tmp_path, "markdown-code-fix")
        readme = project_dir / "README.md"
        readme.write_text(self.UNFORMATTED, encoding="utf-8")
        u.Tests.initialize_git_repo(project_dir)
        context = m.Infra.GateContext(
            repository_root=tmp_path, reports_dir=tmp_path, apply_fixes=True
        )

        result = FlextInfraMarkdownCodeGate(tmp_path).fix(project_dir, context)

        tm.that(result.result.passed, eq=True)
        tm.that(readme.read_text(encoding="utf-8"), eq=self.FORMATTED)

    def test_code_gate_does_not_splice_broken_blocks(self, tmp_path: Path) -> None:
        """A block that cannot round-trip stays untouched and is reported."""
        project_dir = u.Tests.mk_project(tmp_path, "markdown-code-no-splice")
        readme = project_dir / "README.md"
        readme.write_text(self.SYNTAX_BROKEN, encoding="utf-8")
        context = m.Infra.GateContext(
            repository_root=tmp_path, reports_dir=tmp_path, apply_fixes=True
        )

        result = FlextInfraMarkdownCodeGate(tmp_path).fix(project_dir, context)

        tm.that(readme.read_text(encoding="utf-8"), eq=self.SYNTAX_BROKEN)
        tm.that(result.result.passed, eq=False)
        tm.that(bool(result.issues), eq=True)

    def test_code_gate_lints_doctest_examples_in_docstrings(
        self, tmp_path: Path
    ) -> None:
        """Docstring examples are validated at their source location."""
        project_dir = u.Tests.mk_project(tmp_path, "markdown-code-docstring")
        source_dir = project_dir / c.Infra.DEFAULT_SRC_DIR
        source_dir.mkdir()
        (source_dir / "widget.py").write_text(
            '"""Widget.\n\n>>> def broken(:\n    return 1\n\n"""\n', encoding="utf-8"
        )

        result = u.Tests.check_gate_asserting(
            FlextInfraMarkdownCodeGate,
            tmp_path,
            project_dir,
            passed=False,
            issues_len=2,
        )

        tm.that(result.issues[0].file, eq="src/widget.py")

    def test_code_gate_skips_neutrally_without_embedded_code(
        self, tmp_path: Path
    ) -> None:
        project_dir = u.Tests.mk_project(tmp_path, "markdown-code-empty")
        (project_dir / "README.md").write_text("# Prose only\n", encoding="utf-8")

        result = u.Tests.check_gate_asserting(
            FlextInfraMarkdownCodeGate, tmp_path, project_dir, passed=True, issues_len=0
        )

        tm.that(result.result.passed, eq=True)


__all__: t.StrSequence = ["TestsFlextInfraMarkdownFormatAndCodeGates"]
