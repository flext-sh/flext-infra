"""Tool configuration models for the deps subpackage."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Annotated

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
            m.Field(
                alias="standard-markers",
                description="Standard pytest markers enforced by modernizer.",
            ),
        ]
        standard_addopts: Annotated[
            t.StrSequence,
            m.Field(
                alias="standard-addopts",
                description="Standard pytest addopts enforced by modernizer.",
            ),
        ]

    class TomlsortConfig(m.ArbitraryTypesModel):
        """tomlsort baseline settings loaded from YAML."""

        all: Annotated[bool, m.Field(description="Sort all TOML tables and entries.")]
        in_place: Annotated[bool, m.Field(description="Apply TOML sorting in place.")]
        sort_first: Annotated[
            t.StrSequence, m.Field(description="Top-level TOML sections ordered first.")
        ]

    class YamlfixConfig(m.ArbitraryTypesModel):
        """yamlfix baseline settings loaded from YAML."""

        line_length: Annotated[int, m.Field(description="Maximum YAML line length.")]
        preserve_quotes: Annotated[
            bool, m.Field(description="Preserve quote style in YAML output.")
        ]
        whitelines: Annotated[
            int, m.Field(description="Blank line count between YAML entries.")
        ]
        section_whitelines: Annotated[
            int, m.Field(description="Blank line count between YAML sections.")
        ]
        explicit_start: Annotated[
            bool, m.Field(description="Emit explicit YAML start marker.")
        ]

    class CoverageFailUnderConfig(m.ArbitraryTypesModel):
        """Coverage fail-under thresholds by layer."""

        core: int = m.Field(
            description="Minimum coverage percentage required for core layer."
        )
        domain: int = m.Field(
            description="Minimum coverage percentage required for domain layer."
        )
        platform: int = m.Field(
            description="Minimum coverage percentage required for platform layer."
        )
        integration: int = m.Field(
            description="Minimum coverage percentage required for integration layer."
        )
        app: int = m.Field(
            description="Minimum coverage percentage required for app layer."
        )

    class CoverageConfig(m.ArbitraryTypesModel):
        """Coverage baseline settings loaded from YAML."""

        fail_under: FlextInfraModelsDepsToolSettings.CoverageFailUnderConfig = m.Field(
            alias="fail-under",
            description="Coverage fail-under thresholds by layer.",
        )
        show_missing: Annotated[
            bool,
            m.Field(
                alias="show-missing",
                description="Display missing lines in coverage report.",
            ),
        ] = True
        skip_covered: Annotated[
            bool,
            m.Field(
                alias="skip-covered",
                description="Skip covered files in coverage report.",
            ),
        ] = False
        precision: Annotated[
            int, m.Field(description="Decimal precision for coverage percentages.")
        ] = 2
        omit: Annotated[
            t.StrSequence,
            m.Field(default_factory=list, description="Coverage run omit globs."),
        ]

    class ToolConfigTools(m.ArbitraryTypesModel):
        """Tool map loaded from YAML."""

        codespell: FlextInfraModelsDepsToolSettings.CodespellConfig = m.Field(
            description="Codespell settings"
        )
        ruff: FlextInfraModelsDepsToolSettings.RuffConfig = m.Field(
            description="Ruff settings"
        )
        mypy: FlextInfraModelsDepsToolSettings.MypyConfig = m.Field(
            description="Mypy settings"
        )
        pydantic_mypy: FlextInfraModelsDepsToolSettings.PydanticMypyConfig = m.Field(
            alias="pydantic-mypy", description="Pydantic mypy plugin configuration."
        )
        pyright: FlextInfraModelsDepsToolSettings.PyrightConfig = m.Field(
            description="Pyright settings"
        )
        pyrefly: FlextInfraModelsDepsToolSettings.PyreflyConfig = m.Field(
            description="Pyrefly settings"
        )
        pytest: FlextInfraModelsDepsToolSettings.PytestConfig = m.Field(
            description="Pytest settings"
        )
        tomlsort: FlextInfraModelsDepsToolSettings.TomlsortConfig = m.Field(
            description="Tomlsort settings"
        )
        yamlfix: FlextInfraModelsDepsToolSettings.YamlfixConfig = m.Field(
            description="Yamlfix settings"
        )
        coverage: FlextInfraModelsDepsToolSettings.CoverageConfig = m.Field(
            description="Coverage configuration with per-project-type thresholds."
        )

    class ProjectTypeOverrideConfig(m.ArbitraryTypesModel):
        """Per-project-type override settings."""

        pyright: Annotated[
            t.StrMapping,
            m.Field(description="Pyright override settings for this project type."),
        ] = m.Field(default_factory=dict)

    class ProjectTypeOverridesConfig(m.ArbitraryTypesModel):
        """Project-type-specific override matrix from tool_config.yml."""

        core: FlextInfraModelsDepsToolSettings.ProjectTypeOverrideConfig = m.Field(
            description="Core overrides"
        )
        domain: FlextInfraModelsDepsToolSettings.ProjectTypeOverrideConfig = m.Field(
            description="Domain overrides"
        )
        platform: FlextInfraModelsDepsToolSettings.ProjectTypeOverrideConfig = m.Field(
            description="Platform overrides"
        )
        integration: FlextInfraModelsDepsToolSettings.ProjectTypeOverrideConfig = (
            m.Field(description="Integration overrides")
        )
        app: FlextInfraModelsDepsToolSettings.ProjectTypeOverrideConfig = m.Field(
            description="App overrides"
        )

    class LazyInitConfig(m.ArbitraryTypesModel):
        """Declarative policy for ``__init__.py`` lazy export generation."""

        root_namespace_files: Annotated[
            t.StrSequence,
            m.Field(
                alias="root-namespace-files",
                description="Governed root facade filenames enforced by gen-init.",
            ),
        ]
        public_file_aliases: Annotated[
            t.StrMapping,
            m.Field(
                alias="public-file-aliases",
                description="Canonical alias by governed root facade filename.",
            ),
        ]
        public_file_suffixes: Annotated[
            t.StrMapping,
            m.Field(
                alias="public-file-suffixes",
                description="Canonical class suffix by governed root facade filename.",
            ),
        ]
        private_family_tokens: Annotated[
            Mapping[str, t.StrSequence],
            m.Field(
                alias="private-family-tokens",
                description="Accepted family markers for private namespace packages.",
            ),
        ]
        surface_prefixes: Annotated[
            t.StrMapping,
            m.Field(
                alias="surface-prefixes",
                description="Class prefixes by wrapper surface such as tests/examples/scripts.",
            ),
        ]
        inherited_exports: Annotated[
            Mapping[str, t.StrSequence],
            m.Field(
                alias="inherited-exports",
                description="Allowed inherited exports from parent package by root surface.",
            ),
        ]
        main_export_files: Annotated[
            t.StrSequence,
            m.Field(
                alias="main-export-files",
                description="Root files allowed to export module-level main().",
            ),
        ]

    class ToolConfigDocument(m.ArbitraryTypesModel):
        """Root schema for tool_config.yml."""

        tools: FlextInfraModelsDepsToolSettings.ToolConfigTools = m.Field(
            description="Tools"
        )
        project_type_overrides: FlextInfraModelsDepsToolSettings.ProjectTypeOverridesConfig = m.Field(
            alias="project-type-overrides",
            description="Per-project-type configuration overrides.",
        )
        lazy_init: FlextInfraModelsDepsToolSettings.LazyInitConfig = m.Field(
            alias="lazy-init",
            description="Declarative lazy-init generation policy.",
        )


__all__: list[str] = ["FlextInfraModelsDepsToolSettings"]
