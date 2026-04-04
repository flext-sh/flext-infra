"""Phase: Ensure coverage configuration in pyproject.toml."""

from __future__ import annotations

from collections.abc import MutableSequence

import tomlkit
from tomlkit.items import Item, Table

from flext_infra import c, m, t, u


class FlextInfraEnsureCoverageConfigPhase:
    """Ensure coverage report configuration with per-project-type thresholds."""

    def __init__(self, tool_config: m.Infra.ToolConfigDocument) -> None:
        self._tool_config = tool_config

    def apply(
        self,
        doc: tomlkit.TOMLDocument,
        *,
        project_kind: str = "core",
    ) -> t.StrSequence:
        changes: MutableSequence[str] = []
        tool: Item | None = None
        if c.Infra.TOOL in doc:
            raw_tool = doc[c.Infra.TOOL]
            if isinstance(raw_tool, Item):
                tool = raw_tool
        if not isinstance(tool, Table):
            tool = tomlkit.table()
            doc[c.Infra.TOOL] = tool

        coverage_tbl = u.Infra.ensure_table(tool, "coverage")
        run_tbl = u.Infra.ensure_table(coverage_tbl, "run")
        report_tbl = u.Infra.ensure_table(coverage_tbl, "report")

        cov_config = self._tool_config.tools.coverage
        fail_under_map: t.IntMapping = {
            "core": cov_config.fail_under.core,
            "domain": cov_config.fail_under.domain,
            "platform": cov_config.fail_under.platform,
            "integration": cov_config.fail_under.integration,
            "app": cov_config.fail_under.app,
        }
        fail_under = fail_under_map.get(project_kind, cov_config.fail_under.core)

        expected_omit = sorted(set(cov_config.omit))
        _ = u.Cli.toml_sync_value(
            report_tbl,
            "fail_under",
            fail_under,
            changes,
            f"tool.coverage.report.fail_under set to {fail_under}",
        )
        _ = u.Cli.toml_sync_value(
            report_tbl,
            "show_missing",
            True,
            changes,
            "tool.coverage.report.show_missing set to true",
        )
        _ = u.Cli.toml_sync_value(
            report_tbl,
            "skip_covered",
            False,
            changes,
            "tool.coverage.report.skip_covered set to false",
        )
        _ = u.Cli.toml_sync_value(
            report_tbl,
            "precision",
            cov_config.precision,
            changes,
            f"tool.coverage.report.precision set to {cov_config.precision}",
        )
        _ = u.Cli.toml_sync_string_list(
            run_tbl,
            "omit",
            expected_omit,
            changes,
            f"tool.coverage.run.omit set to {expected_omit}",
        )

        return changes


__all__ = ["FlextInfraEnsureCoverageConfigPhase"]
