"""Tool configuration models for the deps subpackage.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from types import MappingProxyType
from typing import Annotated

from annotated_types import Len

from flext_cli import m
from flext_infra._models.deps_tool_config_linters import (
    FlextInfraModelsDepsToolConfigLinters,
)
from flext_infra._models.deps_tool_config_type_checkers import (
    FlextInfraModelsDepsToolConfigTypeCheckers,
)

# Local non-empty string contract (external annotated_types only; no facade).
type NonEmptyStr = Annotated[str, Len(1)]


class FlextInfraModelsDepsToolSettings(
    FlextInfraModelsDepsToolConfigLinters, FlextInfraModelsDepsToolConfigTypeCheckers
):
    """Models for tool configuration loaded from YAML."""

    class DeptryConfig(m.ArbitraryTypesModel):
        """Deptry namespace and dependency-group policy."""

        known_first_party: Annotated[
            tuple[str, ...],
            m.Field(
                alias="known-first-party",
                description="Base first-party namespaces extended by project metadata.",
            ),
        ]
        pep621_dev_dependency_groups: Annotated[
            tuple[str, ...],
            m.Field(
                alias="pep621-dev-dependency-groups",
                description="PEP 735 groups treated as development dependencies.",
            ),
        ]

    class HatchConfig(m.ArbitraryTypesModel):
        """Hatch metadata policy."""

        allow_direct_references: Annotated[
            bool,
            m.Field(
                alias="allow-direct-references",
                description="Allow direct references in project metadata.",
            ),
        ]
        packaged_data_dirs: Annotated[
            Sequence[str],
            m.Field(
                alias="packaged-data-dirs",
                default_factory=tuple,
                description=(
                    "Root data directories force-included into the wheel when "
                    "present (e.g. config, templates), so they survive install."
                ),
            ),
        ]

    class PytestConfig(m.ArbitraryTypesModel):
        """Pytest baseline settings loaded from YAML."""

        # mro-j47u (codex): every rendered pytest value is validated config data.
        min_version: Annotated[
            NonEmptyStr,
            m.Field(alias="min-version", description="Minimum pytest version."),
        ]
        python_classes: Annotated[
            tuple[str, ...],
            m.Field(
                alias="python-classes",
                description="Canonical pytest test class patterns.",
            ),
        ]
        python_files: Annotated[
            tuple[str, ...],
            m.Field(
                alias="python-files",
                description="Canonical pytest test module patterns.",
            ),
        ]
        # mro-wkii.17 (codex): collection roots are validated config, not local state.
        test_paths: Annotated[
            tuple[str, ...],
            m.Field(
                alias="test-paths",
                description="Canonical tracked roots collected by pytest.",
            ),
        ]
        filter_warnings: Annotated[
            tuple[str, ...],
            m.Field(
                alias="filter-warnings", description="Canonical pytest warning filters."
            ),
        ]

        standard_markers: Annotated[
            Sequence[str],
            m.Field(
                alias="standard-markers",
                description="Standard pytest markers enforced by modernizer.",
            ),
        ]
        standard_addopts: Annotated[
            Sequence[str],
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
            Sequence[str], m.Field(description="Top-level TOML sections ordered first.")
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

        # mro-p68a.5 (codex): production coverage is limited to declared sources.
        source: Annotated[
            Sequence[str],
            m.Field(
                default_factory=tuple,
                description="Production source roots measured by coverage.",
            ),
        ]
        fail_under: FlextInfraModelsDepsToolSettings.CoverageFailUnderConfig = m.Field(
            alias="fail-under", description="Coverage fail-under thresholds by layer."
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
        exclude_also: Annotated[
            Sequence[str],
            m.Field(
                alias="exclude-also",
                default_factory=tuple,
                description=(
                    "Coverage report line patterns excluded from runtime coverage."
                ),
            ),
        ]
        omit: Annotated[
            Sequence[str],
            m.Field(
                default_factory=tuple,
                description="Glob patterns excluded from coverage collection.",
            ),
        ]

    class VultureConfig(m.ArbitraryTypesModel):
        """Vulture production-reachability policy loaded from YAML."""

        # NOTE (multi-agent, mro-j47u): keep dead-code scope fully config-owned.
        exclude: Annotated[
            tuple[str, ...],
            m.Field(
                description="Declaration-only path patterns excluded from Vulture."
            ),
        ]
        min_confidence: Annotated[
            int,
            m.Field(
                alias="min-confidence",
                description="Minimum confidence reported as dead production code.",
            ),
        ]
        paths: Annotated[
            tuple[str, ...],
            m.Field(description="Production roots scanned for unreachable code."),
        ]
        verbose: bool = m.Field(
            description="Enable Vulture's internal scanner trace when requested."
        )

    class ToolConfigTools(m.ArbitraryTypesModel):
        """Tool map loaded from YAML."""

        codespell: FlextInfraModelsDepsToolSettings.CodespellConfig = m.Field(
            description="Codespell settings"
        )
        deptry: FlextInfraModelsDepsToolSettings.DeptryConfig = m.Field(
            description="Deptry settings"
        )
        hatch: FlextInfraModelsDepsToolSettings.HatchConfig = m.Field(
            description="Hatch metadata settings"
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
        vulture: FlextInfraModelsDepsToolSettings.VultureConfig = m.Field(
            description="Vulture production-reachability settings"
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
            Mapping[str, str],
            m.Field(description="Pyright override settings for this project type."),
        ] = m.Field(default_factory=lambda: MappingProxyType({}))

    class ProjectTypeOverridesConfig(m.ArbitraryTypesModel):
        """Project-type-specific override matrix from ``config/tooling.yaml``."""

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
            Sequence[str],
            m.Field(
                alias="root-namespace-files",
                description="Governed root facade filenames enforced by gen-init.",
            ),
        ]
        public_file_aliases: Annotated[
            Mapping[str, str],
            m.Field(
                alias="public-file-aliases",
                description="Canonical alias by governed root facade filename.",
            ),
        ]
        public_file_suffixes: Annotated[
            Mapping[str, str],
            m.Field(
                alias="public-file-suffixes",
                description="Canonical class suffix by governed root facade filename.",
            ),
        ]
        private_family_tokens: Annotated[
            Mapping[str, Sequence[str]],
            m.Field(
                alias="private-family-tokens",
                description="Accepted family markers for private namespace packages.",
            ),
        ]
        surface_prefixes: Annotated[
            Mapping[str, str],
            m.Field(
                alias="surface-prefixes",
                description=(
                    "Class prefixes by wrapper surface such as tests/examples/scripts."
                ),
            ),
        ]
        inherited_exports: Annotated[
            Mapping[str, Sequence[str]],
            m.Field(
                alias="inherited-exports",
                description=(
                    "Allowed inherited exports from parent package by root surface."
                ),
            ),
        ]
        main_export_files: Annotated[
            Sequence[str],
            m.Field(
                alias="main-export-files",
                description="Root files allowed to export module-level main().",
            ),
        ]
        side_effect_free_packages: Annotated[
            Sequence[str],
            m.Field(
                alias="side-effect-free-packages",
                description=(
                    "Package basenames whose generated initializer must not import "
                    "siblings eagerly."
                ),
            ),
        ]

    class ToolConfigDocument(m.ArbitraryTypesModel):
        """Root schema for canonical ``config/tooling.yaml`` policy data."""

        tools: FlextInfraModelsDepsToolSettings.ToolConfigTools = m.Field(
            description="Tools"
        )
        project_type_overrides: Annotated[
            FlextInfraModelsDepsToolSettings.ProjectTypeOverridesConfig,
            m.Field(
                alias="project-type-overrides",
                description="Per-project-type configuration overrides.",
            ),
        ]
        lazy_init: FlextInfraModelsDepsToolSettings.LazyInitConfig = m.Field(
            alias="lazy-init", description="Declarative lazy-init generation policy."
        )

    class ToolingScalarSetting(m.ArbitraryTypesModel):
        """One validated scalar setting rendered into an explicit TOML table."""

        name: Annotated[NonEmptyStr, m.Field(description="TOML setting name")]
        value: Annotated[
            str, m.Field(description="Validated Pyright diagnostic severity")
        ]

    class ToolingPyrightEnvironment(m.ArbitraryTypesModel):
        """One resolved Pyright execution environment."""

        root: Annotated[NonEmptyStr, m.Field(description="Environment root")]
        extra_paths: Annotated[
            tuple[str, ...], m.Field(description="Resolved environment import paths")
        ]
        settings: Annotated[
            tuple[FlextInfraModelsDepsToolSettings.ToolingScalarSetting, ...],
            m.Field(description="Resolved environment diagnostics"),
        ]

    # mro-j47u (codex): explicit runtime-only values keep the Jinja structure full.
    class ToolingRuntimeContext(m.ArbitraryTypesModel):
        """Resolved project/workspace values consumed by the complete template."""

        project_kind: Annotated[
            NonEmptyStr, m.Field(description="Resolved project classification")
        ]
        coverage_fail_under: Annotated[
            int, m.Field(ge=0, le=100, description="Resolved coverage threshold")
        ]
        first_party: Annotated[
            tuple[str, ...], m.Field(description="Resolved first-party namespaces")
        ]
        mypy_path: Annotated[
            tuple[str, ...], m.Field(description="Resolved Mypy search paths")
        ]
        pyrefly_interpreter_path: Annotated[
            NonEmptyStr, m.Field(description="Resolved Pyrefly interpreter")
        ]
        pyrefly_search_path: Annotated[
            tuple[str, ...], m.Field(description="Resolved Pyrefly search paths")
        ]
        pyrefly_project_includes: Annotated[
            tuple[str, ...], m.Field(description="Resolved Pyrefly production includes")
        ]
        pyright_exclude: Annotated[
            tuple[str, ...], m.Field(description="Resolved Pyright exclusions")
        ]
        pyright_ignore: Annotated[
            tuple[str, ...], m.Field(description="Resolved Pyright ignored paths")
        ] = ()
        pyright_include: Annotated[
            tuple[str, ...], m.Field(description="Resolved Pyright production roots")
        ]
        pyright_extra_paths: Annotated[
            tuple[str, ...], m.Field(description="Resolved Pyright import paths")
        ]
        pyright_venv: Annotated[
            NonEmptyStr,
            m.Field(description="Resolved Pyright virtual environment name"),
        ]
        pyright_venv_path: Annotated[
            NonEmptyStr,
            m.Field(description="Resolved Pyright virtual environment base"),
        ]
        pyright_settings: Annotated[
            tuple[FlextInfraModelsDepsToolSettings.ToolingScalarSetting, ...],
            m.Field(description="Resolved Pyright scalar settings"),
        ]
        pyright_execution_environments: Annotated[
            tuple[FlextInfraModelsDepsToolSettings.ToolingPyrightEnvironment, ...],
            m.Field(description="Resolved Pyright environments"),
        ]
        ruff_src: Annotated[
            tuple[str, ...], m.Field(description="Resolved Ruff source roots")
        ]
        ruff_ignore: Annotated[
            tuple[str, ...],
            m.Field(description="Resolved ordinary and justified Ruff ignores"),
        ]


__all__: list[str] = ["FlextInfraModelsDepsToolSettings"]
