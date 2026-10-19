"""Ruff and Mypy tool configuration models for the deps subpackage.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import Annotated, Literal, Self

from flext_cli import m

from flext_infra import c, t
from flext_infra._models import FlextInfraModelsDepsToolConfigProject


class FlextInfraModelsDepsToolConfigLinters(FlextInfraModelsDepsToolConfigProject):
    """Linters tool configuration models."""

    class CodespellConfig(m.ArbitraryTypesModel):
        """Codespell settings loaded from YAML."""

        check_filenames: Annotated[
            bool,
            m.Field(
                alias="check-filenames",
                description="Check filenames in addition to file contents.",
            ),
        ]
        ignore_words_list: Annotated[
            str,
            m.Field(
                alias="ignore-words-list",
                description="Comma-separated allowlist for known project terms.",
            ),
        ] = ""

    class RuffFormatConfig(m.ArbitraryTypesModel):
        """Ruff format settings loaded from YAML."""

        docstring_code_format: Annotated[
            bool,
            m.Field(
                alias="docstring-code-format",
                description="Enable ruff docstring code block formatting.",
            ),
        ]
        indent_style: Annotated[
            str,
            m.Field(
                alias="indent-style",
                description="Indent style for ruff formatter output.",
            ),
        ]
        line_ending: Annotated[
            str,
            m.Field(
                alias="line-ending",
                description="Line ending style for ruff formatter output.",
            ),
        ]
        quote_style: Annotated[
            str,
            m.Field(
                alias="quote-style",
                description="Quote style for ruff formatter output.",
            ),
        ]
        skip_magic_trailing_comma: Annotated[
            bool,
            m.Field(
                alias="skip-magic-trailing-comma",
                description="Collapse short comma-terminated constructs onto one line.",
            ),
        ]

    class RuffIsortConfig(m.ArbitraryTypesModel):
        """Ruff isort settings loaded from YAML."""

        combine_as_imports: Annotated[
            bool,
            m.Field(
                alias="combine-as-imports",
                description="Combine `as` imports in grouped isort blocks.",
            ),
        ]
        force_single_line: Annotated[
            bool,
            m.Field(
                alias="force-single-line",
                description="Force single-line imports in isort output.",
            ),
        ]
        split_on_trailing_comma: Annotated[
            bool,
            m.Field(
                alias="split-on-trailing-comma",
                description="Split imports when a trailing comma exists.",
            ),
        ]

    class RuffPydocstyleConfig(m.ArbitraryTypesModel):
        """Ruff pydocstyle settings loaded from YAML."""

        convention: Annotated[
            Literal["google", "numpy", "pep257"],
            m.Field(
                description=(
                    "Docstring convention; Ruff disables the docstring rules "
                    "it does not use, one of each mutually exclusive pair "
                    "included."
                ),
            ),
        ]

    class RuffPylintConfig(m.ArbitraryTypesModel):
        """Ruff Pylint policy for operator-approved native type descriptors."""

        allow_dunder_method_names: Annotated[
            t.SequenceOf[Literal["__base__", "__bases__"]],
            m.Field(
                alias="allow-dunder-method-names",
                description=(
                    "Only Python type.__base__ and type.__bases__ read-only "
                    "protocol properties are authorized by the operator."
                ),
            ),
        ]

    class RuffTypeCheckingConfig(m.ArbitraryTypesModel):
        """Ruff flake8-type-checking settings loaded from YAML."""

        runtime_evaluated_roots: Annotated[
            t.SequenceOf[t.NonEmptyStr],
            m.Field(
                alias="runtime-evaluated-roots",
                min_length=1,
                description=(
                    "Qualified base classes whose subclasses evaluate their "
                    "annotations at runtime; codegen derives every project "
                    "base inheriting one into runtime-evaluated-base-classes."
                ),
            ),
        ]

    class RuffLintConfig(m.ArbitraryTypesModel):
        """Ruff lint settings loaded from YAML."""

        select: Annotated[
            t.StrSequence,
            m.Field(description="Ruff lint rule selectors."),
        ] = m.Field(default_factory=tuple)
        extend_select: Annotated[
            t.StrSequence,
            m.Field(
                alias="extend-select",
                description=(
                    "Selectors enabled on top of the baseline selection; "
                    "explicit selectors take precedence over the pydocstyle "
                    "convention baseline in Ruff."
                ),
            ),
        ] = m.Field(default_factory=tuple)
        rule_owners: Annotated[
            t.MappingKV[t.Infra.RuffRule, t.NonEmptyStr],
            m.Field(
                alias="rule-owners",
                description=(
                    "Rules enforced by another registered canonical gate, never "
                    "waived; projection verifies its complete check/repair election."
                ),
            ),
        ]

        @m.field_validator("rule_owners")
        @classmethod
        def require_distinct_registered_rule_owners(
            cls,
            owners: t.StrMapping,
        ) -> t.StrMapping:
            """Reject unknown owners and delegation back to the lint gate.

            Returns:
                The declared ownership mapping without introducing defaults.

            Raises:
                ValueError: If any rule has an unknown or self-owned gate.

            """
            invalid = sorted(
                f"{rule}: {owner}"
                for rule, owner in owners.items()
                if owner == c.Infra.LINT or owner not in c.Infra.ALLOWED_GATES
            )
            if invalid:
                msg = "Ruff rules require distinct registered owners: " + ", ".join(
                    invalid
                )
                raise ValueError(msg)
            return owners

        unfixable: Annotated[
            t.StrSequence,
            m.Field(
                description=(
                    "Rules whose Ruff fixes delete code or diagnostics; reported, "
                    "never auto-fixed."
                ),
            ),
        ]
        ruling_disabled_rules: Annotated[
            t.VariadicTuple[t.NonEmptyStr],
            m.Field(
                alias="ruling-disabled-rules",
                description=(
                    "Operator-ruled rules disabled at the SSOT because the "
                    "lazy facade architecture requires what they forbid; "
                    "projected into lint ignore, never silenced by manual "
                    "hints."
                ),
            ),
        ] = ()
        extend_safe_fixes: Annotated[
            t.StrSequence,
            m.Field(
                alias="extend-safe-fixes",
                description=(
                    "Rules whose unsafe Ruff fixes are proven to preserve code, "
                    "comments and diagnostics."
                ),
            ),
        ]
        banned_api: Annotated[
            t.StrMapping,
            m.Field(
                alias="banned-api",
                description="Forbidden direct APIs and their canonical alternatives.",
            ),
        ]
        ban_relative_imports: Annotated[
            Literal["all"],
            m.Field(
                alias="ban-relative-imports",
                description="Relative imports are banned; every import is absolute.",
            ),
        ]
        copyright_notice_rgx: Annotated[
            t.NonEmptyStr,
            m.Field(
                alias="copyright-notice-rgx",
                description="Regex every module's copyright notice must match.",
            ),
        ]
        fix_recipes: Annotated[
            t.MappingKV[t.Infra.RuffRule, c.Infra.LintFixRecipe],
            m.Field(
                alias="fix-recipes",
                description=(
                    "Ruff rule name -> repair make fix applies to the findings "
                    "Ruff reports without a fix of its own."
                ),
            ),
        ]
        fix_recipe_phases: Annotated[
            t.VariadicTuple[t.VariadicTuple[c.Infra.LintFixRecipe]],
            m.Field(
                alias="fix-recipe-phases",
                description=(
                    "Recipe phases make fix applies in order; Ruff re-reads "
                    "the tree after each phase so a later phase sees the "
                    "findings an earlier one created or cured."
                ),
            ),
        ]
        isort: FlextInfraModelsDepsToolConfigLinters.RuffIsortConfig = m.Field(
            description="Ruff isort configuration",
        )
        pydocstyle: FlextInfraModelsDepsToolConfigLinters.RuffPydocstyleConfig = (
            m.Field(description="Ruff pydocstyle configuration")
        )
        pylint: FlextInfraModelsDepsToolConfigLinters.RuffPylintConfig = m.Field(
            description="Ruff Pylint native type descriptor policy",
        )
        flake8_type_checking: Annotated[
            FlextInfraModelsDepsToolConfigLinters.RuffTypeCheckingConfig,
            m.Field(
                alias="flake8-type-checking",
                description="Ruff flake8-type-checking configuration",
            ),
        ]

    class RuffConfig(m.ArbitraryTypesModel):
        """Ruff top-level settings loaded from YAML."""

        extend_exclude: Annotated[
            t.StrSequence,
            m.Field(
                alias="extend-exclude",
                description=(
                    "Workspace exclusions added to Ruff's defaults: "
                    "provider-owned tool-home projections stay outside the "
                    "member lint scope."
                ),
            ),
        ] = m.Field(default_factory=tuple)
        namespace_packages: Annotated[
            t.StrSequence,
            m.Field(
                alias="namespace-packages",
                description="Intentional PEP 420 namespace roots checked by Ruff.",
            ),
        ] = m.Field(default_factory=tuple)
        fix: Annotated[bool, m.Field(description="Enable automatic ruff fixes")]
        findings_exit_codes: Annotated[
            t.VariadicTuple[int],
            m.Field(
                alias="findings-exit-codes",
                description="Exit statuses with which Ruff reports its findings.",
            ),
        ]
        line_length: Annotated[
            int,
            m.Field(alias="line-length", description="Maximum line length."),
        ]
        preview: Annotated[bool, m.Field(description="Enable preview ruff behavior.")]
        respect_gitignore: Annotated[
            bool,
            m.Field(
                alias="respect-gitignore",
                description="Respect .gitignore exclusions.",
            ),
        ]
        show_fixes: Annotated[
            bool,
            m.Field(
                alias="show-fixes",
                description="Display fixed violations in ruff output.",
            ),
        ]
        src: Annotated[
            t.StrSequence,
            m.Field(description="Source roots used by ruff import analysis."),
        ] = m.Field(default_factory=tuple)
        target_version: Annotated[
            str,
            m.Field(
                alias="target-version",
                description="Python target version for ruff.",
            ),
        ]
        format: FlextInfraModelsDepsToolConfigLinters.RuffFormatConfig = m.Field(
            description="Ruff format configuration",
        )
        lint: FlextInfraModelsDepsToolConfigLinters.RuffLintConfig = m.Field(
            description="Ruff lint configuration",
        )

    class MypyOverrideConfig(m.ArbitraryTypesModel):
        """Single [[tool.mypy.overrides]] entry."""

        modules: Annotated[
            t.StrSequence,
            m.Field(description="Module patterns for this override."),
        ]
        follow_untyped_imports: Annotated[
            bool,
            m.Field(
                alias="follow-untyped-imports",
                description="Analyze installed source even without typing metadata.",
            ),
        ] = False
        justification: Annotated[
            str,
            m.Field(
                description=(
                    "Required citation (GitHub issue / PEP / mypy docs) justifying "
                    "this override. AGENTS.md:319 forbids suppressions without "
                    "evidence; leave empty only for strictly transitional overrides "
                    "with a TODO in the module comment."
                ),
            ),
        ] = ""

    class MypyConfig(m.ArbitraryTypesModel):
        """Mypy baseline settings loaded from YAML."""

        timeout_seconds: Annotated[
            int,
            m.Field(
                gt=0,
                description=(
                    "Mypy wall-time budget in seconds (SSOT); a project"
                    " overlay may only lower it."
                ),
            ),
        ]
        plugins: Annotated[
            t.StrSequence,
            m.Field(
                description="Mypy plugins, including mandatory Pydantic 2 support.",
            ),
        ]

        @m.field_validator("plugins")
        @classmethod
        def require_pydantic_plugin(cls, plugins: t.StrSequence) -> t.StrSequence:
            """Reject configurations without the mandatory Pydantic 2 plugin.

            Returns:
                The validated plugin declarations.

            Raises:
                ValueError: If Pydantic 2 support is missing or replaced by v1.

            """
            if "pydantic.mypy" not in plugins or "pydantic.v1.mypy" in plugins:
                msg = "Mypy requires pydantic.mypy and forbids pydantic.v1.mypy"
                raise ValueError(msg)
            return plugins

        boolean_settings: Annotated[
            t.BoolMapping,
            m.Field(
                alias="boolean-settings",
                description="Mypy boolean settings keyed by option name.",
            ),
        ]
        string_settings: Annotated[
            t.StrMapping,
            m.Field(
                alias="string-settings",
                description=(
                    "Mypy string-valued settings keyed by option name "
                    "(e.g. follow_imports='normal')."
                ),
            ),
        ]
        ruling_disable_error_codes: Annotated[
            t.VariadicTuple[t.NonEmptyStr],
            m.Field(
                alias="ruling-disable-error-codes",
                description=(
                    "Operator-ruled mypy error codes suspended fleet-wide "
                    "until the facade-alias family is cured; the tool-tables "
                    "phase renders them as disable_error_code."
                ),
            ),
        ] = ()
        overrides: Annotated[
            t.VariadicTuple[FlextInfraModelsDepsToolConfigLinters.MypyOverrideConfig],
            m.Field(
                description=(
                    "Per-module mypy overrides for "
                    "auto-generated files and PEP 695 generics."
                ),
            ),
        ] = m.Field(
            default_factory=tuple,
            description=(
                "Per-module mypy overrides for "
                "auto-generated files and PEP 695 generics."
            ),
        )

        @m.model_validator(mode="after")
        def reject_policy_shadow(self) -> Self:
            """Refuse ambiguous options and diagnostic suppression.

            Returns:
                The validated settings without modifying their declared values.

            Raises:
                ValueError: If generic settings bypass a dedicated policy owner.

            """
            boolean_keys = {
                key.strip().replace("-", "_") for key in self.boolean_settings
            }
            strings = {
                key.strip().replace("-", "_"): value
                for key, value in self.string_settings.items()
            }
            reserved = {
                c.Infra.PLUGINS,
                "disable_error_code",
                c.Infra.PYTHON_VERSION_UNDERSCORE,
                "overrides",
                "mypy_path",
            }
            if (boolean_keys | strings.keys()) & reserved:
                msg = "Mypy policy cannot be shadowed by generic options"
                raise ValueError(msg)
            if (
                boolean_keys & strings.keys()
                or len(boolean_keys) != len(self.boolean_settings)
                or len(strings) != len(self.string_settings)
            ):
                msg = "Mypy policy rejects duplicate generic options"
                raise ValueError(msg)
            if "enable_error_code" in boolean_keys:
                msg = "Mypy policy enable_error_code requires a string setting"
                raise ValueError(msg)
            if any(
                not key.isascii() or not key.isidentifier()
                for key in (*self.boolean_settings, *self.string_settings)
            ):
                msg = "Mypy policy requires plain option names, not TOML syntax"
                raise ValueError(msg)
            if self.boolean_settings.get("ignore_errors", False) or (
                "ignore_errors" in strings
            ):
                msg = "Mypy policy cannot ignore diagnostics"
                raise ValueError(msg)
            return self

    class PydanticMypyConfig(m.ArbitraryTypesModel):
        """Pydantic mypy plugin settings loaded from YAML."""

        init_forbid_extra: Annotated[
            bool,
            m.Field(
                description=(
                    "Enable forbid-extra init behavior in pydantic mypy plugin."
                ),
            ),
        ]
        init_typed: Annotated[
            bool,
            m.Field(
                description="Enable typed __init__ signatures in pydantic mypy plugin.",
            ),
        ]
        warn_required_dynamic_aliases: Annotated[
            bool,
            m.Field(
                description="Warn on required dynamic aliases in pydantic mypy plugin.",
            ),
        ]


__all__: list[str] = ["FlextInfraModelsDepsToolConfigLinters"]
