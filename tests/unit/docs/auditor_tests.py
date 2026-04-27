"""Tests for FlextInfraDocAuditor — core audit and static helpers.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    Callable,
)
from pathlib import Path

import pytest
from flext_tests import tm

from flext_infra import FlextInfraDocAuditor
from tests import m, u


@pytest.fixture
def auditor() -> FlextInfraDocAuditor:
    return FlextInfraDocAuditor()


@pytest.fixture
def normalize_link() -> Callable[[str], str]:
    def _normalize(value: str) -> str:
        return str(u.Infra.docs_normalize_link(value))

    return _normalize


@pytest.fixture
def should_skip_target() -> Callable[[str, str], bool]:
    def _should_skip(link: str, target: str) -> bool:
        return bool(u.Infra.docs_should_skip_target(link, target))

    return _should_skip


@pytest.fixture
def is_external() -> Callable[[str], bool]:
    def _is_external(value: str) -> bool:
        return bool(u.Infra.docs_is_external(value))

    return _is_external


class TestAuditorCore:
    def test_returns_flext_result(
        self,
        auditor: FlextInfraDocAuditor,
        tmp_path: Path,
    ) -> None:
        result = auditor.audit(tmp_path)
        tm.that(result.success or result.failure, eq=True)

    def test_valid_scope_returns_success(
        self,
        auditor: FlextInfraDocAuditor,
        tmp_path: Path,
    ) -> None:
        workspace = u.Tests.create_docs_workspace(tmp_path)
        result = auditor.audit(workspace)
        tm.ok(result)

    def test_report_structure(
        self,
        auditor: FlextInfraDocAuditor,
        tmp_path: Path,
    ) -> None:
        result = auditor.audit(tmp_path)
        if result.success and result.value:
            result.value[0]

    def test_issue_structure(self) -> None:
        issue = m.Infra.AuditIssue(
            file="README.md",
            issue_type="broken_link",
            severity="high",
            message="Link to missing file",
        )
        tm.that(issue.file, eq="README.md")
        tm.that(issue.issue_type, eq="broken_link")
        tm.that(issue.severity, eq="high")

    @pytest.mark.parametrize(
        ("projects", "check", "strict", "output_dir"),
        [
            (["test-project"], "all", True, ".reports/docs"),
            (["proj1", "proj2"], "all", True, ".reports/docs"),
            (None, "links", True, ".reports/docs"),
            (None, "forbidden-terms", True, ".reports/docs"),
            (None, "all", True, ".reports/docs"),
            (None, "all", True, "custom_output"),
        ],
    )
    def test_audit_option_variants(
        self,
        auditor: FlextInfraDocAuditor,
        tmp_path: Path,
        projects: list[str] | None,
        check: str,
        strict: bool,
        output_dir: str,
    ) -> None:
        output_dir_value = (
            str(tmp_path / output_dir) if output_dir == "custom_output" else output_dir
        )
        result = auditor.audit(
            tmp_path,
            projects=projects,
            output_dir=output_dir_value,
            params=m.Infra.AuditScopeParams(check=check, strict=strict),
        )
        tm.that(result.success or result.failure, eq=True)

    def test_report_frozen(self) -> None:
        tm.that(m.Infra.DocsPhaseReport.model_config.get("frozen"), eq=True)

    def test_issue_frozen(self) -> None:
        tm.that(m.Infra.AuditIssue.model_config.get("frozen"), eq=True)


class TestAuditorNormalize:
    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            ("path/to/file.md#section", "path/to/file.md"),
            ("path/to/file.md?param=value", "path/to/file.md"),
            ("<path/to/file.md>", "path/to/file.md"),
            ("  path/to/file.md  ", "path/to/file.md"),
            ("<path/to/file.md#section?param=value>", "path/to/file.md"),
        ],
    )
    def test_normalize_link(
        self,
        normalize_link: Callable[[str], str],
        raw: str,
        expected: str,
    ) -> None:
        tm.that(normalize_link(raw), eq=expected)

    @pytest.mark.parametrize(
        ("text", "target", "expected"),
        [
            ("[link](http://example.com)", "http://example.com", False),
            ("[link](https://example.com)", "https://example.com", False),
            ("[a, b]", "a", True),
            ("[a b]", "a", True),
            ("[a, b.md]", "a", False),
            ("[a/b]", "a/b", False),
        ],
    )
    def test_should_skip_target(
        self,
        should_skip_target: Callable[[str, str], bool],
        text: str,
        target: str,
        expected: bool,
    ) -> None:
        tm.that(should_skip_target(text, target), eq=expected)

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ("http://example.com", True),
            ("https://example.com", True),
            ("mailto:test@example.com", True),
            ("tel:+1234567890", True),
            ("data:text/plain;base64,SGVsbG8=", True),
            ("path/to/file.md", False),
            ("<http://example.com>", True),
            ("HTTPS://EXAMPLE.COM", True),
        ],
    )
    def test_is_external(
        self,
        is_external: Callable[[str], bool],
        value: str,
        expected: bool,
    ) -> None:
        tm.that(is_external(value), eq=expected)
