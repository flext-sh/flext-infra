"""Mise toolchain and beads configuration models.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import re
from pathlib import Path
from types import MappingProxyType
from typing import Annotated, Literal, Self

from flext_core import c, m

from flext_infra import t
from flext_infra._models.mise_toolchain_base import FlextInfraModelsMiseToolchainBase


class FlextInfraModelsMiseToolchain:
    """Mise toolchain and beads configuration models."""

    class UvOverridePackage(
        FlextInfraModelsMiseToolchainBase.SchemaRecord, strict=True
    ):
        """Native UV package selector for a scoped dependency override."""

        name: Annotated[
            t.StrictStr,
            m.Field(
                min_length=1, description="Package whose dependencies are replaced"
            ),
        ]
        version: Annotated[
            t.StrictStr | None,
            m.Field(
                min_length=1, description="Optional native package version selector"
            ),
        ] = None

        @m.model_validator(mode="after")
        def _validate_version(self) -> Self:
            if "version" in self.model_fields_set and self.version is None:
                msg = "scoped UV override version must be text when declared"
                raise ValueError(msg)
            return self

    class UvScopedOverride(FlextInfraModelsMiseToolchainBase.SchemaRecord, strict=True):
        """One native UV scoped override, never a global dependency override."""

        package: Annotated[
            FlextInfraModelsMiseToolchain.UvOverridePackage,
            m.Field(description="Package selector owning this override's scope"),
        ]
        dependencies: Annotated[
            t.ListOf[t.StrictStr],
            m.Field(
                description=(
                    "Native scoped registry requirements; other dependencies "
                    "remain unchanged"
                )
            ),
        ]

    class UvOverrideEntries(
        m.RootModel[t.ListOf[t.NonEmptyStr | UvScopedOverride]], strict=True
    ):
        """Native ordered global-string and scoped-table override grammar."""

    class BeadsToolSpec(FlextInfraModelsMiseToolchainBase.SchemaRecord):
        """Beads ledger and Gas City projection contract."""

        ownership_command_prefix: Annotated[
            t.VariadicTuple[t.NonEmptyStr],
            m.Field(
                min_length=1,
                description="Public ownership command projected into each repository",
            ),
        ]
        endpoint_origin: Annotated[
            Literal["inherited_city"],
            m.Field(description="Gas City-owned endpoint inheritance mode"),
        ]
        endpoint_status: Annotated[
            Literal["verified"],
            m.Field(description="Canonical status for a managed-city inherited rig"),
        ]
        required_custom_types: Annotated[
            t.VariadicTuple[t.NonEmptyStr],
            m.Field(
                min_length=1,
                description="Immutable custom bead types required by Gas City",
            ),
        ]
        dolt_mode: Annotated[
            t.NonEmptyStr,
            m.Field(
                description=(
                    "Rendered as dolt_mode in .beads/metadata.json and, for a "
                    "Gas City rig, as dolt.mode in .beads/config.yaml. Change "
                    "toolchain.beads.dolt_mode; never the projection."
                ),
            ),
        ]
        export_auto: Annotated[
            bool,
            m.Field(
                description=(
                    "Rendered as export.auto. Override toolchain.beads.export_auto."
                ),
            ),
        ]
        backup_enabled: Annotated[
            bool,
            m.Field(
                description=(
                    "Rendered as backup.enabled. Override "
                    "toolchain.beads.backup_enabled."
                ),
            ),
        ]
        dolt_disable_event_flush: Annotated[
            bool,
            m.Field(
                description=(
                    "Rendered for a Gas City rig as the nested "
                    "dolt: disable-event-flush switch gc reads. Override "
                    "toolchain.beads.dolt_disable_event_flush."
                ),
            ),
        ]

        @m.model_validator(mode="after")
        def _validate_required_custom_types(self) -> Self:
            """Reject ambiguous duplicate type declarations at the owner.

            Returns:
                The resulting ``Self``.

            Raises:
                ValueError: If beads required_custom_types must be unique.

            """
            if len(set(self.required_custom_types)) != len(self.required_custom_types):
                msg = "beads required_custom_types must be unique"
                raise ValueError(msg)
            return self

    class MiseToolVersionProbe(FlextInfraModelsMiseToolchainBase.SchemaRecord):
        """Declared command whose output proves the provisioned tool version.

        The setup reality proof resolves ``binary`` through ``mise which``,
        runs it with ``arguments``, and searches the output for ``pattern``
        with its single ``{version}`` placeholder replaced by the escaped
        mise.lock version. The probe is data; no tool has a default probe.
        """

        tool: Annotated[
            t.NonEmptyStr | None,
            m.Field(
                description=(
                    "Declared prerequisite tool key owning an external probe executable"
                )
            ),
        ] = None
        resources: Annotated[
            t.VariadicTuple[t.NonEmptyStr],
            m.Field(
                description=(
                    "Exact relative installed resources authenticated before an "
                    "external probe"
                )
            ),
        ] = ()
        binary: Annotated[
            t.NonEmptyStr,
            m.Field(description="Executable name resolved through `mise which`"),
        ]
        arguments: Annotated[
            t.VariadicTuple[t.NonEmptyStr],
            m.Field(description="Arguments that make the binary print its version"),
        ]
        pattern: Annotated[
            t.NonEmptyStr,
            m.Field(
                description=(
                    "Multiline regular expression the probe output must match; "
                    "exactly one `{version}` placeholder stands for the escaped "
                    "mise.lock version"
                ),
            ),
        ]
        environment: Annotated[
            t.StrMapping,
            m.Field(
                description=(
                    "Environment overrides the probe process receives; empty "
                    "for every tool whose version command prints only its "
                    "identity"
                ),
            ),
        ] = m.Field(default_factory=lambda: MappingProxyType[str, str]({}))

        @m.model_validator(mode="after")
        def _validate_pattern(self) -> Self:
            """Require one version placeholder and a compilable expression.

            Returns:
                The resulting ``Self``.

            Raises:
                ValueError: If the pattern carries no single placeholder.

            """
            placeholder = "{version}"
            if self.pattern.count(placeholder) != 1:
                msg = (
                    "version_probe.pattern must carry exactly one "
                    f"{placeholder} placeholder: {self.pattern}"
                )
                raise ValueError(msg)
            # A malformed expression raises re.PatternError unchanged here.
            re.compile(self.pattern.replace(placeholder, c.ParserBooleanToken.ZERO))
            if self.tool is not None and not self.resources:
                msg_0 = "external version probes require installed resources"
                raise ValueError(msg_0)
            for resource in self.resources:
                parts = resource.split("/")
                if any(
                    not part or part in {".", ".."} or "\\" in part or "\0" in part
                    for part in parts
                ):
                    msg_0 = "version probe resources require exact relative components"
                    raise ValueError(msg_0)
            return self

    class MiseHttpToolOptions(FlextInfraModelsMiseToolchainBase.SchemaRecord):
        """Native HTTP backend declarations, projected without URL inference."""

        url: Annotated[
            t.NonEmptyStr, m.Field(description="Native HTTP artifact URL template")
        ]
        version_list_url: Annotated[
            t.NonEmptyStr | None,
            m.Field(description="Authoritative native release-list URL"),
        ] = None
        version_json_path: Annotated[
            t.NonEmptyStr | None,
            m.Field(description="Native jq-like version extraction path"),
        ] = None
        version_regex: Annotated[
            t.NonEmptyStr | None,
            m.Field(description="Native release-list extraction regular expression"),
        ] = None
        version_expr: Annotated[
            t.NonEmptyStr | None, m.Field(description="Native release-list expression")
        ] = None
        version_order: Annotated[
            Literal["source", "semver"] | None,
            m.Field(description="Native ordering of discovered releases"),
        ] = None
        checksum: Annotated[
            t.NonEmptyStr | None, m.Field(description="Declared native artifact digest")
        ] = None
        checksum_url: Annotated[
            t.NonEmptyStr | None,
            m.Field(description="Authoritative published checksum URL"),
        ] = None
        checksum_expr: Annotated[
            t.NonEmptyStr | None,
            m.Field(description="Native checksum manifest expression"),
        ] = None
        format: Annotated[
            t.NonEmptyStr | None, m.Field(description="Native archive format")
        ] = None
        strip_components: Annotated[
            int | None, m.Field(ge=0, description="Native archive directory stripping")
        ] = None
        bin_path: Annotated[
            t.NonEmptyStr | None,
            m.Field(description="Native install-relative executable directory"),
        ] = None

    class MisePostinstallOptions(FlextInfraModelsMiseToolchainBase.SchemaRecord):
        """Native per-tool postinstall contract, including warm installation policy."""

        run: Annotated[t.NonEmptyStr, m.Field(description="Native postinstall command")]
        when: Annotated[
            Literal["always"] | None,
            m.Field(description="Run on every installation when explicitly declared"),
        ] = None

    class MiseToolEntry(FlextInfraModelsMiseToolchainBase.SchemaRecord):
        """One declarative fleet tool rendered into generated ``.mise.toml``.

        The entry table is the single toolchain surface: per-tool YAML keys,
        model fields, and template lines do not exist (ADR-005 s1 data-backed
        structures, ADR-018 p.10 deriving beats listing).
        """

        name: Annotated[
            t.NonEmptyStr,
            m.Field(
                description=(
                    "Tool identity; the [tools] key when no selector is declared"
                ),
            ),
        ]
        selector: Annotated[
            t.NonEmptyStr | None,
            m.Field(
                default=None,
                description=(
                    "Full Mise selector (aqua:, github:) rendered as the "
                    "[tools] key; the fleet toolchain has no npm: backend"
                ),
            ),
        ] = None
        version: Annotated[
            t.NonEmptyStr,
            m.Field(
                description=(
                    "Release selector: 'latest', a major.minor line, or an "
                    "exact released version; never a lock build identity"
                ),
            ),
        ]
        version_prefix: Annotated[
            t.NonEmptyStr | None,
            m.Field(
                default=None,
                description=(
                    "Release tag prefix keeping unrelated tags out of resolution"
                ),
            ),
        ] = None
        bin: Annotated[
            t.NonEmptyStr | None,
            m.Field(
                description="Native backend executable name for single-file artifacts"
            ),
        ] = None
        form: Annotated[
            Literal["scalar", "table"],
            m.Field(
                default="scalar",
                description=(
                    "Rendered [tools] shape; the projection byte contract. "
                    "scalar (default) is the bare assignment; table carries "
                    "native backend options"
                ),
            ),
        ] = "scalar"
        http: Annotated[
            FlextInfraModelsMiseToolchain.MiseHttpToolOptions | None,
            m.Field(
                description="Native HTTP backend options for a declared source artifact"
            ),
        ] = None
        depends: Annotated[
            t.VariadicTuple[t.NonEmptyStr],
            m.Field(description="Declared tool keys installed before this tool"),
        ] = ()
        install_env: Annotated[
            t.StrMapping,
            m.Field(
                description="Native installation environment, part of the tool identity"
            ),
        ] = m.Field(default_factory=lambda: MappingProxyType[str, str]({}))
        postinstall: Annotated[
            FlextInfraModelsMiseToolchain.MisePostinstallOptions | None,
            m.Field(
                description="Native source build or qualification after installation"
            ),
        ] = None
        lock_checksum: Annotated[
            bool,
            m.Field(
                default=True,
                description=(
                    "Whether the tool's current-platform mise.lock section "
                    "must carry a checksum; false only for a tool whose "
                    "upstream release metadata publishes none"
                ),
            ),
        ] = True
        version_probe: Annotated[
            FlextInfraModelsMiseToolchain.MiseToolVersionProbe,
            m.Field(
                description=(
                    "Command whose output proves the provisioned version in "
                    "the setup reality proof; every tool declares one"
                ),
            ),
        ]

    class MiseToolchainProofOptions(m.FrozenModel):
        """Validated immutable inputs for one native toolchain proof."""

        entry: Annotated[
            FlextInfraModelsMiseToolchain.MiseToolEntry,
            m.Field(description="Declared tool entry currently under proof."),
        ]
        lock: Annotated[
            t.JsonMapping,
            m.Field(description="Authenticated Mise lock mapping."),
        ]
        platform_name: Annotated[
            str,
            m.Field(description="Resolved platform identity of the running host."),
        ]
        mise_binary: Annotated[
            Path,
            m.Field(
                description="Managed Mise executable answering read-only queries.",
            ),
        ]
        declared: Annotated[
            t.SequenceOf[FlextInfraModelsMiseToolchain.MiseToolEntry],
            m.Field(
                description="All declared tool entries electable as probe owners.",
            ),
        ]
        proven: Annotated[
            frozenset[str],
            m.Field(description="Selectors already proven before this entry."),
        ]

    class ToolchainSpec(FlextInfraModelsMiseToolchainBase.SchemaRecord):
        """Language-runtime and native-tool versions shared by generated projects.

        Native tools use moving ``latest`` selectors; Python retains its
        required major.minor runtime line. Only ``make upg`` resolves the
        selectors and writes mise.lock; setup installs frozen from that lock.
        Python linters and type checkers remain owned by pyproject manifests.
        """

        python_version: Annotated[
            t.NonEmptyStr,
            m.Field(
                pattern=r"^[0-9]+\.[0-9]+(\.[0-9]+)?$",
                description=(
                    "Python toolchain line: major.minor ('3.13') or the full "
                    "install pin ('3.13.15') when the mise asset registry "
                    "requires it"
                ),
            ),
        ]
        dependency_cooldown_days: Annotated[
            int,
            m.Field(
                ge=1,
                description=(
                    "Supply-chain cooldown in days, the single value every "
                    "resolver honours: the generated mise minimum_release_age "
                    "and every dependabot ecosystem entry. Forks and local "
                    "projects (direct git references) are excluded."
                ),
            ),
        ]
        uv_link_mode: Annotated[
            t.NonEmptyStr,
            m.Field(description="Portable uv installation link mode"),
        ]
        uv_environments: Annotated[
            t.VariadicTuple[t.NonEmptyStr],
            m.Field(
                description=(
                    "Marker expressions limiting the environments uv resolves "
                    "for the generated lock. Empty resolves every environment."
                ),
            ),
        ] = ()
        uv_constraint_dependencies: Annotated[
            t.VariadicTuple[t.NonEmptyStr],
            m.Field(
                description=(
                    "PEP 508 constraints rendered into every generated "
                    "[tool.uv] constraint-dependencies from this SSOT. The "
                    "declared value replaces any retained value; empty "
                    "removes the key so no orphan cap survives without an "
                    "owner (operator directive 2026-09-08: artificial pins "
                    "are exterminated, never retained)."
                ),
            ),
        ] = ()
        uv_override_dependencies: Annotated[
            t.VariadicTuple[
                t.NonEmptyStr | FlextInfraModelsMiseToolchain.UvScopedOverride
            ],
            m.Field(
                description=(
                    "Native global or scoped overrides rendered into every generated "
                    "[tool.uv] override-dependencies from this SSOT. Declared "
                    "for consumers whose transitive dependency graph pins a "
                    "flext family member on a different integration ref than "
                    "the declared line: the override resolves the whole "
                    "family to one provider and ref. The declared value "
                    "replaces any retained value; empty removes the key."
                ),
            ),
        ] = ()
        environment_path_prepends: Annotated[
            t.VariadicTuple[t.NonEmptyStr],
            m.Field(
                default=(),
                description=(
                    "Extra directories the generated shell activation prepends "
                    "to PATH when they exist. Installation data expressed as "
                    "shell-expandable paths; empty by default so the engine "
                    "never names a specific tool installation."
                ),
            ),
        ] = ()
        mise_lockfile: Annotated[
            bool,
            m.Field(
                description=(
                    "Rendered as [settings] lockfile and bootstrap MISE_LOCKFILE. "
                    "Keep true: "
                    "make upg writes the committed mise.lock. "
                    "Override toolchain.mise_lockfile; never edit the projection."
                ),
            ),
        ] = True
        mise_disable_update_warning: Annotated[
            bool,
            m.Field(
                description=(
                    "Rendered as [settings] disable_update_warning. "
                    "The self-managed Mise release moves through make upg."
                ),
            ),
        ] = True
        mise_provenance_api_failures_fatal: Annotated[
            Literal[True],
            m.Field(
                description=(
                    "Rendered as [settings] provenance_api_failures_fatal. "
                    "API failures must remain fatal. Native attestation absence "
                    "is a distinct result, not an API-failure waiver."
                ),
            ),
        ] = True
        mise_locked_verify_provenance: Annotated[
            bool,
            m.Field(
                description=(
                    "Rendered as [settings] locked_verify_provenance. "
                    "Locked installation may consume the existing lock and "
                    "checksums without requerying provenance. Lock-time "
                    "provenance handling remains independent."
                ),
            ),
        ] = False
        mise_lockfile_platforms: Annotated[
            t.VariadicTuple[t.NonEmptyStr],
            m.Field(
                min_length=1,
                description=(
                    "Rendered as [settings] lockfile_platforms: the platforms "
                    "`make upg` resolves into mise.lock, with the current host "
                    "always included by mise. "
                    "Override toolchain.mise_lockfile_platforms."
                ),
            ),
        ]
        python_compile: Annotated[
            bool,
            m.Field(
                description=(
                    "Rendered as [settings.python] compile and bootstrap "
                    "MISE_PYTHON_COMPILE. False restricts Python resolution "
                    "and installation to precompiled builds. "
                    "Override toolchain.python_compile."
                ),
            ),
        ]
        tools: Annotated[
            t.VariadicTuple[FlextInfraModelsMiseToolchain.MiseToolEntry],
            m.Field(
                min_length=1,
                description=(
                    "Declarative fleet tool table rendered into generated "
                    ".mise.toml [tools]; entry order is the projection order. "
                    "Override toolchain.tools entries; never the projection"
                ),
            ),
        ]
        tool_version_pins: Annotated[
            t.MappingKV[t.NonEmptyStr, t.NonEmptyStr],
            m.Field(
                description=(
                    "Exact-version pins layered over the tools table by the "
                    "override files (dict keys deep-merge per tool); `latest` "
                    "re-resolves upstream and drifts from mise.lock between "
                    "upg runs, so overrides pin the versions mise.lock "
                    "resolves and `make upg` advances them deliberately"
                ),
            ),
        ]
        mise_selector: Annotated[
            t.NonEmptyStr,
            m.Field(
                description=(
                    "Mise backend selector rendered as the self-managed [tools] "
                    "entry: mise installs and pins itself through mise.lock. "
                    "Override toolchain.mise_selector."
                ),
            ),
        ]
        mise_version: Annotated[
            t.NonEmptyStr,
            m.Field(
                description=(
                    "Mise release rendered as the self-managed [tools] entry "
                    "version: 'latest', or a held release while upstream's "
                    "newest one is broken"
                ),
            ),
        ]
        beads: Annotated[
            FlextInfraModelsMiseToolchain.BeadsToolSpec,
            m.Field(description="Beads ledger projection (.beads config)"),
        ]

        @m.computed_field
        @property
        def python_required_version(self) -> str:
            """PEP 440 requirement spanning the configured Python minor line.

            Returns:
                The resulting ``str``.

            """
            major, minor = self.python_version.split(".")[:2]
            next_minor = int(minor) + 1
            return f">={self.python_version},<{major}.{next_minor}"

        @m.computed_field
        @property
        def python_selector(self) -> str:
            """Pyenv-style selector for the configured Python minor line.

            Returns:
                The resulting ``str``.

            """
            return self.python_version

        @m.computed_field
        @property
        def tool_versions(self) -> t.MappingKV[str, str]:
            """Effective release selector per tool: pins layered over entries.

            Returns:
                The resulting ``t.MappingKV[str, str]``.

            """
            return {
                entry.name: self.tool_version_pins.get(entry.name, entry.version)
                for entry in self.tools
            }

        @m.computed_field
        @property
        def tool_selectors(self) -> t.MappingKV[str, str]:
            """Declared Mise selector of every selector-bearing fleet tool.

            Returns:
                The resulting ``t.MappingKV[str, str]``.

            """
            return {
                entry.name: entry.selector
                for entry in self.tools
                if entry.selector is not None
            }

        @m.computed_field
        @property
        def tool_keys(self) -> t.MappingKV[str, str]:
            """The [tools] key (selector, else name) of every fleet tool.

            The same key names the tool's ``mise.lock`` table.

            Returns:
                The resulting ``t.MappingKV[str, str]``.

            """
            return {entry.name: entry.selector or entry.name for entry in self.tools}

        @m.computed_field
        @property
        def mise_install_keys(self) -> t.VariadicTuple[str]:
            """Every [tools] key the project declares, in projection order.

            ``make setup``/``make upg`` pass this explicit list to
            ``mise install`` so only the declared toolchain is provisioned,
            never a tool from the operator's global Mise registry.

            Returns:
                The resulting ``t.VariadicTuple[str]``.

            """
            return (
                "python",
                self.mise_selector,
                *(entry.selector or entry.name for entry in self.tools),
            )

        @m.computed_field
        @property
        def tool_version_prefixes(self) -> t.MappingKV[str, str]:
            """Declared release tag prefix of every prefix-bearing fleet tool.

            Returns:
                The resulting ``t.MappingKV[str, str]``.

            """
            return {
                entry.name: entry.version_prefix
                for entry in self.tools
                if entry.version_prefix is not None
            }

        @m.model_validator(mode="after")
        def _validate_version_selectors(self) -> Self:
            """Reject build-identity selectors mise/aube cannot resolve.

            A value like ``0.45.3~7a027ead`` is an aube lock build-identity
            directory name, not a published package version; aube rejects it
            ("no version ... matches range") and the whole toolchain lifecycle
            (make upg/gen/setup, and therefore CI) breaks. Only real selectors
            (``latest``, a major.minor line, or a released version) may reach
            the lock. Tool identities are unique and every non-scalar form
            carries the selector its projection renders as the [tools] key.

            Returns:
                The resulting ``Self``.

            Raises:
                ValueError: If ``offenders``, ``duplicate_names``, or ``keyless``.

            """
            offenders = (
                sorted(
                    f"tools[{entry.name}].version"
                    for entry in self.tools
                    if "~" in entry.version
                )
                + sorted(
                    f"tool_version_pins[{name}]"
                    for name, pinned in self.tool_version_pins.items()
                    if "~" in pinned
                )
                + sorted(
                    field
                    for field, value in self
                    if field.endswith("_version")
                    and isinstance(value, str)
                    and "~" in value
                )
            )
            if offenders:
                msg = (
                    "toolchain version selectors must be resolvable package "
                    "versions, not build identities: " + ", ".join(offenders)
                )
                raise ValueError(msg)
            unknown_pins = sorted(
                set(self.tool_version_pins) - {entry.name for entry in self.tools},
            )
            if unknown_pins:
                msg = "tool_version_pins must name declared tools: " + ", ".join(
                    unknown_pins,
                )
                raise ValueError(msg)
            duplicate_names = sorted(
                {
                    entry.name
                    for entry in self.tools
                    if [other.name for other in self.tools].count(entry.name) > 1
                },
            )
            if duplicate_names:
                msg = "toolchain tools must declare unique names: " + ", ".join(
                    duplicate_names,
                )
                raise ValueError(msg)
            declared_keys = {"python", self.mise_selector, *self.tool_keys.values()}
            undeclared_dependencies = sorted(
                f"{entry.name}:{dependency}"
                for entry in self.tools
                for dependency in entry.depends
                if dependency not in declared_keys
            )
            if undeclared_dependencies:
                msg = (
                    "tool installation dependencies must be declared tools: "
                    + ", ".join(undeclared_dependencies)
                )
                raise ValueError(msg)
            invalid_probes = sorted(
                entry.name
                for entry in self.tools
                if entry.version_probe.tool is not None
                and entry.version_probe.tool not in entry.depends
            )
            if invalid_probes:
                raise ValueError(
                    "external probe tools must be declared installation dependencies: "
                    + ", ".join(invalid_probes)
                )
            non_http = sorted(
                entry.name
                for entry in self.tools
                if entry.http is not None
                and not (entry.selector or entry.name).startswith("http:")
            )
            if non_http:
                msg = "HTTP options require native HTTP selectors: " + ", ".join(
                    non_http
                )
                raise ValueError(msg)
            npm_backed = sorted(
                entry.name
                for entry in self.tools
                if (entry.selector or entry.name).startswith("npm:")
            )
            if npm_backed:
                msg = (
                    "the fleet toolchain has no npm backend (ADR-025); "
                    "declare a checksum-locked native selector for: "
                    + ", ".join(npm_backed)
                )
                raise ValueError(msg)
            return self

    class BeadsEndpointSpec(FlextInfraModelsMiseToolchainBase.SchemaRecord):
        """Static network endpoint projected into Beads configuration."""

        host: Annotated[t.NonEmptyStr, m.Field(description="Beads server host")]
        port: Annotated[
            int,
            m.Field(
                ge=1,
                le=65535,
                description="Beads server TCP port declared by deployment",
            ),
        ]


__all__: list[str] = ["FlextInfraModelsMiseToolchain"]
