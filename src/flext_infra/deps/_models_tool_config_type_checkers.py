"""Pyright and Pyrefly tool configuration models for the deps subpackage."""

from __future__ import annotations

from typing import Annotated

from pydantic import ConfigDict, Field

from flext_core import m
from flext_infra import c, t


class PyrightConfig(m.ArbitraryTypesModel):
    """Pyright strict settings loaded from YAML."""

    class ExecutionEnvironment(m.FrozenStrictModel):
        """Pyright execution environment entry."""

        model_config = ConfigDict(populate_by_name=True)

        root: Annotated[str, Field(description="Execution environment root path.")]
        report_private_usage: Annotated[
            str,
            Field(
                alias=c.Infra.REPORT_PRIVATE_USAGE,
                description="reportPrivateUsage override for this environment.",
            ),
        ]
        extra_paths: Annotated[
            t.StrSequence,
            Field(
                alias=c.Infra.EXTRA_PATHS,
                description="extraPaths applied to this execution environment.",
            ),
        ]

    class PathRulesConfig(m.ArbitraryTypesModel):
        """Path resolution rules loaded from YAML."""

        source_dir: Annotated[
            str,
            Field(alias="source-dir", description="Primary source directory name."),
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
        Field(alias="strict-settings", description="Pyright strict baseline options."),
    ]
    extended_settings: Annotated[
        t.StrMapping,
        Field(
            alias="extended-settings",
            description="Pyright extended settings options.",
        ),
    ] = Field(default_factory=dict)
    lazy_import_suppressions: Annotated[
        t.StrMapping,
        Field(
            alias="lazy-import-suppressions",
            description="Pyright rules suppressed in ALL envs due to lazy import pattern.",
        ),
    ] = Field(default_factory=dict)
    source_env_suppressions: Annotated[
        t.StrMapping,
        Field(
            alias="source-env-suppressions",
            description="Additional pyright rules suppressed in source env only.",
        ),
    ] = Field(default_factory=dict)
    test_like_env_suppressions: Annotated[
        t.StrMapping,
        Field(
            alias="test-like-env-suppressions",
            description="Additional pyright rules suppressed in test-like envs.",
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
            Field(alias="source-dir", description="Primary source directory name."),
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
        Field(alias="python-version", description="Pyrefly python-version baseline."),
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
        Field(alias="path-rules", description="Pyrefly search-path rules."),
    ]


__all__ = [
    "PyreflyConfig",
    "PyrightConfig",
]
