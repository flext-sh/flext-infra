"""Coverage phase tests for deps modernizer."""

from __future__ import annotations

from collections.abc import MutableMapping

import tomlkit
from flext_tests import tm

from flext_infra import FlextInfraEnsureCoverageConfigPhase, m, u


def _test_tool_config() -> m.Infra.ToolConfigDocument:
    result = u.Infra.load_tool_config()
    tm.that(not result.is_failure, eq=True)
    if result.is_failure:
        msg = "failed to load tool config"
        raise ValueError(msg)
    return result.value


class TestEnsureCoverageConfigPhase:
    """Tests coverage config phase behavior."""

    def test_apply_sets_report_and_run_fields(self) -> None:
        doc = tomlkit.document()
        doc["tool"] = tomlkit.table()
        changes = FlextInfraEnsureCoverageConfigPhase(_test_tool_config()).apply(
            doc,
            project_kind="integration",
        )
        tm.that(
            any("tool.coverage.report.fail_under" in item for item in changes), eq=True
        )
        tm.that(any("tool.coverage.run.omit" in item for item in changes), eq=True)
        tool = doc["tool"]
        assert isinstance(tool, MutableMapping)
        coverage = tool["coverage"]
        assert isinstance(coverage, MutableMapping)
        run = coverage["run"]
        assert isinstance(run, MutableMapping)
        omit = run["omit"]
        tm.that(str(omit), has="dependency_injector/providers.pyx")
