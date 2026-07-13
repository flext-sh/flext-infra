"""Pytest phase tests for deps modernizer."""

from __future__ import annotations

from typing import TYPE_CHECKING

import tomlkit
from flext_tests import tm
from tomlkit import TOMLDocument

from flext_infra.deps.phases.ensure_pytest import FlextInfraEnsurePytestConfigPhase
from tests import t
from tests import u

if TYPE_CHECKING:
    from tests import m


def _test_tool_config() -> m.Infra.ToolConfigDocument:
    result = u.Infra.load_tool_config()
    tm.that(not result.failure, eq=True)
    if result.failure:
        msg = "failed to load tool settings"
        raise ValueError(msg)
    return result.value


def _doc_mapping(doc: TOMLDocument) -> t.JsonMapping:
    return t.Cli.JSON_MAPPING_ADAPTER.validate_python(
        u.normalize_to_json_value(doc.unwrap())
    )


def _mapping(value: t.JsonValue) -> t.JsonMapping:
    return t.Cli.JSON_MAPPING_ADAPTER.validate_python(value)


def _strings(value: t.JsonValue) -> t.StrSequence:
    return t.Infra.STR_SEQ_ADAPTER.validate_python(value)


class TestsFlextInfraDepsModernizerPytest:
    """Tests pytest settings phase behavior."""

    def test_apply_sets_expected_ini_options(self) -> None:
        tool_config = _test_tool_config()
        doc = tomlkit.document()

        _ = FlextInfraEnsurePytestConfigPhase(tool_config).apply(doc)

        ini = _mapping(
            _mapping(_mapping(_doc_mapping(doc)["tool"])["pytest"])["ini_options"]
        )
        tm.that(ini["minversion"], eq="8.0")
        tm.that(list(_strings(ini["python_classes"])), eq=["Test*"])
        tm.that(
            set(_strings(ini["python_files"])),
            eq={"*_test.py", "*_tests.py", "test_*.py"},
        )
        tm.that(
            set(_strings(ini["addopts"])),
            eq=set(tool_config.tools.pytest.standard_addopts),
        )
        tm.that(
            set(_strings(ini["markers"])),
            eq=set(tool_config.tools.pytest.standard_markers),
        )

    def test_apply_merges_existing_project_specific_entries(self) -> None:
        tool_config = _test_tool_config()
        doc = tomlkit.parse(
            """
[tool.pytest.ini_options]
minversion = "7.0"
python_classes = ["Spec*"]
python_files = ["spec_*.py"]
addopts = ["--maxfail=1"]
markers = ["custom: custom marker"]
"""
        )

        _ = FlextInfraEnsurePytestConfigPhase(tool_config).apply(doc)

        ini = _mapping(
            _mapping(_mapping(_doc_mapping(doc)["tool"])["pytest"])["ini_options"]
        )
        tm.that(ini["minversion"], eq="8.0")
        tm.that(set(_strings(ini["python_classes"])), eq={"Spec*", "Test*"})
        tm.that(
            set(_strings(ini["python_files"])),
            eq={"spec_*.py", "*_test.py", "*_tests.py", "test_*.py"},
        )
        tm.that(
            set(_strings(ini["addopts"])),
            eq={"--maxfail=1", *tool_config.tools.pytest.standard_addopts},
        )
        tm.that(
            set(_strings(ini["markers"])),
            eq={"custom: custom marker", *tool_config.tools.pytest.standard_markers},
        )

    def test_apply_is_idempotent(self) -> None:
        tool_config = _test_tool_config()
        phase = FlextInfraEnsurePytestConfigPhase(tool_config)
        doc = tomlkit.document()

        _ = phase.apply(doc)
        second_changes = phase.apply(doc)

        tm.that(second_changes, empty=True)
