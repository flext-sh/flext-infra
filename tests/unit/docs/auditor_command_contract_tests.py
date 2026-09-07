"""Behavior tests for the public documentation command-contract audit."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra import config
from flext_tests import tm
from tests import m, u

if TYPE_CHECKING:
    from pathlib import Path


class TestsDocsCommandContract:
    """Prove canonical Make, Testmon, and public-test documentation policy."""

    @staticmethod
    def test_accepts_every_declared_verb_rendered_from_the_ssot() -> None:
        """Each declared verb, written exactly as its own spec requires, passes."""
        lines = "\n".join(
            f"make {spec.name} APPLY=Y" if spec.requires_apply else f"make {spec.name}"
            for spec in config.Infra.codegen.make.verbs
        )
        content = f"# Commands\n\n```bash\n{lines}\n```\n"

        issues = u.Infra.docs_command_contract_content_issues(
            content, relative_path="docs/guides/testing.md"
        )

        tm.that(issues, eq=[])

    @staticmethod
    def test_ignores_prose_that_begins_with_make() -> None:
        content = """# Scope

Make surfaces and documentation are changed at their canonical owner.
"""

        issues = u.Infra.docs_command_contract_content_issues(
            content, relative_path="docs/guides/make-commands.md"
        )

        tm.that(issues, eq=[])

    @staticmethod
    def test_rejects_invented_make_selectors() -> None:
        content = """```bash
make test PROJECT=flext-demo MATCH=unit
```
"""

        issues = u.Infra.docs_command_contract_content_issues(
            content, relative_path="docs/guides/testing.md"
        )

        tm.that(len(issues), eq=1)
        tm.that(issues[0].issue_type, eq="command_contract")
        tm.that(issues[0].message, has="invented Make selector")

    @staticmethod
    def test_reads_apply_requirement_from_config_ssot() -> None:
        """A mutating verb documented without the apply token is rejected."""
        mutating = next(
            spec.name for spec in config.Infra.codegen.make.verbs if spec.requires_apply
        )
        content = f"```bash\nmake {mutating}\n```\n"

        issues = u.Infra.docs_command_contract_content_issues(
            content, relative_path="docs/guides/getting-started.md"
        )

        tm.that(len(issues), eq=1)
        tm.that(issues[0].message, has="requires `APPLY=Y`")

    @staticmethod
    def test_rejects_apply_on_a_read_only_verb() -> None:
        """A read-only verb documented with the apply token is rejected."""
        read_only = next(
            spec.name
            for spec in config.Infra.codegen.make.verbs
            if not spec.requires_apply
        )
        content = f"```bash\nmake {read_only} APPLY=Y\n```\n"

        issues = u.Infra.docs_command_contract_content_issues(
            content, relative_path="docs/guides/getting-started.md"
        )

        tm.that(len(issues), eq=1)
        tm.that(issues[0].message, has="rejects `APPLY=Y`")

    @staticmethod
    def test_rejects_raw_pytest_execution() -> None:
        content = """```bash
PYTHONPATH=src python -m pytest tests/unit
```
"""

        issues = u.Infra.docs_command_contract_content_issues(
            content, relative_path="docs/guides/testing.md"
        )

        tm.that(len(issues), eq=1)
        tm.that(issues[0].message, has="bypasses `make test APPLY=Y`")

    @staticmethod
    def test_rejects_direct_tool_execution() -> None:
        content = """```bash
ruff check src
```
"""

        issues = u.Infra.docs_command_contract_content_issues(
            content, relative_path="docs/standards/development.md"
        )

        tm.that(len(issues), eq=1)
        tm.that(issues[0].message, has="bypasses the root Make dispatcher")

    @staticmethod
    def test_scans_recursive_live_docs_from_typed_scope(
        infra_test_workspace: Path,
    ) -> None:
        docs_root = infra_test_workspace / "docs"
        governed = {
            docs_root / "guides" / "nested" / "commands.md": (
                "```bash\nruff check src\n```\n"
            ),
            docs_root / "standards" / "nested" / "commands.md": (
                "```bash\nmake test PROJECT=demo\n```\n"
            ),
        }
        for path, content in governed.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            u.write_file(path, content)
        ungoverned = docs_root / "architecture" / "historical.md"
        ungoverned.parent.mkdir(parents=True, exist_ok=True)
        u.write_file(ungoverned, "```bash\nruff check src\n```\n")
        excluded = docs_root / "standards" / "historical" / "commands.md"
        excluded.parent.mkdir(parents=True, exist_ok=True)
        u.write_file(excluded, "```bash\nruff check src\n```\n")
        u.write_file(
            infra_test_workspace / "pyproject.toml",
            (
                "[project]\nname='infra-pkg'\nversion='0.0.0'\n\n"
                "[tool.flext.docs]\n"
                'exclude_docs=["standards/historical/**"]\n'
            ),
        )
        scope = m.Infra.DocScope(
            name="infra-pkg",
            path=infra_test_workspace,
            report_dir=infra_test_workspace / ".reports" / "docs",
            package_name="infra_pkg",
        )

        issues = u.Infra.docs_command_contract_issues(scope)

        tm.that(len(issues), eq=2)
        tm.that(
            {issue.file for issue in issues},
            eq={"docs/guides/nested/commands.md", "docs/standards/nested/commands.md"},
        )

    @staticmethod
    def test_rejects_test_double_examples() -> None:
        content = """```python
from unittest.mock import patch

result = patch("package.owner")
```
"""

        issues = u.Infra.docs_command_contract_content_issues(
            content, relative_path="docs/standards/testing.md"
        )

        tm.that(len(issues), eq=2)
        tm.that(issues[0].message, has="test-double code")
