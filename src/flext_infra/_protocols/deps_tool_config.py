# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
src/flext_infra/_protocols/deps_tool_config
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Literal, Protocol, runtime_checkable

from flext_infra import c, t

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraProtocolsDepsToolConfig:
    """Own the structural contracts declared by its model source."""

    @runtime_checkable
    class ModStageConfig(Protocol):
        """Structural data contract projected from the owning model."""

        name: t.NonEmptyStr
        kind: c.Infra.ModStageKind
        shapes: t.StrTuple
        select: t.StrTuple

    @runtime_checkable
    class ModPhasesConfig(Protocol):
        """Structural data contract projected from the owning model."""

        import_alignment: bool
        pass_cap: int
        stages: tuple[p.Infra.ModStageConfig, ...]

    @runtime_checkable
    class ModConfig(Protocol):
        """Structural data contract projected from the owning model."""

        phases: p.Infra.ModPhasesConfig

    @runtime_checkable
    class PytestWorkerCeiling(Protocol):
        """Structural data contract projected from the owning model."""

        workers: int | None
        cpu_fraction: str | None

    @runtime_checkable
    class PytestConfig(Protocol):
        """Structural data contract projected from the owning model."""

        slow_timeout_seconds: int
        slow_marker: t.NonEmptyStr
        run_timeout_seconds: int
        termination_grace_seconds: int
        max_failures: int
        enforcement_plugin: t.NonEmptyStr
        progress_args: tuple[t.NonEmptyStr, ...]
        report_args: tuple[t.NonEmptyStr, ...]
        diagnostic_args: tuple[t.NonEmptyStr, ...]
        parallel_workers: int
        parallel_worker_memory_gb: int
        parallel_distribution: Literal["load", "loadscope"]
        loadscope_reorder: bool
        parallel_schedule_chunk: int
        parallel_worker_overrides: Mapping[str, p.Infra.PytestWorkerCeiling]
        profile_sort: Literal[
            "calls",
            "cumulative",
            "filename",
            "line",
            "name",
            "nfl",
            "pcalls",
            "stdname",
            "time",
        ]
        profile_limit: int
        profile_suite_filename: t.NonEmptyStr
        profile_process_directory: t.NonEmptyStr
        standard_markers: Sequence[str]
        external_gate_markers: tuple[str, ...]
        ci_excluded_markers: tuple[str, ...]
        ci_excluded_fixtures: tuple[str, ...]

        @property
        def parallel_arguments(self) -> t.StrTuple: ...

    @runtime_checkable
    class TomlsortConfig(Protocol):
        """Structural data contract projected from the owning model."""

        process_timeout_seconds: int

    @runtime_checkable
    class JscpdToolConfig(Protocol):
        """Structural data contract projected from the owning model."""

        similarity: float
        semantic: p.Infra.JscpdSemantic
        ignore_patterns: t.StrTuple
        ignore: Sequence[str]

    @runtime_checkable
    class MarkdownProjectedBlock(Protocol):
        """Structural data contract projected from the owning model."""

        writer: t.NonEmptyStr
        begin: t.RegexPattern
        end: t.RegexPattern

    @runtime_checkable
    class MarkdownConfig(Protocol):
        """Structural data contract projected from the owning model."""

        projected_blocks: tuple[p.Infra.MarkdownProjectedBlock, ...]
        findings_exit_codes: tuple[int, ...]
        rules: t.Infra.SettingsPairs
        native_rules: t.Infra.SettingsPairs
        native_settings: t.Infra.SettingsPairs

    @runtime_checkable
    class ToolConfigTools(Protocol):
        """Structural data contract projected from the owning model."""

        markdown: p.Infra.MarkdownConfig
        ruff: p.Infra.RuffConfig
        mypy: p.Infra.MypyConfig
        pyright: p.Infra.PyrightConfig
        pyrefly: p.Infra.PyreflyConfig
        pytest: p.Infra.PytestConfig
        tomlsort: p.Infra.TomlsortConfig
        jscpd: p.Infra.JscpdToolConfig

    @runtime_checkable
    class LazyInitConfig(Protocol):
        """Structural data contract projected from the owning model."""

        import_layer_order: tuple[t.NonEmptyStr, ...]
        layer_aliases: Mapping[t.NonEmptyStr, t.NonEmptyStr]
        stdlib_backports: tuple[t.NonEmptyStr, ...]
        reverse_import_mode: Literal["type_checking"]
        forward_import_form: Literal["absolute"]

    @runtime_checkable
    class FacadeMembersConfig(Protocol):
        """Structural data contract projected from the owning model."""

        owners: Mapping[c.Infra.FacadeMemberKind, t.NonEmptyStr]
        model_declaration_modules: tuple[t.NonEmptyStr, ...]
        type_constructor_modules: tuple[t.NonEmptyStr, ...]

    @runtime_checkable
    class SmellsConfig(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def fix_text(self) -> Mapping[t.NonEmptyStr, t.NonEmptyStr]: ...
        @property
        def enforce(self) -> Mapping[t.NonEmptyStr, t.Infra.EnforcementIds]: ...

    @runtime_checkable
    class AccessorPolicyConfig(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def forbidden_prefixes(self) -> Mapping[t.NonEmptyStr, t.NonEmptyStr]: ...

    @runtime_checkable
    class ToolConfigDocument(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def settings(self) -> Mapping[t.NonEmptyStr, t.Infra.SettingsPairs]: ...
        @property
        def derived_tool_roots(self) -> tuple[t.NonEmptyStr, ...]: ...
        @property
        def derived_settings(
            self,
        ) -> Mapping[t.NonEmptyStr, tuple[t.NonEmptyStr, ...]]: ...
        @property
        def raw_check_receipt_suffix(self) -> t.NonEmptyStr: ...
        @property
        def tools(self) -> p.Infra.ToolConfigTools: ...
        @property
        def lazy_init(self) -> p.Infra.LazyInitConfig: ...
        @property
        def facade_members(self) -> p.Infra.FacadeMembersConfig: ...
        @property
        def smells(self) -> p.Infra.SmellsConfig: ...
        @property
        def accessor_policy(self) -> p.Infra.AccessorPolicyConfig: ...
        @property
        def mod(self) -> p.Infra.ModConfig: ...

    @runtime_checkable
    class ToolingInputs(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def document(self) -> p.Infra.ToolConfigDocument: ...
        @property
        def sources(self) -> tuple[p.Cli.AtomicFileState, ...]: ...

    @runtime_checkable
    class ToolingRuntimeContext(Protocol):
        """Structural data contract projected from the owning model."""

        document: p.Infra.ToolConfigDocument | None
        project_kind: t.NonEmptyStr
        configuration: str
        tool_options: Mapping[str, t.JsonMapping]
        sources: tuple[p.Cli.AtomicFileState, ...]


__all__: list[str] = [
    "FlextInfraProtocolsDepsToolConfig",
]
