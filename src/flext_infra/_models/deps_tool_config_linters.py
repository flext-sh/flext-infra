"""Ruff and Mypy tool configuration models for the deps subpackage."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Annotated

from pydantic import Field

from flext_core import m
from flext_infra import t


class FlextInfraDepsModelsToolConfigLinters:
    """Linters tool configuration models."""

    class CodespellConfig(m.ArbitraryTypesModel):
        """Codespell settings loaded from YAML."""

        check_filenames: Annotated[
            bool,
            Field(
                alias="check-filenames",
                description="Check filenames in addition to file contents.",
            ),
        ]
        ignore_words_list: Annotated[
            str,
            Field(
                alias="ignore-words-list",
                description="Comma-separated allowlist for known project terms.",
            ),
        ] = ""

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
            Field(description="Ruff lint rule selectors."),
        ] = Field(default_factory=list)
        ignore: Annotated[
            t.StrSequence,
            Field(description="Ruff lint rule ignore list."),
        ] = Field(default_factory=list)
        isort: FlextInfraDepsModelsToolConfigLinters.RuffIsortConfig = Field(
            description="Ruff isort configuration"
        )
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
            Field(description="Directory/file globs excluded from ruff checks."),
        ] = Field(default_factory=list)
        fix: Annotated[bool, Field(description="Enable automatic ruff fixes")]
        line_length: Annotated[
            int, Field(alias="line-length", description="Maximum line length.")
        ]
        preview: Annotated[bool, Field(description="Enable preview ruff behavior.")]
        respect_gitignore: Annotated[
            bool,
            Field(
                alias="respect-gitignore", description="Respect .gitignore exclusions."
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
            Field(description="Source roots used by ruff import analysis."),
        ] = Field(default_factory=list)
        target_version: Annotated[
            str,
            Field(
                alias="target-version", description="Python target version for ruff."
            ),
        ]
        format: FlextInfraDepsModelsToolConfigLinters.RuffFormatConfig = Field(
            description="Ruff format configuration"
        )
        lint: FlextInfraDepsModelsToolConfigLinters.RuffLintConfig = Field(
            description="Ruff lint configuration"
        )

    class MypyOverrideConfig(m.ArbitraryTypesModel):
        """Single [[tool.mypy.overrides]] entry."""

        modules: Annotated[
            t.StrSequence, Field(description="Module patterns for this override.")
        ]
        disable_error_codes: Annotated[
            t.StrSequence,
            Field(
                alias="disable-error-codes",
                description="Error codes disabled for these modules.",
            ),
        ]

    class MypyConfig(m.ArbitraryTypesModel):
        """Mypy baseline settings loaded from YAML."""

        plugins: Annotated[t.StrSequence, Field(description="Mypy plugins list.")] = (
            Field(default_factory=list)
        )
        disabled_error_codes: Annotated[
            t.StrSequence,
            Field(
                alias="disabled-error-codes",
                description="Mypy error codes disabled by default.",
            ),
        ]
        boolean_settings: Annotated[
            t.BoolMapping,
            Field(
                alias="boolean-settings",
                description="Mypy boolean settings keyed by option name.",
            ),
        ]
        overrides: Annotated[
            tuple[FlextInfraDepsModelsToolConfigLinters.MypyOverrideConfig, ...],
            Field(
                description="Per-module mypy overrides for auto-generated files and PEP 695 generics."
            ),
        ] = Field(
            default_factory=tuple,
            description="Per-module mypy overrides for auto-generated files and PEP 695 generics.",
        )

    class PydanticMypyConfig(m.ArbitraryTypesModel):
        """Pydantic mypy plugin settings loaded from YAML."""

        init_forbid_extra: Annotated[
            bool,
            Field(
                description="Enable forbid-extra init behavior in pydantic mypy plugin."
            ),
        ]
        init_typed: Annotated[
            bool,
            Field(
                description="Enable typed __init__ signatures in pydantic mypy plugin."
            ),
        ]
        warn_required_dynamic_aliases: Annotated[
            bool,
            Field(
                description="Warn on required dynamic aliases in pydantic mypy plugin."
            ),
        ]


__all__ = [
    "FlextInfraDepsModelsToolConfigLinters",
]
