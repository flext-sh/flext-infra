"""Mise toolchain and beads configuration models."""

from __future__ import annotations

from fnmatch import fnmatchcase
from typing import Annotated, Literal, Self

from flext_cli import m, u

from flext_infra import t


class _ConfigContract(m.ContractModel):
    """Private declarative base for schema-loaded codegen records."""

    model_config = m.ConfigDict(
        strict=False, frozen=True, extra="forbid", str_strip_whitespace=False
    )


class FlextInfraModelsMiseToolchain:
    """Mise toolchain and beads configuration models."""

    class MiseToolSpec(_ConfigContract):
        """One mise backend declared in ``codegen.yaml``, projected to ``.mise.toml``.

        Override the YAML fields. Never edit ``.mise.toml``. Never pin a SHA.
        ``track: release`` always uses ``version: latest``. ``track: branch``
        requires ``branch`` (no default ``main``) and interpolates that name.
        """

        selector: Annotated[
            t.NonEmptyStr,
            m.Field(
                description=(
                    "Mise backend selector (github:/aqua:/npm:). Override "
                    "toolchain.<tool>.selector; never the .mise.toml key."
                )
            ),
        ]
        track: Annotated[
            Literal["release", "branch"],
            m.Field(
                description=(
                    "release = newest GitHub/registry release. branch = named "
                    "branch SHAs as they appear. Override toolchain.<tool>.track."
                )
            ),
        ] = "release"
        version: Annotated[
            Literal["latest"],
            m.Field(
                description=(
                    "Required when track=release; always latest, never a tag. "
                    "Override toolchain.<tool>.version."
                )
            ),
        ]
        prerelease: Annotated[
            bool,
            m.Field(
                description=(
                    "github backend: include prerelease tags in latest. "
                    "Override toolchain.<tool>.prerelease."
                )
            ),
        ] = False
        branch: Annotated[
            t.NonEmptyStr | None,
            m.Field(
                description=(
                    "Required when track=branch (e.g. 0.12.0-dev). No default "
                    "main. Override toolchain.<tool>.branch."
                )
            ),
        ] = None
        github_attestations: Annotated[
            bool,
            m.Field(
                description=(
                    "GitHub Artifact Attestations. Keep false so setup never "
                    "silently requires a GitHub credential. Override "
                    "toolchain.<tool>.github_attestations."
                )
            ),
        ] = False

        @u.model_validator(mode="after")
        def _validate_track(self) -> Self:
            """Fail closed: branch track names the branch; release forbids one."""
            if self.track == "branch":
                if self.branch is None:
                    msg = (
                        "track=branch requires branch in codegen.yaml (no default main)"
                    )
                    raise ValueError(msg)
            elif self.branch is not None:
                msg = "track=release forbids branch; use version: latest"
                raise ValueError(msg)
            return self

    ToolchainSpec = MiseToolSpec
    """Alias for the base mise toolchain specification."""

    class ProtectedMiseToolSpec(MiseToolSpec):
        """One fleet-owned mise distribution identity."""

        selector_patterns: Annotated[
            t.VariadicTuple[t.NonEmptyStr],
            m.Field(
                min_length=1,
                description="Glob patterns identifying equivalent mise distributions",
            ),
        ]

        @u.model_validator(mode="after")
        def _validate_distribution_patterns(self) -> Self:
            """Require one unambiguous pattern set covering the canonical selector."""
            if len(set(self.selector_patterns)) != len(self.selector_patterns):
                msg = "protected mise selector_patterns must be unique"
                raise ValueError(msg)
            if not any(
                fnmatchcase(self.selector, pattern)
                for pattern in self.selector_patterns
            ):
                msg = (
                    "canonical mise selector is not covered by selector_patterns: "
                    f"{self.selector}"
                )
                raise ValueError(msg)
            return self

    class BeadsEndpointSpec(_ConfigContract):
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

    class BeadsToolSpec(ProtectedMiseToolSpec):
        """Canonical Beads distribution and Gas City projection contract."""

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
                    "Rendered as dolt.mode in .beads/config.yaml. Change "
                    "toolchain.beads.dolt_mode; never the projection."
                )
            ),
        ]
        export_auto: Annotated[
            bool,
            m.Field(
                description=(
                    "Rendered as export.auto. Override toolchain.beads.export_auto."
                )
            ),
        ]
        backup_enabled: Annotated[
            bool,
            m.Field(
                description=(
                    "Rendered as backup.enabled. Override "
                    "toolchain.beads.backup_enabled."
                )
            ),
        ]
        dolt_disable_event_flush: Annotated[
            bool,
            m.Field(
                description=(
                    "Rendered as dolt.disable-event-flush. Override "
                    "toolchain.beads.dolt_disable_event_flush."
                )
            ),
        ]

        @u.model_validator(mode="after")
        def _validate_required_custom_types(self) -> Self:
            """Reject ambiguous duplicate type declarations at the owner."""
            if len(set(self.required_custom_types)) != len(self.required_custom_types):
                msg = "beads required_custom_types must be unique"
                raise ValueError(msg)
            return self

    class MiseBootstrapEnvironmentSpec(_ConfigContract):
        """Validated environment contract rendered into generated Mise setup."""

        storage_root_variable: Annotated[
            t.NonEmptyStr,
            m.Field(description="Required caller variable naming persistent storage"),
        ]
        fixed_environment: Annotated[
            t.VariadicTuple[t.Pair[str, str]],
            m.Field(min_length=1, description="Literal fail-closed Mise settings"),
        ]
        transient_environment: Annotated[
            t.VariadicTuple[t.Pair[t.NonEmptyStr, t.NonEmptyStr]],
            m.Field(min_length=1, description="Scratch-relative environment paths"),
        ]
        persistent_environment: Annotated[
            t.VariadicTuple[t.Pair[t.NonEmptyStr, t.NonEmptyStr]],
            m.Field(min_length=1, description="Storage-relative environment paths"),
        ]
        empty_files: Annotated[
            t.VariadicTuple[t.NonEmptyStr],
            m.Field(min_length=1, description="Scratch-relative empty policy files"),
        ]
        passthrough_environment: Annotated[
            t.VariadicTuple[t.NonEmptyStr],
            m.Field(min_length=1, description="Explicitly reinjected host variables"),
        ]

        @u.model_validator(mode="after")
        def _validate_environment_contract(self) -> Self:
            """Reject shell-unsafe, ambiguous, or escaping generated values."""
            groups = (
                self.fixed_environment,
                self.transient_environment,
                self.persistent_environment,
            )
            names = [name for group in groups for name, _ in group]
            names.extend(self.passthrough_environment)
            if len(names) != len(set(names)):
                msg = "Mise bootstrap environment variables must be globally unique"
                raise ValueError(msg)
            for name in names:
                normalized = name.replace("_", "A")
                if not normalized.isalnum() or name != name.upper():
                    msg = f"invalid Mise bootstrap environment variable: {name}"
                    raise ValueError(msg)
                persistent = dict(self.persistent_environment)
                if persistent.get(self.storage_root_variable) != ".":
                    msg = "Mise storage variable must own the persistent root"
                    raise ValueError(msg)
                for _name, value in self.fixed_environment:
                    if any(character in value for character in ("'", "\n", "\r", "\0")):
                        msg = "Mise fixed environment values must be literal-shell safe"
                        raise ValueError(msg)
                relative_paths = (
                    *(value for _, value in self.transient_environment),
                    *(value for _, value in self.persistent_environment),
                    *self.empty_files,
                )
                for path in relative_paths:
                    if path.startswith("/") or ".." in path:
                        msg = f"relative path must not be absolute or escape: {path}"
                        raise ValueError(msg)
            return self


__all__: list[str] = ["FlextInfraModelsMiseToolchain"]
