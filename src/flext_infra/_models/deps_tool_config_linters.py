"""Ruff and Mypy tool configuration models for the deps subpackage.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import Annotated

from flext_cli import m

from flext_infra import c, t
from flext_infra._models import FlextInfraModelsDepsToolConfigProject


class FlextInfraModelsDepsToolConfigLinters(FlextInfraModelsDepsToolConfigProject):
    """Linters tool configuration models."""

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

        ruling_disabled_rules: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(
                alias="ruling-disabled-rules",
                strict=False,
                description=(
                    "Operator-ruled rules disabled at the SSOT because the "
                    "lazy facade architecture requires what they forbid; "
                    "projected into lint ignore, never silenced by manual "
                    "hints."
                ),
            ),
        ] = ()
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
        flake8_type_checking: Annotated[
            FlextInfraModelsDepsToolConfigLinters.RuffTypeCheckingConfig,
            m.Field(
                alias="flake8-type-checking",
                description="Ruff flake8-type-checking configuration",
            ),
        ]

    class RuffConfig(m.ArbitraryTypesModel):
        """Ruff top-level settings loaded from YAML."""

        findings_exit_codes: Annotated[
            tuple[int, ...],
            m.Field(
                alias="findings-exit-codes",
                strict=False,
                description="Exit statuses with which Ruff reports its findings.",
            ),
        ]
        lint: FlextInfraModelsDepsToolConfigLinters.RuffLintConfig = m.Field(
            description="Ruff lint configuration",
        )

    class MypyOverrideConfig(m.ArbitraryTypesModel):
        """Single [[tool.mypy.overrides]] entry."""

        modules: Annotated[
            t.StrSequence,
            m.Field(description="Module patterns for this override."),
        ]
        settings: Annotated[
            t.Infra.SettingsPairs,
            m.Field(description="Native override options as ordered key/value pairs."),
        ] = ()
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
        """Execution budget and ownership policy for native Mypy options."""

        timeout_seconds: Annotated[
            int,
            m.Field(gt=0, description="Mypy wall-time budget in seconds."),
        ]
        ruling_disable_error_codes: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(
                alias="ruling-disable-error-codes",
                strict=False,
                description="Operator-authorized suspended diagnostics.",
            ),
        ] = ()
        overrides: Annotated[
            t.VariadicTuple[FlextInfraModelsDepsToolConfigLinters.MypyOverrideConfig],
            m.Field(description="Module scopes and justified native option pairs."),
        ] = ()


__all__: list[str] = ["FlextInfraModelsDepsToolConfigLinters"]
