"""Regression tests for docs codeblock and exported-docstring auditing."""

from __future__ import annotations

from pathlib import Path

from flext_infra._utilities.docs_api import FlextInfraUtilitiesDocsApi
from tests import m, u


def test_docs_python_codeblock_issues_ignore_snippet_only_rules(
    tmp_path: Path,
) -> None:
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    (docs_dir / "snippet.md").write_text(
        "```python\ndef ready() -> bool:\n    return True\n\n\nassert ready()\n```\n",
        encoding="utf-8",
    )
    scope = m.Infra.DocScope(
        name="test",
        path=tmp_path,
        report_dir=tmp_path / "reports",
    )

    issues = u.Infra.docs_python_codeblock_issues(scope)

    assert issues == []


def test_docs_python_codeblock_issues_report_invalid_python(
    tmp_path: Path,
) -> None:
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    (docs_dir / "broken.md").write_text(
        "```python\n**Happy coding!** 🚀\n```\n",
        encoding="utf-8",
    )
    scope = m.Infra.DocScope(
        name="test",
        path=tmp_path,
        report_dir=tmp_path / "reports",
    )

    issues = u.Infra.docs_python_codeblock_issues(scope)

    assert len(issues) == 1
    assert issues[0].issue_type == "python_codeblock"
    assert issues[0].file == "docs/broken.md"


def test_docstring_issues_accept_assignment_docstrings(tmp_path: Path) -> None:
    package_root = tmp_path / "src" / "demo_pkg"
    package_root.mkdir(parents=True, exist_ok=True)
    (package_root / "__init__.py").write_text(
        '"""Demo package."""\n',
        encoding="utf-8",
    )
    (package_root / "lazy.py").write_text(
        '"""Lazy helpers for docs tests."""\n\n'
        "from __future__ import annotations\n\n"
        "class DemoLazy:\n"
        '    """Simple lazy holder for docs tests."""\n\n'
        "lazy = DemoLazy()\n"
        '"""Shared lazy singleton."""\n',
        encoding="utf-8",
    )

    issues = FlextInfraUtilitiesDocsApi.docstring_issues(
        tmp_path,
        {
            "package_name": "demo_pkg",
            "modules": ["demo_pkg.lazy"],
            "target_map": {"lazy": "demo_pkg.lazy"},
        },
    )

    assert issues == []
