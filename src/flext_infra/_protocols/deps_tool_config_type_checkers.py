# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
src/flext_infra/_protocols/deps_tool_config_type_checkers
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from flext_cli import FlextCliProtocols

if TYPE_CHECKING:
    from flext_infra import t
    from flext_infra._protocols import FlextInfraProtocolsDepsToolConfigLinters


class FlextInfraProtocolsDepsToolConfigTypeCheckers:
    """Own the structural contracts declared by its model source."""

    @runtime_checkable
    class DiagnosticPathException(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def root(self) -> t.NonEmptyStr:
            """Project-relative file or directory the rules govern."""
            ...

        @property
        def rationale(self) -> t.NonEmptyStr:
            """Verified technical cause of the exception."""
            ...

        @property
        def authorization(
            self,
        ) -> (
            FlextInfraProtocolsDepsToolConfigLinters.TrackerAuthorization
            | FlextInfraProtocolsDepsToolConfigLinters.OperatorAuthorization
        ):
            """Tracker key or verbatim operator approval."""
            ...

        @property
        def changes(
            self,
        ) -> tuple[FlextInfraProtocolsDepsToolConfigLinters.DiagnosticRuleChange, ...]:
            """Rule-level changes, each naming its checker."""
            ...

    @runtime_checkable
    class PyrightConfig(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def path_rules(
            self,
        ) -> FlextInfraProtocolsDepsToolConfigTypeCheckers.PyrightConfigPathRulesConfig:
            """Pyright path resolution and execution-env rules."""
            ...

        ruling_disabled_rules: tuple[t.NonEmptyStr, ...]

    @runtime_checkable
    class PyrightConfigExecutionEnvironment(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def root(self) -> str:
            """Execution environment root path."""
            ...

        @property
        def report_private_usage(self) -> str:
            """ReportPrivateUsage override for this environment."""
            ...

        @property
        def extra_paths(self) -> Sequence[str]:
            """ExtraPaths applied to this execution environment."""
            ...

        @property
        def diagnostic_levels(self) -> Mapping[str, str]:
            """Structural member projected from the owning model.

            Authorized native rule levels the renderer adds to this environment's
            payload.
            """
            ...

    @runtime_checkable
    class PyrightConfigPathRulesConfig(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        project_root_env_dirs: Sequence[str]
        source_dir: str
        project_root: str
        env_dirs: Sequence[str]
        test_like_dirs: Sequence[str]
        default_excludes: Sequence[str]
        ignored_diagnostic_globs: Sequence[str]

        @property
        def diagnostic_path_exceptions(
            self,
        ) -> tuple[
            FlextInfraProtocolsDepsToolConfigTypeCheckers.DiagnosticPathException, ...
        ]:
            """Structural member projected from the owning model.

            Authorized rule exceptions; each entry renders its Pyright environment
            and its Pyrefly sub-config.
            """
            ...

        source_report_private_usage: str
        test_like_report_private_usage: str
        other_report_private_usage: str

    @runtime_checkable
    class PyreflyConfig(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        findings_exit_codes: tuple[int, ...]
        ruling_disabled_rules: tuple[t.NonEmptyStr, ...]

        @property
        def path_rules(
            self,
        ) -> FlextInfraProtocolsDepsToolConfigTypeCheckers.PyreflyConfigPathRulesConfig:
            """Pyrefly search-path rules."""
            ...

    @runtime_checkable
    class PyreflyConfigPathRulesConfig(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        source_dir: str
        project_root: str
        env_dirs: Sequence[str]
        workspace_include_children: bool
        workspace_include_child_env_dirs: Sequence[str]
        project_shared_search_paths: Sequence[str]


__all__: list[str] = [
    "FlextInfraProtocolsDepsToolConfigTypeCheckers",
]
