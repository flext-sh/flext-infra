# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
src/flext_infra/_protocols/deps_tool_config_type_checkers
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from flext_infra import t

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraProtocolsDepsToolConfigTypeCheckers:
    """Own the structural contracts declared by its model source."""

    @runtime_checkable
    class DiagnosticPathException(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def root(self) -> t.NonEmptyStr: ...
        @property
        def rationale(self) -> t.NonEmptyStr: ...
        @property
        def authorization(
            self,
        ) -> p.Infra.TrackerAuthorization | p.Infra.OperatorAuthorization: ...
        @property
        def changes(self) -> tuple[p.Infra.DiagnosticRuleChange, ...]: ...

    @runtime_checkable
    class PyrightConfig(Protocol):
        """Structural data contract projected from the owning model."""

        path_rules: p.Infra.PyrightConfig.PathRulesConfig

        @runtime_checkable
        class ExecutionEnvironment(Protocol):
            """Structural data contract projected from the owning model."""

            @property
            def root(self) -> str: ...
            @property
            def report_private_usage(self) -> str: ...
            @property
            def extra_paths(self) -> Sequence[str]: ...
            @property
            def diagnostic_levels(self) -> Mapping[str, str]: ...

        @runtime_checkable
        class PathRulesConfig(Protocol):
            """Structural data contract projected from the owning model."""

            project_root_env_dirs: Sequence[str]
            source_dir: str
            project_root: str
            env_dirs: Sequence[str]
            test_like_dirs: Sequence[str]
            default_excludes: Sequence[str]
            ignored_diagnostic_globs: Sequence[str]
            diagnostic_path_exceptions: tuple[p.Infra.DiagnosticPathException, ...]
            source_report_private_usage: str
            test_like_report_private_usage: str
            other_report_private_usage: str

    @runtime_checkable
    class PyreflyConfig(Protocol):
        """Structural data contract projected from the owning model."""

        findings_exit_codes: tuple[int, ...]
        path_rules: p.Infra.PyreflyConfig.PathRulesConfig

        @runtime_checkable
        class PathRulesConfig(Protocol):
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
