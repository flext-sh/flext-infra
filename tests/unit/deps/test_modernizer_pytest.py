"""Pytest phase tests for deps modernizer."""

from __future__ import annotations

import tomlkit
from flext_tests import tm
from tomlkit import TOMLDocument

from flext_infra import config
from flext_infra.deps.phases.ensure_pytest import FlextInfraEnsurePytestConfigPhase
from tests import t
from tests import u


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
        """Populate every canonical pytest option in an empty document."""
        tool_config = config.Infra.tooling
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

    def test_apply_replaces_policy_and_merges_extension_entries(self) -> None:
        """Replace policy flags while retaining declared discovery extensions."""
        tool_config = config.Infra.tooling
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
            eq=set(tool_config.tools.pytest.standard_addopts),
        )
        tm.that(
            set(_strings(ini["markers"])),
            eq={"custom: custom marker", *tool_config.tools.pytest.standard_markers},
        )

    def test_apply_is_idempotent(self) -> None:
        """Leave a document unchanged after the canonical policy is present."""
        tool_config = config.Infra.tooling
        phase = FlextInfraEnsurePytestConfigPhase(tool_config)
        doc = tomlkit.document()

        _ = phase.apply(doc)
        second_changes = phase.apply(doc)

        tm.that(second_changes, empty=True)
