# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
src/flext_infra/_protocols/deps_tool_config
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Literal, Protocol, runtime_checkable

from flext_cli import FlextCliProtocols

if TYPE_CHECKING:
    from flext_cli import p

    from flext_infra import c, t
    from flext_infra._protocols import (
        FlextInfraProtocolsDepsToolConfigLinters,
        FlextInfraProtocolsDepsToolConfigTypeCheckers,
        FlextInfraProtocolsDuplication,
    )


class FlextInfraProtocolsDepsToolConfig:
    """Own the structural contracts declared by its model source."""

    @runtime_checkable
    class ModStageConfig(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        name: t.NonEmptyStr
        kind: c.Infra.ModStageKind
        shapes: t.StrTuple
        select: t.StrTuple

    @runtime_checkable
    class ModPhasesConfig(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        import_alignment: bool
        pass_cap: int

        @property
        def stages(
            self,
        ) -> tuple[FlextInfraProtocolsDepsToolConfig.ModStageConfig, ...]:
            """Structural member projected from the owning model.

            Ordered native cascade stages of make mod: ast-grep stages apply
            natively, the ruff stage repairs imports.
            """
            ...

    @runtime_checkable
    class ModConfig(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def phases(self) -> FlextInfraProtocolsDepsToolConfig.ModPhasesConfig:
            """Phase toggles read from config/tooling.yaml."""
            ...

        scan_threads: t.PositiveInt

    @runtime_checkable
    class PytestWorkerCeiling(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        workers: int | None
        cpu_fraction: str | None

    @runtime_checkable
    class PytestConfig(FlextCliProtocols.BaseModel, Protocol):
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

        @property
        def parallel_worker_overrides(
            self,
        ) -> Mapping[str, FlextInfraProtocolsDepsToolConfig.PytestWorkerCeiling]:
            """Structural member projected from the owning model.

            Per declared-project worker ceilings (``[project].name`` → absolute
            ``workers`` or CPU ``cpu_fraction``) resolved by the runner over the
            fleet-wide ``parallel-workers`` default: a consumer whose measured suite
            cannot fit the single-worker process boundary declares its ceiling here,
            inside the fleet cycle. The legacy bare-integer form still reads as an
            absolute ``workers`` ceiling.
            """
            ...

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
        def parallel_arguments(self) -> t.StrTuple:
            """Native scheduler arguments derived from the typed policy."""
            ...

        @property
        def external_gate_deselection(self) -> str:
            """Pytest ``-m`` expression that skips external gates."""
            ...

        @property
        def slow_suite_stop_reserve_seconds(self) -> int:
            """Derive the slow-phase reserve bounded by the slow ceiling."""
            ...

        @property
        def slow_serial_suite_stop_reserve_seconds(self) -> int:
            """Derive the slow-phase serial reserve: one slow item plus grace."""
            ...

        @property
        def xdist_items_per_worker(self) -> int:
            """Structural member projected from the owning model.

            Xdist depth per worker: the running item plus one queued, or a chunk.
            """
            ...

    @runtime_checkable
    class TomlsortConfig(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        process_timeout_seconds: int

    @runtime_checkable
    class JscpdToolConfig(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        similarity: float

        @property
        def semantic(self) -> FlextInfraProtocolsDuplication.JscpdSemantic:
            """Embedding pass host (--semantic)."""
            ...

        ignore_patterns: t.StrTuple
        ignore: Sequence[str]

    @runtime_checkable
    class MarkdownProjectedBlock(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        writer: t.NonEmptyStr
        begin: t.RegexPattern
        end: t.RegexPattern

    @runtime_checkable
    class MarkdownConfig(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def projected_blocks(
            self,
        ) -> tuple[FlextInfraProtocolsDepsToolConfig.MarkdownProjectedBlock, ...]:
            """Structural member projected from the owning model.

            Foreign writers whose marker-delimited blocks the Markdown lint reads as
            masked lines; FLEXT-owned blocks never appear.
            """
            ...

        findings_exit_codes: tuple[int, ...]
        default_enabled: bool
        extend_enable: t.StrTuple
        rules: t.Infra.SettingsPairs
        native_settings: t.Infra.SettingsPairs

    @runtime_checkable
    class ToolConfigTools(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def markdown(self) -> FlextInfraProtocolsDepsToolConfig.MarkdownConfig:
            """Markdown lint settings."""
            ...

        @property
        def ruff(self) -> FlextInfraProtocolsDepsToolConfigLinters.RuffConfig:
            """Ruff settings."""
            ...

        @property
        def mypy(self) -> FlextInfraProtocolsDepsToolConfigLinters.MypyConfig:
            """Mypy settings."""
            ...

        @property
        def pyright(
            self,
        ) -> FlextInfraProtocolsDepsToolConfigTypeCheckers.PyrightConfig:
            """Pyright settings."""
            ...

        @property
        def pyrefly(
            self,
        ) -> FlextInfraProtocolsDepsToolConfigTypeCheckers.PyreflyConfig:
            """Pyrefly settings."""
            ...

        @property
        def pytest(self) -> FlextInfraProtocolsDepsToolConfig.PytestConfig:
            """Pytest settings."""
            ...

        @property
        def tomlsort(self) -> FlextInfraProtocolsDepsToolConfig.TomlsortConfig:
            """Tomlsort settings."""
            ...

        @property
        def jscpd(self) -> FlextInfraProtocolsDepsToolConfig.JscpdToolConfig:
            """Jscpd clone-semantics passes."""
            ...

    @runtime_checkable
    class LazyInitConfig(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        import_layer_order: tuple[t.NonEmptyStr, ...]
        layer_aliases: Mapping[t.NonEmptyStr, t.NonEmptyStr]
        stdlib_backports: tuple[t.NonEmptyStr, ...]
        reverse_import_mode: Literal["type_checking"]
        forward_import_form: Literal["absolute"]

    @runtime_checkable
    class FacadeMembersConfig(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        owners: Mapping[c.Infra.FacadeMemberKind, t.NonEmptyStr]
        model_declaration_modules: tuple[t.NonEmptyStr, ...]
        type_constructor_modules: tuple[t.NonEmptyStr, ...]

    @runtime_checkable
    class SmellsConfig(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def fix_text(self) -> Mapping[t.NonEmptyStr, t.NonEmptyStr]:
            """Structural member projected from the owning model.

            Repair text appended to each qlty finding, keyed by the qlty check name
            (the SARIF ruleId suffix).
            """
            ...

        @property
        def enforce(self) -> Mapping[t.NonEmptyStr, t.Infra.EnforcementIds]:
            """Structural member projected from the owning model.

            qlty check name -> enforcement law ids the smells gate claims for that
            check; active only for a check with declared repair text.
            """
            ...

    @runtime_checkable
    class AccessorPolicyConfig(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def forbidden_prefixes(self) -> Mapping[t.NonEmptyStr, t.NonEmptyStr]:
            """Structural member projected from the owning model.

            Public method-name prefixes that declare an accessor, mapped to the
            domain-verb guidance that replaces them.
            """
            ...

    @runtime_checkable
    class ToolConfigDocument(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def settings(self) -> Mapping[t.NonEmptyStr, t.Infra.SettingsPairs]:
            """Structural member projected from the owning model.

            Native tool-table paths and ordered option pairs. Later pairs replace
            complete values without reordering arrays.
            """
            ...

        @property
        def derived_tool_roots(self) -> tuple[t.NonEmptyStr, ...]:
            """Structural member projected from the owning model.

            Native roots whose owner combines declared options with typed topology
            or execution policy.
            """
            ...

        @property
        def derived_settings(self) -> Mapping[t.NonEmptyStr, tuple[t.NonEmptyStr, ...]]:
            """Native keys owned by topology and execution policy."""
            ...

        @property
        def raw_check_receipt_suffix(self) -> t.NonEmptyStr:
            """Filename suffix for verbatim native check receipts."""
            ...

        @property
        def tools(self) -> FlextInfraProtocolsDepsToolConfig.ToolConfigTools:
            """Tools."""
            ...

        @property
        def lazy_init(self) -> FlextInfraProtocolsDepsToolConfig.LazyInitConfig:
            """Declarative lazy-init generation policy."""
            ...

        @property
        def facade_members(
            self,
        ) -> FlextInfraProtocolsDepsToolConfig.FacadeMembersConfig:
            """Declarative single-owner policy for facade members."""
            ...

        @property
        def smells(self) -> FlextInfraProtocolsDepsToolConfig.SmellsConfig:
            """Repair guidance for qlty smell findings."""
            ...

        @property
        def accessor_policy(
            self,
        ) -> FlextInfraProtocolsDepsToolConfig.AccessorPolicyConfig:
            """Accessor naming policy of the accessor migration."""
            ...

        @property
        def mod(self) -> FlextInfraProtocolsDepsToolConfig.ModConfig:
            """Declarative make-mod phase policy."""
            ...

    @runtime_checkable
    class ToolingInputs(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def document(self) -> FlextInfraProtocolsDepsToolConfig.ToolConfigDocument:
            """Validated project-specific tooling configuration."""
            ...

        @property
        def sources(self) -> tuple[p.Cli.AtomicFileState, ...]:
            """Captured canonical and project configuration layers."""
            ...

    @runtime_checkable
    class ToolingRuntimeContext(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def document(
            self,
        ) -> FlextInfraProtocolsDepsToolConfig.ToolConfigDocument | None:
            """The elected tooling policy shared by every render context."""
            ...

        project_kind: t.NonEmptyStr
        configuration: str
        tool_options: Mapping[str, t.JsonMapping]
        sources: tuple[p.Cli.AtomicFileState, ...]


__all__: list[str] = [
    "FlextInfraProtocolsDepsToolConfig",
]
