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

if TYPE_CHECKING:
    from flext_infra import c, t


class FlextInfraProtocolsDepsToolConfigLinters:
    """Own the structural contracts declared by its model source."""

    @runtime_checkable
    class TrackerAuthorization(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def tracker_key(self) -> t.NonEmptyStr:
            """Tracker memory or item key recording the approval."""
            ...

    @runtime_checkable
    class OperatorAuthorization(FlextCliProtocols.BaseModel, Protocol):
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
    class DiagnosticRuleChange(FlextCliProtocols.BaseModel, Protocol):
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
    class RuffLintConfig(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        rule_owners: Mapping[t.Infra.RuffRule, t.NonEmptyStr]
        ruling_disabled_rules: tuple[t.NonEmptyStr, ...]
        enforce: Mapping[t.Infra.RuffRule, t.Infra.EnforcementIds]
        fix_recipes: Mapping[t.Infra.RuffRule, c.Infra.LintFixRecipe]
        fix_recipe_phases: tuple[tuple[c.Infra.LintFixRecipe, ...], ...]

    @runtime_checkable
    class RuffConfig(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        findings_exit_codes: tuple[int, ...]
        lint: FlextInfraProtocolsDepsToolConfigLinters.RuffLintConfig

    @runtime_checkable
    class MypyOverrideConfig(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        modules: Sequence[str]
        settings: t.Infra.SettingsPairs
        justification: str

    @runtime_checkable
    class MypyConfig(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        timeout_seconds: int
        max_timeout_seconds: int
        ruling_disable_error_codes: tuple[t.NonEmptyStr, ...]
        overrides: tuple[
            FlextInfraProtocolsDepsToolConfigLinters.MypyOverrideConfig, ...
        ]


__all__: list[str] = [
    "FlextInfraProtocolsDepsToolConfigLinters",
]
