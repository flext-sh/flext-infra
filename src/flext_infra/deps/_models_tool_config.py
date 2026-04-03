"""Tool configuration models for the deps subpackage."""

from __future__ import annotations

from typing import Annotated

from pydantic import Field

from flext_core import m
from flext_infra import t
from flext_infra.deps._models_tool_config_linters import (
    MypyConfig,
    MypyOverrideConfig,
    PydanticMypyConfig,
    RuffConfig,
    RuffFormatConfig,
    RuffIsortConfig,
    RuffLintConfig,
)
from flext_infra.deps._models_tool_config_type_checkers import (
    PyreflyConfig,
    PyrightConfig,
)


class FlextInfraDepsModelsToolConfig:
    """Models for tool configuration loaded from YAML."""

    # -- Ruff / Mypy (from _models_tool_config_linters) --
    RuffFormatConfig = RuffFormatConfig
    RuffIsortConfig = RuffIsortConfig
    RuffLintConfig = RuffLintConfig
    RuffConfig = RuffConfig
    MypyOverrideConfig = MypyOverrideConfig
    MypyConfig = MypyConfig
    PydanticMypyConfig = PydanticMypyConfig

    # -- Pyright / Pyrefly (from _models_tool_config_type_checkers) --
    PyrightConfig = PyrightConfig
    PyreflyConfig = PyreflyConfig

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

        core: Annotated[
            int,
            Field(description="Minimum coverage percentage required for core layer."),
        ]
        domain: Annotated[
            int,
            Field(description="Minimum coverage percentage required for domain layer."),
        ]
        platform: Annotated[
            int,
            Field(
                description="Minimum coverage percentage required for platform layer."
            ),
        ]
        integration: Annotated[
            int,
            Field(
                description="Minimum coverage percentage required for integration layer."
            ),
        ]
        app: Annotated[
            int,
            Field(description="Minimum coverage percentage required for app layer."),
        ]

    class CoverageConfig(m.ArbitraryTypesModel):
        """Coverage baseline settings loaded from YAML."""

        fail_under: Annotated[
            FlextInfraDepsModelsToolConfig.CoverageFailUnderConfig,
            Field(
                alias="fail-under",
                description="Coverage fail-under thresholds by layer.",
            ),
        ]
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

        ruff: FlextInfraDepsModelsToolConfig.RuffConfig
        mypy: FlextInfraDepsModelsToolConfig.MypyConfig
        pydantic_mypy: Annotated[
            FlextInfraDepsModelsToolConfig.PydanticMypyConfig,
            Field(
                alias="pydantic-mypy", description="Pydantic mypy plugin configuration."
            ),
        ]
        pyright: FlextInfraDepsModelsToolConfig.PyrightConfig
        pyrefly: FlextInfraDepsModelsToolConfig.PyreflyConfig
        pytest: FlextInfraDepsModelsToolConfig.PytestConfig
        tomlsort: FlextInfraDepsModelsToolConfig.TomlsortConfig
        yamlfix: FlextInfraDepsModelsToolConfig.YamlfixConfig
        coverage: Annotated[
            FlextInfraDepsModelsToolConfig.CoverageConfig,
            Field(
                description="Coverage configuration with per-project-type thresholds."
            ),
        ]

    class ProjectTypeOverrideConfig(m.ArbitraryTypesModel):
        """Per-project-type override settings."""

        pyright: Annotated[
            t.StrMapping,
            Field(description="Pyright override settings for this project type."),
        ] = Field(default_factory=dict)

    class ProjectTypeOverridesConfig(m.ArbitraryTypesModel):
        """Project-type-specific override matrix from tool_config.yml."""

        core: Annotated[
            FlextInfraDepsModelsToolConfig.ProjectTypeOverrideConfig, Field()
        ]
        domain: Annotated[
            FlextInfraDepsModelsToolConfig.ProjectTypeOverrideConfig, Field()
        ]
        platform: Annotated[
            FlextInfraDepsModelsToolConfig.ProjectTypeOverrideConfig, Field()
        ]
        integration: Annotated[
            FlextInfraDepsModelsToolConfig.ProjectTypeOverrideConfig, Field()
        ]
        app: Annotated[
            FlextInfraDepsModelsToolConfig.ProjectTypeOverrideConfig, Field()
        ]

    class ToolConfigDocument(m.ArbitraryTypesModel):
        """Root schema for tool_config.yml."""

        tools: FlextInfraDepsModelsToolConfig.ToolConfigTools
        project_type_overrides: Annotated[
            FlextInfraDepsModelsToolConfig.ProjectTypeOverridesConfig,
            Field(
                alias="project-type-overrides",
                description="Per-project-type configuration overrides.",
            ),
        ]


__all__ = ["FlextInfraDepsModelsToolConfig"]
