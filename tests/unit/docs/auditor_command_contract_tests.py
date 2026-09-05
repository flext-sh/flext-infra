"""Behavior tests for the public documentation command-contract audit."""

from __future__ import annotations

from flext_tests import tm
from tests import u


class TestsDocsCommandContract:
    """Prove canonical Make, Testmon, and public-test documentation policy."""

    @staticmethod
    def test_accepts_canonical_root_commands() -> None:
        content = """# Commands

```bash
make setup APPLY=Y
make help
make gen APPLY=Y
make test APPLY=Y
make check APPLY=Y
```
"""

        issues = u.Infra.docs_command_contract_content_issues(
            content, relative_path="docs/guides/testing.md"
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
        content = """```bash
make setup
```
"""

        issues = u.Infra.docs_command_contract_content_issues(
            content, relative_path="docs/guides/getting-started.md"
        )

        tm.that(len(issues), eq=1)
        tm.that(issues[0].message, has="requires `APPLY=Y`")

    @staticmethod
    def test_rejects_raw_pytest_execution() -> None:
        content = """```bash
python -m pytest tests/unit
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
