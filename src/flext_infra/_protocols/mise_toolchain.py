# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
src/flext_infra/_protocols/mise_toolchain
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Literal, Protocol, runtime_checkable

from flext_cli import FlextCliProtocols

from flext_infra._protocols import FlextInfraProtocolsMiseToolchainBase

if TYPE_CHECKING:
    from flext_infra import t


class FlextInfraProtocolsMiseToolchain:
    """Own the structural contracts declared by its model source."""

    @runtime_checkable
    class UvOverridePackage(
        FlextInfraProtocolsMiseToolchainBase.SchemaRecord, Protocol
    ):
        """Structural data contract projected from the owning model."""

        @property
        def name(self) -> t.StrictStr:
            """Package whose dependencies are replaced."""
            ...

        @property
        def version(self) -> t.StrictStr | None:
            """Optional native package version selector."""
            ...

    @runtime_checkable
    class UvScopedOverride(FlextInfraProtocolsMiseToolchainBase.SchemaRecord, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def package(self) -> FlextInfraProtocolsMiseToolchain.UvOverridePackage:
            """Package selector owning this override's scope."""
            ...

        @property
        def dependencies(self) -> list[t.StrictStr]:
            """Structural member projected from the owning model.

            Native scoped registry requirements; other dependencies remain
            unchanged.
            """
            ...

    @runtime_checkable
    class UvOverrideEntries(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def root(
            self,
        ) -> Sequence[
            t.NonEmptyStr | FlextInfraProtocolsMiseToolchain.UvScopedOverride
        ]:
            """Structural member projected from the owning model."""
            ...

    @runtime_checkable
    class BeadsToolSpec(FlextInfraProtocolsMiseToolchainBase.SchemaRecord, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def ownership_command_prefix(self) -> tuple[t.NonEmptyStr, ...]:
            """Public ownership command projected into each repository."""
            ...

        @property
        def endpoint_origin(self) -> Literal["inherited_city"]:
            """Gas City-owned endpoint inheritance mode."""
            ...

        @property
        def endpoint_status(self) -> Literal["verified"]:
            """Canonical status for a managed-city inherited rig."""
            ...

        @property
        def required_custom_types(self) -> tuple[t.NonEmptyStr, ...]:
            """Immutable custom bead types required by Gas City."""
            ...

        @property
        def dolt_mode(self) -> t.NonEmptyStr:
            """Structural member projected from the owning model.

            Rendered as dolt_mode in .beads/metadata.json and, for a Gas City rig,
            as dolt.mode in .beads/config.yaml. Change toolchain.beads.dolt_mode;
            never the projection.
            """
            ...

        @property
        def export_auto(self) -> bool:
            """Rendered as export.auto. Override toolchain.beads.export_auto."""
            ...

        @property
        def backup_enabled(self) -> bool:
            """Structural member projected from the owning model.

            Rendered as backup.enabled. Override toolchain.beads.backup_enabled.
            """
            ...

        @property
        def dolt_disable_event_flush(self) -> bool:
            """Structural member projected from the owning model.

            Rendered for a Gas City rig as the nested dolt: disable-event-flush
            switch gc reads. Override toolchain.beads.dolt_disable_event_flush.
            """
            ...

    @runtime_checkable
    class MiseToolVersionProbe(
        FlextInfraProtocolsMiseToolchainBase.SchemaRecord, Protocol
    ):
        """Structural data contract projected from the owning model."""

        @property
        def tool(self) -> t.NonEmptyStr | None:
            """Structural member projected from the owning model.

            Declared prerequisite tool key owning an external probe executable.
            """
            ...

        @property
        def resources(self) -> tuple[t.NonEmptyStr, ...]:
            """Structural member projected from the owning model.

            Exact relative installed resources authenticated before an external
            probe.
            """
            ...

        @property
        def binary(self) -> t.NonEmptyStr:
            """Executable name resolved through `mise which`."""
            ...

        @property
        def arguments(self) -> tuple[t.NonEmptyStr, ...]:
            """Arguments that make the binary print its version."""
            ...

        @property
        def pattern(self) -> t.NonEmptyStr:
            """Structural member projected from the owning model.

            Multiline regular expression the probe output must match; exactly one
            `{version}` placeholder stands for the escaped mise.lock version.
            """
            ...

        @property
        def environment(self) -> Mapping[str, str]:
            """Structural member projected from the owning model.

            Environment overrides the probe process receives; empty for every tool
            whose version command prints only its identity.
            """
            ...

    @runtime_checkable
    class MiseHttpToolOptions(
        FlextInfraProtocolsMiseToolchainBase.SchemaRecord, Protocol
    ):
        """Structural data contract projected from the owning model."""

        @property
        def url(self) -> t.NonEmptyStr:
            """Native HTTP artifact URL template."""
            ...

        @property
        def version_list_url(self) -> t.NonEmptyStr | None:
            """Authoritative native release-list URL."""
            ...

        @property
        def version_json_path(self) -> t.NonEmptyStr | None:
            """Native jq-like version extraction path."""
            ...

        @property
        def version_regex(self) -> t.NonEmptyStr | None:
            """Native release-list extraction regular expression."""
            ...

        @property
        def version_expr(self) -> t.NonEmptyStr | None:
            """Native release-list expression."""
            ...

        @property
        def version_order(self) -> Literal["source", "semver"] | None:
            """Native ordering of discovered releases."""
            ...

        @property
        def checksum(self) -> t.NonEmptyStr | None:
            """Declared native artifact digest."""
            ...

        @property
        def checksum_url(self) -> t.NonEmptyStr | None:
            """Authoritative published checksum URL."""
            ...

        @property
        def checksum_expr(self) -> t.NonEmptyStr | None:
            """Native checksum manifest expression."""
            ...

        @property
        def format(self) -> t.NonEmptyStr | None:
            """Native archive format."""
            ...

        @property
        def strip_components(self) -> int | None:
            """Native archive directory stripping."""
            ...

        @property
        def bin_path(self) -> t.NonEmptyStr | None:
            """Native install-relative executable directory."""
            ...

    @runtime_checkable
    class MisePostinstallOptions(
        FlextInfraProtocolsMiseToolchainBase.SchemaRecord, Protocol
    ):
        """Structural data contract projected from the owning model."""

        @property
        def run(self) -> t.NonEmptyStr:
            """Native postinstall command."""
            ...

        @property
        def when(self) -> Literal["always"] | None:
            """Run on every installation when explicitly declared."""
            ...

    @runtime_checkable
    class MiseToolEntry(FlextInfraProtocolsMiseToolchainBase.SchemaRecord, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def name(self) -> t.NonEmptyStr:
            """Tool identity; the [tools] key when no selector is declared."""
            ...

        @property
        def selector(self) -> t.NonEmptyStr | None:
            """Structural member projected from the owning model.

            Full Mise selector (aqua:, github:) rendered as the [tools] key; the
            fleet toolchain has no npm: backend.
            """
            ...

        @property
        def version(self) -> t.NonEmptyStr:
            """Structural member projected from the owning model.

            Release selector: 'latest', a major.minor line, or an exact released
            version; never a lock build identity.
            """
            ...

        @property
        def version_prefix(self) -> t.NonEmptyStr | None:
            """Release tag prefix keeping unrelated tags out of resolution."""
            ...

        @property
        def bin(self) -> t.NonEmptyStr | None:
            """Native backend executable name for single-file artifacts."""
            ...

        @property
        def form(self) -> Literal["scalar", "table"]:
            """Structural member projected from the owning model.

            Rendered [tools] shape; the projection byte contract. scalar (default)
            is the bare assignment; table carries native backend options.
            """
            ...

        @property
        def http(self) -> FlextInfraProtocolsMiseToolchain.MiseHttpToolOptions | None:
            """Native HTTP backend options for a declared source artifact."""
            ...

        @property
        def depends(self) -> tuple[t.NonEmptyStr, ...]:
            """Declared tool keys installed before this tool."""
            ...

        @property
        def install_env(self) -> Mapping[str, str]:
            """Native installation environment, part of the tool identity."""
            ...

        @property
        def postinstall(
            self,
        ) -> FlextInfraProtocolsMiseToolchain.MisePostinstallOptions | None:
            """Native source build or qualification after installation."""
            ...

        @property
        def lock_checksum(self) -> bool:
            """Structural member projected from the owning model.

            Whether the tool's current-platform mise.lock section must carry a
            checksum; false only for a tool whose upstream release metadata
            publishes none.
            """
            ...

        @property
        def version_probe(
            self,
        ) -> FlextInfraProtocolsMiseToolchain.MiseToolVersionProbe:
            """Structural member projected from the owning model.

            Command whose output proves the provisioned version in the setup reality
            proof; every tool declares one.
            """
            ...

    @runtime_checkable
    class MiseToolchainProofOptions(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def entry(self) -> FlextInfraProtocolsMiseToolchain.MiseToolEntry:
            """Declared tool entry currently under proof."""
            ...

        @property
        def lock(self) -> t.JsonMapping:
            """Authenticated Mise lock mapping."""
            ...

        @property
        def platform_name(self) -> str:
            """Resolved platform identity of the running host."""
            ...

        @property
        def mise_binary(self) -> Path:
            """Managed Mise executable answering read-only queries."""
            ...

        @property
        def declared(self) -> Sequence[FlextInfraProtocolsMiseToolchain.MiseToolEntry]:
            """All declared tool entries electable as probe owners."""
            ...

        @property
        def proven(self) -> frozenset[str]:
            """Selectors already proven before this entry."""
            ...

    @runtime_checkable
    class ToolchainUvSpec(FlextInfraProtocolsMiseToolchainBase.SchemaRecord, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def python_version(self) -> t.NonEmptyStr:
            """Structural member projected from the owning model.

            Python toolchain line: major.minor ('3.13') or the full install pin
            ('3.13.15') when the mise asset registry requires it.
            """
            ...

        @property
        def dependency_cooldown_days(self) -> int:
            """Structural member projected from the owning model.

            Supply-chain cooldown in days, the single value every resolver honours:
            the generated mise minimum_release_age, the [tool.uv] exclude-newer span
            and every dependabot ecosystem entry. Forks and local projects (direct
            git, URL and path sources) are outside it natively.
            """
            ...

        @property
        def dependency_cooldown_exceptions(
            self,
        ) -> Mapping[t.NonEmptyStr, t.NonEmptyStr]:
            """Structural member projected from the owning model.

            Registry packages released inside the cooldown on purpose, each mapped
            to its advisory id or critical-fix reason: rendered as [tool.uv]
            exclude-newer-package false and excluded from the dependabot pip
            cooldown. Repository config overlays add entries; remove one once the
            fixed release ages past the cooldown.
            """
            ...

        @property
        def uv_link_mode(self) -> t.NonEmptyStr:
            """Portable uv installation link mode."""
            ...

        @property
        def uv_environments(self) -> tuple[t.NonEmptyStr, ...]:
            """Structural member projected from the owning model.

            Marker expressions limiting the environments uv resolves for the
            generated lock. Empty resolves every environment.
            """
            ...

        @property
        def uv_constraint_dependencies(self) -> tuple[t.NonEmptyStr, ...]:
            """Structural member projected from the owning model.

            PEP 508 constraints rendered into every generated [tool.uv] constraint-
            dependencies from this SSOT. The declared value replaces any retained
            value; empty removes the key so no orphan cap survives without an owner
            (operator directive 2026-09-08: artificial pins are exterminated, never
            retained).
            """
            ...

        @property
        def editable_sources(self) -> Mapping[str, Path]:
            """Structural member projected from the owning model.

            Additional installed distributions bound to explicit local sources by
            make setup FLEXT; a relative source resolves against that FLEXT
            workspace; cannot conflict with it.
            """
            ...

        @property
        def uv_override_dependencies(
            self,
        ) -> tuple[
            t.NonEmptyStr | FlextInfraProtocolsMiseToolchain.UvScopedOverride, ...
        ]:
            """Structural member projected from the owning model.

            Native global or scoped overrides rendered into every generated
            [tool.uv] override-dependencies from this SSOT. Declared for consumers
            whose transitive dependency graph pins a flext family member on a
            different integration ref than the declared line: the override resolves
            the whole family to one provider and ref. The declared value replaces
            any retained value; empty removes the key.
            """
            ...

        @property
        def environment_path_prepends(self) -> tuple[t.NonEmptyStr, ...]:
            """Structural member projected from the owning model.

            Extra directories the generated shell activation prepends to PATH when
            they exist. Installation data expressed as shell-expandable paths; empty
            by default so the engine never names a specific tool installation.
            """
            ...

    @runtime_checkable
    class ToolchainSpec(ToolchainUvSpec, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def mise_lockfile(self) -> bool:
            """Structural member projected from the owning model.

            Rendered as [settings] lockfile and bootstrap MISE_LOCKFILE. Keep true:
            make upg writes the committed mise.lock. Override
            toolchain.mise_lockfile; never edit the projection.
            """
            ...

        @property
        def mise_activate_aggressive(self) -> bool:
            """Structural member projected from the owning model.

            Rendered as [settings] activate_aggressive. Keep project tool
            directories ahead of inherited host directories when Mise constructs the
            environment.
            """
            ...

        @property
        def mise_disable_update_warning(self) -> bool:
            """Structural member projected from the owning model.

            Rendered as [settings] disable_update_warning. The self-managed Mise
            release moves through make upg.
            """
            ...

        @property
        def mise_provenance_api_failures_fatal(self) -> Literal[True]:
            """Structural member projected from the owning model.

            Rendered as [settings] provenance_api_failures_fatal. API failures must
            remain fatal. Native attestation absence is a distinct result, not an
            API-failure waiver.
            """
            ...

        @property
        def mise_locked_verify_provenance(self) -> bool:
            """Structural member projected from the owning model.

            Rendered as [settings] locked_verify_provenance. Locked installation may
            consume the existing lock and checksums without requerying provenance.
            Lock-time provenance handling remains independent.
            """
            ...

        @property
        def mise_lockfile_platforms(self) -> tuple[t.NonEmptyStr, ...]:
            """Structural member projected from the owning model.

            Rendered as [settings] lockfile_platforms: the platforms `make upg`
            resolves into mise.lock, with the current host always included by mise.
            Override toolchain.mise_lockfile_platforms.
            """
            ...

        @property
        def python_compile(self) -> bool:
            """Structural member projected from the owning model.

            Rendered as [settings.python] compile and bootstrap MISE_PYTHON_COMPILE.
            False restricts Python resolution and installation to precompiled
            builds. Override toolchain.python_compile.
            """
            ...

        @property
        def tools(self) -> tuple[FlextInfraProtocolsMiseToolchain.MiseToolEntry, ...]:
            """Structural member projected from the owning model.

            Declarative fleet tool table rendered into generated .mise.toml [tools];
            entry order is the projection order. Override toolchain.tools entries;
            never the projection.
            """
            ...

        @property
        def tool_version_pins(self) -> Mapping[t.NonEmptyStr, t.NonEmptyStr]:
            """Structural member projected from the owning model.

            Exact-version pins layered over the tools table by the override files
            (dict keys deep-merge per tool); `latest` re-resolves upstream and
            drifts from mise.lock between upg runs, so overrides pin the versions
            mise.lock resolves and `make upg` advances them deliberately.
            """
            ...

        @property
        def mise_selector(self) -> t.NonEmptyStr:
            """Structural member projected from the owning model.

            Mise backend selector rendered as the self-managed [tools] entry: mise
            installs and pins itself through mise.lock. Override
            toolchain.mise_selector.
            """
            ...

        @property
        def mise_version(self) -> t.NonEmptyStr:
            """Structural member projected from the owning model.

            Mise release rendered as the self-managed [tools] entry version:
            'latest', or a held release while upstream's newest one is broken.
            """
            ...

        @property
        def beads(self) -> FlextInfraProtocolsMiseToolchain.BeadsToolSpec:
            """Beads ledger projection (.beads config)."""
            ...

        @property
        def python_required_version(self) -> str:
            """PEP 440 requirement spanning the configured Python minor line."""
            ...

        @property
        def python_selector(self) -> str:
            """Pyenv-style selector for the configured Python minor line."""
            ...

        @property
        def tool_versions(self) -> Mapping[str, str]:
            """Effective release selector per tool: pins layered over entries."""
            ...

        @property
        def tool_selectors(self) -> Mapping[str, str]:
            """Declared Mise selector of every selector-bearing fleet tool."""
            ...

        @property
        def tool_keys(self) -> Mapping[str, str]:
            """The [tools] key (selector, else name) of every fleet tool."""
            ...

        @property
        def mise_install_keys(self) -> tuple[str, ...]:
            """Every [tools] key the project declares, in projection order."""
            ...

    @runtime_checkable
    class BeadsEndpointSpec(
        FlextInfraProtocolsMiseToolchainBase.SchemaRecord, Protocol
    ):
        """Structural data contract projected from the owning model."""

        @property
        def host(self) -> t.NonEmptyStr:
            """Beads server host."""
            ...

        @property
        def port(self) -> int:
            """Beads server TCP port declared by deployment."""
            ...


__all__: list[str] = [
    "FlextInfraProtocolsMiseToolchain",
]
