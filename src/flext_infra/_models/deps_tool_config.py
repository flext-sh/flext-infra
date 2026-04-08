"""Tool configuration models for the deps subpackage."""

from __future__ import annotations

from typing import Annotated

from pydantic import Field

from flext_core import m
from flext_infra import (
    FlextInfraModelsDepsToolConfigLinters,
    FlextInfraModelsDepsToolConfigTypeCheckers,
    t,
)


class FlextInfraModelsDepsToolSettings(
    FlextInfraModelsDepsToolConfigLinters,
    FlextInfraModelsDepsToolConfigTypeCheckers,
):
    """Models for tool configuration loaded from YAML."""

    class PytestConfig(m.ArbitraryTypesModel):
        """Pytest baseline settings loaded from YAML."""

        standard_markers: Annotated[
            t.StrSequence,
            Field(
                alias="standard-markers",
                description="Standard pytest markers enforced by modernizer.",
            ),
        ]
        standard_addopts: Annotated[
            t.StrSequence,
            Field(
                alias="standard-addopts",
                description="Standard pytest addopts enforced by modernizer.",
            ),
        ]

    class TomlsortConfig(m.ArbitraryTypesModel):
        """tomlsort baseline settings loaded from YAML."""

        all: Annotated[bool, Field(description="Sort all TOML tables and entries.")]
        in_place: Annotated[bool, Field(description="Apply TOML sorting in place.")]
        sort_first: Annotated[
            t.StrSequence, Field(description="Top-level TOML sections ordered first.")
        ]

    class YamlfixConfig(m.ArbitraryTypesModel):
        """yamlfix baseline settings loaded from YAML."""

        line_length: Annotated[int, Field(description="Maximum YAML line length.")]
        preserve_quotes: Annotated[
            bool, Field(description="Preserve quote style in YAML output.")
        ]
        whitelines: Annotated[
            int, Field(description="Blank line count between YAML entries.")
        ]
        section_whitelines: Annotated[
            int, Field(description="Blank line count between YAML sections.")
        ]
        explicit_start: Annotated[
            bool, Field(description="Emit explicit YAML start marker.")
        ]

    class CoverageFailUnderConfig(m.ArbitraryTypesModel):
        """Coverage fail-under thresholds by layer."""

        core: int = Field(
            description="Minimum coverage percentage required for core layer."
        )
        domain: int = Field(
            description="Minimum coverage percentage required for domain layer."
        )
        platform: int = Field(
            description="Minimum coverage percentage required for platform layer."
        )
        integration: int = Field(
            description="Minimum coverage percentage required for integration layer."
        )
        app: int = Field(
            description="Minimum coverage percentage required for app layer."
        )

    class CoverageConfig(m.ArbitraryTypesModel):
        """Coverage baseline settings loaded from YAML."""

        fail_under: FlextInfraModelsDepsToolSettings.CoverageFailUnderConfig = Field(
            alias="fail-under",
            description="Coverage fail-under thresholds by layer.",
        )
        show_missing: Annotated[
            bool,
            Field(
                default=True,
                alias="show-missing",
                description="Display missing lines in coverage report.",
            ),
        ]
        skip_covered: Annotated[
            bool,
            Field(
                default=False,
                alias="skip-covered",
                description="Skip covered files in coverage report.",
            ),
        ]
        precision: Annotated[
            int,
            Field(default=2, description="Decimal precision for coverage percentages."),
        ]
        omit: Annotated[
            t.StrSequence,
            Field(default_factory=list, description="Coverage run omit globs."),
        ]

    class ToolConfigTools(m.ArbitraryTypesModel):
        """Tool map loaded from YAML."""

        codespell: FlextInfraModelsDepsToolSettings.CodespellConfig = Field(
            description="Codespell config"
        )
        ruff: FlextInfraModelsDepsToolSettings.RuffConfig = Field(
            description="Ruff config"
        )
        mypy: FlextInfraModelsDepsToolSettings.MypyConfig = Field(
            description="Mypy config"
        )
        pydantic_mypy: FlextInfraModelsDepsToolSettings.PydanticMypyConfig = Field(
            alias="pydantic-mypy", description="Pydantic mypy plugin configuration."
        )
        pyright: FlextInfraModelsDepsToolSettings.PyrightConfig = Field(
            description="Pyright config"
        )
        pyrefly: FlextInfraModelsDepsToolSettings.PyreflyConfig = Field(
            description="Pyrefly config"
        )
        pytest: FlextInfraModelsDepsToolSettings.PytestConfig = Field(
            description="Pytest config"
        )
        tomlsort: FlextInfraModelsDepsToolSettings.TomlsortConfig = Field(
            description="Tomlsort config"
        )
        yamlfix: FlextInfraModelsDepsToolSettings.YamlfixConfig = Field(
            description="Yamlfix config"
        )
        coverage: FlextInfraModelsDepsToolSettings.CoverageConfig = Field(
            description="Coverage configuration with per-project-type thresholds."
        )

    class ProjectTypeOverrideConfig(m.ArbitraryTypesModel):
        """Per-project-type override settings."""

        pyright: Annotated[
            t.StrMapping,
            Field(description="Pyright override settings for this project type."),
        ] = Field(default_factory=dict)

    class ProjectTypeOverridesConfig(m.ArbitraryTypesModel):
        """Project-type-specific override matrix from tool_config.yml."""

        core: FlextInfraModelsDepsToolSettings.ProjectTypeOverrideConfig = Field(
            description="Core overrides"
        )
        domain: FlextInfraModelsDepsToolSettings.ProjectTypeOverrideConfig = Field(
            description="Domain overrides"
        )
        platform: FlextInfraModelsDepsToolSettings.ProjectTypeOverrideConfig = Field(
            description="Platform overrides"
        )
        integration: FlextInfraModelsDepsToolSettings.ProjectTypeOverrideConfig = Field(
            description="Integration overrides"
        )
        app: FlextInfraModelsDepsToolSettings.ProjectTypeOverrideConfig = Field(
            description="App overrides"
        )

    class ToolConfigDocument(m.ArbitraryTypesModel):
        """Root schema for tool_config.yml."""

        tools: FlextInfraModelsDepsToolSettings.ToolConfigTools = Field(
            description="Tools"
        )
        project_type_overrides: FlextInfraModelsDepsToolSettings.ProjectTypeOverridesConfig = Field(
            alias="project-type-overrides",
            description="Per-project-type configuration overrides.",
        )


__all__ = ["FlextInfraModelsDepsToolSettings"]
