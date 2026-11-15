"""Ruff, Mypy and diagnostic-authorization models for the deps subpackage.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from datetime import date
from typing import Annotated, Self

from flext_cli import m

from flext_infra import c, t
from flext_infra._models import FlextInfraModelsDepsToolConfigProject


class FlextInfraModelsDepsToolConfigLinters(FlextInfraModelsDepsToolConfigProject):
    """Linters tool configuration models."""

    class TrackerAuthorization(m.ContractModel):
        """Authorization recorded under one canonical tracker key."""

        tracker_key: t.NonEmptyStr = m.Field(
            alias="tracker-key",
            description="Tracker memory or item key recording the approval.",
        )

    class OperatorAuthorization(m.ContractModel):
        """Authorization quoted verbatim from the operator."""

        operator_words: t.NonEmptyStr = m.Field(
            alias="operator-words", description="The operator's approval, verbatim."
        )
        authorized_on: date = m.Field(
            alias="date",
            strict=False,
            description="Calendar date on which the operator approved.",
        )
        channel: Annotated[
            t.NonEmptyStr,
            m.Field(description="Channel and session that carried the approval."),
        ]

    class DiagnosticRuleChange(m.ContractModel):
        """One checker rule moved from its policy level to an authorized level."""

        checker: Annotated[
            t.NonEmptyStr,
            m.Field(description="Type checker owning the rule."),
        ]
        rule: Annotated[
            t.NonEmptyStr,
            m.Field(description="Native rule name of that checker."),
        ]
        old: Annotated[
            t.NonEmptyStr,
            m.Field(description="Level the policy applies outside the exception."),
        ]
        new: Annotated[
            t.NonEmptyStr,
            m.Field(description="Level authorized inside the exception root."),
        ]

        @m.model_validator(mode="after")
        def _validate_native_vocabulary(self) -> Self:
            """Accept only native rule names and levels of the declared checker.

            Returns:
                The validated change.

            Raises:
                ValueError: If the checker, rule, or a level is not native, or
                    the change keeps the policy level.

            """
            levels = c.Infra.DIAGNOSTIC_LEVELS.get(self.checker)
            if levels is None:
                msg = (
                    f"unknown checker {self.checker!r}; declare one of "
                    f"{sorted(c.Infra.DIAGNOSTIC_LEVELS)}"
                )
                raise ValueError(msg)
            pattern = c.Infra.DIAGNOSTIC_RULE_PATTERNS[self.checker]
            if re.fullmatch(pattern, self.rule) is None:
                msg = f"{self.rule!r} is not a native {self.checker} rule name"
                raise ValueError(msg)
            for level in (self.old, self.new):
                if level not in levels:
                    msg = (
                        f"{level!r} is not a native {self.checker} level; "
                        f"declare one of {sorted(levels)}"
                    )
                    raise ValueError(msg)
            if self.old == self.new:
                msg = f"{self.checker} {self.rule} keeps level {self.old!r}"
                raise ValueError(msg)
            return self

    class RuffLintConfig(m.ArbitraryTypesModel):
        """Ruff lint settings loaded from YAML."""

        rule_owners: Mapping[t.Infra.RuffRule, t.NonEmptyStr] = m.Field(
            alias="rule-owners",
            description=(
                "Rules enforced by another registered canonical gate, never waived; "
                "projection verifies its complete check/repair election."
            ),
        )

        @m.field_validator("rule_owners")
        @classmethod
        def require_distinct_registered_rule_owners(
            cls,
            owners: Mapping[str, str],
        ) -> Mapping[str, str]:
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

        ruling_disabled_rules: tuple[t.NonEmptyStr, ...] = m.Field(
            (),
            alias="ruling-disabled-rules",
            strict=False,
            description=(
                "Operator-ruled rules disabled at the SSOT because the lazy facade "
                "architecture requires what they forbid; projected into lint ignore, "
                "never silenced by manual hints."
            ),
        )
        enforce: Annotated[
            Mapping[t.Infra.RuffRule, t.Infra.EnforcementIds],
            m.Field(
                description=(
                    "Ruff rule name -> enforcement law ids the rule claims; a "
                    "claim is active only while the lint selection enables it."
                ),
            ),
        ]
        fix_recipes: Mapping[t.Infra.RuffRule, c.Infra.LintFixRecipe] = m.Field(
            alias="fix-recipes",
            description=(
                "Ruff rule name -> repair make fix applies to the findings Ruff reports"
                " without a fix of its own."
            ),
        )
        fix_recipe_phases: tuple[tuple[c.Infra.LintFixRecipe, ...], ...] = m.Field(
            alias="fix-recipe-phases",
            description=(
                "Recipe phases make fix applies in order; Ruff re-reads the tree after "
                "each phase so a later phase sees the findings an earlier one created "
                "or cured."
            ),
        )

    class RuffConfig(m.ArbitraryTypesModel):
        """Ruff top-level settings loaded from YAML."""

        findings_exit_codes: tuple[int, ...] = m.Field(
            alias="findings-exit-codes",
            strict=False,
            description="Exit statuses with which Ruff reports its findings.",
        )
        lint: FlextInfraModelsDepsToolConfigLinters.RuffLintConfig = m.Field(
            description="Ruff lint configuration",
        )

    class MypyOverrideConfig(m.ArbitraryTypesModel):
        """Single [[tool.mypy.overrides]] entry."""

        modules: Annotated[
            Sequence[str],
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
            m.Field(
                gt=0,
                strict=True,
                description="Default Mypy wall-time budget in seconds.",
            ),
        ]
        max_timeout_seconds: Annotated[
            int,
            m.Field(
                gt=0,
                strict=True,
                description="Finite project budget ceiling in seconds.",
            ),
        ]

        @m.model_validator(mode="after")
        def validate_timeout_ceiling(self) -> Self:
            """Keep the default inside the declared finite ceiling.

            Returns:
                The validated policy.

            Raises:
                ValueError: If the default exceeds the ceiling.

            """
            if self.timeout_seconds > self.max_timeout_seconds:
                msg = "Mypy default timeout exceeds max_timeout_seconds"
                raise ValueError(msg)
            return self

        ruling_disable_error_codes: tuple[t.NonEmptyStr, ...] = m.Field(
            (),
            alias="ruling-disable-error-codes",
            strict=False,
            description="Operator-authorized suspended diagnostics.",
        )
        overrides: Annotated[
            tuple[
                FlextInfraModelsDepsToolConfigLinters.MypyOverrideConfig,
                ...,
            ],
            m.Field(description="Module scopes and justified native option pairs."),
        ] = ()


__all__: list[str] = ["FlextInfraModelsDepsToolConfigLinters"]
