# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
src/flext_infra/_protocols/_config/release
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from flext_infra._protocols._config import FlextInfraProtocolsConfigContract

if TYPE_CHECKING:
    from flext_infra import c, t


class FlextInfraProtocolsConfigRelease:
    """Own the structural contracts declared by its model source."""

    @runtime_checkable
    class ReleaseAutomationOverrideSpec(
        FlextInfraProtocolsConfigContract.ConfigContract, Protocol
    ):
        """Structural data contract projected from the owning model."""

        @property
        def release_branch(self) -> t.NonEmptyStr | None:
            """Branch that produces releases."""
            ...

        @property
        def build_command(self) -> t.NonEmptyStr | None:
            """Command that produces the artifacts."""
            ...

        @property
        def version_variables(self) -> tuple[t.NonEmptyStr, ...]:
            """Extra file:variable version anchors."""
            ...

    @runtime_checkable
    class ReleaseAutomationSpec(
        FlextInfraProtocolsConfigContract.ConfigContract, Protocol
    ):
        """Structural data contract projected from the owning model."""

        @property
        def tool(self) -> t.NonEmptyStr:
            """Release automation distribution."""
            ...

        @property
        def runner(self) -> t.NonEmptyStr:
            """Command runner that invokes the tool."""
            ...

        @property
        def commit_parser(self) -> t.NonEmptyStr:
            """Commit convention driving the bump."""
            ...

        @property
        def release_branch(self) -> t.NonEmptyStr:
            """Branch that produces releases."""
            ...

        @property
        def version_variables(self) -> tuple[t.NonEmptyStr, ...]:
            """file:variable anchors the tool rewrites."""
            ...

        @property
        def version_toml(self) -> tuple[t.NonEmptyStr, ...]:
            """file:tomlpath anchors the tool rewrites."""
            ...

        @property
        def build_command(self) -> t.NonEmptyStr:
            """Command that produces the artifacts."""
            ...

        @property
        def tag_format(self) -> t.NonEmptyStr:
            """Tag shape, shared with the workflow."""
            ...

        @property
        def changelog_file(self) -> t.NonEmptyStr:
            """Generated changelog destination."""
            ...

        @property
        def overrides(
            self,
        ) -> Mapping[
            t.NonEmptyStr,
            FlextInfraProtocolsConfigRelease.ReleaseAutomationOverrideSpec,
        ]:
            """Per-distribution deviations from the shared contract."""
            ...

    @runtime_checkable
    class ReleasePolicySpec(FlextInfraProtocolsConfigContract.ConfigContract, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def publishable_prefixes(self) -> tuple[t.NonEmptyStr, ...]:
            """Structural member projected from the owning model.

            Distribution-name prefixes eligible for build/publish. Empty means every
            resolved project is eligible.
            """
            ...

        @property
        def bump_types(self) -> Mapping[t.NonEmptyStr, c.Infra.VersionBump]:
            """Conventional Commits type -> semantic version bump."""
            ...

        @property
        def maintenance_line(self) -> tuple[t.NonNegativeInt, t.NonNegativeInt] | None:
            """Permitted major/minor release line; unset is unrestricted."""
            ...

        @property
        def finalize_maintenance(self) -> bool:
            """Structural member projected from the owning model.

            Finalize the declared maintenance line with a patch release instead of
            deriving a new major/minor line from commit titles.
            """
            ...

        @property
        def publish_index(self) -> bool:
            """Permit explicitly requested package index publication."""
            ...

        @property
        def publish_url(self) -> t.NonEmptyStr:
            """Package index upload endpoint for verified artifacts."""
            ...

        @property
        def build_constraints(
            self,
        ) -> tuple[FlextInfraProtocolsConfigRelease.BuildConstraintSpec, ...]:
            """Structural member projected from the owning model.

            Hash-pinned build-backend requirements every release artifact is built
            with; projected to config/build-constraints.txt.
            """
            ...

    @runtime_checkable
    class BuildConstraintSpec(
        FlextInfraProtocolsConfigContract.ConfigContract, Protocol
    ):
        """Structural data contract projected from the owning model."""

        @property
        def name(self) -> t.NonEmptyStr:
            """Distribution name."""
            ...

        @property
        def version(self) -> t.NonEmptyStr:
            """Exact version."""
            ...

        @property
        def hashes(self) -> tuple[t.NonEmptyStr, ...]:
            """Accepted sha256 digests."""
            ...

    @runtime_checkable
    class UvEnvironmentPlan(FlextInfraProtocolsConfigContract.ConfigContract, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def project_root(self) -> Path:
            """Selected project root."""
            ...

        @property
        def environment_root(self) -> Path:
            """Project supplying the active .venv."""
            ...

        @property
        def python_version(self) -> t.NonEmptyStr:
            """Mise/Python version selector."""
            ...

        @property
        def groups(self) -> tuple[str, ...]:
            """Ordered dependency groups synchronized by setup."""
            ...


__all__: list[str] = [
    "FlextInfraProtocolsConfigRelease",
]
