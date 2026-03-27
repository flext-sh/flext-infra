"""Domain models for the deps subpackage."""

from __future__ import annotations

from collections.abc import Mapping, MutableSequence
from typing import Annotated

from flext_core import m
from pydantic import Field

from flext_infra import t


class FlextInfraDepsModels:
    """Models for dependency detection and modernization reporting."""

    class RuffFormatConfig(m.ArbitraryTypesModel):
        """Ruff format settings loaded from YAML."""

        docstring_code_format: Annotated[
            bool,
            Field(
                alias="docstring-code-format",
                description="Enable ruff docstring code block formatting.",
            ),
        ]
        indent_style: Annotated[
            str,
            Field(
                alias="indent-style",
                description="Indent style for ruff formatter output.",
            ),
        ]
        line_ending: Annotated[
            str,
            Field(
                alias="line-ending",
                description="Line ending style for ruff formatter output.",
            ),
        ]
        quote_style: Annotated[
            str,
            Field(
                alias="quote-style",
                description="Quote style for ruff formatter output.",
            ),
        ]

    class RuffIsortConfig(m.ArbitraryTypesModel):
        """Ruff isort settings loaded from YAML."""

        combine_as_imports: Annotated[
            bool,
            Field(
                alias="combine-as-imports",
                description="Combine `as` imports in grouped isort blocks.",
            ),
        ]
        force_single_line: Annotated[
            bool,
            Field(
                alias="force-single-line",
                description="Force single-line imports in isort output.",
            ),
        ]
        split_on_trailing_comma: Annotated[
            bool,
            Field(
                alias="split-on-trailing-comma",
                description="Split imports when a trailing comma exists.",
            ),
        ]

    class RuffLintConfig(m.ArbitraryTypesModel):
        """Ruff lint settings loaded from YAML."""

        select: Annotated[
            t.StrSequence,
            Field(
                description="Ruff lint rule selectors.",
            ),
        ] = Field(default_factory=list)
        ignore: Annotated[
            t.StrSequence,
            Field(
                description="Ruff lint rule ignore list.",
            ),
        ] = Field(default_factory=list)
        isort: FlextInfraDepsModels.RuffIsortConfig
        per_file_ignores: Annotated[
            Mapping[str, t.StrSequence],
            Field(
                alias="per-file-ignores",
                description="Per-file ignore mapping from glob pattern to ruff rule IDs.",
            ),
        ]

    class RuffConfig(m.ArbitraryTypesModel):
        """Ruff top-level settings loaded from YAML."""

        exclude: Annotated[
            t.StrSequence,
            Field(
                description="Directory/file globs excluded from ruff checks.",
            ),
        ] = Field(default_factory=list)
        fix: Annotated[bool, Field(description="Enable automatic ruff fixes")]
        line_length: Annotated[
            int,
            Field(alias="line-length", description="Maximum line length."),
        ]
        preview: Annotated[bool, Field(description="Enable preview ruff behavior.")]
        respect_gitignore: Annotated[
            bool,
            Field(
                alias="respect-gitignore",
                description="Respect .gitignore exclusions.",
            ),
        ]
        show_fixes: Annotated[
            bool,
            Field(
                alias="show-fixes",
                description="Display fixed violations in ruff output.",
            ),
        ]
        src: Annotated[
            t.StrSequence,
            Field(
                description="Source roots used by ruff import analysis.",
            ),
        ] = Field(default_factory=list)
        target_version: Annotated[
            str,
            Field(
                alias="target-version",
                description="Python target version for ruff.",
            ),
        ]
        format: FlextInfraDepsModels.RuffFormatConfig
        lint: FlextInfraDepsModels.RuffLintConfig

    class MypyConfig(m.ArbitraryTypesModel):
        """Mypy baseline settings loaded from YAML."""

        plugins: Annotated[
            t.StrSequence,
            Field(
                description="Mypy plugins list.",
            ),
        ] = Field(default_factory=list)
        disabled_error_codes: Annotated[
            t.StrSequence,
            Field(
                alias="disabled-error-codes",
                description="Mypy error codes disabled by default.",
            ),
        ]
        boolean_settings: Annotated[
            Mapping[str, bool],
            Field(
                alias="boolean-settings",
                description="Mypy boolean settings keyed by option name.",
            ),
        ]

    class PydanticMypyConfig(m.ArbitraryTypesModel):
        """Pydantic mypy plugin settings loaded from YAML."""

        init_forbid_extra: Annotated[
            bool,
            Field(
                description="Enable forbid-extra init behavior in pydantic mypy plugin.",
            ),
        ]
        init_typed: Annotated[
            bool,
            Field(
                description="Enable typed __init__ signatures in pydantic mypy plugin.",
            ),
        ]
        warn_required_dynamic_aliases: Annotated[
            bool,
            Field(
                description="Warn on required dynamic aliases in pydantic mypy plugin.",
            ),
        ]

    class PyrightConfig(m.ArbitraryTypesModel):
        """Pyright strict settings loaded from YAML."""

        class PathRulesConfig(m.ArbitraryTypesModel):
            """Path resolution rules loaded from YAML."""

            source_dir: Annotated[
                str,
                Field(
                    alias="source-dir",
                    description="Primary source directory name.",
                ),
            ]
            project_root: Annotated[
                str,
                Field(
                    alias="project-root",
                    description="Project root path entry used in path resolution.",
                ),
            ]
            env_dirs: Annotated[
                t.StrSequence,
                Field(
                    alias="env-dirs",
                    description="Canonical execution environment directories in order.",
                ),
            ]
            test_like_dirs: Annotated[
                t.StrSequence,
                Field(
                    alias="test-like-dirs",
                    description="Env dirs that should include project root in extraPaths.",
                ),
            ]
            default_excludes: Annotated[
                t.StrSequence,
                Field(
                    alias="default-excludes",
                    description="Always-applied pyright exclude globs.",
                ),
            ]
            dynamic_exclude_dirs: Annotated[
                t.StrSequence,
                Field(
                    alias="dynamic-exclude-dirs",
                    description="Directory names excluded only when present in project.",
                ),
            ]
            root_typings_paths: Annotated[
                t.StrSequence,
                Field(
                    alias="root-typings-paths",
                    description="Typings paths used in workspace-root config.",
                ),
            ]
            project_typings_paths: Annotated[
                t.StrSequence,
                Field(
                    alias="project-typings-paths",
                    description="Typings paths used in subproject configs.",
                ),
            ]
            ignored_diagnostic_globs: Annotated[
                t.StrSequence,
                Field(
                    alias="ignored-diagnostic-globs",
                    description="Pyright ignore globs for files that remain on search paths but must not emit diagnostics.",
                ),
            ]
            source_report_private_usage: Annotated[
                str,
                Field(
                    alias="source-report-private-usage",
                    description="reportPrivateUsage value for source-dir execution envs.",
                ),
            ]
            test_like_report_private_usage: Annotated[
                str,
                Field(
                    alias="test-like-report-private-usage",
                    description="reportPrivateUsage value for test-like execution envs.",
                ),
            ]
            other_report_private_usage: Annotated[
                str,
                Field(
                    alias="other-report-private-usage",
                    description="reportPrivateUsage value for non-source/non-test-like envs.",
                ),
            ]
            root_venv_path: Annotated[
                str,
                Field(
                    alias="root-venv-path",
                    description="venvPath to use in workspace-root pyright config.",
                ),
            ]
            project_venv_path: Annotated[
                str,
                Field(
                    alias="project-venv-path",
                    description="venvPath to use in subproject pyright config.",
                ),
            ]
            venv_name: Annotated[
                str,
                Field(
                    alias="venv-name",
                    description="Virtualenv directory name shared across pyright configs.",
                ),
            ]

        strict_settings: Annotated[
            t.StrMapping,
            Field(
                alias="strict-settings",
                description="Pyright strict baseline options.",
            ),
        ]
        extended_settings: Annotated[
            t.StrMapping,
            Field(
                alias="extended-settings",
                description="Pyright extended settings options.",
            ),
        ] = Field(default_factory=dict)
        path_rules: Annotated[
            PathRulesConfig,
            Field(
                alias="path-rules",
                description="Pyright path resolution and execution-env rules.",
            ),
        ]

    class PyreflyConfig(m.ArbitraryTypesModel):
        """Pyrefly strict settings loaded from YAML."""

        class PathRulesConfig(m.ArbitraryTypesModel):
            """Path resolution rules loaded from YAML."""

            source_dir: Annotated[
                str,
                Field(
                    alias="source-dir",
                    description="Primary source directory name.",
                ),
            ]
            project_root: Annotated[
                str,
                Field(
                    alias="project-root",
                    description="Project root path entry used in search-path.",
                ),
            ]
            root_typings_paths: Annotated[
                t.StrSequence,
                Field(
                    alias="root-typings-paths",
                    description="Typings paths used in workspace-root config.",
                ),
            ]
            project_typings_paths: Annotated[
                t.StrSequence,
                Field(
                    alias="project-typings-paths",
                    description="Typings paths used in subproject configs.",
                ),
            ]
            env_dirs: Annotated[
                t.StrSequence,
                Field(
                    alias="env-dirs",
                    description="Canonical directories used to build project-includes.",
                ),
            ]
            workspace_include_children: Annotated[
                bool,
                Field(
                    alias="workspace-include-children",
                    description="Whether root pyrefly should include child projects.",
                ),
            ]
            workspace_include_child_env_dirs: Annotated[
                t.StrSequence,
                Field(
                    alias="workspace-include-child-env-dirs",
                    description="Child env dirs included by root pyrefly when enabled.",
                ),
            ]
            include_path_dependencies_in_search_path: Annotated[
                bool,
                Field(
                    alias="include-path-dependencies-in-search-path",
                    description="Include resolved path dependencies in pyrefly search-path.",
                ),
            ]
            project_shared_search_paths: Annotated[
                t.StrSequence,
                Field(
                    alias="project-shared-search-paths",
                    description="Additional shared workspace paths for subproject pyrefly search-path.",
                ),
            ]

        python_version: Annotated[
            str,
            Field(
                alias="python-version",
                description="Pyrefly python-version baseline.",
            ),
        ]
        ignore_errors_in_generated_code: Annotated[
            bool,
            Field(
                alias="ignore-errors-in-generated-code",
                description="Enable ignoring errors in generated code.",
            ),
        ]
        disable_project_excludes_heuristics: Annotated[
            bool,
            Field(
                alias="disable-project-excludes-heuristics",
                description="Disable implicit project-exclude heuristics in pyrefly.",
            ),
        ]
        use_ignore_files: Annotated[
            bool,
            Field(
                alias="use-ignore-files",
                description="Whether pyrefly should apply .gitignore/.ignore files.",
            ),
        ]
        strict_errors: Annotated[
            t.StrSequence,
            Field(
                alias="strict-errors",
                description="Pyrefly errors enabled as strict defaults.",
            ),
        ]
        disabled_errors: Annotated[
            t.StrSequence,
            Field(
                alias="disabled-errors",
                description="Pyrefly errors disabled by default.",
            ),
        ]
        project_exclude_globs: Annotated[
            t.StrSequence,
            Field(
                alias="project-exclude-globs",
                description="Globs excluded from pyrefly project checking.",
            ),
        ]
        path_rules: Annotated[
            PathRulesConfig,
            Field(
                alias="path-rules",
                description="Pyrefly search-path rules.",
            ),
        ]

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
            t.StrSequence,
            Field(
                description="Top-level TOML sections ordered first.",
            ),
        ]

    class YamlfixConfig(m.ArbitraryTypesModel):
        """yamlfix baseline settings loaded from YAML."""

        line_length: Annotated[int, Field(description="Maximum YAML line length.")]
        preserve_quotes: Annotated[
            bool,
            Field(description="Preserve quote style in YAML output."),
        ]
        whitelines: Annotated[
            int,
            Field(description="Blank line count between YAML entries."),
        ]
        section_whitelines: Annotated[
            int,
            Field(
                description="Blank line count between YAML sections.",
            ),
        ]
        explicit_start: Annotated[
            bool,
            Field(description="Emit explicit YAML start marker."),
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
                description="Minimum coverage percentage required for platform layer.",
            ),
        ]
        integration: Annotated[
            int,
            Field(
                description="Minimum coverage percentage required for integration layer.",
            ),
        ]
        app: Annotated[
            int,
            Field(description="Minimum coverage percentage required for app layer."),
        ]

    class CoverageConfig(m.ArbitraryTypesModel):
        """Coverage baseline settings loaded from YAML."""

        fail_under: Annotated[
            FlextInfraDepsModels.CoverageFailUnderConfig,
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
            Field(
                default=2,
                description="Decimal precision for coverage percentages.",
            ),
        ]

    class ToolConfigTools(m.ArbitraryTypesModel):
        """Tool map loaded from YAML."""

        ruff: FlextInfraDepsModels.RuffConfig
        mypy: FlextInfraDepsModels.MypyConfig
        pydantic_mypy: Annotated[
            FlextInfraDepsModels.PydanticMypyConfig,
            Field(
                alias="pydantic-mypy",
                description="Pydantic mypy plugin configuration.",
            ),
        ]
        pyright: FlextInfraDepsModels.PyrightConfig
        pyrefly: FlextInfraDepsModels.PyreflyConfig
        pytest: FlextInfraDepsModels.PytestConfig
        tomlsort: FlextInfraDepsModels.TomlsortConfig
        yamlfix: FlextInfraDepsModels.YamlfixConfig
        coverage: Annotated[
            FlextInfraDepsModels.CoverageConfig,
            Field(
                description="Coverage configuration with per-project-type thresholds.",
            ),
        ]

    class ProjectTypeOverrideConfig(m.ArbitraryTypesModel):
        """Per-project-type override settings."""

        pyright: Annotated[
            t.StrMapping,
            Field(
                description="Pyright override settings for this project type.",
            ),
        ] = Field(default_factory=dict)

    class ProjectTypeOverridesConfig(m.ArbitraryTypesModel):
        """Project-type-specific override matrix from tool_config.yml."""

        core: Annotated[
            FlextInfraDepsModels.ProjectTypeOverrideConfig,
            Field(),
        ]
        domain: Annotated[
            FlextInfraDepsModels.ProjectTypeOverrideConfig,
            Field(),
        ]
        platform: Annotated[
            FlextInfraDepsModels.ProjectTypeOverrideConfig,
            Field(),
        ]
        integration: Annotated[
            FlextInfraDepsModels.ProjectTypeOverrideConfig,
            Field(),
        ]
        app: Annotated[
            FlextInfraDepsModels.ProjectTypeOverrideConfig,
            Field(),
        ]

    class DependencyLimitsInfo(m.ArbitraryTypesModel):
        """Dependency limits configuration metadata."""

        python_version: str | None = None
        limits_path: Annotated[str, Field(default="")]

    class PipCheckReport(m.ArbitraryTypesModel):
        """Pip check execution report with status and output lines."""

        ok: bool = True
        lines: t.StrSequence = Field(default_factory=list)

    class ToolConfigDocument(m.ArbitraryTypesModel):
        """Root schema for tool_config.yml."""

        tools: FlextInfraDepsModels.ToolConfigTools
        project_type_overrides: Annotated[
            FlextInfraDepsModels.ProjectTypeOverridesConfig,
            Field(
                alias="project-type-overrides",
                description="Per-project-type configuration overrides.",
            ),
        ]

    class DeptryIssueGroups(m.ArbitraryTypesModel):
        """Deptry issue grouping model by error code (DEP001-DEP004)."""

        dep001: Annotated[
            MutableSequence[Mapping[str, t.Primitives | None]],
            Field(
                description="DEP001 issues",
            ),
        ] = Field(default_factory=lambda: list[Mapping[str, t.Primitives | None]]())
        dep002: Annotated[
            MutableSequence[Mapping[str, t.Primitives | None]],
            Field(
                description="DEP002 issues",
            ),
        ] = Field(default_factory=lambda: list[Mapping[str, t.Primitives | None]]())
        dep003: Annotated[
            MutableSequence[Mapping[str, t.Primitives | None]],
            Field(
                description="DEP003 issues",
            ),
        ] = Field(default_factory=lambda: list[Mapping[str, t.Primitives | None]]())
        dep004: Annotated[
            MutableSequence[Mapping[str, t.Primitives | None]],
            Field(
                description="DEP004 issues",
            ),
        ] = Field(default_factory=lambda: list[Mapping[str, t.Primitives | None]]())

    class DeptryReport(m.ArbitraryTypesModel):
        """Deptry analysis report with categorized issue modules."""

        missing: t.StrSequence = Field(default_factory=list)
        unused: t.StrSequence = Field(default_factory=list)
        transitive: t.StrSequence = Field(default_factory=list)
        dev_in_runtime: t.StrSequence = Field(default_factory=list)
        raw_count: Annotated[t.NonNegativeInt, Field(default=0)]

    class ProjectDependencyReport(m.ArbitraryTypesModel):
        """Project-level dependency report combining deptry results."""

        project: Annotated[t.NonEmptyStr, Field()]
        deptry: FlextInfraDepsModels.DeptryReport

    class TypingsReport(m.ArbitraryTypesModel):
        """Typing stubs analysis report with required/current/delta packages."""

        required_packages: t.StrSequence = Field(default_factory=list)
        hinted: t.StrSequence = Field(default_factory=list)
        missing_modules: t.StrSequence = Field(default_factory=list)
        current: t.StrSequence = Field(default_factory=list)
        to_add: t.StrSequence = Field(default_factory=list)
        to_remove: t.StrSequence = Field(default_factory=list)
        limits_applied: bool = False
        python_version: str | None = None

    class ProjectRuntimeReport(m.ArbitraryTypesModel):
        """Project runtime dependency and typings report."""

        deptry: FlextInfraDepsModels.DeptryReport
        typings: FlextInfraDepsModels.TypingsReport | None = None

    class WorkspaceDependencyReport(m.ArbitraryTypesModel):
        """Workspace-level dependency analysis report aggregating all projects."""

        workspace: str
        projects: Annotated[
            Mapping[str, FlextInfraDepsModels.ProjectRuntimeReport],
            Field(description="Per-project reports"),
        ] = Field(default_factory=dict)
        pip_check: FlextInfraDepsModels.PipCheckReport | None = None
        dependency_limits: FlextInfraDepsModels.DependencyLimitsInfo | None = None


__all__ = ["FlextInfraDepsModels"]
