"""Coverage phase tests for deps modernizer."""

from __future__ import annotations

import tomlkit
from flext_tests import tm
from tomlkit import TOMLDocument

from flext_infra import config
from flext_infra.deps.phases.ensure_coverage import FlextInfraEnsureCoverageConfigPhase
from tests import t, u


def _doc_mapping(doc: TOMLDocument) -> t.JsonMapping:
    return t.Cli.JSON_MAPPING_ADAPTER.validate_python(
        u.normalize_to_json_value(doc.unwrap())
    )


def _mapping(value: t.JsonValue) -> t.JsonMapping:
    return t.Cli.JSON_MAPPING_ADAPTER.validate_python(value)


def _strings(value: t.JsonValue) -> t.StrSequence:
    return t.Infra.STR_SEQ_ADAPTER.validate_python(value)


class TestsFlextInfraDepsModernizerCoverage:
    """Tests coverage settings phase behavior."""

    def test_apply_sets_report_and_run_state(self) -> None:
        """Verify apply sets report and run state."""
        tool_config = config.Infra.tooling
        doc = tomlkit.document()

        _ = FlextInfraEnsureCoverageConfigPhase(tool_config).apply(
            doc, project_kind="integration"
        )

        tool = _mapping(_doc_mapping(doc)["tool"])
        coverage = _mapping(tool["coverage"])
        report = _mapping(coverage["report"])
        run = _mapping(coverage["run"])
        tm.that(
            report["fail_under"], eq=tool_config.tools.coverage.fail_under.integration
        )
        tm.that(report["show_missing"], eq=True)
        tm.that(report["skip_covered"], eq=False)
        tm.that(report["precision"], eq=tool_config.tools.coverage.precision)
        tm.that(
            list(_strings(report["exclude_also"])),
            eq=sorted(set(tool_config.tools.coverage.exclude_also)),
        )
        tm.that(
            list(_strings(run["omit"])), eq=sorted(set(tool_config.tools.coverage.omit))
        )

    def test_apply_is_idempotent(self) -> None:
        """Verify apply is idempotent."""
        tool_config = config.Infra.tooling
        phase = FlextInfraEnsureCoverageConfigPhase(tool_config)
        doc = tomlkit.document()

        _ = phase.apply(doc, project_kind="core")
        second_changes = phase.apply(doc, project_kind="core")

        tm.that(second_changes, empty=True)
