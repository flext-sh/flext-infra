"""Mypy phase tests for deps modernizer."""

from __future__ import annotations

from typing import TYPE_CHECKING

import tomlkit

from flext_infra.deps.phases.ensure_mypy import FlextInfraEnsureMypyConfigPhase
from flext_infra.deps.phases.ensure_pydantic_mypy import (
    FlextInfraEnsurePydanticMypyConfigPhase,
)
from tests import u
from flext_tests import tm

from tests import m



class TestsFlextInfraDepsModernizerMypy:
    """Declarative tests for generated mypy and pydantic-mypy settings."""

    def test_mypy_phase_sets_expected_state(
        self, tool_config_document: p.Infra.ToolConfigDocument
    ) -> None:
        """Verify mypy phase sets expected state."""
        doc = tomlkit.document()

        _ = FlextInfraEnsureMypyConfigPhase(tool_config_document).apply(doc)

        mypy_mapping = u.Tests.toml_mapping(
            u.Tests.toml_mapping(u.Tests.toml_doc_mapping(doc)["tool"])["mypy"]
        )
        tm.that(mypy_mapping["python_version"], eq="3.13")
        tm.that(mypy_mapping["exclude"], eq=tool_config_document.tools.mypy.exclude)
        tm.that(
            set(u.Tests.toml_strings(mypy_mapping["plugins"])),
            eq=set(tool_config_document.tools.mypy.plugins),
        )
        tm.that(
            set(u.Tests.toml_strings(mypy_mapping["disable_error_code"])),
            eq=set(tool_config_document.tools.mypy.disabled_error_codes),
        )
        tm.that(
            list(u.Tests.toml_list(mypy_mapping["overrides"])),
            eq=[
                {
                    "module": list(entry.modules),
                    "disable_error_code": list(entry.disable_error_codes),
                }
                for entry in tool_config_document.tools.mypy.overrides
            ],
        )
        for key, value in tool_config_document.tools.mypy.boolean_settings.items():
            tm.that(mypy_mapping[key], eq=value)

    def test_mypy_phase_keeps_misc_globally_disabled(
        self, tool_config_document: p.Infra.ToolConfigDocument
    ) -> None:
        """Verify mypy phase keeps misc globally disabled."""
        doc = tomlkit.document()

        _ = FlextInfraEnsureMypyConfigPhase(tool_config_document).apply(doc)

        mypy_mapping = u.Tests.toml_mapping(
            u.Tests.toml_mapping(u.Tests.toml_doc_mapping(doc)["tool"])["mypy"]
        )
        tm.that(u.Tests.toml_strings(mypy_mapping["disable_error_code"]), has="misc")

    def test_mypy_phase_removes_legacy_test_overrides(
        self, tool_config_document: p.Infra.ToolConfigDocument
    ) -> None:
        """Verify mypy phase removes legacy test overrides."""
        doc = tomlkit.document()

        _ = FlextInfraEnsureMypyConfigPhase(tool_config_document).apply(doc)

        mypy_mapping = u.Tests.toml_mapping(
            u.Tests.toml_mapping(u.Tests.toml_doc_mapping(doc)["tool"])["mypy"]
        )
        override_modules = {
            tuple(u.Tests.toml_strings(u.Tests.toml_mapping(entry)["module"]))
            for entry in u.Tests.toml_list(mypy_mapping["overrides"])
        }
        tm.that(
            override_modules,
            lacks=(
                "*.constants",
                "*.models",
                "*.protocols",
                "*.typings",
                "*.utilities",
            ),
        )
        tm.that(
            (override_modules),
            lacks=("tests", "tests.*", "tests.integration.*", "tests.unit.*"),
        )
        tm.that(override_modules, lacks=("tests.helpers.*",))
        tm.that(override_modules, lacks=("tests.integration.patterns.*",))

    def test_mypy_phase_replaces_managed_lists_and_overrides(
        self, tool_config_document: p.Infra.ToolConfigDocument
    ) -> None:
        """Verify mypy phase replaces managed lists and overrides."""
        doc = tomlkit.parse(
            """
[tool.mypy]
plugins = ["custom.plugin"]
exclude = "^legacy/fixtures(?:/|$)"
disable_error_code = ["misc"]
overrides = [{ module = ["legacy.*"], disable_error_code = ["misc"] }]
"""
        )

        _ = FlextInfraEnsureMypyConfigPhase(tool_config_document).apply(doc)

        mypy_mapping = u.Tests.toml_mapping(
            u.Tests.toml_mapping(u.Tests.toml_doc_mapping(doc)["tool"])["mypy"]
        )
        tm.that(mypy_mapping["exclude"], eq=tool_config_document.tools.mypy.exclude)
        tm.that(
            list(u.Tests.toml_strings(mypy_mapping["plugins"])),
            eq=list(tool_config_document.tools.mypy.plugins),
        )
        tm.that(
            list(u.Tests.toml_strings(mypy_mapping["disable_error_code"])),
            eq=list(tool_config_document.tools.mypy.disabled_error_codes),
        )
        tm.that(
            list(u.Tests.toml_list(mypy_mapping["overrides"])),
            eq=[
                {
                    "module": list(entry.modules),
                    "disable_error_code": list(entry.disable_error_codes),
                }
                for entry in tool_config_document.tools.mypy.overrides
            ],
        )

    def test_mypy_phase_removes_deprecated_strict_concatenate(self) -> None:
        """Verify mypy phase removes deprecated strict concatenate."""
        tool_config_document = u.Tests.tool_config_document()
        doc = tomlkit.parse(
            """
[tool.mypy]
strict_concatenate = true
warn_return_any = false
"""
        )

        _ = FlextInfraEnsureMypyConfigPhase(tool_config_document).apply(doc)

        mypy_mapping = u.Tests.toml_mapping(
            u.Tests.toml_mapping(u.Tests.toml_doc_mapping(doc)["tool"])["mypy"]
        )
        tm.that(mypy_mapping, lacks="strict_concatenate")
        tm.that(
            mypy_mapping["warn_return_any"],
            eq=tool_config_document.tools.mypy.boolean_settings["warn_return_any"],
        )

    def test_mypy_phase_is_idempotent(
        self, tool_config_document: p.Infra.ToolConfigDocument
    ) -> None:
        """Verify mypy phase is idempotent."""
        phase = FlextInfraEnsureMypyConfigPhase(tool_config_document)
        doc = tomlkit.document()

        _ = phase.apply(doc)
        second_changes = phase.apply(doc)

        tm.that(second_changes, eq=[])

    def test_pydantic_mypy_phase_sets_expected_state(
        self, tool_config_document: p.Infra.ToolConfigDocument
    ) -> None:
        """Verify pydantic mypy phase sets expected state."""
        doc = tomlkit.document()

        _ = FlextInfraEnsurePydanticMypyConfigPhase(tool_config_document).apply(doc)

        pydantic_mypy_mapping = u.Tests.toml_mapping(
            u.Tests.toml_mapping(u.Tests.toml_doc_mapping(doc)["tool"])["pydantic-mypy"]
        )
        tm.that(
            pydantic_mypy_mapping["init_forbid_extra"],
            eq=tool_config_document.tools.pydantic_mypy.init_forbid_extra,
        )
        tm.that(
            pydantic_mypy_mapping["init_typed"],
            eq=tool_config_document.tools.pydantic_mypy.init_typed,
        )
        tm.that(
            pydantic_mypy_mapping["warn_required_dynamic_aliases"],
            eq=tool_config_document.tools.pydantic_mypy.warn_required_dynamic_aliases,
        )

    def test_pydantic_mypy_phase_is_idempotent(
        self, tool_config_document: p.Infra.ToolConfigDocument
    ) -> None:
        """Verify pydantic mypy phase is idempotent."""
        phase = FlextInfraEnsurePydanticMypyConfigPhase(tool_config_document)
        doc = tomlkit.document()

        _ = phase.apply(doc)
        second_changes = phase.apply(doc)

        tm.that(second_changes, eq=[])
