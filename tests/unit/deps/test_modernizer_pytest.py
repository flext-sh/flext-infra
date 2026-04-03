"""Pytest phase tests for deps modernizer."""

from __future__ import annotations

from collections.abc import MutableMapping

import tomlkit
from flext_tests import tm
from tests import m, u

from flext_infra import FlextInfraEnsurePytestConfigPhase


def _test_tool_config() -> m.Infra.ToolConfigDocument:
    result = u.load_tool_config()
    tm.that(not result.is_failure, eq=True)
    if result.is_failure:
        msg = "failed to load tool config"
        raise ValueError(msg)
    return result.value


class TestEnsurePytestConfigPhase:
    """Tests pytest config phase behavior."""

    def test_ensure_pytest_config_sets_fields(self) -> None:
        doc = tomlkit.document()
        doc["tool"] = tomlkit.table()
        changes = FlextInfraEnsurePytestConfigPhase(_test_tool_config()).apply(doc)
        tm.that(any("minversion" in c for c in changes), eq=True)
        tm.that(any("python_classes" in c for c in changes), eq=True)
        tm.that(any("python_files" in c for c in changes), eq=True)
        tm.that(any("addopts" in c for c in changes), eq=True)
        tm.that(any("markers" in c for c in changes), eq=True)

    def test_ensure_pytest_config_preserves_existing(self) -> None:
        doc = tomlkit.document()
        doc["tool"] = {
            "pytest": {
                "ini_options": {"minversion": "8.0", "python_classes": ["Test*"]},
            },
        }
        _ = FlextInfraEnsurePytestConfigPhase(_test_tool_config()).apply(doc)
        tool = doc["tool"]
        assert isinstance(tool, MutableMapping)
        tm.that(tool, is_=MutableMapping)
        pytest_section = tool["pytest"]
        assert isinstance(pytest_section, MutableMapping)
        tm.that(pytest_section, is_=MutableMapping)
        ini_options = pytest_section["ini_options"]
        assert isinstance(ini_options, MutableMapping)
        tm.that(ini_options, is_=MutableMapping)
        tm.that(str(ini_options["minversion"]), eq="8.0")


def test_ensure_pytest_config_phase_apply_minversion() -> None:
    doc = tomlkit.document()
    doc["tool"] = tomlkit.table()
    tool = doc["tool"]
    assert isinstance(tool, MutableMapping)
    tm.that(tool, is_=MutableMapping)
    tool["pytest"] = tomlkit.table()
    pytest_section = tool["pytest"]
    assert isinstance(pytest_section, MutableMapping)
    tm.that(pytest_section, is_=MutableMapping)
    pytest_section["ini_options"] = tomlkit.table()
    changes = FlextInfraEnsurePytestConfigPhase(_test_tool_config()).apply(doc)
    tm.that(any("minversion set to 8.0" in c for c in changes), eq=True)
    ini_options = pytest_section["ini_options"]
    assert isinstance(ini_options, MutableMapping)
    tm.that(ini_options, is_=MutableMapping)
    tm.that(str(ini_options["minversion"]), eq="8.0")


def test_ensure_pytest_config_phase_apply_python_classes() -> None:
    doc = tomlkit.document()
    doc["tool"] = tomlkit.table()
    tool = doc["tool"]
    assert isinstance(tool, MutableMapping)
    tm.that(tool, is_=MutableMapping)
    tool["pytest"] = tomlkit.table()
    pytest_section = tool["pytest"]
    assert isinstance(pytest_section, MutableMapping)
    tm.that(pytest_section, is_=MutableMapping)
    pytest_section["ini_options"] = tomlkit.table()
    changes = FlextInfraEnsurePytestConfigPhase(_test_tool_config()).apply(doc)
    tm.that(any("python_classes updated" in c for c in changes), eq=True)


def test_ensure_pytest_config_phase_apply_markers() -> None:
    doc = tomlkit.document()
    doc["tool"] = tomlkit.table()
    tool = doc["tool"]
    assert isinstance(tool, MutableMapping)
    tm.that(tool, is_=MutableMapping)
    tool["pytest"] = tomlkit.table()
    pytest_section = tool["pytest"]
    assert isinstance(pytest_section, MutableMapping)
    tm.that(pytest_section, is_=MutableMapping)
    pytest_section["ini_options"] = tomlkit.table()
    changes = FlextInfraEnsurePytestConfigPhase(_test_tool_config()).apply(doc)
    tm.that(any("markers" in c for c in changes), eq=True)
