"""Mypy phase tests for deps modernizer."""

from __future__ import annotations

import tomlkit

from flext_infra import (
    FlextInfraEnsureMypyConfigPhase,
    FlextInfraEnsurePydanticMypyConfigPhase,
)
from tests import m, u


class TestsFlextInfraDepsModernizerMypy:
    """Declarative tests for generated mypy and pydantic-mypy settings."""

    def test_mypy_phase_sets_expected_state(
        self,
        tool_config_document: m.Infra.ToolConfigDocument,
    ) -> None:
        doc = tomlkit.document()

        _ = FlextInfraEnsureMypyConfigPhase(tool_config_document).apply(doc)

        mypy_mapping = u.Tests.toml_mapping(
            u.Tests.toml_mapping(u.Tests.toml_doc_mapping(doc)["tool"])["mypy"],
        )
        assert mypy_mapping["python_version"] == "3.13"
        assert mypy_mapping["exclude"] == tool_config_document.tools.mypy.exclude
        assert set(u.Tests.toml_strings(mypy_mapping["plugins"])) == set(
            tool_config_document.tools.mypy.plugins,
        )
        assert set(u.Tests.toml_strings(mypy_mapping["disable_error_code"])) == set(
            tool_config_document.tools.mypy.disabled_error_codes,
        )
        assert list(u.Tests.toml_list(mypy_mapping["overrides"])) == [
            {
                "module": list(entry.modules),
                "disable_error_code": list(entry.disable_error_codes),
            }
            for entry in tool_config_document.tools.mypy.overrides
        ]
        for key, value in tool_config_document.tools.mypy.boolean_settings.items():
            assert mypy_mapping[key] == value

    def test_mypy_phase_keeps_misc_globally_disabled(
        self,
        tool_config_document: m.Infra.ToolConfigDocument,
    ) -> None:
        doc = tomlkit.document()

        _ = FlextInfraEnsureMypyConfigPhase(tool_config_document).apply(doc)

        mypy_mapping = u.Tests.toml_mapping(
            u.Tests.toml_mapping(u.Tests.toml_doc_mapping(doc)["tool"])["mypy"],
        )
        assert "misc" in u.Tests.toml_strings(mypy_mapping["disable_error_code"])

    def test_mypy_phase_removes_legacy_test_overrides(
        self,
        tool_config_document: m.Infra.ToolConfigDocument,
    ) -> None:
        doc = tomlkit.document()

        _ = FlextInfraEnsureMypyConfigPhase(tool_config_document).apply(doc)

        mypy_mapping = u.Tests.toml_mapping(
            u.Tests.toml_mapping(u.Tests.toml_doc_mapping(doc)["tool"])["mypy"],
        )
        override_modules = {
            tuple(u.Tests.toml_strings(u.Tests.toml_mapping(entry)["module"]))
            for entry in u.Tests.toml_list(mypy_mapping["overrides"])
        }
        assert (
            "*.constants",
            "*.models",
            "*.protocols",
            "*.typings",
            "*.utilities",
        ) not in override_modules
        assert ("tests", "tests.*", "tests.integration.*", "tests.unit.*") not in (
            override_modules
        )
        assert ("tests.helpers.*",) not in override_modules
        assert ("tests.integration.patterns.*",) not in override_modules

    def test_mypy_phase_replaces_managed_lists_and_overrides(
        self,
        tool_config_document: m.Infra.ToolConfigDocument,
    ) -> None:
        doc = tomlkit.parse(
            """
[tool.mypy]
plugins = ["custom.plugin"]
exclude = "^legacy/fixtures(?:/|$)"
disable_error_code = ["misc"]
overrides = [{ module = ["legacy.*"], disable_error_code = ["misc"] }]
""",
        )

        _ = FlextInfraEnsureMypyConfigPhase(tool_config_document).apply(doc)

        mypy_mapping = u.Tests.toml_mapping(
            u.Tests.toml_mapping(u.Tests.toml_doc_mapping(doc)["tool"])["mypy"],
        )
        assert mypy_mapping["exclude"] == tool_config_document.tools.mypy.exclude
        assert list(u.Tests.toml_strings(mypy_mapping["plugins"])) == list(
            tool_config_document.tools.mypy.plugins,
        )
        assert list(u.Tests.toml_strings(mypy_mapping["disable_error_code"])) == list(
            tool_config_document.tools.mypy.disabled_error_codes,
        )
        assert list(u.Tests.toml_list(mypy_mapping["overrides"])) == [
            {
                "module": list(entry.modules),
                "disable_error_code": list(entry.disable_error_codes),
            }
            for entry in tool_config_document.tools.mypy.overrides
        ]

    def test_mypy_phase_is_idempotent(
        self,
        tool_config_document: m.Infra.ToolConfigDocument,
    ) -> None:
        phase = FlextInfraEnsureMypyConfigPhase(tool_config_document)
        doc = tomlkit.document()

        _ = phase.apply(doc)
        second_changes = phase.apply(doc)

        assert second_changes == []

    def test_pydantic_mypy_phase_sets_expected_state(
        self,
        tool_config_document: m.Infra.ToolConfigDocument,
    ) -> None:
        doc = tomlkit.document()

        _ = FlextInfraEnsurePydanticMypyConfigPhase(tool_config_document).apply(doc)

        pydantic_mypy_mapping = u.Tests.toml_mapping(
            u.Tests.toml_mapping(u.Tests.toml_doc_mapping(doc)["tool"])[
                "pydantic-mypy"
            ],
        )
        assert (
            pydantic_mypy_mapping["init_forbid_extra"]
            == tool_config_document.tools.pydantic_mypy.init_forbid_extra
        )
        assert (
            pydantic_mypy_mapping["init_typed"]
            == tool_config_document.tools.pydantic_mypy.init_typed
        )
        assert (
            pydantic_mypy_mapping["warn_required_dynamic_aliases"]
            == tool_config_document.tools.pydantic_mypy.warn_required_dynamic_aliases
        )

    def test_pydantic_mypy_phase_is_idempotent(
        self,
        tool_config_document: m.Infra.ToolConfigDocument,
    ) -> None:
        phase = FlextInfraEnsurePydanticMypyConfigPhase(tool_config_document)
        doc = tomlkit.document()

        _ = phase.apply(doc)
        second_changes = phase.apply(doc)

        assert second_changes == []
