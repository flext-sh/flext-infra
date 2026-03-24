"""Pytest phase tests for deps modernizer."""

from __future__ import annotations

from collections.abc import MutableMapping

import tomlkit
from flext_tests import tm

from flext_infra import FlextInfraEnsurePytestConfigPhase, m, u


def _test_tool_config() -> m.Infra.ToolConfigDocument:
    result = u.Infra.load_tool_config()
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
        tm.that(tool, is_=MutableMapping)
        if not isinstance(tool, MutableMapping):
            return
        pytest_section = tool["pytest"]
        tm.that(pytest_section, is_=MutableMapping)
        if not isinstance(pytest_section, MutableMapping):
            return
        ini_options = pytest_section["ini_options"]
        tm.that(ini_options, is_=MutableMapping)
        if isinstance(ini_options, MutableMapping):
            tm.that(str(ini_options["minversion"]), eq="8.0")


def test_ensure_pytest_config_phase_apply_minversion() -> None:
    doc = tomlkit.document()
    doc["tool"] = tomlkit.table()
    tool = doc["tool"]
    tm.that(tool, is_=MutableMapping)
    if not isinstance(tool, MutableMapping):
        return
    tool["pytest"] = tomlkit.table()
    pytest_section = tool["pytest"]
    tm.that(pytest_section, is_=MutableMapping)
    if not isinstance(pytest_section, MutableMapping):
        return
    pytest_section["ini_options"] = tomlkit.table()
    changes = FlextInfraEnsurePytestConfigPhase(_test_tool_config()).apply(doc)
    tm.that(any("minversion set to 8.0" in c for c in changes), eq=True)
    ini_options = pytest_section["ini_options"]
    tm.that(ini_options, is_=MutableMapping)
    if isinstance(ini_options, MutableMapping):
        tm.that(str(ini_options["minversion"]), eq="8.0")


def test_ensure_pytest_config_phase_apply_python_classes() -> None:
    doc = tomlkit.document()
    doc["tool"] = tomlkit.table()
    tool = doc["tool"]
    tm.that(tool, is_=MutableMapping)
    if not isinstance(tool, MutableMapping):
        return
    tool["pytest"] = tomlkit.table()
    pytest_section = tool["pytest"]
    tm.that(pytest_section, is_=MutableMapping)
    if not isinstance(pytest_section, MutableMapping):
        return
    pytest_section["ini_options"] = tomlkit.table()
    changes = FlextInfraEnsurePytestConfigPhase(_test_tool_config()).apply(doc)
    tm.that(any("python_classes updated" in c for c in changes), eq=True)


def test_ensure_pytest_config_phase_apply_markers() -> None:
    doc = tomlkit.document()
    doc["tool"] = tomlkit.table()
    tool = doc["tool"]
    tm.that(tool, is_=MutableMapping)
    if not isinstance(tool, MutableMapping):
        return
    tool["pytest"] = tomlkit.table()
    pytest_section = tool["pytest"]
    tm.that(pytest_section, is_=MutableMapping)
    if not isinstance(pytest_section, MutableMapping):
        return
    pytest_section["ini_options"] = tomlkit.table()
    changes = FlextInfraEnsurePytestConfigPhase(_test_tool_config()).apply(doc)
    tm.that(any("markers" in c for c in changes), eq=True)
