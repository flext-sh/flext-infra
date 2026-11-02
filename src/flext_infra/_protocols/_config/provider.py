# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
src/flext_infra/_protocols/_config/provider
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from flext_infra import c, t

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraProtocolsConfigProvider:
    """Own the structural contracts declared by its model source."""

    @runtime_checkable
    class ProviderIdentitySpec(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def name(self) -> t.NonEmptyStr: ...
        @property
        def organization(self) -> t.NonEmptyStr: ...
        @property
        def base_url(self) -> t.NonEmptyStr: ...

    @runtime_checkable
    class RepositorySourceSpec(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def distribution(self) -> t.NonEmptyStr: ...
        @property
        def provider(self) -> t.NonEmptyStr: ...
        @property
        def kind(self) -> c.Infra.ProjectKind: ...
        @property
        def internal_distribution_prefix(self) -> str: ...

    @runtime_checkable
    class BranchPolicySpec(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def lane_remote(self) -> t.NonEmptyStr: ...
        @property
        def lane_temporary_roots(self) -> tuple[Path, ...]: ...
        @property
        def lane_pr_limit(self) -> int: ...
        @property
        def lane_governance_file(self) -> Path | None: ...
        @property
        def ci_trigger_branches(self) -> tuple[t.NonEmptyStr, ...]: ...
        @property
        def preservation_ref_namespaces(self) -> tuple[t.NonEmptyStr, ...]: ...
        @property
        def integration_branch(self) -> t.NonEmptyStr: ...

    @runtime_checkable
    class GithubActionPinSpec(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def repository(self) -> t.NonEmptyStr: ...
        @property
        def version(self) -> t.NonEmptyStr: ...

    @runtime_checkable
    class CiPrivateSubmoduleDeployKeySpec(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def secret(self) -> t.NonEmptyStr: ...
        @property
        def submodule(self) -> t.NonEmptyStr: ...
        @property
        def path(self) -> t.NonEmptyStr: ...
        @property
        def remote(self) -> t.NonEmptyStr: ...

    @runtime_checkable
    class CiPrivateDependencyAuthSpec(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def app_id_secret(self) -> t.NonEmptyStr: ...
        @property
        def private_key_secret(self) -> t.NonEmptyStr: ...
        @property
        def repositories(self) -> tuple[t.NonEmptyStr, ...]: ...

    @runtime_checkable
    class CiSuperprojectCheckoutSpec(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def repository(self) -> t.NonEmptyStr: ...
        @property
        def ref(self) -> t.NonEmptyStr: ...
        @property
        def path(self) -> t.NonEmptyStr: ...

    @runtime_checkable
    class CiPrivateSubmodulesSpec(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def known_hosts(self) -> tuple[t.NonEmptyStr, ...]: ...
        @property
        def paths(self) -> tuple[t.NonEmptyStr, ...]: ...
        @property
        def deploy_keys(
            self,
        ) -> tuple[p.Infra.CiPrivateSubmoduleDeployKeySpec, ...]: ...


__all__: list[str] = [
    "FlextInfraProtocolsConfigProvider",
]
