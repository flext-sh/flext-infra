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

from flext_infra import c, t

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraProtocolsConfigRelease:
    """Own the structural contracts declared by its model source."""

    @runtime_checkable
    class ReleaseAutomationOverrideSpec(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def release_branch(self) -> t.NonEmptyStr | None: ...
        @property
        def build_command(self) -> t.NonEmptyStr | None: ...
        @property
        def version_variables(self) -> tuple[t.NonEmptyStr, ...]: ...

    @runtime_checkable
    class ReleaseAutomationSpec(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def tool(self) -> t.NonEmptyStr: ...
        @property
        def runner(self) -> t.NonEmptyStr: ...
        @property
        def commit_parser(self) -> t.NonEmptyStr: ...
        @property
        def release_branch(self) -> t.NonEmptyStr: ...
        @property
        def version_variables(self) -> tuple[t.NonEmptyStr, ...]: ...
        @property
        def version_toml(self) -> tuple[t.NonEmptyStr, ...]: ...
        @property
        def build_command(self) -> t.NonEmptyStr: ...
        @property
        def tag_format(self) -> t.NonEmptyStr: ...
        @property
        def changelog_file(self) -> t.NonEmptyStr: ...
        @property
        def overrides(
            self,
        ) -> Mapping[t.NonEmptyStr, p.Infra.ReleaseAutomationOverrideSpec]: ...

    @runtime_checkable
    class ReleasePolicySpec(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def publishable_prefixes(self) -> tuple[t.NonEmptyStr, ...]: ...
        @property
        def bump_types(self) -> Mapping[t.NonEmptyStr, c.Infra.VersionBump]: ...
        @property
        def maintenance_line(
            self,
        ) -> tuple[t.NonNegativeInt, t.NonNegativeInt] | None: ...
        @property
        def finalize_maintenance(self) -> bool: ...
        @property
        def publish_index(self) -> bool: ...
        @property
        def publish_url(self) -> t.NonEmptyStr: ...
        @property
        def build_constraints(self) -> tuple[p.Infra.BuildConstraintSpec, ...]: ...

    @runtime_checkable
    class BuildConstraintSpec(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def name(self) -> t.NonEmptyStr: ...
        @property
        def version(self) -> t.NonEmptyStr: ...
        @property
        def hashes(self) -> tuple[t.NonEmptyStr, ...]: ...

    @runtime_checkable
    class UvEnvironmentPlan(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def project_root(self) -> Path: ...
        @property
        def environment_root(self) -> Path: ...
        @property
        def python_version(self) -> t.NonEmptyStr: ...
        @property
        def groups(self) -> tuple[str, ...]: ...


__all__: list[str] = [
    "FlextInfraProtocolsConfigRelease",
]
