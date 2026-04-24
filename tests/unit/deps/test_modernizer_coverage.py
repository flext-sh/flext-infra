"""Coverage phase tests for deps modernizer."""

from __future__ import annotations

import tomlkit
from flext_tests import tm
from tomlkit import TOMLDocument

from flext_infra import FlextInfraEnsureCoverageConfigPhase
from tests import m, t, u


def _test_tool_config() -> m.Infra.ToolConfigDocument:
    result = u.Infra.load_tool_config()
    tm.that(not result.failure, eq=True)
    if result.failure:
        msg = "failed to load tool settings"
        raise ValueError(msg)
    return result.value


def _doc_mapping(doc: TOMLDocument) -> t.JsonMapping:
    return t.Cli.JSON_MAPPING_ADAPTER.validate_python(
        u.Cli.normalize_json_value(doc.unwrap()),
    )


def _mapping(value: t.JsonValue) -> t.JsonMapping:
    return t.Cli.JSON_MAPPING_ADAPTER.validate_python(value)


def _strings(value: t.JsonValue) -> t.StrSequence:
    return t.Infra.STR_SEQ_ADAPTER.validate_python(value)


class TestsFlextInfraDepsModernizerCoverage:
    """Tests coverage settings phase behavior."""

    def test_apply_sets_report_and_run_state(self) -> None:
        tool_config = _test_tool_config()
        doc = tomlkit.document()

        _ = FlextInfraEnsureCoverageConfigPhase(tool_config).apply(
            doc,
            project_kind="integration",
        )

        tool = _mapping(_doc_mapping(doc)["tool"])
        coverage = _mapping(tool["coverage"])
        report = _mapping(coverage["report"])
        run = _mapping(coverage["run"])
        assert report["fail_under"] == tool_config.tools.coverage.fail_under.integration
        assert report["show_missing"] is True
        assert report["skip_covered"] is False
        assert report["precision"] == tool_config.tools.coverage.precision
        assert list(_strings(run["omit"])) == sorted(
            set(tool_config.tools.coverage.omit)
        )

    def test_apply_is_idempotent(self) -> None:
        tool_config = _test_tool_config()
        phase = FlextInfraEnsureCoverageConfigPhase(tool_config)
        doc = tomlkit.document()

        _ = phase.apply(doc, project_kind="core")
        second_changes = phase.apply(doc, project_kind="core")

        tm.that(second_changes, empty=True)
