"""Public build-workflow tests for docs services."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra.docs.builder import FlextInfraDocBuilder
from flext_tests import tm
from tests import c, u

if TYPE_CHECKING:
    from pathlib import Path


def test_build_returns_repository_report(tmp_path: Path) -> None:
    workspace = u.Tests.create_docs_workspace(tmp_path)

    result = FlextInfraDocBuilder().build(
        workspace, output_dir=c.Infra.DEFAULT_DOCS_OUTPUT_DIR
    )

    tm.ok(result)
    tm.that([report.scope for report in result.value], eq=["root"])
    tm.that(
        all(report.result == c.Infra.ResultStatus.FAIL for report in result.value),
        eq=True,
    )
    tm.that(all(not report.passed for report in result.value), eq=True)


def test_build_uses_custom_output_dir(tmp_path: Path) -> None:
    workspace = u.Tests.create_docs_workspace(tmp_path)

    result = FlextInfraDocBuilder().build(workspace, output_dir=".custom-docs")

    tm.ok(result)
    tm.that((workspace / ".custom-docs/build-report.md").exists(), eq=True)


def test_build_missing_settings_failure_has_empty_site_dir(tmp_path: Path) -> None:
    workspace = u.Tests.create_docs_workspace(tmp_path)

    result = FlextInfraDocBuilder().build(workspace)

    tm.ok(result)
    tm.that(result.value[0].result, eq=c.Infra.ResultStatus.FAIL)
    tm.that(result.value[0].passed, eq=False)
    tm.that(result.value[0].site_dir, eq="")
