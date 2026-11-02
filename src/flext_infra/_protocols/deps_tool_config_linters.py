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

from flext_infra import c, t

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraProtocolsDepsToolConfigLinters:
    """Own the structural contracts declared by its model source."""

    @runtime_checkable
    class TrackerAuthorization(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def tracker_key(self) -> t.NonEmptyStr: ...

    @runtime_checkable
    class OperatorAuthorization(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def operator_words(self) -> t.NonEmptyStr: ...
        @property
        def authorized_on(self) -> date: ...
        @property
        def channel(self) -> t.NonEmptyStr: ...

    @runtime_checkable
    class DiagnosticRuleChange(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def checker(self) -> t.NonEmptyStr: ...
        @property
        def rule(self) -> t.NonEmptyStr: ...
        @property
        def old(self) -> t.NonEmptyStr: ...
        @property
        def new(self) -> t.NonEmptyStr: ...

    @runtime_checkable
    class RuffTypeCheckingConfig(Protocol):
        """Structural data contract projected from the owning model."""

        runtime_evaluated_roots: Sequence[t.NonEmptyStr]

    @runtime_checkable
    class RuffLintConfig(Protocol):
        """Structural data contract projected from the owning model."""

        rule_owners: Mapping[t.Infra.RuffRule, t.NonEmptyStr]
        ruling_disabled_rules: tuple[t.NonEmptyStr, ...]
        enforce: Mapping[t.Infra.RuffRule, t.Infra.EnforcementIds]
        fix_recipes: Mapping[t.Infra.RuffRule, c.Infra.LintFixRecipe]
        fix_recipe_phases: tuple[tuple[c.Infra.LintFixRecipe, ...], ...]
        flake8_type_checking: p.Infra.RuffTypeCheckingConfig

    @runtime_checkable
    class RuffConfig(Protocol):
        """Structural data contract projected from the owning model."""

        findings_exit_codes: tuple[int, ...]
        lint: p.Infra.RuffLintConfig

    @runtime_checkable
    class MypyOverrideConfig(Protocol):
        """Structural data contract projected from the owning model."""

        modules: Sequence[str]
        settings: t.Infra.SettingsPairs
        justification: str

    @runtime_checkable
    class MypyConfig(Protocol):
        """Structural data contract projected from the owning model."""

        timeout_seconds: int
        max_timeout_seconds: int
        ruling_disable_error_codes: tuple[t.NonEmptyStr, ...]
        overrides: tuple[p.Infra.MypyOverrideConfig, ...]


__all__: list[str] = [
    "FlextInfraProtocolsDepsToolConfigLinters",
]
