"""Mypy phase tests for deps modernizer."""

from __future__ import annotations

import tomlkit
from flext_tests import tm
from tests import m, t, u

from flext_infra import (
    FlextInfraEnsureMypyConfigPhase,
    FlextInfraEnsurePydanticMypyConfigPhase,
)


def _test_tool_config() -> m.Infra.ToolConfigDocument:
    result = u.Infra.load_tool_config()
    tm.that(not result.is_failure, eq=True)
    if result.is_failure:
        msg = "failed to load tool config"
        raise ValueError(msg)
    return result.value


def _doc_mapping(doc: t.Cli.TomlDocument) -> t.Cli.JsonMapping:
    return t.Cli.JSON_MAPPING_ADAPTER.validate_python(
        u.Cli.normalize_json_value(doc.unwrap()),
    )


def _mapping(value: t.Cli.JsonValue) -> t.Cli.JsonMapping:
    return t.Cli.JSON_MAPPING_ADAPTER.validate_python(value)


def _strings(value: t.Cli.JsonValue) -> t.StrSequence:
    return t.Infra.STR_SEQ_ADAPTER.validate_python(value)


def _override_list(value: t.Cli.JsonValue) -> t.Cli.JsonList:
    return t.Cli.JSON_LIST_ADAPTER.validate_python(value)


class TestEnsureMypyConfigPhase:
    """Tests mypy config phase behavior."""

    def test_apply_sets_expected_mypy_state(self) -> None:
        tool_config = _test_tool_config()
        doc = tomlkit.document()

        _ = FlextInfraEnsureMypyConfigPhase(tool_config).apply(doc)

        mypy_mapping = _mapping(_mapping(_doc_mapping(doc)["tool"])["mypy"])
        assert mypy_mapping["python_version"] == "3.13"
        assert set(_strings(mypy_mapping["plugins"])) == set(
            tool_config.tools.mypy.plugins
        )
        assert set(_strings(mypy_mapping["disable_error_code"])) == set(
            tool_config.tools.mypy.disabled_error_codes,
        )
        expected_overrides = [
            {
                "module": list(entry.modules),
                "disable_error_code": list(entry.disable_error_codes),
            }
            for entry in tool_config.tools.mypy.overrides
        ]
        assert list(_override_list(mypy_mapping["overrides"])) == expected_overrides
        for key, value in tool_config.tools.mypy.boolean_settings.items():
            assert mypy_mapping[key] == value

    def test_apply_merges_lists_and_replaces_overrides(self) -> None:
        tool_config = _test_tool_config()
        doc = tomlkit.parse(
            """
[tool.mypy]
plugins = ["custom.plugin"]
disable_error_code = ["misc"]
overrides = [{ module = ["legacy.*"], disable_error_code = ["misc"] }]
""",
        )

        _ = FlextInfraEnsureMypyConfigPhase(tool_config).apply(doc)

        mypy_mapping = _mapping(_mapping(_doc_mapping(doc)["tool"])["mypy"])
        assert set(_strings(mypy_mapping["plugins"])) == {
            "custom.plugin",
            *tool_config.tools.mypy.plugins,
        }
        assert set(_strings(mypy_mapping["disable_error_code"])) == {
            "misc",
            *tool_config.tools.mypy.disabled_error_codes,
        }
        assert list(_override_list(mypy_mapping["overrides"])) == [
            {
                "module": list(entry.modules),
                "disable_error_code": list(entry.disable_error_codes),
            }
            for entry in tool_config.tools.mypy.overrides
        ]

    def test_apply_is_idempotent(self) -> None:
        tool_config = _test_tool_config()
        phase = FlextInfraEnsureMypyConfigPhase(tool_config)
        doc = tomlkit.document()

        _ = phase.apply(doc)
        second_changes = phase.apply(doc)

        tm.that(second_changes, eq=[])


class TestEnsurePydanticMypyConfigPhase:
    """Tests pydantic-mypy config phase behavior."""

    def test_apply_sets_expected_pydantic_mypy_state(self) -> None:
        tool_config = _test_tool_config()
        doc = tomlkit.document()

        _ = FlextInfraEnsurePydanticMypyConfigPhase(tool_config).apply(doc)

        pydantic_mypy_mapping = _mapping(
            _mapping(_doc_mapping(doc)["tool"])["pydantic-mypy"],
        )
        assert (
            pydantic_mypy_mapping["init_forbid_extra"]
            == tool_config.tools.pydantic_mypy.init_forbid_extra
        )
        assert (
            pydantic_mypy_mapping["init_typed"]
            == tool_config.tools.pydantic_mypy.init_typed
        )
        assert (
            pydantic_mypy_mapping["warn_required_dynamic_aliases"]
            == tool_config.tools.pydantic_mypy.warn_required_dynamic_aliases
        )

    def test_apply_is_idempotent(self) -> None:
        tool_config = _test_tool_config()
        phase = FlextInfraEnsurePydanticMypyConfigPhase(tool_config)
        doc = tomlkit.document()

        _ = phase.apply(doc)
        second_changes = phase.apply(doc)

        tm.that(second_changes, eq=[])
