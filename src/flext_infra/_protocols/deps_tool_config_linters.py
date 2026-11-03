# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
src/flext_infra/_protocols/deps_tool_config_linters
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import date
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from flext_cli import FlextCliProtocols

from flext_infra import t

if TYPE_CHECKING:
    from flext_infra._constants import FlextInfraConstantsCheck
    from flext_infra._typings import FlextInfraTypesBase


class FlextInfraProtocolsDepsToolConfigLinters:
    """Own the structural contracts declared by its model source."""

    @runtime_checkable
    class TrackerAuthorization(FlextCliProtocols.Model, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def tracker_key(self) -> t.NonEmptyStr:
            """Tracker memory or item key recording the approval."""
            ...

    @runtime_checkable
    class OperatorAuthorization(FlextCliProtocols.Model, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def operator_words(self) -> t.NonEmptyStr:
            """The operator's approval, verbatim."""
            ...

        @property
        def authorized_on(self) -> date:
            """Calendar date on which the operator approved."""
            ...

        @property
        def channel(self) -> t.NonEmptyStr:
            """Channel and session that carried the approval."""
            ...

    @runtime_checkable
    class DiagnosticRuleChange(FlextCliProtocols.Model, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def checker(self) -> t.NonEmptyStr:
            """Type checker owning the rule."""
            ...

        @property
        def rule(self) -> t.NonEmptyStr:
            """Native rule name of that checker."""
            ...

        @property
        def old(self) -> t.NonEmptyStr:
            """Level the policy applies outside the exception."""
            ...

        @property
        def new(self) -> t.NonEmptyStr:
            """Level authorized inside the exception root."""
            ...

    @runtime_checkable
    class RuffLintConfig(FlextCliProtocols.Model, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def rule_owners(self) -> Mapping[FlextInfraTypesBase.RuffRule, t.NonEmptyStr]:
            """Structural member projected from the owning model.

            Rules enforced by another registered canonical gate, never waived;
            projection verifies its complete check/repair election.
            """
            ...

        ruling_disabled_rules: tuple[t.NonEmptyStr, ...]

        @property
        def enforce(
            self,
        ) -> Mapping[FlextInfraTypesBase.RuffRule, FlextInfraTypesBase.EnforcementIds]:
            """Structural member projected from the owning model.

            Ruff rule name -> enforcement law ids the rule claims; a claim is active
            only while the lint selection enables it.
            """
            ...

        @property
        def fix_recipes(
            self,
        ) -> Mapping[
            FlextInfraTypesBase.RuffRule, FlextInfraConstantsCheck.LintFixRecipe
        ]:
            """Structural member projected from the owning model.

            Ruff rule name -> repair make fix applies to the findings Ruff reports
            without a fix of its own.
            """
            ...

        @property
        def fix_recipe_phases(
            self,
        ) -> tuple[tuple[FlextInfraConstantsCheck.LintFixRecipe, ...], ...]:
            """Structural member projected from the owning model.

            Recipe phases make fix applies in order; Ruff re-reads the tree after
            each phase so a later phase sees the findings an earlier one created or
            cured.
            """
            ...

    @runtime_checkable
    class RuffConfig(FlextCliProtocols.Model, Protocol):
        """Structural data contract projected from the owning model."""

        findings_exit_codes: tuple[int, ...]

        @property
        def lint(self) -> FlextInfraProtocolsDepsToolConfigLinters.RuffLintConfig:
            """Ruff lint configuration."""
            ...

    @runtime_checkable
    class MypyOverrideConfig(FlextCliProtocols.Model, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def modules(self) -> Sequence[str]:
            """Module patterns for this override."""
            ...

        @property
        def settings(self) -> FlextInfraTypesBase.SettingsPairs:
            """Native override options as ordered key/value pairs."""
            ...

        @property
        def justification(self) -> str:
            """Structural member projected from the owning model.

            Required citation (GitHub issue / PEP / mypy docs) justifying this
            override. AGENTS.md:319 forbids suppressions without evidence; leave
            empty only for strictly transitional overrides with a TODO in the module
            comment.
            """
            ...

    @runtime_checkable
    class MypyConfig(FlextCliProtocols.Model, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def timeout_seconds(self) -> int:
            """Default Mypy wall-time budget in seconds."""
            ...

        @property
        def max_timeout_seconds(self) -> int:
            """Finite project budget ceiling in seconds."""
            ...

        ruling_disable_error_codes: tuple[t.NonEmptyStr, ...]

        @property
        def overrides(
            self,
        ) -> tuple[FlextInfraProtocolsDepsToolConfigLinters.MypyOverrideConfig, ...]:
            """Module scopes and justified native option pairs."""
            ...


__all__: list[str] = [
    "FlextInfraProtocolsDepsToolConfigLinters",
]
